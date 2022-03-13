# AUTOGENERATED! DO NOT EDIT! File to edit: source/03_pcell.ipynb (unless otherwise specified).

__all__ = ['pcell']

# Internal Cell
from functools import partial
from inspect import Parameter, Signature, signature
from typing import Callable

import pya
from .cell import copy_tree

CELL_CONVERTERS = {}

# Internal Cell
def _klayout_type(param: Parameter):
    type_map = {
        pya.PCellDeclarationHelper.TypeInt: pya.PCellDeclarationHelper.TypeInt,
        "TypeInt": pya.PCellDeclarationHelper.TypeInt,
        "int": pya.PCellDeclarationHelper.TypeInt,
        int: pya.PCellDeclarationHelper.TypeInt,
        pya.PCellDeclarationHelper.TypeDouble: pya.PCellDeclarationHelper.TypeDouble,
        "TypeDouble": pya.PCellDeclarationHelper.TypeDouble,
        "float": pya.PCellDeclarationHelper.TypeDouble,
        float: pya.PCellDeclarationHelper.TypeDouble,
        pya.PCellDeclarationHelper.TypeString: pya.PCellDeclarationHelper.TypeString,
        "TypeString": pya.PCellDeclarationHelper.TypeString,
        "str": pya.PCellDeclarationHelper.TypeString,
        str: pya.PCellDeclarationHelper.TypeString,
        pya.PCellDeclarationHelper.TypeBoolean: pya.PCellDeclarationHelper.TypeBoolean,
        "TypeBoolean": pya.PCellDeclarationHelper.TypeBoolean,
        "bool": pya.PCellDeclarationHelper.TypeBoolean,
        bool: pya.PCellDeclarationHelper.TypeBoolean,
        pya.PCellDeclarationHelper.TypeLayer: pya.PCellDeclarationHelper.TypeLayer,
        "TypeLayer": pya.PCellDeclarationHelper.TypeLayer,
        "LayerInfo": pya.PCellDeclarationHelper.TypeLayer,
        pya.LayerInfo: pya.PCellDeclarationHelper.TypeLayer,
        pya.PCellDeclarationHelper.TypeShape: pya.PCellDeclarationHelper.TypeShape,
        "TypeShape": pya.PCellDeclarationHelper.TypeShape,
        "Shape": pya.PCellDeclarationHelper.TypeShape,
        pya.Shape: pya.PCellDeclarationHelper.TypeShape,
        pya.PCellDeclarationHelper.TypeList: pya.PCellDeclarationHelper.TypeList,
        "TypeList": pya.PCellDeclarationHelper.TypeList,
        "list": pya.PCellDeclarationHelper.TypeList,
        list: pya.PCellDeclarationHelper.TypeList,
    }
    try:
        annotation = param.annotation
        if annotation is Parameter.empty:
            annotation = type(param.default)
    except AttributeError:
        annotation = param
    if not annotation in type_map:
        raise ValueError(
            f"Cannot create pcell. Parameter {param.name!r} has unsupported type: {annotation!r}"
        )
    return type_map[annotation]

# Internal Cell
def _python_type(param: Parameter):
    type_map = {
        pya.PCellDeclarationHelper.TypeInt: int,
        "TypeInt": int,
        "int": int,
        int: int,
        pya.PCellDeclarationHelper.TypeDouble: float,
        "TypeDouble": float,
        "float": float,
        float: float,
        pya.PCellDeclarationHelper.TypeString: str,
        "TypeString": str,
        "str": str,
        str: str,
        pya.PCellDeclarationHelper.TypeBoolean: bool,
        "TypeBoolean": bool,
        "bool": bool,
        bool: bool,
        pya.PCellDeclarationHelper.TypeLayer: pya.LayerInfo,
        "TypeLayer": pya.LayerInfo,
        "LayerInfo": pya.LayerInfo,
        pya.LayerInfo: pya.LayerInfo,
        pya.PCellDeclarationHelper.TypeShape: pya.Shape,
        "TypeShape": pya.Shape,
        "Shape": pya.Shape,
        pya.Shape: pya.Shape,
        pya.PCellDeclarationHelper.TypeList: list,
        "TypeList": list,
        "list": list,
        list: list,
    }
    try:
        annotation = param.annotation
        if annotation is Parameter.empty:
            annotation = type(param.default)
    except AttributeError:
        annotation = param
    if not annotation in type_map:
        raise ValueError(
            f"Cannot create pcell. Parameter {param.name!r} has unsupported type: {annotation!r}"
        )
    return type_map[annotation]

# Internal Cell

def _validate_on_error(on_error):
    on_error = on_error.lower()
    if not on_error in ["raise", "ignore"]:
        raise ValueError("on_error should be 'raise' or 'ignore'.")
    return on_error

def _validate_parameter(name, param):
    if param.kind == Parameter.VAR_POSITIONAL:
        raise ValueError(
            f"Cannot create pcell from functions with var positional [*args] arguments."
        )
    elif param.kind == Parameter.VAR_KEYWORD:
        raise ValueError(
            f"Cannot create pcell from functions with var keyword [**kwargs] arguments."
        )
    elif param.kind == Parameter.POSITIONAL_ONLY:
        raise ValueError(
            f"Cannot create pcell from functions with positional arguments. Please use keyword arguments."
        )
    elif (param.kind == Parameter.POSITIONAL_OR_KEYWORD) and (param.default is Parameter.empty):
        raise ValueError(
            f"Cannot create pcell from functions with positional arguments. Please use keyword arguments."
        )
    return Parameter(
        name,
        kind=Parameter.KEYWORD_ONLY,
        default=param.default,
        annotation=_python_type(_klayout_type(_python_type(param))),
    )

def _pcell_parameters(func: Callable, on_error="raise"):
    sig = signature(func)
    params = sig.parameters
    on_error = _validate_on_error(on_error)
    new_params = {
        "name": Parameter(
            "name", kind=Parameter.KEYWORD_ONLY, default=func.__name__, annotation=str
        )
    }
    for name, param in params.items():
        try:
            new_params[name] = _validate_parameter(name, param)
        except ValueError:
            if on_error == "raise":
                raise
    return new_params

# Cell

def pcell(func=None, on_error="raise"):
    """create a KLayout PCell from a native python function

    Args:
        func: the function creating a KLayout cell

    Returns:
        the Klayout PCell
    """
    if func is None:
        return partial(pcell, on_error=on_error)

    params = _pcell_parameters(func, on_error=on_error)


    def init(self):
        pya.PCellDeclarationHelper.__init__(self)
        for name, param in params.items():
            self.param(
                name,
                _klayout_type(param),
                name.replace("_", " "),
                default=param.default,
            )
        self.func = func
        self.names = tuple(params)

    def call(self, **kwargs):
        name = kwargs.pop("name", func.__name__)
        keys = signature(self.func).parameters
        if name in keys:
            obj = self.func(**kwargs)
        else:
            obj = self.func(**kwargs, name=name)
        obj.name = name
        return obj

    def produce_impl(self):
        kwargs = {name: getattr(self, name) for name in self.names}
        cell = self(**kwargs)
        copy_tree(cell, self.cell, on_same_name="replace")

    def display_text_impl(self):
        return f"{self.name}<{self.__class__.__name__}>"

    DynamicPCell = type(
        func.__name__,
        (pya.PCellDeclarationHelper,),
        {
            "__init__": init,
            "__call__": call,
            "__doc__": func.__doc__
            if func.__doc__ is not None
            else f"a {func.__name__} PCell.",
            "produce_impl": produce_impl,
            "display_text_impl": display_text_impl,
        },
    )
    pcell = DynamicPCell()
    pcell.__signature__ = Signature(list(params.values()), return_annotation=pya.Cell)
    pcell.name = func.__name__
    return pcell