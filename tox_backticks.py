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

    return used


def _run_backtick(reader, venv, variable):
    setenv = venv.envconfig.setenv
    value = setenv.definitions[variable]
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
            ignore_ret=False,
        )
        action.setactivity('backticks', '{}={}'.format(variable, result))

    setenv.definitions[variable] = result
    setenv.resolved = {}

    return result


@hookimpl
def tox_runtest_pre(venv):
    """Post process config after parsing."""
    setenv = venv.envconfig.setenv

    backtick_variables = dict(
        (variable, _get_used_envvars(value))
        for variable, value in setenv.definitions.items()
        if len(value) > 2 and value.startswith('`') and value.endswith('`')
    )
    if not backtick_variables:
        return

    reader = setenv.reader

    while backtick_variables:
        if len(backtick_variables) == 1:
            variable = list(backtick_variables)[0]
            _run_backtick(reader, venv, variable)
            break

        unresolved = set(backtick_variables)
        resolved = [
            variable for variable, uses in backtick_variables.items()
            if not uses.intersection(unresolved)
        ]

        for variable in resolved:
            _run_backtick(reader, venv, variable)
            del backtick_variables[variable]

    venv.envconfig.commands = reader.getargvlist('commands')
    venv.envconfig.commands_pre = reader.getargvlist('commands_pre')
    venv.envconfig.commands_post = reader.getargvlist('commands_post')
