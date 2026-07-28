from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import Any
import yaml

@dataclass(frozen=True)
class CMOConfig:
    install_dir: Path
    import_export_dir: Path
    lua_dir: Path
    process_name: str

@dataclass(frozen=True)
class ScenarioConfig:
    title: str
    player_side: str
    controlled_unit: str

@dataclass(frozen=True)
class ProtocolConfig:
    action_filename: str
    action_interval_seconds: int
    observation_interval_seconds: int
    observation_timeout_seconds: float
    poll_interval_seconds: float
    time_compression: int

@dataclass(frozen=True)
class RewardConfig:
    score_delta_scale: float
    step_penalty: float
    success_bonus: float
    failure_penalty: float

@dataclass(frozen=True)
class RLConfig:
    waypoint_step_deg: float
    max_episode_steps: int
    target_success_distance_km: float
    max_target_distance_km: float
    distance_progress_scale: float
    contact_reward: float
    no_contact_penalty: float
    fuel_penalty_scale: float
    auto_launch: bool
    soft_reset: bool

@dataclass(frozen=True)
class Tutorial3Config:
    route: tuple[tuple[float, float], ...]
    waypoint_reached_km: float
    default_speed_kts: float | None
    default_altitude_m: float | None

@dataclass(frozen=True)
class AppConfig:
    cmo: CMOConfig
    scenario: ScenarioConfig
    protocol: ProtocolConfig
    reward: RewardConfig
    rl: RLConfig
    tutorial3: Tutorial3Config

    @property
    def observation_path(self) -> Path:
        return self.cmo.import_export_dir / f"{self.scenario.title}.inst"

    @property
    def scenario_ended_path(self) -> Path:
        return self.cmo.import_export_dir / f"{self.scenario.title}_scen_has_ended.inst"

    @property
    def action_path(self) -> Path:
        return self.cmo.lua_dir / "pycmo_tutorial3" / self.protocol.action_filename

def _required(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping: raise KeyError(f"설정 키가 없습니다: {key}")
    return mapping[key]

def load_config(path: str | Path = "config.yaml") -> AppConfig:
    path=Path(path)
    if not path.exists(): raise FileNotFoundError(f"{path}가 없습니다.")
    raw=yaml.safe_load(path.read_text(encoding='utf-8')) or {}
    cmo=_required(raw,'cmo'); scenario=_required(raw,'scenario'); protocol=_required(raw,'protocol')
    reward=raw.get('reward',{}); rl=raw.get('rl',{}); tutorial3=raw.get('tutorial3',{})
    route=tuple((float(p[0]),float(p[1])) for p in tutorial3.get('route',[]))
    return AppConfig(
      cmo=CMOConfig(Path(_required(cmo,'install_dir')),Path(_required(cmo,'import_export_dir')),Path(_required(cmo,'lua_dir')),str(cmo.get('process_name','Command.exe'))),
      scenario=ScenarioConfig(str(_required(scenario,'title')),str(_required(scenario,'player_side')),str(scenario.get('controlled_unit',''))),
      protocol=ProtocolConfig(str(protocol.get('action_filename','pycmo_agent_action.lua')),int(protocol.get('action_interval_seconds',1)),int(protocol.get('observation_interval_seconds',5)),float(protocol.get('observation_timeout_seconds',60)),float(protocol.get('poll_interval_seconds',0.2)),int(protocol.get('time_compression',0))),
      reward=RewardConfig(float(reward.get('score_delta_scale',10)),float(reward.get('step_penalty',-0.01)),float(reward.get('success_bonus',200)),float(reward.get('failure_penalty',-100))),
      rl=RLConfig(float(rl.get('waypoint_step_deg',0.03)),int(rl.get('max_episode_steps',100)),float(rl.get('target_success_distance_km',20)),float(rl.get('max_target_distance_km',300)),float(rl.get('distance_progress_scale',0.2)),float(rl.get('contact_reward',0.02)),float(rl.get('no_contact_penalty',-0.05)),float(rl.get('fuel_penalty_scale',2)),bool(rl.get('auto_launch',True)),bool(rl.get('soft_reset',True))),
      tutorial3=Tutorial3Config(route,float(tutorial3.get('waypoint_reached_km',3)),None if tutorial3.get('default_speed_kts') is None else float(tutorial3['default_speed_kts']),None if tutorial3.get('default_altitude_m') is None else float(tutorial3['default_altitude_m']))
    )
