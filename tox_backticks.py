import itertools
import re

import pluggy
from tox.config import _ArgvlistReader, Replacer

hookimpl = pluggy.HookimplMarker('tox')


def _get_used_envvars(value):
    used = set()
    matches = re.finditer(Replacer.RE_ITEM_REF, value)
    for match in matches:
        g = match.groupdict()
        if g['sub_type'] != 'env':
            continue
        used.add(g['substitution_value'])
        if g['default_value']:
            used.update(_get_used_envvars(g['default_value']))

    return used


def _run_backtick(reader, venv, variable):
    setenv = venv.envconfig.setenv
    value = setenv.definitions[variable]
    # non-backtick values may also pass through here
    if not value.startswith('`') or not value.endswith('`'):
        return

    cmdstr = value[1:-1]

    argvlist = _ArgvlistReader.getargvlist(reader, cmdstr, replace=True)
    argv = argvlist[0]

    with venv.new_action('backticks', venv.envconfig.envdir) as action:
        result = venv._pcall(
            argv,
            cwd=venv.envconfig.changedir,
            action=action,
            redirect=True,
            returnout=True,
            ignore_ret=True,
        )
        action.setactivity('backticks', '{}={}'.format(variable, result))

    setenv.definitions[variable] = result
    setenv.resolved = {}

    return result


@hookimpl
def tox_runtest_pre(venv):
    """Post process config after parsing."""
    setenv = venv.envconfig.setenv

    # Invalid variable names are not our concern, but typically they
    # have a default value defined.
    valid_variable_names = set(setenv.definitions)

    backtick_variables = dict(
        (variable, _get_used_envvars(value) & valid_variable_names)
        for variable, value in setenv.definitions.items()
        if len(value) > 2 and value.startswith('`') and value.endswith('`')
    )
    if not backtick_variables:
        return

    reader = setenv.reader

    backtick_variables_keys = set(backtick_variables.keys())

    # Any non-backtick variable used in backticks to needs to be checked
    used_non_backtick_variables = any(
        uses - backtick_variables_keys for uses in backtick_variables.values()
    )

    if used_non_backtick_variables:
        # Load `uses` of all non-backtick variables
        non_backtick_variables = dict(
            (variable, _get_used_envvars(value) & valid_variable_names)
            for variable, value in setenv.definitions.items()
            if variable not in backtick_variables
        )

        # Walk back up chain of variables that refer to a backtick variable
        # and include them in the backtick variables
        unresolved = True
        while unresolved:
            keys = set(non_backtick_variables)

            unresolved = set([
                variable for variable, uses in non_backtick_variables.items()
                if uses - keys
            ])

            if unresolved:
                # Any variable that refers to a backtick variable needs to be
                # processed as a backtick variable, and other other non-backtick
                # variables need to be re-checked
                for variable in unresolved:
                    backtick_variables[variable] = non_backtick_variables[variable]
                    del non_backtick_variables[variable]
            else:
                # All remaining non_backtick_variables can be ignored
                for uses in backtick_variables.values():
                    uses -= keys

    while backtick_variables:

        resolved = set([
            variable for variable, uses in backtick_variables.items()
            if not uses
        ])

        for variable in resolved:
            _run_backtick(reader, venv, variable)
            del backtick_variables[variable]

        for uses in backtick_variables.values():
            uses -= resolved

    venv.envconfig.commands = reader.getargvlist('commands')
    venv.envconfig.commands_pre = reader.getargvlist('commands_pre')
    venv.envconfig.commands_post = reader.getargvlist('commands_post')
