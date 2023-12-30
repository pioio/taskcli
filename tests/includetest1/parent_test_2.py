#!/usr/bin/env python3
import dis
import os

import subdir.subsubdir.tasks as child_tasks2

from taskcli import dispatch, task
from taskcli.include import include

include(child_tasks2)


if __name__ == "__main__":
    child_tasks2.subsubchild()
    dispatch()
