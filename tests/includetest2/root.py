import os

from taskcli import dispatch, include, task


@task
def roottask() -> None:
    from subdir.subsubdir import tasks as subsubtasks

    cwd = os.getcwd()
    print(cwd)
    subsubtasks.subsub_function()
    subsubtasks.subsub_task()


if __name__ == "__main__":
    dispatch()