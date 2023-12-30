"""Entrypoint for the 'taskcli' command."""

import json
import logging
import os
import sys
import time


import taskcli.include

from . import envvars, task, taskfiledev, utils
from .parser import build_initial_parser
from .utils import print_err, print_error

from .logging import get_logger
log = get_logger(__name__)

import importlib.util

def main() -> None:  # noqa: C901
    """Entrypoint for the 'taskcli' command."""
    start = time.time()
    INVALID_TIME = -1.0

    try:
        import taskcli
    except ImportError:
        print("'taskcli' module is not installed, please install it with 'pip install taskcli'")  # noqa: T201
        sys.exit(1)

    parser = build_initial_parser()
    argv = sys.argv[1:]
    argconfig, _ = parser.parse_known_args(argv or sys.argv[1:])

    tasks_found = False
    import_took = INVALID_TIME
    include_took = INVALID_TIME

    already_loaded = set()


    def include_from_file(filename, namespace="", alias_namespace=""):
        log.separator(f"Importing objects from {filename}")

        absolute_filepath = os.path.abspath(filename)
        log.debug(f"Absolute filepath: {absolute_filepath}")

        dir = os.path.dirname(absolute_filepath)
        sys.path.append(dir)
        # import module by name
        basename = os.path.basename(absolute_filepath)
        start_import = time.time()


        module_name = basename.replace(".py", "").replace("-", "_")
        log.debug(f"Importing module: {module_name}")
        imported_module = __import__(module_name)

        nonlocal import_took
        import_took = time.time() - start_import

        log.separator(f"Including tasks from {filename}")
        already_loaded.add(filename)

        start_include = time.time() # FIXME: called for extra includes

        # This includes the tasks from 'sometasks' into THIS module (main)
        taskcli.include.include(imported_module, skip_include_info=True, namespace=namespace, alias_namespace=alias_namespace)
        nonlocal include_took, tasks_found
        include_took = time.time() - start_include
        tasks_found = True


    for filename in argconfig.file.split(","):
        filename = filename.strip()
        if os.path.exists(filename):
            include_from_file(filename)

    if not tasks_found:
        for filename in envvars.TASKCLI_EXTRA_TASKS_PY_FILENAMES.value.split(","):
            filename = filename.strip()
            if os.path.exists(filename):
                #include_from_file(filename, namespace=".", alias_namespace="..")
                include_from_file(filename)
                break # for now only one

    log.separator(f"Finished include and imports")
    # This part be right after importing the default ./task.p and before anything else
    # this way we allow ./tasks.py to change the default config, which in turn
    # might impact the output of get_argv()   (the default argument)
    argv = get_argv()

    this_module = sys.modules[__name__]
    taskfile_took = INVALID_TIME
    if taskfiledev.should_include_taskfile_dev(argv=argv):
        log.separator("Initializing go-task")
        start_taskfile = time.time()
        tasks_were_included = taskfiledev.include_tasks(to_module=this_module)
        if tasks_were_included:
            tasks_found = True
        taskfile_took = time.time() - start_taskfile

    dispatch_took = INVALID_TIME
    try:
        start_dispatch = time.time()
        log.separator("Dispatching tasks")
        taskcli.dispatch(argv=argv, tasks_found=tasks_found)
        dispatch_took = time.time() - start_dispatch
    finally:
        if envvars.TASKCLI_ADV_PRINT_RUNTIME.is_true():
            took = time.time() - start
            utils.print_stderr(f"Runtime: {took:.3f}s")
            if import_took != INVALID_TIME:
                utils.print_stderr(f"    Import: {import_took:.3f}s")

            if include_took != INVALID_TIME:
                utils.print_stderr(f"   Include: {include_took:.3f}s")

            if dispatch_took != INVALID_TIME:
                utils.print_stderr(f"  Dispatch: {dispatch_took:.3f}s")

            if taskfile_took != INVALID_TIME:
                utils.print_stderr(
                    f"  Taskfile: {taskfile_took:.3f}s (time to run the 'task' binary, "
                    f"{envvars.TASKCLI_GOTASK_TASK_BINARY_FILEPATH})"
                )


def get_argv() -> list[str]:
    """Return the command line arguments. Prefixed with default options if needed.

    There's a different set of default options for 't|taskcli' and 'tt' commands
    """
    from taskcli import tt

    if utils.is_basename_tt():
        # when calling with "tt"

        # Let's always add --show-hidden - more consistent behavior to users who forget to specify it
        # when customizing options.
        builtin_tt_options = ["--show-hidden"]
        argv = ["--show-hidden"] + tt.config.default_options_tt + sys.argv[1:]
        if tt.config.default_options_tt:
            log.debug(
                f"Using custom default options (tt): {tt.config.default_options_tt}, "
                f"plus the built-in options: {builtin_tt_options}"
            )
    else:
        # when calling with "t" or "taskcli"
        argv = tt.config.default_options + sys.argv[1:]
        if tt.config.default_options:
            log.debug(f"Using custom default options (taskcli): {tt.config.default_options}")
    return argv
