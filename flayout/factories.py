# AUTOGENERATED! DO NOT EDIT! File to edit: source/04_factories.ipynb (unless otherwise specified).

__all__ = ['Point', 'Points', 'Shape', 'layer', 'point', 'vector', 'polygon', 'polygon', 'polygon', 'path']

# Internal Cell
import sys
from typing import Any, Dict, List, NamedTuple, Optional, Tuple, Union, overload

import flayout as fl
import numpy as np
import pya

from .cell import (
    LibReference,
    PCellLibReference,
    PCellReference,
    Reference,
    add_cell_to_layout,
    add_cells_to_layout,
    add_lib_cell_to_layout,
    add_lib_pcell_to_layout,
    add_pcells_to_layout,
    reference,
)

# Cell
Point = Union[pya.DPoint, Tuple[int, int], Tuple[float, float]]
Points = Union[List[Point], np.ndarray]

# Cell
Shape = Union[pya.DBox, pya.DSimplePolygon, pya.DPolygon, pya.DPath, pya.Box, pya.SimplePolygon, pya.Polygon, pya.Path, np.ndarray]

# Cell
def layer(lr: int, dt: int, name: str = "") -> pya.LayerInfo:
    layer = pya.LayerInfo(int(lr), int(dt))
    if name:
        layer.name = name
    return layer

# Cell
def point(x: Union[float, int], y: Union[float, int]) -> pya.DPoint:
    """create a KLayout DPoint

    Args:
        x: the x-value of the point
        y: the y-value of the point

    Returns:
        the point
    """
    return pya.DPoint(float(x), float(y))

# Cell
def vector(x: Union[float, int], y: Union[float, int]) -> pya.DVector:
    """create a KLayout DVector

    Args:
        x: the x-value of the vector
        y: the y-value of the vector

    Returns:
        the vector
    """
    return pya.DVector(float(x), float(y))

# Cell
@overload
def polygon(
    hull: Points,
    *,
    holes: None = None,
    raw: bool = False,
) -> pya.DSimplePolygon:
    ...


@overload
def polygon(
    hull: Points,
    *,
    holes: List[Points] = None,
    raw: bool = False,
) -> pya.DPolygon:
    ...


def polygon(
    hull: Points,
    *,
    holes: Optional[List[Points]] = None,
    raw: bool = False,
) -> Union[pya.DSimplePolygon, pya.DPolygon]:
    """create a KLayout polygon

    Args:
        hull: the points that make the polygon hull
        holes: the collection of points that make the polygon holes
        raw: if true, the points won't be compressed.

    Returns:
        the polygon
    """
    hull = [(p if isinstance(p, (pya.Point, pya.DPoint)) else point(*p)) for p in hull]
    if holes is None:
        poly = pya.DSimplePolygon(hull, raw)
    else:
        poly = pya.DPolygon(hull, raw)
        for hole in holes:
            hole = [(p if isinstance(p, pya.DPoint) else point(*p)) for p in hole]
            poly.insert_hole(hole)
    return poly

# Cell
def path(
    pts: Points,
    width: float,
    *,
    bgn_ext: float = 0.0,
    end_ext: float = 0.0,
    round: bool = False,
) -> pya.DPath:
    """create a KLayout path

    Args:
        pts: the points that make the path
        width: the width of the path
        bgn_ext: the begin extension of the path
        end_ext: the end extension of the path
        round: round the ends of the path

    Returns:
        the path
    """
    pts = [(p if isinstance(p, (pya.Point, pya.DPoint)) else point(*p)) for p in pts]
    print(pts)
    return pya.DPath(pts, width, bgn_ext, end_ext, round)