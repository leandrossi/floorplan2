from acala_engine import (
    CellType,
    ZoneType,
    RoomType,
    SecurityLevel,
    ProductType,
    MapElementType,
    DeviceType,
    GridMap,
    Room,
    Zone,
    MapElement,
    DevicePlacement,
    InstallationProposal,
)


def test_enums_basic_values():
    assert CellType.OUTDOOR.value == -1
    assert CellType.INDOOR.value == 0
    assert CellType.WALL.value == 1
    assert CellType.DOOR.value == 2
    assert CellType.WINDOW.value == 3
    assert CellType.PROHIBITED.value == 4

    assert ZoneType.RED.value == "red"
    assert ZoneType.PROHIBITED.value == "prohibited"
    assert RoomType.BEDROOM.value == "bedroom"
    assert SecurityLevel.OPTIMAL.value == "optimal"
    assert ProductType.ALARM.value == "alarm"
    assert MapElementType.ELECTRIC_BOARD.value == "electric_board"
    assert DeviceType.SIREN_INDOOR.value == "siren_indoor"


def test_grid_and_room_construction():
    cells = [
        [1, 1, 1],
        [1, 0, 1],
        [1, 1, -1],
    ]

    grid = GridMap(cells=cells, cell_size_m=0.25, height=3, width=3)
    assert grid.height == 3
    assert grid.width == 3
    assert grid.cells[1][1] == CellType.INDOOR

    room = Room(id="room_1", cells=[(1, 1)])
    assert room.room_type is RoomType.UNKNOWN
    assert room.is_critical is True


def test_zone_element_and_device_placement():
    zone = Zone(id="zone_red_1", zone_type=ZoneType.RED, cells=[(1, 1), (1, 2)])
    assert zone.zone_type is ZoneType.RED
    assert (1, 1) in zone.cells

    element = MapElement(
        id="door_1",
        element_type=MapElementType.DOOR,
        cells=[(1, 2)],
        room_id="room_1",
    )
    assert element.element_type is MapElementType.DOOR
    assert element.room_id == "room_1"

    device = DevicePlacement(
        id="dev_panel_1",
        device_type=DeviceType.PANEL,
        cell=(1, 1),
        room_id="room_1",
        reasons=["near_electric_board"],
        is_out_of_standard=False,
    )
    assert device.device_type is DeviceType.PANEL
    assert "near_electric_board" in device.reasons
    assert device.is_out_of_standard is False


def test_installation_proposal_basic_shape():
    grid = GridMap(cells=[[0]], cell_size_m=0.5, height=1, width=1)
    room = Room(id="room_1", cells=[(0, 0)])
    zone = Zone(id="zone_red_1", zone_type=ZoneType.RED, cells=[(0, 0)])
    element = MapElement(id="door_1", element_type=MapElementType.DOOR, cells=[(0, 0)])
    device = DevicePlacement(id="dev_panel_1", device_type=DeviceType.PANEL, cell=(0, 0))

    proposal = InstallationProposal(
        product_type=ProductType.ALARM,
        security_level=SecurityLevel.OPTIMAL,
        grid_map=grid,
        rooms=[room],
        zones=[zone],
        elements=[element],
        devices=[device],
    )

    assert proposal.product_type is ProductType.ALARM
    assert proposal.security_level is SecurityLevel.OPTIMAL
    assert proposal.grid_map.height == 1
    assert len(proposal.rooms) == 1
    assert len(proposal.devices) == 1
