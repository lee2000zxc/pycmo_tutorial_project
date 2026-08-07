import pytest
from cmo_tutorial.actions import (
    fire_first_available_weapon,
    lua_quote,
    set_course,
    set_position,
    shutdown_bridge,
)
from cmo_tutorial.actions import Action
from cmo_tutorial.protocol import FileProtocol


def test_lua_quote():
    assert lua_quote("O'Brien") == "'O\\'Brien'"


def test_set_course_validation():
    with pytest.raises(ValueError):
        set_course("Blue", "A", 100, 0)


def test_set_course_obeys_waypoint_while_attacking():
    action = set_course("Blue", "A", 32.0, 35.0)

    assert "ScenEdit_SetDoctrine" in action.lua
    assert "guid=unit.guid" in action.lua
    assert "ignore_plotted_course=false" in action.lua
    assert action.lua.index("ignore_plotted_course=false") < action.lua.index(
        "course={{"
    )


def test_attack_temporarily_prioritizes_attack_geometry():
    action = fire_first_available_weapon(
        "attacker-guid",
        "contact-guid",
        (516,),
    )

    assert "guid=attacker_guid" in action.lua
    assert "ignore_plotted_course=true" in action.lua
    assert action.lua.index("ignore_plotted_course=true") < action.lua.index(
        "ScenEdit_AttackContact"
    )


def test_set_position_generates_immediate_unit_update():
    action = set_position("Israel", "Sufa #1", 32.9, 35.6, 90.0)

    assert "ScenEdit_SetUnit" in action.lua
    assert "latitude=32.90000000" in action.lua
    assert "longitude=35.60000000" in action.lua
    assert "heading=90.0000" in action.lua


def test_protocol_wraps_actions_with_monotonic_sequence(tmp_path):
    from types import SimpleNamespace

    action_path = tmp_path / "pycmo_agent_action.lua"
    config = SimpleNamespace(action_path=action_path)
    protocol = FileProtocol(config)

    returned_first_id = protocol.send(Action("first", "print('first')"))
    first = action_path.read_text(encoding="utf-8")
    returned_second_id = protocol.send(Action("second", "print('second')"))
    second = action_path.read_text(encoding="utf-8")

    first_id = next(
        line for line in first.splitlines() if line.startswith("local action_id")
    )
    second_id = next(
        line for line in second.splitlines() if line.startswith("local action_id")
    )
    assert first_id.endswith(":1'")
    assert second_id.endswith(":2'")
    assert first_id != second_id
    assert returned_first_id in first_id
    assert returned_second_id in second_id
    assert "action_id ~= PYCMO_LAST_ACTION_ID" in second
    assert "PYCMO_LAST_ACTION_ID = action_id" in second


def test_shutdown_bridge_removes_persistent_events():
    action = shutdown_bridge()
    assert "PyCMO Export observation" in action.lua
    assert "PyCMO Execute agent action" in action.lua
    assert "ScenEdit_SetEvent" in action.lua
    assert "mode='remove'" in action.lua
