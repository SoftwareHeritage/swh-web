# flake8: noqa


def somefunc(param1="", param2=0):
    r"""A docstring"""
    if param1 > param2:  # interesting
        print("Gre'ater")
    return (param2 - param1 + 1) or None


class SomeClass:
    pass
