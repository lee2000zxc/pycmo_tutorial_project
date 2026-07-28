from __future__ import annotations

from dataclasses import dataclass


def lua_quote(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace("'", "\\'")
        .replace("\r", "\\r")
        .replace("\n", "\\n")
    )
    return f"'{escaped}'"


@dataclass(frozen=True)
class Action:
    name: str
    lua: str


def noop() -> Action:
    return Action("noop", "-- pycmo no-op\n")


def set_course(
    side: str,
    unit_name: str,
    latitude: float,
    longitude: float,
) -> Action:
    if not -90 <= latitude <= 90:
        raise ValueError("latitude 범위는 -90~90이어야 합니다.")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude 범위는 -180~180이어야 합니다.")

    lua = f"""\
local unit = ScenEdit_GetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}}})
if unit ~= nil then
    ScenEdit_SetUnit({{
        side={lua_quote(side)},
        unitname={lua_quote(unit_name)},
        course={{{{
            latitude={latitude:.8f},
            longitude={longitude:.8f},
            TypeOf='ManualPlottedCourseWaypoint'
        }}}}
    }})
end
"""
    return Action(f"set_course({latitude:.5f}, {longitude:.5f})", lua)


def set_speed(side: str, unit_name: str, speed_kts: float) -> Action:
    if speed_kts < 0:
        raise ValueError("speed_kts는 0 이상이어야 합니다.")
    return Action(
        f"set_speed({speed_kts:.1f})",
        f"ScenEdit_SetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}, speed={speed_kts:.2f}}})\n",
    )


def set_altitude(side: str, unit_name: str, altitude_m: float) -> Action:
    return Action(
        f"set_altitude({altitude_m:.1f})",
        f"ScenEdit_SetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}, altitude={altitude_m:.2f}}})\n",
    )

def attack_contact(
    attacker_guid: str,
    contact_guid: str,
) -> Action:
    lua = f"""\
local attacker_id = {lua_quote(attacker_guid)}
local contact_id = {lua_quote(contact_guid)}

local ok, result = pcall(function()
    return ScenEdit_AttackContact(
        attacker_id,
        contact_id,
        {{
            mode = 0
        }}
    )
end)

if ok then
    print(
        "PyCMO attack command result: " ..
        tostring(result)
    )
else
    print(
        "PyCMO attack command error: " ..
        tostring(result)
    )
end
"""

    return Action(
        f"attack_contact({contact_guid})",
        lua,
    )

def set_course_speed_altitude(
    side: str,
    unit_name: str,
    latitude: float,
    longitude: float,
    speed_kts: float | None,
    altitude_m: float | None,
) -> Action:
    parts = [set_course(side, unit_name, latitude, longitude).lua]
    name = f"waypoint({latitude:.5f}, {longitude:.5f})"
    if speed_kts is not None:
        parts.append(set_speed(side, unit_name, speed_kts).lua)
    if altitude_m is not None:
        parts.append(set_altitude(side, unit_name, altitude_m).lua)
    return Action(name, "\n".join(parts))


def rtb(side: str, unit_name: str, enabled: bool = True) -> Action:
    value = "true" if enabled else "false"
    return Action(
        f"rtb({enabled})",
        f"ScenEdit_SetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}, RTB={value}}})\n",
    )


def launch(side: str, unit_name: str, enabled: bool = True) -> Action:
    value = "true" if enabled else "false"
    lua = f"""\
local unit = ScenEdit_GetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}}})
if unit ~= nil then
    if unit.isOperating then
        print('PyCMO launch skipped: already operating')
    else
        local ok, result = pcall(function() return unit:Launch({value}) end)
        if not ok then print('PyCMO launch error: ' .. tostring(result)) end
    end
else
    print('PyCMO launch failed: unit not found')
end
"""
    return Action(f"launch({enabled})", lua)
