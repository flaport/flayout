# AUTOGENERATED! DO NOT EDIT! File to edit: source/02_cell.ipynb (unless otherwise specified).

__all__ = ['reference', 'copy_tree', 'add_cells_to_layout', 'add_pcells_to_layout']

# Internal Cell
import sys
from typing import Any, Dict, List, NamedTuple, Union

import flayout as fl
import pya


class DoesNotExist:
    pass

try:
    from gdspy import Cell as GdsPyCell
except ImportError:
    GdsPyCell = DoesNotExist

# Internal Cell
COPY_IMPLEMENTATIONS = {}
MAX_DEPTH = 2 * sys.getrecursionlimit()
ON_SAME_NAME_DOC = """what to do when the layout containing the destination cell
            already contains a cell with the same name. 'skip' (default): don't
            add the new child cell, use the one already present in the layout
            in stead. This will make the instances in the new cell point to the
            cell already in the layout.  'replace': replace the cell
            already present in the layout. This will make the instances in all
            cells alread present in the target cell's layout point to the newly
            added cell. 'add_suffix': add the new cell, but change its name by
            adding a suffix (this is the default behavior of KLayout's native
            cell.copy_tree method.)"""

# Internal Cell
class Reference(NamedTuple):
    cell: pya.Cell
    trans: pya.CplxTrans


class LibReference(NamedTuple):
    lib: pya.Library
    cell: pya.Cell
    trans: pya.CplxTrans


class PCellReference(NamedTuple):
    cell: pya.PCellDeclaration
    trans: pya.CplxTrans
    params: Dict


class PCellLibReference(NamedTuple):
    lib: pya.Library
    cell: pya.PCellDeclaration
    trans: pya.CplxTrans
    params: Dict

# Cell
def reference(*args) -> Union[Reference, LibReference, PCellReference, PCellLibReference]:
    """create a cell reference

    Note:
        this is not a native KLayout datastructure,
        but rather a convenience wrapper to ease the cell constructor API.

    Args:
        cell: the cell to create a reference for
        trans: the transformation to apply to the cell upon adding

    Returns:
        the cell reference
    """
    cell_str = _get_object_from_type(args, str)
    if cell_str is not None:
        num_dots = cell_str.count(".")
        if num_dots != 1:
            raise ValueError(
                "Reference to cell by string name should have format '<lib_name>.<cell_name>'."
            )
        lib_name, cell_name = cell_str.split(".")
        lib = pya.Library.library_by_name(lib_name)
        if lib is None:
            raise ValueError(
                f"Cannot use cell {cell_str!r}. Library {lib_name!r} does not exist (or is not registered)."
            )

        # search for pcell in library
        cell = lib.layout().pcell_declaration(cell_name)

        # search for normal cell in library
        if cell is None:
            try:
                cell_idx = lib.layout().cell_by_name(cell_name)
                cell = lib.layout().cell(cell_idx)
            except RuntimeError:
                raise ValueError(
                    f"Cannot use cell {cell_str!r}. Cell {cell_name!r} does not exist "
                    f"in library {lib_name!r}."
                )

        args = (
            arg
            for arg in args
            if not (str(arg) == cell_str or arg is cell or arg is lib)
        )
        return reference(cell, lib, *args)

    lib = _get_object_from_type(args, pya.Library)
    cell = _get_object_from_type(args, (pya.Cell, pya.PCellDeclaration))
    trans = _get_object_from_type(
        args,
        (pya.CplxTrans, pya.ICplxTrans, pya.DCplxTrans),
        default=pya.CplxTrans(1.0, 0.0, False, 0, 0),
    )

    if isinstance(cell, pya.Cell):
        if lib is None:
            return Reference(cell, trans)
        else:
            return LibReference(lib, cell, trans)
    elif isinstance(cell, pya.PCellDeclaration):
        params = _get_object_from_type(args, dict, default={})
        if lib is None:
            return PCellReference(cell, trans, params)
        else:
            return PCellLibReference(lib, cell, trans, params)
    else:
        raise ValueError(f"No cell found in reference tuple: {tuple(args)}.")

def _get_object_from_type(objs, cls, default=None):
    selected = [obj for obj in objs if isinstance(obj, cls)]
    if len(selected) > 1:
        raise ValueError(
            f"Only one argument of type {cls.__name__!r} expected. "
            f"Got: {', '.join(repr(s) for s in selected)}."
        )
    if not selected:
        return default
    return selected[0]

# Internal Cell
def _copy_klayout(source, dest, on_same_name, depth=0):
    if depth > MAX_DEPTH:
        return  # basically just to make type checker happy

    # if on_same_name == "add_suffix":
    #    return dest.copy_tree(source)
    #    # default klayout behavior. Not used because our implementation is
    #    # slightly different in the order cells are added

    dest_layout = dest.layout()
    source_layout = source.layout()
    for layer in source_layout.layer_infos():
        source_idx = source_layout.layer(layer)
        dest_idx = dest_layout.layer(layer)
        for shape in source.each_shape(source_idx):
            dest.shapes(dest_idx).insert(shape)

    source_cells_map = {}
    for idx in source.each_child_cell():
        current_cell = source_layout.cell(idx)
        source_cells_map[idx] = _add_cell_to_layout(
            dest_layout, current_cell, on_same_name, depth
        )

    for inst in source.each_inst():
        dest_ref = pya.CellInstArray(source_cells_map[inst.cell_index], inst.cplx_trans)
        dest.insert(dest_ref)

COPY_IMPLEMENTATIONS[pya.Cell] = _copy_klayout

# Internal Cell
def _copy_gdspy(source, dest, on_same_name, depth=0):
    if depth > MAX_DEPTH:
        return  # basically just to make type checker happy
    dest_layout = dest.layout()
    for lr, dt in source.get_layers():
        dest_idx = dest_layout.layer(pya.LayerInfo(lr, dt))
        for arr in source.get_polygons(by_spec=(lr, dt), depth=1):
            dest.shapes(dest_idx).insert(
                pya.DPolygon([pya.DPoint(x, y) for x, y in arr])
            )
        for arr in source.get_paths(depth=1):
            raise NotImplementedError("Cannot convert native gdspy paths (yet).")

    source_cells_map = {}
    child_cells = sorted(
        set(ref.ref_cell for ref in source.references), key=lambda c: c.name
    )
    for current_cell in child_cells:
        if on_same_name == "skip" and dest_layout.has_cell(current_cell.name):
            source_cells_map[current_cell.name] = dest_layout.cell_by_name(
                current_cell.name
            )
            continue
        elif on_same_name == "replace" and dest_layout.has_cell(current_cell.name):
            dest_layout.delete_cell(dest_layout.cell_by_name(current_cell.name))
        new_cell = dest_layout.create_cell(current_cell.name)
        _copy_gdspy(current_cell, new_cell, on_same_name, depth=depth + 1)
        new_cell._layout = dest_layout
        source_cells_map[current_cell.name] = dest_layout.cell_by_name(
            current_cell.name
        )

    for ref in source.references:
        dest_cell = source_cells_map[ref.ref_cell.name]
        mag = ref.magnification if ref.magnification is not None else 1.0
        rot = ref.rotation if ref.rotation is not None else 0.0
        x, y = ref.origin
        dest_trans = pya.CplxTrans(
            mag, rot, ref.x_reflection, int(1000.0 * x), int(1000.0 * y)
        )
        dest_ref = pya.CellInstArray(dest_cell, dest_trans)
        dest.insert(dest_ref)

if GdsPyCell is not DoesNotExist:
    COPY_IMPLEMENTATIONS[GdsPyCell] = _copy_gdspy

# Cell

def copy_tree(source: pya.Cell, dest: pya.Cell, on_same_name: str = "skip"):
    f"""Copy the contents of a cell into another cell

    Args:
        source: the source cell to copy the contents from
        dest: the destination cell to copy the contents into
        on_same_name: {ON_SAME_NAME_DOC}
    """
    on_same_name = _validate_on_same_name(on_same_name)
    for cls, _copy_impl in COPY_IMPLEMENTATIONS.items():
        if isinstance(source, cls):
            break
    else:
        raise TypeError(
            f"Error in copy_tree: source is not a supported cell type. "
            f"Got: {type(source)}. Expected: {', '.join(t.__name__ for t in COPY_IMPLEMENTATIONS)}."
        )

    _copy_impl(source, dest, on_same_name)
    return dest

def _validate_on_same_name(on_same_name):
    on_same_name = on_same_name.lower()
    allowed_on_same_name = ["skip", "replace", "add_suffix"]
    if not on_same_name in allowed_on_same_name:
        raise ValueError(
            "on_same_name should be one of the following: "
            f"{', '.join(repr(key) for key in allowed_on_same_name)}."
        )
    return on_same_name

# Cell
def add_cells_to_layout(
    layout: pya.Layout,
    cells: List[pya.Cell],
    on_same_name: str = "skip",
    depth: int = 0,
):
    f"""Add multiple cells to a layout

    Args:
        layout: The layout to add the cell into
        cells: the cells to add into the layout
        on_same_name: {ON_SAME_NAME_DOC}
    """
    cells = sorted(cells, key=lambda c: c.hierarchy_levels())
    for cell in cells:
        _add_cell_to_layout(layout, cell, on_same_name, depth)
    return layout

def _add_lib_cell_to_layout(layout: pya.Layout, lib: pya.Library, cell: pya.Cell):
    """Add a library Cell to a layout

    Args:
        layout: The layout to add the cell into
        lib: The library to which the cell belongs
        cell: the cell to add into the layout
    """
    pcell = cell.pcell_declaration()
    if pcell is not None:
        return _add_lib_pcell_to_layout(layout, lib, pcell, cell.pcell_parameters())
    else:
        cell_idx = lib.layout().cell_by_name(cell.name)
        return layout.add_lib_cell(lib, cell_idx)


def _add_cell_to_layout(
    layout: pya.Layout, cell: pya.Cell, on_same_name: str = "skip", depth: int = 0
):
    f"""Add a cell to a layout

    Args:
        layout: The layout to add the cell into
        cell: the cell to add into the layout
        on_same_name: {ON_SAME_NAME_DOC}
    """
    if cell.is_proxy():
        _add_lib_cell_to_layout(layout, cell.library(), cell)
    if on_same_name == "skip" and layout.has_cell(cell.name):
        return layout.cell_by_name(cell.name)
    elif on_same_name == "replace" and layout.has_cell(cell.name):
        layout.delete_cell(layout.cell_by_name(cell.name))
    new_cell = layout.create_cell(cell.name)
    _copy_klayout(cell, new_cell, on_same_name, depth=depth + 1)
    new_cell._layout = layout
    return layout.cell_by_name(new_cell.name)

# Cell

def add_pcells_to_layout(layout, pcells):
    for pcell in pcells:
        func = pcell
        while hasattr(func, "func"):
            func = func.func
        layout.register_pcell(func.__name__, pcell)

def _get_pcell_param_value(params, param):
    value = params.get(param.name, param.default)
    if param.type == pya.PCellDeclarationHelper.TypeLayer:
        if not isinstance(value, pya.LayerInfo):
            value = pya.LayerInfo(*value)
    return value

def _add_lib_pcell_to_layout(
    layout: pya.Layout,
    lib: pya.Library,
    pcell: pya.PCellDeclaration,
    params: Dict[str, Any],
):
    """Add a library PCell to a layout

    Args:
        layout: The layout to add the cell into
        lib: The library to which the cell belongs
        cell: the cell to add into the layout
        params: the parameters to instantiate the pcell with
    """
    if isinstance(params, dict):
        params_list = [
            _get_pcell_param_value(params, p) for p in pcell.get_parameters()
        ]
    else:
        params_list = params
    return layout.add_pcell_variant(lib, pcell.id(), params_list)