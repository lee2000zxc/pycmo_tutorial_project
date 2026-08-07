from __future__ import annotations
from dataclasses import dataclass

def lua_quote(value: str) -> str:
    escaped=(value.replace("\\","\\\\").replace("'","\\'").replace("\r","\\r").replace("\n","\\n"))
    return f"'{escaped}'"

@dataclass(frozen=True)
class Action:
    name: str
    lua: str

def noop() -> Action:
    return Action('noop','-- pycmo no-op\n')


def shutdown_bridge() -> Action:
    """Remove the persistent CMO events installed by bootstrap.lua."""
    lua = """
local function remove_event(name)
    pcall(function()
        ScenEdit_SetEvent(name, {mode='remove'})
    end)
end

local function remove_trigger(name)
    pcall(function()
        ScenEdit_SetTrigger({description=name, mode='remove'})
    end)
end

local function remove_action(name)
    pcall(function()
        ScenEdit_SetAction({description=name, mode='remove'})
    end)
end

remove_event('PyCMO Export observation')
remove_event('PyCMO Execute agent action')
remove_trigger('PyCMO Export observation trigger')
remove_trigger('PyCMO Execute agent action trigger')
remove_action('PyCMO Export observation action')
remove_action('PyCMO Execute agent action action')

print('PyCMO Tutorial 3 bridge stopped')
"""
    return Action("shutdown_bridge", lua)

def set_course(
    side: str,
    unit_name: str,
    latitude: float,
    longitude: float,
) -> Action:
    if not -90 <= latitude <= 90:
        raise ValueError(
            "latitude 범위는 -90~90이어야 합니다."
        )

    if not -180 <= longitude <= 180:
        raise ValueError(
            "longitude 범위는 -180~180이어야 합니다."
        )

    lua = f"""
local unit = ScenEdit_GetUnit({{
    side={lua_quote(side)},
    unitname={lua_quote(unit_name)}
}})

if unit ~= nil then
    -- A manual attack allocation can leave the aircraft in Engaged Offensive.
    -- Make RL movement actions authoritative even while a target is assigned.
    local doctrine_ok, doctrine_result = pcall(function()
        return ScenEdit_SetDoctrine(
            {{guid=unit.guid}},
            {{ignore_plotted_course=false}}
        )
    end)

    if not doctrine_ok then
        print(
            'PyCMO set ignore_plotted_course error: '
            .. tostring(doctrine_result)
        )
    end

    -- RTB 상태도 해제한다.
    pcall(function()
        ScenEdit_SetUnit({{
            side={lua_quote(side)},
            unitname={lua_quote(unit_name)},
            RTB=false
        }})
    end)

    -- 새로운 수동 웨이포인트를 설정한다.
    local course_ok, course_result = pcall(function()
        return ScenEdit_SetUnit({{
            side={lua_quote(side)},
            unitname={lua_quote(unit_name)},
            course={{{{
                latitude={latitude:.8f},
                longitude={longitude:.8f},
                TypeOf='ManualPlottedCourseWaypoint'
            }}}}
        }})
    end)

    if not course_ok then
        print(
            'PyCMO set course error: '
            .. tostring(course_result)
        )
    else
        print('PyCMO manual course applied')
    end
else
    print('PyCMO set course failed: unit not found')
end
"""

    return Action(
        f"set_course({latitude:.5f}, {longitude:.5f})",
        lua,
    )


def set_position(
    side: str,
    unit_name: str,
    latitude: float,
    longitude: float,
    heading: float,
) -> Action:
    """Move a unit immediately to the configured episode start position."""
    if not -90 <= latitude <= 90:
        raise ValueError("latitude must be between -90 and 90")
    if not -180 <= longitude <= 180:
        raise ValueError("longitude must be between -180 and 180")
    if not 0 <= heading < 360:
        raise ValueError("heading must be between 0 (inclusive) and 360")

    lua = f"""
local ok, result = pcall(function()
    return ScenEdit_SetUnit({{
        side={lua_quote(side)},
        unitname={lua_quote(unit_name)},
        latitude={latitude:.8f},
        longitude={longitude:.8f},
        heading={heading:.4f},
        RTB=false
    }})
end)

if not ok then
    print('PyCMO set start position error: ' .. tostring(result))
else
    print('PyCMO episode start position applied')
end
"""
    return Action(
        f"set_position({latitude:.5f}, {longitude:.5f}, {heading:.1f})",
        lua,
    )

def set_speed(side: str, unit_name: str, speed_kts: float) -> Action:
    if speed_kts<0: raise ValueError('speed_kts는 0 이상이어야 합니다.')
    return Action(f'set_speed({speed_kts:.1f})',f"ScenEdit_SetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}, speed={speed_kts:.2f}}})\n")

def set_altitude(side: str, unit_name: str, altitude_m: float) -> Action:
    return Action(f'set_altitude({altitude_m:.1f})',f"ScenEdit_SetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}, altitude={altitude_m:.2f}}})\n")

def fire_first_available_weapon(
    attacker_guid: str,
    contact_guid: str,
    candidate_dbids: tuple[int, ...],
    quantity: int = 1,
) -> Action:
    if quantity <= 0:
        raise ValueError(
            "quantity는 1 이상이어야 합니다."
        )

    candidates = tuple(
        int(dbid)
        for dbid in candidate_dbids
        if int(dbid) > 0
    )

    if not candidates:
        return noop()

    candidates_lua = ", ".join(
        str(dbid) for dbid in candidates
    )

    lua = f"""
local attacker_guid = {lua_quote(attacker_guid)}
local contact_guid = {lua_quote(contact_guid)}
local candidates = {{{candidates_lua}}}

local assigned = false
local assigned_weapon_dbid = nil

-- A previous waypoint action makes the aircraft obey its plotted course.
-- Temporarily give attack geometry priority again for this attack command.
local doctrine_ok, doctrine_result = pcall(function()
    return ScenEdit_SetDoctrine(
        {{guid=attacker_guid}},
        {{ignore_plotted_course=true}}
    )
end)

if not doctrine_ok then
    print(
        'PyCMO set attack course priority error: '
        .. tostring(doctrine_result)
    )
end

for _, weapon_dbid in ipairs(candidates) do
    local call_ok, attack_result = pcall(function()
        return ScenEdit_AttackContact(
            attacker_guid,
            contact_guid,
            {{
                mode = 1,
                weapon = weapon_dbid,
                qty = {int(quantity)}
            }}
        )
    end)

    if not call_ok then
        print(
            'PyCMO AttackContact Lua error: weapon='
            .. tostring(weapon_dbid)
            .. ', error='
            .. tostring(attack_result)
        )

    elseif attack_result == true then
        assigned = true
        assigned_weapon_dbid = weapon_dbid

        print(
            'PyCMO attack assigned: weapon='
            .. tostring(weapon_dbid)
        )

        break

    else
        print(
            'PyCMO attack assignment rejected: weapon='
            .. tostring(weapon_dbid)
            .. ', result='
            .. tostring(attack_result)
        )
    end
end

if not assigned then
    PYCMO_LAST_ATTACK_ASSIGNED = false
    print(
        'PyCMO: no candidate weapon attack was assigned'
    )
else
    PYCMO_LAST_ATTACK_ASSIGNED = true
    PYCMO_LAST_ASSIGNED_WEAPON_DBID = assigned_weapon_dbid
    print(
        'PyCMO: attack assignment completed, weapon='
        .. tostring(assigned_weapon_dbid)
    )
end
"""

    return Action(
        (
            "fire_first_available_weapon("
            f"target={contact_guid}, "
            f"candidates={candidates}, "
            f"qty={quantity})"
        ),
        lua,
    )

def set_course_speed_altitude(side: str, unit_name: str, latitude: float, longitude: float, speed_kts: float|None, altitude_m: float|None) -> Action:
    parts=[set_course(side,unit_name,latitude,longitude).lua]
    if speed_kts is not None: parts.append(set_speed(side,unit_name,speed_kts).lua)
    if altitude_m is not None: parts.append(set_altitude(side,unit_name,altitude_m).lua)
    return Action(f'waypoint({latitude:.5f}, {longitude:.5f})','\n'.join(parts))

def rtb(side: str, unit_name: str, enabled: bool=True) -> Action:
    value='true' if enabled else 'false'
    return Action(f'rtb({enabled})',f"ScenEdit_SetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}, RTB={value}}})\n")

def launch(side: str, unit_name: str, enabled: bool=True) -> Action:
    value='true' if enabled else 'false'
    lua=f"""local unit = ScenEdit_GetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}}})
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
    return Action(f'launch({enabled})',lua)
