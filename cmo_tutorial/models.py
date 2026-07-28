from __future__ import annotations
from dataclasses import dataclass, field

@dataclass(frozen=True)
class UnitState:
    guid: str; name: str; side: str; unit_type: str; dbid: int|None
    latitude: float|None; longitude: float|None; altitude_m: float|None
    heading_deg: float|None; speed_kts: float|None; throttle: str|None
    fuel_current: float|None; fuel_max: float|None
    is_operating: bool|None = None; condition: str|None = None; host_facility: str|None = None
    @property
    def fuel_ratio(self):
        if self.fuel_current is None or self.fuel_max in (None,0): return None
        return self.fuel_current/self.fuel_max

@dataclass(frozen=True)
class ContactState:
    guid: str; name: str|None; contact_type: str|None
    latitude: float|None; longitude: float|None; altitude_m: float|None; speed_kts: float|None

@dataclass(frozen=True)
class SideState:
    guid: str; name: str; total_score: float
    contacts: tuple[ContactState,...]=field(default_factory=tuple)

@dataclass(frozen=True)
class Observation:
    title: str; scenario_time: int; start_time: int|None; duration: int|None
    status: str|None; time_compression: int|None
    sides: tuple[SideState,...]; units: tuple[UnitState,...]; scenario_ended: bool=False
    def side(self,name):
        for s in self.sides:
            if s.name==name:return s
        raise KeyError(f"관측값에서 side를 찾을 수 없습니다: {name}")
    def controllable_units(self,player_side): return tuple(u for u in self.units if u.side==player_side)
    def aircraft(self,player_side): return tuple(u for u in self.controllable_units(player_side) if u.unit_type.lower()=='aircraft')
