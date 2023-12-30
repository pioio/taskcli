import os

from taskcli import dispatch, task
from taskcli.include import include


@task
def child1() -> None:
    print("child1: " + os.getcwd())


@task(change_dir=False)
def child2() -> None:
    print("child2: " + os.getcwd())
