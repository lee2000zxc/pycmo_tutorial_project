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
    kill_reward: float
    ownship_loss_penalty: float
    mission_success_reward: float


@dataclass(frozen=True)
class RLConfig:
    waypoint_step_deg: float
    max_episode_steps: int
    target_success_distance_km: float
    max_target_distance_km: float

    distance_progress_scale: float

    contact_acquired_reward: float
    contact_maintain_reward: float
    no_contact_penalty: float

    heading_alignment_scale: float

    preferred_attack_min_km: float
    preferred_attack_max_km: float
    preferred_range_reward: float

    too_close_distance_km: float
    too_close_penalty: float

    valid_attack_reward: float
    invalid_attack_penalty: float
    attack_request_cost: float

    fuel_penalty_scale: float
    action_change_penalty: float

    reward_clip_min: float
    reward_clip_max: float

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
        return (
            self.cmo.import_export_dir
            / f"{self.scenario.title}_scen_has_ended.inst"
        )

    @property
    def action_path(self) -> Path:
        return (
            self.cmo.lua_dir
            / "pycmo_tutorial3"
            / self.protocol.action_filename
        )


def _required(mapping: dict[str, Any], key: str) -> Any:
    if key not in mapping:
        raise KeyError(f"설정 키가 없습니다: {key}")
    return mapping[key]


def _bool_value(value: Any, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False
    return bool(value)


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"{config_path}가 없습니다.")

    raw = yaml.safe_load(
        config_path.read_text(encoding="utf-8")
    ) or {}

    cmo = _required(raw, "cmo")
    scenario = _required(raw, "scenario")
    protocol = _required(raw, "protocol")
    reward = raw.get("reward", {})
    rl = raw.get("rl", {})
    tutorial3 = raw.get("tutorial3", {})

    route = tuple(
        (float(point[0]), float(point[1]))
        for point in tutorial3.get("route", [])
    )

    return AppConfig(
        cmo=CMOConfig(
            install_dir=Path(_required(cmo, "install_dir")),
            import_export_dir=Path(
                _required(cmo, "import_export_dir")
            ),
            lua_dir=Path(_required(cmo, "lua_dir")),
            process_name=str(
                cmo.get("process_name", "Command.exe")
            ),
        ),
        scenario=ScenarioConfig(
            title=str(_required(scenario, "title")),
            player_side=str(
                _required(scenario, "player_side")
            ),
            controlled_unit=str(
                scenario.get("controlled_unit", "")
            ),
        ),
        protocol=ProtocolConfig(
            action_filename=str(
                protocol.get(
                    "action_filename",
                    "pycmo_agent_action.lua",
                )
            ),
            action_interval_seconds=int(
                protocol.get("action_interval_seconds", 5)
            ),
            observation_interval_seconds=int(
                protocol.get("observation_interval_seconds", 5)
            ),
            observation_timeout_seconds=float(
                protocol.get("observation_timeout_seconds", 60.0)
            ),
            poll_interval_seconds=float(
                protocol.get("poll_interval_seconds", 0.2)
            ),
            time_compression=int(
                protocol.get("time_compression", 0)
            ),
        ),
        reward=RewardConfig(
            score_delta_scale=float(
                reward.get("score_delta_scale", 1.0)
            ),
            step_penalty=float(
                reward.get("step_penalty", -0.01)
            ),
            success_bonus=float(
                reward.get("success_bonus", 100.0)
            ),
            failure_penalty=float(
                reward.get("failure_penalty", -100.0)
            ),
            kill_reward=float(
                reward.get("kill_reward", 100.0)
            ),
            ownship_loss_penalty=float(
                reward.get("ownship_loss_penalty", -100.0)
            ),
            mission_success_reward=float(
                reward.get("mission_success_reward", 200.0)
            ),
        ),
        rl=RLConfig(
            waypoint_step_deg=float(
                rl.get("waypoint_step_deg", 0.03)
            ),
            max_episode_steps=int(
                rl.get("max_episode_steps", 100)
            ),
            target_success_distance_km=float(
                rl.get("target_success_distance_km", 20.0)
            ),
            max_target_distance_km=float(
                rl.get("max_target_distance_km", 300.0)
            ),
            distance_progress_scale=float(
                rl.get("distance_progress_scale", 1.0)
            ),
            contact_acquired_reward=float(
                rl.get("contact_acquired_reward", 0.1)
            ),
            contact_maintain_reward=float(
                rl.get("contact_maintain_reward", 0.005)
            ),
            no_contact_penalty=float(
                rl.get("no_contact_penalty", -0.02)
            ),
            heading_alignment_scale=float(
                rl.get("heading_alignment_scale", 0.02)
            ),
            preferred_attack_min_km=float(
                rl.get("preferred_attack_min_km", 25.0)
            ),
            preferred_attack_max_km=float(
                rl.get("preferred_attack_max_km", 60.0)
            ),
            preferred_range_reward=float(
                rl.get("preferred_range_reward", 0.05)
            ),
            too_close_distance_km=float(
                rl.get("too_close_distance_km", 10.0)
            ),
            too_close_penalty=float(
                rl.get("too_close_penalty", -0.05)
            ),
            valid_attack_reward=float(
                rl.get("valid_attack_reward", 0.02)
            ),
            invalid_attack_penalty=float(
                rl.get("invalid_attack_penalty", -0.05)
            ),
            attack_request_cost=float(
                rl.get("attack_request_cost", -0.01)
            ),
            fuel_penalty_scale=float(
                rl.get("fuel_penalty_scale", 1.0)
            ),
            action_change_penalty=float(
                rl.get("action_change_penalty", -0.002)
            ),
            reward_clip_min=float(
                rl.get("reward_clip_min", -200.0)
            ),
            reward_clip_max=float(
                rl.get("reward_clip_max", 200.0)
            ),
            auto_launch=_bool_value(
                rl.get("auto_launch"),
                True,
            ),
            soft_reset=_bool_value(
                rl.get("soft_reset"),
                True,
            ),
        ),
        tutorial3=Tutorial3Config(
            route=route,
            waypoint_reached_km=float(
                tutorial3.get("waypoint_reached_km", 3.0)
            ),
            default_speed_kts=(
                None
                if tutorial3.get("default_speed_kts") is None
                else float(tutorial3["default_speed_kts"])
            ),
            default_altitude_m=(
                None
                if tutorial3.get("default_altitude_m") is None
                else float(tutorial3["default_altitude_m"])
            ),
        ),
    )
