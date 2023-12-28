import inspect
from math import e
from operator import is_
from typing import Any, TypeVar
from webbrowser import get

from . import annotations
from .utils import param_to_cli_option

# So that we don't duplicate the default value of arg annotation
default_arg_annotation = annotations.Arg()
import typing
from typing import get_origin, get_args, List, Union
from types import UnionType

class Parameter:
    """A wrapper around inspect.Parameter to make it easier to work with."""

    class Empty:
        """A class to represent an empty value."""

    POSITIONAL_ONLY = inspect.Parameter.POSITIONAL_ONLY
    POSITIONAL_OR_KEYWORD = inspect.Parameter.POSITIONAL_OR_KEYWORD
    KEYWORD_ONLY = inspect.Parameter.KEYWORD_ONLY
    VAR_POSITIONAL = inspect.Parameter.VAR_POSITIONAL
    VAR_KEYWORD = inspect.Parameter.VAR_KEYWORD


    def __init__(self, param: inspect.Parameter):
        """Read the parameter and stores the information in this class for easier access."""
        # original inspect.Parameter
        self.param: inspect.Parameter = param

        param_using_typing_annotated = getattr(param.annotation, "__metadata__", None) is not None

        # Metadata coming from typing.Annotated, empty list if not using it
        self.metadata: list[Any] = [] if not param_using_typing_annotated else param.annotation.__metadata__

        self.arg_annotation: annotations.Arg | None = None
        for data in self.metadata:
            if isinstance(data, annotations.Arg):
                self.arg_annotation = data
                break

        self.kind = param.kind
        assert self.kind in [
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.KEYWORD_ONLY,
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ]

        # type can come from three places
        # 1. The annotation  (foobar: int)
        # ### 2. The default value (foobar=5)
        # 3. The Arg annotation (foobar: annotations.Arg[int])
        # ### 4. The Arg annotation default (foobar: annotations.Arg[int, arg(default=5)])
        # If both are present, the annotation takes precedence
        self.type = param.annotation if not param_using_typing_annotated else param.annotation.__origin__



        if self.type is inspect.Parameter.empty:
            self.type = Parameter.Empty

        self.help: str | None = None
        for data in self.metadata:  # Find the help string in annotation
            if isinstance(data, str):
                self.help = data
                break

        # Default value is either in the in the signature (precedence), or
        # in the custom arg annotation (where it can be a shared default for many parameters)
        self.default: Any = Parameter.Empty
        if param.default is not inspect.Parameter.empty:
            self.default = param.default
        elif self.arg_annotation:
            if self.arg_annotation.default is not annotations.Empty:
                self.default = self.arg_annotation.default

        self.name = param.name

    def is_positional(self) -> bool:
        """Return True if the parameter is positional, False if it is keyword-only (i.e. requiring --flag)."""
        return self.kind in [
            inspect.Parameter.POSITIONAL_ONLY,
            inspect.Parameter.POSITIONAL_OR_KEYWORD,
            inspect.Parameter.VAR_KEYWORD, # ??? not sure ...
        ]

    @property
    def important(self) -> bool:
        """Return True if the parameter is marked as important."""
        return self.arg_annotation.important if self.arg_annotation else default_arg_annotation.important

    def has_default(self) -> bool:
        """Return True if the parameter has a default value."""
        return self.default is not Parameter.Empty

    def get_argparse_names(self) -> list[str]:
        """Return the names for argparse, in order of precedence."""
        # TODO: return single flag params also
        if self.is_positional():
            name = self.name.replace("_", "-")
        else:
            name = param_to_cli_option(self.name)
        return [name]



    def has_supported_type(self) -> bool:
        """Return True if the type of the parameter is supported by taskcli (in the context of adding it to argparse).

        If param has unsupported type, but a default value, the task can be still be run,
        but the parameter will not be added to argparse.
        """
        if self.type is Parameter.Empty:
            # no type annotation, will assume it's a string
            return True

        if self.is_union_list_none():
            return True

        if self.is_list():
            type_of_list = self.get_list_type_args()
            if type_of_list in [int, float, str]:
                return True
            elif type_of_list is None:
                return True
            else:
                return False

        if self.type in [int, float, str, bool]:
            return True

        return False

    def is_union_list_none(self) -> bool:
        if self.type is inspect.Parameter.empty:
            return False

        if self.is_union_of(list, None.__class__):
            return True

        if self.is_union():
            union_args = get_args(self.type)
            if len(union_args) == 2:

                foundlist = False
                foundnone = False
                for arg in union_args:
                    if get_origin(arg) is list:
                        foundlist = True
                    if arg is None.__class__:
                        foundnone = True
                if foundlist and foundnone:
                    return True

        return False

    def is_union(self) -> bool:
        #   'get_origin(self.annotation) is Union'  ->   python 3.9 syntax, Union[list|None]
        # 'isinstance(self.annotation, UnionType)'  ->   python 3.10 syntax,  list|None
        return get_origin(self.type) is Union or isinstance(self.type, UnionType)

    def is_union_of(self, typevar1, typevar2): # "None.__class__" for non
        assert typevar1 is not None, "use   None.__class__ for None"
        assert typevar2 is not None, "use   None.__class__ for None"
        if not self.is_union():
            return False
        if get_args(self.type) == (typevar1, typevar2) or get_args(self.type) == (typevar2, typevar1):
            return True
        return False

    def is_bool(self) -> bool:
        if self.type is bool:
            # type set explicitly
            return True
        if self.type == Parameter.Empty and self.has_default() and isinstance(self.default, bool):
            # Type set implicitly via the default value
            return True
        return False

    def is_list(self) -> bool:
        if self.is_union():
            return False

        annotation = self.type
        if get_origin(annotation) is list:
            return True
        if annotation is list:
            return True

        return False

    def get_the_list_type(self) -> Any:
        """Return the type of the list, or raise if not a list.

        If the annotation is a list or list[X], it simpl returns that.
        If the type is a list[x]|None, it returns the list part from that union.
        """
        if self.is_list():
            return self.type
        elif self.is_union_list_none():
            return self.get_list_from_union()
        else:
            msg = "Not a list"
            raise Exception(msg)

    def list_has_type_args(self) -> bool:
        """Can be called on x:list nad x:list|None."""
        listtype = self.get_the_list_type()

        list_arg_types = get_args(listtype)

        if list_arg_types is None:
            return False

        if len(list_arg_types) == 1:
            return True

        return False

    def get_list_from_union(self) -> Any:
        """Return the list type from a union of list and None."""
        assert self.is_union_list_none()
        union_args = get_args(self.type)
        assert len(union_args) == 2
        for arg in union_args:
            if get_origin(arg) is list:
                return arg

    def get_list_type_args(self) -> None|Any:
        """Return the type arguments of the list annotation, or None if there are none."""
        listtypevar = self.get_the_list_type()

        list_arg_types = get_args(listtypevar)
        if list_arg_types is None:
            return None
        assert isinstance(list_arg_types, tuple)
        if len(list_arg_types) == 0:
            return None
        assert len(list_arg_types) == 1, f"list_arg_types: {list_arg_types}"
        return list_arg_types[0]
