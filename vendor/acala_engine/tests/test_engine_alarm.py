"""
Engine tests using inline Scenario construction (no fixture files needed).

The studio_apartment matrix is embedded directly so this test suite is
fully self-contained and portable.
"""

from acala_engine import (
    CellType,
    DeviceType,
    MapElementType,
    ProductType,
    SecurityLevel,
    ZoneType,
    build_scenario,
    make_element,
    make_room,
    plan_installation,
)

O = -1   # outdoor
I = 0    # indoor
W = 1    # wall
D = 2    # door
Wi = 3   # window
P = 4    # prohibited

STUDIO_CELLS = [
    [O,  O,  O,  O,  O,  O,  O,  O,  O,  O],
    [O,  W,  W,  W,  D,  W,  W,  W,  W,  O],
    [O,  W,  I,  I,  I,  I,  I,  I, Wi,  O],
    [O,  W,  I,  I,  I,  I,  I,  I,  W,  O],
    [O,  W,  I,  I,  I,  P,  I,  I,  W,  O],
    [O,  W,  I,  I,  I,  I,  I,  I,  W,  O],
    [O,  W,  W,  W,  W,  W,  W,  W,  W,  O],
    [O,  O,  O,  O,  O,  O,  O,  O,  O,  O],
]


def _make_studio_scenario(security_level="optimal"):
    return build_scenario(
        cells=STUDIO_CELLS,
        cell_size_m=0.5,
        security_level=security_level,
        fixture_name="studio_apartment",
        rooms=[
            make_room(
                id="room_1",
                cells=[
                    (2, 2), (3, 2), (4, 2), (5, 2),
                    (2, 3), (3, 3), (4, 3), (5, 3),
                    (2, 4), (3, 4), (4, 4), (5, 4),
                    (2, 5), (3, 5), (4, 5), (5, 5),
                ],
                room_type="living",
            ),
        ],
        elements=[
            make_element(id="elem_1", element_type="main_entry", position=(1, 4)),
            make_element(id="elem_2", element_type="electric_board", position=(3, 2)),
            make_element(id="elem_3", element_type="heat_source", position=(5, 4)),
        ],
    )


def test_plan_installation_basic_proposal_shape():
    scenario = _make_studio_scenario()
    proposal = plan_installation(scenario)

    assert proposal.product_type is ProductType.ALARM
    assert proposal.security_level == scenario.security_level
    assert proposal.grid_map is scenario.grid_map
    assert proposal.rooms == scenario.rooms
    assert proposal.elements == scenario.elements

    assert len(proposal.zones) >= 1

    device_types = {d.device_type for d in proposal.devices}
    assert DeviceType.PANEL in device_types
    assert DeviceType.KEYBOARD in device_types


def test_panel_near_electric_board_and_not_in_prohibited():
    scenario = _make_studio_scenario()
    proposal = plan_installation(scenario)

    boards = [e for e in proposal.elements if e.element_type is MapElementType.ELECTRIC_BOARD]
    assert len(boards) == 1
    board_cell = boards[0].cells[0]

    panels = [d for d in proposal.devices if d.device_type is DeviceType.PANEL]
    assert len(panels) == 1
    panel = panels[0]

    r, c = panel.cell
    assert CellType(scenario.grid_map.cells[r][c]) is CellType.INDOOR

    br, bc = board_cell
    assert abs(panel.cell[0] - br) + abs(panel.cell[1] - bc) <= 1


def test_keyboard_near_main_entry_and_not_in_prohibited():
    scenario = _make_studio_scenario()
    proposal = plan_installation(scenario)

    main_entries = [
        e for e in proposal.elements
        if e.element_type is MapElementType.DOOR and e.is_main_entry
    ]
    assert len(main_entries) == 1
    main_cell = main_entries[0].cells[0]

    keyboards = [d for d in proposal.devices if d.device_type is DeviceType.KEYBOARD]
    assert len(keyboards) == 1
    keyboard = keyboards[0]

    r, c = keyboard.cell
    assert CellType(scenario.grid_map.cells[r][c]) is CellType.INDOOR

    mr, mc = main_cell
    assert abs(keyboard.cell[0] - mr) + abs(keyboard.cell[1] - mc) <= 1


def test_magnetics_on_exterior_openings_and_vary_by_profile():
    scenario = _make_studio_scenario()

    main_entries = [
        e for e in scenario.elements
        if e.element_type is MapElementType.DOOR and e.is_main_entry
    ]
    assert len(main_entries) == 1
    main_cell = main_entries[0].cells[0]

    proposal_min = plan_installation(scenario, security_level=SecurityLevel.MIN)
    mags_min = [d for d in proposal_min.devices if d.device_type is DeviceType.MAGNETIC]
    assert len(mags_min) >= 1
    assert main_cell in {d.cell for d in mags_min}

    for d in mags_min:
        r, c = d.cell
        assert CellType(scenario.grid_map.cells[r][c]) in (CellType.DOOR, CellType.WINDOW)

    proposal_opt = plan_installation(scenario, security_level=SecurityLevel.OPTIMAL)
    mags_opt = [d for d in proposal_opt.devices if d.device_type is DeviceType.MAGNETIC]

    proposal_max = plan_installation(scenario, security_level=SecurityLevel.MAX)
    mags_max = [d for d in proposal_max.devices if d.device_type is DeviceType.MAGNETIC]

    assert len(mags_min) <= len(mags_opt) <= len(mags_max)


def test_pirs_cover_red_zones_and_vary_by_profile():
    scenario = _make_studio_scenario()

    proposal_min = plan_installation(scenario, security_level=SecurityLevel.MIN)
    proposal_opt = plan_installation(scenario, security_level=SecurityLevel.OPTIMAL)
    proposal_max = plan_installation(scenario, security_level=SecurityLevel.MAX)

    pirs_min = [d for d in proposal_min.devices if d.device_type is DeviceType.PIR]
    pirs_opt = [d for d in proposal_opt.devices if d.device_type is DeviceType.PIR]
    pirs_max = [d for d in proposal_max.devices if d.device_type is DeviceType.PIR]

    red_after_max = {
        c for z in proposal_max.zones if z.zone_type == ZoneType.RED for c in z.cells
    }
    if red_after_max:
        assert len(pirs_max) >= 1
    assert len(pirs_max) >= len(pirs_opt)

    grid = scenario.grid_map
    for d in pirs_min + pirs_opt + pirs_max:
        r, c = d.cell
        assert CellType(grid.cells[r][c]) is CellType.INDOOR


def test_sirens_indoor_and_outdoor_rules():
    scenario = _make_studio_scenario()

    proposal_min = plan_installation(scenario, security_level=SecurityLevel.MIN)
    indoor_min = [d for d in proposal_min.devices if d.device_type is DeviceType.SIREN_INDOOR]
    outdoor_min = [d for d in proposal_min.devices if d.device_type is DeviceType.SIREN_OUTDOOR]
    assert len(indoor_min) == 1
    assert len(outdoor_min) == 0

    panels = [d for d in proposal_min.devices if d.device_type is DeviceType.PANEL]
    assert len(panels) == 1
    assert indoor_min[0].cell == panels[0].cell

    r_in, c_in = indoor_min[0].cell
    assert CellType(scenario.grid_map.cells[r_in][c_in]) is CellType.INDOOR

    proposal_opt = plan_installation(scenario, security_level=SecurityLevel.OPTIMAL)
    outdoor_opt = [d for d in proposal_opt.devices if d.device_type is DeviceType.SIREN_OUTDOOR]
    assert len(outdoor_opt) == 1

    sr, sc = outdoor_opt[0].cell
    assert CellType(scenario.grid_map.cells[sr][sc]) is CellType.WALL
    has_outdoor_neighbour = False
    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = sr + dr, sc + dc
        if 0 <= nr < scenario.grid_map.height and 0 <= nc < scenario.grid_map.width:
            if CellType(scenario.grid_map.cells[nr][nc]) is CellType.OUTDOOR:
                has_outdoor_neighbour = True
                break
    assert has_outdoor_neighbour
