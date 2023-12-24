import re
import sys
import typing

import taskcli

from . import configuration

if typing.TYPE_CHECKING:
    from taskcli.taskcli import TaskCLI

    from .decoratedfunction import Task


ENDC = configuration.get_end_color()
UNDERLINE = configuration.get_underline()


def strip_escape_codes(s: str) -> str:
    """Remove ANSI escape codes from a string. So, removes colors, underlines, etc."""
    return re.sub(r"\033\[[0-9;]*m", "", s).replace(ENDC, "").replace(UNDERLINE, "")


def param_to_cli_option(arg: str) -> str:
    """Convert foo_bar to --foo-bar, and g to -g."""
    if len(arg) == 1:
        return "-" + arg.replace("_", "-")
    else:
        return "--" + arg.replace("_", "-")


def reset_tasks():
    """Clear the list of tasks."""
    # clear included tasks
    taskcli.utils.get_runtime().tasks = []

    # clear tasks in each module
    for module in sys.modules.values():
        if hasattr(module, "decorated_functions"):
            module.decorated_functions = []  # type: ignore


def get_tasks() -> list["Task"]:
    """Return the list of tasks."""
    return taskcli.utils.get_runtime().tasks


def get_root_module() -> str:
    """Return the name of the module of the runtime."""
    return sys.modules["__main__"].__name__


def get_runtime() -> "TaskCLI":
    """Return the TaskCLI runtime."""
    return taskcli.core.task_cli
