"""
Tests for multi-pixel-thick openings (2-thick and 3-thick facades).

Validates that zones, magnetics, PIRs, keyboard, and sirens all work correctly
when doors/windows span multiple rows/columns between exterior and interior.
"""

from acala_engine import (
    CellType,
    DeviceType,
    GridMap,
    MapElementType,
    SecurityLevel,
    ZoneType,
    build_scenario,
    make_element,
    make_room,
    plan_installation,
)
from acala_engine.grid_utils import flood_fill_opening_group
from acala_engine.zones import build_red_zones_for_exterior_openings

O = -1  # outdoor
I = 0   # indoor
W = 1   # wall
D = 2   # door
Wi = 3  # window


# ---- Grid fixtures ----

# 2-thick door on top, 2-thick window on right
THICK2_CELLS = [
    [O,  O,  O,  O,  O,  O,  O,  O],
    [O,  W,  W,  D,  D,  W,  W,  O],
    [O,  W,  W,  D,  D,  W,  W,  O],
    [O,  W,  I,  I,  I,  I,  W,  O],
    [O,  W,  I,  I,  I,  I, Wi,  O],
    [O,  W,  I,  I,  I,  I, Wi,  O],
    [O,  W,  I,  I,  I,  I,  W,  O],
    [O,  W,  W,  W,  W,  W,  W,  O],
    [O,  O,  O,  O,  O,  O,  O,  O],
]

# 3-thick door on bottom, 3-thick window on left
THICK3_CELLS = [
    [O,  O,  O,  O,  O,  O,  O,  O,  O],
    [O,  W,  W,  W,  W,  W,  W,  W,  O],
    [O, Wi,  I,  I,  I,  I,  I,  W,  O],
    [O, Wi,  I,  I,  I,  I,  I,  W,  O],
    [O, Wi,  I,  I,  I,  I,  I,  W,  O],
    [O,  W,  I,  I,  I,  I,  I,  W,  O],
    [O,  W,  I,  I,  I,  I,  I,  W,  O],
    [O,  W,  W,  D,  D,  D,  W,  W,  O],
    [O,  W,  W,  D,  D,  D,  W,  W,  O],
    [O,  W,  W,  D,  D,  D,  W,  W,  O],
    [O,  O,  O,  O,  O,  O,  O,  O,  O],
]


def _scenario_thick2(security_level="optimal"):
    return build_scenario(
        cells=THICK2_CELLS,
        cell_size_m=0.5,
        security_level=security_level,
        fixture_name="thick2",
        rooms=[make_room(id="room_1", cells=[
            (r, c) for r in range(3, 7) for c in range(2, 6)
            if THICK2_CELLS[r][c] == I
        ])],
        elements=[
            make_element(id="e_main", element_type="main_entry", position=(1, 3)),
            make_element(id="e_board", element_type="electric_board", position=(3, 2)),
        ],
    )


def _scenario_thick3(security_level="optimal"):
    return build_scenario(
        cells=THICK3_CELLS,
        cell_size_m=0.5,
        security_level=security_level,
        fixture_name="thick3",
        rooms=[make_room(id="room_1", cells=[
            (r, c) for r in range(2, 7) for c in range(2, 7)
            if THICK3_CELLS[r][c] == I
        ])],
        elements=[
            make_element(id="e_main", element_type="main_entry", position=(9, 4)),
            make_element(id="e_board", element_type="electric_board", position=(3, 3)),
        ],
    )


# ---- flood_fill_opening_group tests ----

def test_flood_fill_opening_group_2thick_door():
    grid = GridMap(cells=THICK2_CELLS, cell_size_m=0.5, height=len(THICK2_CELLS), width=len(THICK2_CELLS[0]))
    group, ext_edge, seeds = flood_fill_opening_group(grid, (1, 3))
    assert len(group) == 4  # 2x2 door block
    assert (1, 3) in ext_edge  # row 1 touches outdoor
    assert (1, 4) in ext_edge
    assert len(seeds) >= 1  # INDOOR seeds from row 3
    for s in seeds:
        assert CellType(grid.cells[s[0]][s[1]]) is CellType.INDOOR


def test_flood_fill_opening_group_3thick_door():
    grid = GridMap(cells=THICK3_CELLS, cell_size_m=0.5, height=len(THICK3_CELLS), width=len(THICK3_CELLS[0]))
    group, ext_edge, seeds = flood_fill_opening_group(grid, (9, 3))
    assert len(group) == 9  # 3x3 door block
    assert any(r == 9 for r, c in ext_edge)  # row 9 touches outdoor (row 10)
    assert len(seeds) >= 1
    for s in seeds:
        assert CellType(grid.cells[s[0]][s[1]]) is CellType.INDOOR


def test_flood_fill_opening_group_2thick_window():
    grid = GridMap(cells=THICK2_CELLS, cell_size_m=0.5, height=len(THICK2_CELLS), width=len(THICK2_CELLS[0]))
    group, ext_edge, seeds = flood_fill_opening_group(grid, (4, 6))
    assert len(group) == 2  # two window cells
    assert len(ext_edge) >= 1  # col 6 touches outdoor at col 7
    assert len(seeds) >= 1


# ---- Red zone tests ----

def test_red_zones_2thick_openings():
    scenario = _scenario_thick2()
    zones = build_red_zones_for_exterior_openings(scenario)
    assert len(zones) >= 1
    all_red = {c for z in zones for c in z.cells}
    assert len(all_red) > 0
    for r, c in all_red:
        assert CellType(scenario.grid_map.cells[r][c]) is CellType.INDOOR


def test_red_zones_3thick_openings():
    scenario = _scenario_thick3()
    zones = build_red_zones_for_exterior_openings(scenario)
    assert len(zones) >= 1
    all_red = {c for z in zones for c in z.cells}
    assert len(all_red) > 0
    for r, c in all_red:
        assert CellType(scenario.grid_map.cells[r][c]) is CellType.INDOOR


# ---- Full plan tests ----

def test_plan_thick2_has_magnetics_and_devices():
    scenario = _scenario_thick2()
    proposal = plan_installation(scenario, security_level=SecurityLevel.OPTIMAL)
    types = {d.device_type for d in proposal.devices}
    assert DeviceType.PANEL in types
    assert DeviceType.KEYBOARD in types
    assert DeviceType.MAGNETIC in types

    mags = [d for d in proposal.devices if d.device_type is DeviceType.MAGNETIC]
    for m in mags:
        r, c = m.cell
        assert CellType(scenario.grid_map.cells[r][c]) in (CellType.DOOR, CellType.WINDOW)


def test_plan_thick3_has_magnetics_and_devices():
    scenario = _scenario_thick3()
    proposal = plan_installation(scenario, security_level=SecurityLevel.OPTIMAL)
    types = {d.device_type for d in proposal.devices}
    assert DeviceType.PANEL in types
    assert DeviceType.KEYBOARD in types
    assert DeviceType.MAGNETIC in types


def test_plan_thick2_keyboard_near_door_interior():
    """Keyboard should be on INDOOR cell near the main entry, even with thick door."""
    scenario = _scenario_thick2()
    proposal = plan_installation(scenario)
    keyboards = [d for d in proposal.devices if d.device_type is DeviceType.KEYBOARD]
    assert len(keyboards) == 1
    kr, kc = keyboards[0].cell
    assert CellType(scenario.grid_map.cells[kr][kc]) is CellType.INDOOR


def test_plan_thick3_keyboard_near_door_interior():
    scenario = _scenario_thick3()
    proposal = plan_installation(scenario)
    keyboards = [d for d in proposal.devices if d.device_type is DeviceType.KEYBOARD]
    assert len(keyboards) == 1
    kr, kc = keyboards[0].cell
    assert CellType(scenario.grid_map.cells[kr][kc]) is CellType.INDOOR


def test_plan_thick2_magnetics_vary_by_profile():
    scenario = _scenario_thick2()
    p_min = plan_installation(scenario, security_level=SecurityLevel.MIN)
    p_opt = plan_installation(scenario, security_level=SecurityLevel.OPTIMAL)
    p_max = plan_installation(scenario, security_level=SecurityLevel.MAX)

    m_min = len([d for d in p_min.devices if d.device_type is DeviceType.MAGNETIC])
    m_opt = len([d for d in p_opt.devices if d.device_type is DeviceType.MAGNETIC])
    m_max = len([d for d in p_max.devices if d.device_type is DeviceType.MAGNETIC])

    assert m_min >= 1  # at least main entry
    assert m_min <= m_opt <= m_max


def test_plan_thick2_outdoor_siren_on_wall():
    """Outdoor siren should find a wall cell even with thick door facade."""
    scenario = _scenario_thick2()
    proposal = plan_installation(scenario, security_level=SecurityLevel.OPTIMAL)
    outdoor = [d for d in proposal.devices if d.device_type is DeviceType.SIREN_OUTDOOR]
    assert len(outdoor) == 1
    sr, sc = outdoor[0].cell
    assert CellType(scenario.grid_map.cells[sr][sc]) is CellType.WALL


def test_plan_thick3_pirs_if_red_remains():
    """With MIN profile (main entry only magnetic), unmagnetized window should create red -> PIRs."""
    scenario = _scenario_thick3()
    proposal = plan_installation(scenario, security_level=SecurityLevel.MIN)
    remaining_red = {c for z in proposal.zones if z.zone_type is ZoneType.RED for c in z.cells}
    pirs = [d for d in proposal.devices if d.device_type is DeviceType.PIR]
    if remaining_red:
        assert len(pirs) >= 1
    for p in pirs:
        r, c = p.cell
        assert CellType(scenario.grid_map.cells[r][c]) is CellType.INDOOR
