from acala_engine import (
    CellType,
    GridMap,
    MapElement,
    MapElementType,
    Scenario,
    SecurityLevel,
)
from acala_engine.zones import (
    build_prohibited_zones_around_hazards,
    build_red_zones_for_exterior_openings,
)


def _make_scenario_for_opening(cells, opening_coord):
    grid = GridMap(
        cells=cells,
        cell_size_m=0.5,
        height=len(cells),
        width=len(cells[0]),
    )
    elements = [
        MapElement(
            id="door_1",
            element_type=MapElementType.DOOR,
            cells=[opening_coord],
        )
    ]
    return Scenario(
        fixture_name="test_fixture",
        cell_size_m=0.5,
        width=grid.width,
        height=grid.height,
        security_level=SecurityLevel.OPTIMAL,
        grid_map=grid,
        rooms=[],
        elements=elements,
        notes="",
    )


def test_build_red_zones_for_exterior_door():
    cells = [
        [-1, -1, -1, -1, -1],
        [1, 1, 2, 1, -1],
        [1, 0, 0, 0, -1],
        [1, 0, 0, 0, -1],
        [1, 1, 1, 1, -1],
    ]
    opening = (1, 2)
    scenario = _make_scenario_for_opening(cells, opening)

    zones = build_red_zones_for_exterior_openings(scenario, influence_depth_m=2.0)
    assert len(zones) == 1
    z = zones[0]
    assert z.zone_type.value == "red"

    for (r, c) in z.cells:
        assert 0 <= r < scenario.height
        assert 0 <= c < scenario.width
        assert CellType(scenario.grid_map.cells[r][c]) is CellType.INDOOR

    assert (2, 2) in z.cells
    assert (3, 2) in z.cells


def test_build_prohibited_zones_around_heat_source():
    cells = [
        [0, 0, 0],
        [0, 4, 0],
        [0, 0, 0],
    ]
    grid = GridMap(cells=cells, cell_size_m=0.5, height=3, width=3)
    elements = [
        MapElement(
            id="heat_1",
            element_type=MapElementType.HEAT_SOURCE,
            cells=[(1, 1)],
        )
    ]
    scenario = Scenario(
        fixture_name="test_fixture_heat",
        cell_size_m=0.5,
        width=3,
        height=3,
        security_level=SecurityLevel.OPTIMAL,
        grid_map=grid,
        rooms=[],
        elements=elements,
        notes="",
    )

    zones = build_prohibited_zones_around_hazards(scenario, radius_m=0.24)
    assert len(zones) == 1
    z = zones[0]
    assert z.zone_type.value == "prohibited"
    assert set(z.cells) == {(1, 1)}
