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

def set_course(side: str, unit_name: str, latitude: float, longitude: float) -> Action:
    if not -90 <= latitude <= 90: raise ValueError('latitude 범위는 -90~90이어야 합니다.')
    if not -180 <= longitude <= 180: raise ValueError('longitude 범위는 -180~180이어야 합니다.')
    lua=f"""local unit = ScenEdit_GetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}}})
if unit ~= nil then
    pcall(function()
        ScenEdit_SetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}, RTB=false}})
    end)
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
    return Action(f'set_course({latitude:.5f}, {longitude:.5f})',lua)

def set_speed(side: str, unit_name: str, speed_kts: float) -> Action:
    if speed_kts<0: raise ValueError('speed_kts는 0 이상이어야 합니다.')
    return Action(f'set_speed({speed_kts:.1f})',f"ScenEdit_SetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}, speed={speed_kts:.2f}}})\n")

def set_altitude(side: str, unit_name: str, altitude_m: float) -> Action:
    return Action(f'set_altitude({altitude_m:.1f})',f"ScenEdit_SetUnit({{side={lua_quote(side)}, unitname={lua_quote(unit_name)}, altitude={altitude_m:.2f}}})\n")

def fire_first_available_weapon(attacker_guid: str, contact_guid: str, candidate_dbids: tuple[int, ...], quantity: int=1) -> Action:
    if quantity<=0: raise ValueError('quantity는 1 이상이어야 합니다.')
    candidates=tuple(int(dbid) for dbid in candidate_dbids if int(dbid)>0)
    if not candidates: return noop()
    candidates_lua=', '.join(str(dbid) for dbid in candidates)
    lua=f"""local attacker_guid = {lua_quote(attacker_guid)}
local contact_guid = {lua_quote(contact_guid)}
local candidates = {{{candidates_lua}}}
local allocated = false

for _, weapon_dbid in ipairs(candidates) do
    local ok, result = pcall(function()
        return ScenEdit_AttackContact(
            attacker_guid,
            contact_guid,
            {{mode = 1, weapon = weapon_dbid, qty = {int(quantity)}}}
        )
    end)
    if ok and result ~= nil and result ~= false then
        print('PyCMO weapon allocated: ' .. tostring(weapon_dbid))
        allocated = true
        break
    end
end

if not allocated then
    print('PyCMO: no candidate weapon could be allocated')
end
"""
    return Action(f'fire_first_available_weapon(target={contact_guid}, candidates={candidates}, qty={quantity})',lua)

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
