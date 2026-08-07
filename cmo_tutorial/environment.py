from __future__ import annotations

from dataclasses import dataclass
import time

from .actions import Action, set_position, shutdown_bridge
from .config import AppConfig
from .models import Observation, UnitState
from .protocol import FileProtocol, ScenarioEnded
from .scenario_controller import SteamScenarioController


@dataclass(frozen=True)
class StepResult:
    observation: Observation
    reward: float
    terminated: bool
    truncated: bool
    info: dict[str, object]


class CMOEnvironment:
    def __init__(
        self,
        config: AppConfig,
        scenario_controller: SteamScenarioController | None = None,
    ):
        self.config = config
        self.protocol = FileProtocol(config)
        self.scenario_controller = (
            scenario_controller
            if scenario_controller is not None
            else SteamScenarioController(config)
        )

        self._previous_score = 0.0
        self._step = 0

        # 시나리오 종료 시 새 observation이 없을 수 있으므로
        # 마지막 정상 observation을 저장한다.
        self._last_observation: Observation | None = None
        self._reset_reference: tuple[str, int, float] | None = None
        self._closed = False

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True

        try:
            self.protocol.send(shutdown_bridge())
        except OSError as exc:
            print(f"[PyCMO shutdown warning] {exc}")

    def restart_scenario(self) -> None:
        # 이전 observation을 stale 상태로 표시하고
        # 이전 scenario-ended marker를 삭제한다.
        self.protocol.prepare_for_scenario_restart()

        # 이전 에피소드의 상태를 초기화한다.
        self._last_observation = None
        self._previous_score = 0.0
        self._step = 0

        message = self.scenario_controller.restart()

        if message:
            print(f"[CMO auto-load] {message}")

    def reset(
        self,
        start_position: tuple[float, float, float] | None = None,
    ) -> tuple[Observation, dict[str, object]]:
        self.protocol.initialize_action_file()

        try:
            observation = self.protocol.wait_for_new(
                allow_existing_first=True
            )

        except ScenarioEnded as exc:
            # reset 시점부터 종료 마커가 발견되는 것은
            # 이전 종료 파일이 남았거나 CMO 재시작이 실패한 경우이다.
            raise RuntimeError(
                "환경 reset 중 CMO 시나리오 종료 상태가 감지되었습니다. "
                "restart_scenario()가 정상적으로 완료되었는지와 "
                "scenario-ended 파일이 제거됐는지 확인하십시오."
            ) from exc

        def reset_values(current: Observation):
            if current.title != self.config.scenario.title:
                raise RuntimeError(
                    "reset 후 다른 CMO 시나리오의 관측을 받았습니다: "
                    f"expected={self.config.scenario.title!r}, "
                    f"actual={current.title!r}"
                )
            side = current.side(self.config.scenario.player_side)
            unit = self.select_controlled_unit(current)
            return unit, side.total_score

        controlled_unit, score = reset_values(observation)

        if self.config.auto_reset.enabled:
            if self._reset_reference is None:
                self._reset_reference = (
                    controlled_unit.guid,
                    observation.scenario_time,
                    score,
                )
            else:
                reference_guid, reference_time, reference_score = (
                    self._reset_reference
                )
                time_tolerance = max(
                    60,
                    self.config.protocol.observation_interval_seconds
                    * max(self.config.auto_reset.target_time_compression, 1)
                    * 3,
                )
                def matches_reference() -> bool:
                    return (
                        controlled_unit.guid == reference_guid
                        and abs(
                            observation.scenario_time - reference_time
                        ) <= time_tolerance
                        and score == reference_score
                    )

                deadline = (
                    time.monotonic()
                    + self.config.auto_reset.restart_timeout_seconds
                )
                while not matches_reference():
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise RuntimeError(
                            "reset 후 초기 상태와 일치하는 관측을 받지 못했습니다: "
                            f"expected_guid={reference_guid!r}, "
                            f"actual_guid={controlled_unit.guid!r}, "
                            f"expected_time~={reference_time}, "
                            f"actual_time={observation.scenario_time}, "
                            f"tolerance={time_tolerance}, "
                            f"expected_score={reference_score}, score={score}"
                        )
                    print(
                        "[CMO reset] reload 전 관측을 무시합니다: "
                        f"scenario_time={observation.scenario_time}"
                    )
                    observation = self.protocol.wait_for_new(
                        allow_existing_first=False,
                        timeout_seconds=remaining,
                    )
                    controlled_unit, score = reset_values(observation)

        start = self.config.scenario
        if start.start_position_enabled:
            start_latitude, start_longitude, start_heading = (
                start_position
                if start_position is not None
                else (
                    start.start_latitude,
                    start.start_longitude,
                    start.start_heading,
                )
            )
            position_action_id = self.protocol.send(
                set_position(
                    start.player_side,
                    start.controlled_unit,
                    start_latitude,
                    start_longitude,
                    start_heading,
                )
            )
            deadline = (
                time.monotonic()
                + self.config.auto_reset.restart_timeout_seconds
            )
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise RuntimeError(
                        "CMO did not apply the configured start position: "
                        f"expected=({start_latitude}, "
                        f"{start_longitude})"
                    )
                observation = self.protocol.wait_for_new(
                    allow_existing_first=False,
                    timeout_seconds=remaining,
                )
                controlled_unit, score = reset_values(observation)
                if (
                    observation.last_action_id == position_action_id
                    and
                    controlled_unit.latitude is not None
                    and controlled_unit.longitude is not None
                    and abs(
                        controlled_unit.latitude - start_latitude
                    ) <= 0.15
                    and abs(
                        controlled_unit.longitude - start_longitude
                    ) <= 0.15
                ):
                    break

        self._last_observation = observation
        self._previous_score = score
        self._step = 0

        return observation, {
            "step": 0,
            "score": score,
            "scenario_ended": False,
            "scenario_title": observation.title,
            "scenario_time": observation.scenario_time,
            "controlled_unit": controlled_unit.name,
            "start_latitude": controlled_unit.latitude,
            "start_longitude": controlled_unit.longitude,
            "start_heading": controlled_unit.heading_deg,
        }

    def step(self, action: Action) -> StepResult:
        if self._last_observation is None:
            raise RuntimeError(
                "CMOEnvironment.reset()을 먼저 호출해야 합니다."
            )

        action_id = self.protocol.send(action)

        scenario_ended = False
        scenario_success_hint = False
        termination_reason: str | None = None
        used_final_observation = False

        try:
            observation = self.protocol.wait_for_new(
                allow_existing_first=False
            )

            # observation 자체에 종료 상태가 포함된 경우도 처리한다.
            scenario_ended = observation.scenario_ended

            if scenario_ended:
                scenario_success_hint = (
                    self.protocol.has_recent_success_hint()
                )
                termination_reason = "observation_scenario_ended"

        except ScenarioEnded as exc:
            scenario_ended = True
            scenario_success_hint = exc.success_hint
            termination_reason = "scenario_ended_marker"

            # Lua 종료 처리에서 최종 observation을 내보낸 경우
            # 해당 observation을 우선 사용한다.
            if exc.final_observation is not None:
                observation = exc.final_observation
                used_final_observation = True
            else:
                # 종료 팝업 때문에 마지막 observation이 새로 생성되지 않은 경우
                # 이전 정상 observation을 사용한다.
                observation = self._last_observation

        score = observation.side(
            self.config.scenario.player_side
        ).total_score

        score_delta = score - self._previous_score

        self._previous_score = score
        self._last_observation = observation
        self._step += 1

        reward = (
            score_delta
            * self.config.reward.score_delta_scale
            + self.config.reward.step_penalty
        )

        if scenario_ended:
            reward += (
                self.config.reward.success_bonus
                if score > 0
                else self.config.reward.failure_penalty
            )

        return StepResult(
            observation=observation,
            reward=reward,
            terminated=scenario_ended,
            truncated=False,
            info={
                "step": self._step,
                "score": score,
                "score_delta": score_delta,
                "action": action.name,
                "action_id": action_id,
                "scenario_ended": scenario_ended,
                "termination_reason": termination_reason,
                "used_final_observation": used_final_observation,
                "scenario_success_hint": scenario_success_hint,
            },
        )

    def select_controlled_unit(
        self,
        observation: Observation,
    ) -> UnitState:
        units = observation.aircraft(
            self.config.scenario.player_side
        )
        configured = (
            self.config.scenario.controlled_unit.strip()
        )

        if configured:
            for unit in units:
                if unit.name == configured:
                    return unit

            available = ", ".join(
                unit.name for unit in units
            )

            raise RuntimeError(
                f"controlled_unit {configured!r}를 찾지 못했습니다. "
                f"Aircraft: {available}"
            )

        if not units:
            raise RuntimeError(
                f"{self.config.scenario.player_side!r} "
                "side의 Aircraft가 없습니다."
            )

        return units[0]
