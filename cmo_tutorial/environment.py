from __future__ import annotations

from dataclasses import dataclass

from .actions import Action
from .config import AppConfig
from .models import Observation, UnitState
from .protocol import FileProtocol
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

    def restart_scenario(self) -> None:
        self.protocol.prepare_for_scenario_restart()
        message = self.scenario_controller.restart()
        if message:
            print(f"[CMO auto-load] {message}")

    def reset(self) -> tuple[Observation, dict[str, object]]:
        self.protocol.initialize_action_file()
        observation = self.protocol.wait_for_new(allow_existing_first=True)
        self._previous_score = observation.side(
            self.config.scenario.player_side
        ).total_score
        self._step = 0
        return observation, {"step": 0}

    def step(self, action: Action) -> StepResult:
        self.protocol.send(action)
        observation = self.protocol.wait_for_new(allow_existing_first=False)
        score = observation.side(self.config.scenario.player_side).total_score
        score_delta = score - self._previous_score
        self._previous_score = score
        self._step += 1

        reward = (
            score_delta * self.config.reward.score_delta_scale
            + self.config.reward.step_penalty
        )
        terminated = observation.scenario_ended
        if terminated:
            reward += (
                self.config.reward.success_bonus
                if score > 0
                else self.config.reward.failure_penalty
            )

        return StepResult(
            observation=observation,
            reward=reward,
            terminated=terminated,
            truncated=False,
            info={
                "step": self._step,
                "score": score,
                "score_delta": score_delta,
                "action": action.name,
            },
        )

    def select_controlled_unit(self, observation: Observation) -> UnitState:
        units = observation.aircraft(self.config.scenario.player_side)
        configured = self.config.scenario.controlled_unit.strip()

        if configured:
            for unit in units:
                if unit.name == configured:
                    return unit
            available = ", ".join(unit.name for unit in units)
            raise RuntimeError(
                f"controlled_unit {configured!r}를 찾지 못했습니다. Aircraft: {available}"
            )

        if not units:
            raise RuntimeError(
                f"{self.config.scenario.player_side!r} side의 Aircraft가 없습니다."
            )
        return units[0]
