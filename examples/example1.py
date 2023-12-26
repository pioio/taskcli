#!/usr/bin/env python3

import logging

from taskcli import arg, runcommand, task

log = logging.getLogger(__name__)
logging = logging.basicConfig(level=logging.DEBUG)


@task()
def add_no_type(a, b):
    assert isinstance(a, str)
    assert isinstance(b, str)
    log.info(a + b)
    return a + b


@task
def add_typed_int(a: int, b: int):
    # no type, defaults to str
    assert isinstance(a, int)
    assert isinstance(b, int)
    log.info(a + b)
    return a + b


@task
def abool(a: bool = False):
    assert isinstance(a, bool)
    log.info(a)
    return a


@task
def alist(a: list[int]):
    assert isinstance(a, list)
    log.info(a)
    return a


# @task(required_env=["FOOBAR", "BAR"])
@task
@arg("a", type=int, help="a help example")
def add_with_def(a: int, b: int = 1):
    assert isinstance(a, int)
    assert isinstance(b, int)
    log.info(a + b)
    return a + b


if __name__ == "__main__":
    runcommand()
