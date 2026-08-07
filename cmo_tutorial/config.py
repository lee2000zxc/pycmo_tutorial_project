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
    start_position_enabled: bool
    start_latitude: float
    start_longitude: float
    start_heading: float
    randomize_start_position: bool
    start_position_random_radius_km: float
    randomize_start_heading: bool
    start_heading_random_range_deg: float


@dataclass(frozen=True)
class AutoResetConfig:
    enabled: bool
    reload_on_first_reset: bool
    scenario_window_title: str
    restart_timeout_seconds: float
    menu_delay_seconds: float
    target_time_compression: int
    dismiss_scenario_end_dialog: bool
    scenario_end_window_title: str
    dismiss_special_messages_dialog: bool
    special_messages_window_title: str


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
    timeout_penalty: float
    kill_reward: float
    ownship_loss_penalty: float
    mission_success_reward: float


@dataclass(frozen=True)
class RLConfig:
    target_contact_types: tuple[str, ...]
    attack_weapon_candidates: tuple[int, ...]
    attack_weapon_quantity: int
    attack_min_distance_km: float
    attack_max_distance_km: float

    attack_cooldown_steps: int
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
    auto_reset: AutoResetConfig
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


def _validate_config(config: AppConfig) -> None:
    if not -90 <= config.scenario.start_latitude <= 90:
        raise ValueError("start_latitude must be between -90 and 90")
    if not -180 <= config.scenario.start_longitude <= 180:
        raise ValueError("start_longitude must be between -180 and 180")
    if not 0 <= config.scenario.start_heading < 360:
        raise ValueError("start_heading must be between 0 and 360")
    if config.scenario.start_position_random_radius_km < 0:
        raise ValueError("start_position_random_radius_km must not be negative")
    if not 0 <= config.scenario.start_heading_random_range_deg <= 180:
        raise ValueError(
            "start_heading_random_range_deg must be between 0 and 180"
        )
    if config.protocol.observation_timeout_seconds <= 0:
        raise ValueError("observation_timeout_seconds must be positive")
    if config.protocol.poll_interval_seconds <= 0:
        raise ValueError("poll_interval_seconds must be positive")
    if config.rl.max_episode_steps <= 0:
        raise ValueError("max_episode_steps must be positive")
    if not config.rl.target_contact_types:
        raise ValueError("target_contact_types must not be empty")
    if config.rl.waypoint_step_deg <= 0:
        raise ValueError("waypoint_step_deg must be positive")
    if config.rl.max_target_distance_km <= 0:
        raise ValueError("max_target_distance_km must be positive")
    if config.rl.attack_min_distance_km > config.rl.attack_max_distance_km:
        raise ValueError("attack distance minimum exceeds maximum")
    if config.rl.preferred_attack_min_km > config.rl.preferred_attack_max_km:
        raise ValueError("preferred attack distance minimum exceeds maximum")
    if config.rl.reward_clip_min >= config.rl.reward_clip_max:
        raise ValueError("reward_clip_min must be less than reward_clip_max")


def load_config(path: str | Path = "config.yaml") -> AppConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise FileNotFoundError(f"{config_path}가 없습니다.")

    raw = yaml.safe_load(
        config_path.read_text(encoding="utf-8")
    ) or {}

    cmo = _required(raw, "cmo")
    scenario = _required(raw, "scenario")
    auto_reset = raw.get("auto_reset", {})
    protocol = _required(raw, "protocol")
    reward = raw.get("reward", {})
    rl = raw.get("rl", {})
    tutorial3 = raw.get("tutorial3", {})

    route = tuple(
        (float(point[0]), float(point[1]))
        for point in tutorial3.get("route", [])
    )

    weapon_candidates = tuple(
        int(dbid)
        for dbid in rl.get(
            "attack_weapon_candidates",
            [],
        )
        if int(dbid) > 0
    )

    target_contact_types = tuple(
        str(value).strip().lower()
        for value in rl.get(
            "target_contact_types",
            ["Air", "Aircraft"],
        )
        if str(value).strip()
    )

    config = AppConfig(
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
            start_position_enabled=_bool_value(
                scenario.get("start_position_enabled"), False
            ),
            start_latitude=float(
                scenario.get("start_latitude", 0.0)
            ),
            start_longitude=float(
                scenario.get("start_longitude", 0.0)
            ),
            start_heading=float(
                scenario.get("start_heading", 0.0)
            ),
            randomize_start_position=_bool_value(
                scenario.get("randomize_start_position"), False
            ),
            start_position_random_radius_km=float(
                scenario.get("start_position_random_radius_km", 0.0)
            ),
            randomize_start_heading=_bool_value(
                scenario.get("randomize_start_heading"), False
            ),
            start_heading_random_range_deg=float(
                scenario.get("start_heading_random_range_deg", 0.0)
            ),
        ),
        auto_reset=AutoResetConfig(
            enabled=_bool_value(
                auto_reset.get("enabled"),
                False,
            ),
            reload_on_first_reset=_bool_value(
                auto_reset.get("reload_on_first_reset"),
                True,
            ),
            scenario_window_title=str(
                auto_reset.get(
                    "scenario_window_title",
                    scenario["title"],
                )
            ),
            restart_timeout_seconds=float(
                auto_reset.get(
                    "restart_timeout_seconds",
                    60.0,
                )
            ),
            menu_delay_seconds=float(
                auto_reset.get(
                    "menu_delay_seconds",
                    1.0,
                )
            ),
            target_time_compression=int(
                auto_reset.get(
                    "target_time_compression",
                    5,
                )
            ),
            dismiss_scenario_end_dialog=_bool_value(
                auto_reset.get("dismiss_scenario_end_dialog"),
                True,
            ),
            scenario_end_window_title=str(
                auto_reset.get(
                    "scenario_end_window_title",
                    "Scenario End",
                )
            ),
            dismiss_special_messages_dialog=_bool_value(
                auto_reset.get("dismiss_special_messages_dialog"),
                True,
            ),
            special_messages_window_title=str(
                auto_reset.get(
                    "special_messages_window_title",
                    "Special Messages",
                )
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
            timeout_penalty=float(
                reward.get("timeout_penalty", -20.0)
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
            target_contact_types=target_contact_types,
            # 공격 관련 설정
            attack_weapon_candidates=weapon_candidates,
            attack_weapon_quantity=int(
                rl.get(
                    "attack_weapon_quantity",
                    1,
                )
            ),
            attack_min_distance_km=float(
                rl.get(
                    "attack_min_distance_km",
                    5.0,
                )
            ),
            attack_max_distance_km=float(
                rl.get(
                    "attack_max_distance_km",
                    80.0,
                )
            ),
            attack_cooldown_steps=int(
                rl.get(
                    "attack_cooldown_steps",
                    3,
                )
            ),

            # 기본 행동 및 에피소드 설정
            waypoint_step_deg=float(
                rl.get(
                    "waypoint_step_deg",
                    0.03,
                )
            ),
            max_episode_steps=int(
                rl.get(
                    "max_episode_steps",
                    100,
                )
            ),
            target_success_distance_km=float(
                rl.get(
                    "target_success_distance_km",
                    20.0,
                )
            ),
            max_target_distance_km=float(
                rl.get(
                    "max_target_distance_km",
                    300.0,
                )
            ),

            # 거리 기반 보상
            distance_progress_scale=float(
                rl.get(
                    "distance_progress_scale",
                    1.0,
                )
            ),

            # 접촉 관련 보상
            contact_acquired_reward=float(
                rl.get(
                    "contact_acquired_reward",
                    0.1,
                )
            ),
            contact_maintain_reward=float(
                rl.get(
                    "contact_maintain_reward",
                    0.005,
                )
            ),
            no_contact_penalty=float(
                rl.get(
                    "no_contact_penalty",
                    -0.02,
                )
            ),

            # 표적 방향 정렬 보상
            heading_alignment_scale=float(
                rl.get(
                    "heading_alignment_scale",
                    0.02,
                )
            ),

            # 적정 교전 거리 보상
            preferred_attack_min_km=float(
                rl.get(
                    "preferred_attack_min_km",
                    25.0,
                )
            ),
            preferred_attack_max_km=float(
                rl.get(
                    "preferred_attack_max_km",
                    60.0,
                )
            ),
            preferred_range_reward=float(
                rl.get(
                    "preferred_range_reward",
                    0.05,
                )
            ),

            # 과도한 근접 패널티
            too_close_distance_km=float(
                rl.get(
                    "too_close_distance_km",
                    10.0,
                )
            ),
            too_close_penalty=float(
                rl.get(
                    "too_close_penalty",
                    -0.05,
                )
            ),

            # 공격 action 관련 보상
            valid_attack_reward=float(
                rl.get(
                    "valid_attack_reward",
                    0.02,
                )
            ),
            invalid_attack_penalty=float(
                rl.get(
                    "invalid_attack_penalty",
                    -0.05,
                )
            ),
            attack_request_cost=float(
                rl.get(
                    "attack_request_cost",
                    -0.01,
                )
            ),

            # 연료 및 행동 변경 패널티
            fuel_penalty_scale=float(
                rl.get(
                    "fuel_penalty_scale",
                    1.0,
                )
            ),
            action_change_penalty=float(
                rl.get(
                    "action_change_penalty",
                    -0.002,
                )
            ),

            # 보상 범위 제한
            reward_clip_min=float(
                rl.get(
                    "reward_clip_min",
                    -200.0,
                )
            ),
            reward_clip_max=float(
                rl.get(
                    "reward_clip_max",
                    200.0,
                )
            ),

            # 환경 동작
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
    _validate_config(config)
    return config
