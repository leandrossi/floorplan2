"""Tests for proposal serialization round-trip."""

from acala_engine import (
    DeviceType,
    ProductType,
    SecurityLevel,
    build_scenario,
    make_element,
    plan_installation,
    installation_to_json,
    installation_from_json,
    installation_to_dict,
    installation_from_dict,
)


def _make_simple_proposal():
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
        security_level="optimal",
        elements=[
            make_element(id="e1", element_type="main_entry", position=(1, 2)),
            make_element(id="e2", element_type="electric_board", position=(2, 1)),
        ],
    )
    return plan_installation(scenario)


def test_proposal_to_dict_and_back():
    proposal = _make_simple_proposal()
    data = installation_to_dict(proposal)

    assert data["product_type"] == "alarm"
    assert data["security_level"] == "optimal"
    assert isinstance(data["devices"], list)

    restored = installation_from_dict(data)
    assert restored.product_type is ProductType.ALARM
    assert restored.security_level is SecurityLevel.OPTIMAL
    assert len(restored.devices) == len(proposal.devices)
    for orig, rest in zip(proposal.devices, restored.devices):
        assert orig.device_type == rest.device_type
        assert orig.cell == rest.cell


def test_proposal_json_round_trip():
    proposal = _make_simple_proposal()
    json_str = installation_to_json(proposal)
    restored = installation_from_json(json_str)

    assert restored.product_type == proposal.product_type
    assert restored.security_level == proposal.security_level
    assert len(restored.devices) == len(proposal.devices)
    assert restored.grid_map.height == proposal.grid_map.height
    assert restored.grid_map.width == proposal.grid_map.width
