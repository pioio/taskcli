#!/usr/bin/env python3

import os

# add ../../ to sys
import sys

from taskcli import dispatch, include, task

sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))

import root as root_tasks  # isort:skip # noqa: E402

include(root_tasks)


def subsub_function():
    # called from root
    cwd = os.getcwd()
    print("subsub_function", cwd)


@task
def subsub_task():
    # called from root
    cwd = os.getcwd()
    print("subsub_task", cwd)


if __name__ == "__main__":
    dispatch()