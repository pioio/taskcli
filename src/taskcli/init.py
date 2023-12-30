import os
import sys


def create_tasks_file(filepath: str) -> None:
    """Create a new baisc tasks.py file."""
    if os.path.exists(filepath):
        print(f"File already exists: {filepath}")  # noqa: T201
        sys.exit(1)
    with open(filepath, "w") as f:
        f.write(content)

    if filepath == "tasks.py":
        print(f"Created file {filepath}, now run 'taskcli' or 'tt' to list task in it.")  # noqa: T201
    else:
        print(f"Created file {filepath}, now run 'taskcli -f {filepath}' or 'tt -f {filepath}' to list task in it.")  # noqa: T201


content = """#!/usr/bin/env python
from taskcli import task, run, tt

@task
def hello_world() -> None:
    print("Hello, World! Today is:")
    run("date")

@task
def say_hello(name:str, *, repeat:int=1) -> None:
    '''Usage: tt say-hello NAME [--repeat=REPEAT]'''
    for x in range(repeat):
        print(f"Hello, {name}")

with tt.Group("mygroup"):
    @task
    def sometask() -> None:
        print("Hello from the group")

if __name__ == "__main__":
    # This 'if' statements is optional.
    # It's here just in case you want to run this script directly via './tasks.py'
    tt.dispatch()
"""
