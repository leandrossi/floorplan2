from acala_engine import CellType, GridMap
from acala_engine.grid_utils import (
    flood_fill_indoor_component,
    find_all_indoor_components,
    is_interior_opening_to_outdoor,
    is_inside,
    iter_neighbors_4,
    radius_expand,
)


def _make_small_grid(cells):
    return GridMap(
        cells=cells,
        cell_size_m=0.5,
        height=len(cells),
        width=len(cells[0]),
    )


def test_is_inside_and_neighbors():
    grid = _make_small_grid(
        [
            [0, 0, 0],
            [0, 0, 0],
            [0, 0, 0],
        ]
    )

    assert is_inside(grid, (0, 0))
    assert is_inside(grid, (2, 2))
    assert not is_inside(grid, (-1, 0))
    assert not is_inside(grid, (3, 1))

    neighbors_center = set(iter_neighbors_4(grid, (1, 1)))
    assert neighbors_center == {(0, 1), (2, 1), (1, 0), (1, 2)}

    neighbors_corner = set(iter_neighbors_4(grid, (0, 0)))
    assert neighbors_corner == {(1, 0), (0, 1)}


def test_is_interior_opening_to_outdoor():
    cells = [
        [-1, -1, -1],
        [1, 2, 1],
        [0, 0, 0],
    ]
    grid = _make_small_grid(cells)

    assert is_interior_opening_to_outdoor(grid, (1, 1))
    assert not is_interior_opening_to_outdoor(grid, (2, 1))


def test_radius_expand_simple():
    grid = _make_small_grid(
        [
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
            [0, 0, 0, 0, 0],
        ]
    )

    cells = set(radius_expand(grid, (1, 2), radius_cells=1))
    expected = {
        (0, 1), (0, 2), (0, 3),
        (1, 1), (1, 2), (1, 3),
        (2, 1), (2, 2), (2, 3),
    }
    assert cells == expected


def test_indoor_components_flood_fill():
    cells = [
        [-1, -1, -1, -1],
        [-1, 0, 0, -1],
        [-1, 1, 0, -1],
        [-1, -1, -1, -1],
    ]
    grid = _make_small_grid(cells)

    comp = flood_fill_indoor_component(grid, (1, 1))
    assert set(comp) == {(1, 1), (1, 2), (2, 2)}

    assert flood_fill_indoor_component(grid, (0, 0)) == []


def test_find_all_indoor_components_two_blobs():
    cells = [
        [-1, 0, 0, -1],
        [-1, -1, -1, -1],
        [-1, 0, 0, -1],
    ]
    grid = _make_small_grid(cells)

    components = find_all_indoor_components(grid)
    assert len(components) == 2
    as_sets = [set(c) for c in components]
    assert {(0, 1), (0, 2)} in as_sets
    assert {(2, 1), (2, 2)} in as_sets
