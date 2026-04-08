"""Tests for scenario_builder helpers — the entry point for the parallel project."""

from acala_engine import (
    CellType,
    MapElementType,
    SecurityLevel,
    build_scenario,
    make_element,
    make_room,
)


def test_build_scenario_minimal():
    cells = [
        [-1, -1, -1],
        [-1,  0, -1],
        [-1, -1, -1],
    ]
    scenario = build_scenario(cells=cells, cell_size_m=0.5)
    assert scenario.width == 3
    assert scenario.height == 3
    assert scenario.cell_size_m == 0.5
    assert scenario.security_level is SecurityLevel.OPTIMAL
    assert scenario.grid_map.cells[1][1] == CellType.INDOOR
    assert scenario.rooms == []
    assert scenario.elements == []


def test_build_scenario_with_rooms_and_elements():
    cells = [
        [-1, -1, -1, -1, -1],
        [-1,  1,  2,  1, -1],
        [-1,  0,  0,  0, -1],
        [-1,  0,  0,  0, -1],
        [-1,  1,  1,  1, -1],
    ]
    scenario = build_scenario(
        cells=cells,
        cell_size_m=0.5,
        security_level="min",
        rooms=[
            make_room(id="r1", cells=[(2, 1), (2, 2), (3, 1), (3, 2)], room_type="bedroom"),
        ],
        elements=[
            make_element(id="e1", element_type="main_entry", position=(1, 2)),
            make_element(id="e2", element_type="electric_board", position=(2, 1)),
        ],
    )

    assert scenario.security_level is SecurityLevel.MIN
    assert len(scenario.rooms) == 1
    assert scenario.rooms[0].room_type.value == "bedroom"
    assert len(scenario.elements) == 2
    assert scenario.elements[0].is_main_entry is True
    assert scenario.elements[0].element_type is MapElementType.DOOR
    assert scenario.elements[1].element_type is MapElementType.ELECTRIC_BOARD


def test_make_element_string_types():
    el = make_element(id="x", element_type="heat_source", position=(3, 3))
    assert el.element_type is MapElementType.HEAT_SOURCE
    assert el.is_main_entry is False

    el2 = make_element(id="y", element_type="main_entry", position=(1, 1))
    assert el2.element_type is MapElementType.DOOR
    assert el2.is_main_entry is True
