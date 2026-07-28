from __future__ import annotations

import math

import numpy as np

try:
    import gymnasium as gym
    from gymnasium import spaces
except ImportError as exc:
    raise ImportError(
        "pip install -r requirements-rl.txt를 실행하십시오."
    ) from exc

from .actions import (
    attack_contact,
    launch,
    noop,
    set_course,
)
from .config import AppConfig
from .environment import CMOEnvironment
from .models import ContactState, Observation, UnitState


class ManualScenarioResetRequired(RuntimeError):
    pass


class CMOTutorialGymEnv(gym.Env):
    metadata = {"render_modes": []}

    def __init__(self, config: AppConfig):
        super().__init__()

        self.config = config
        self.env = CMOEnvironment(config)

        self.current_observation: Observation | None = None
        self.episode_steps = 0
        self.reset_count = 0

        self.previous_target_distance_km: float | None = None
        self.previous_fuel_ratio: float | None = None

        # 0: no-op
        # 1~8: 이동
        # 9: 가장 가까운 contact 공격
        self.action_space = spaces.Discrete(10)

        self.observation_space = spaces.Box(
            low=-1.0,
            high=1.0,
            shape=(14,),
            dtype=np.float32,
        )

    def _unit(
        self,
        observation: Observation,
    ) -> UnitState:
        return self.env.select_controlled_unit(
            observation
        )

    @staticmethod
    def _relative_km(
        unit: UnitState,
        latitude: float,
        longitude: float,
    ) -> tuple[float, float]:
        if unit.latitude is None or unit.longitude is None:
            return 0.0, 0.0

        north_km = (
            latitude - unit.latitude
        ) * 111.0

        east_km = (
            longitude - unit.longitude
        ) * 111.0 * math.cos(
            math.radians(unit.latitude)
        )

        return north_km, east_km

    def _nearest_contact(
        self,
        observation: Observation,
        unit: UnitState,
    ) -> tuple[ContactState | None, float | None]:
        """
        가장 가까운 contact와 거리를 함께 반환한다.

        반환:
            (contact, distance_km)

        contact가 없으면:
            (None, None)
        """
        if unit.latitude is None or unit.longitude is None:
            return None, None

        side = observation.side(
            self.config.scenario.player_side
        )

        valid_contacts = [
            contact
            for contact in side.contacts
            if contact.latitude is not None
            and contact.longitude is not None
            and contact.guid
        ]

        if not valid_contacts:
            return None, None

        def distance_squared(
            contact: ContactState,
        ) -> float:
            north_km, east_km = self._relative_km(
                unit,
                contact.latitude,
                contact.longitude,
            )

            return (
                north_km * north_km
                + east_km * east_km
            )

        target = min(
            valid_contacts,
            key=distance_squared,
        )

        north_km, east_km = self._relative_km(
            unit,
            target.latitude,
            target.longitude,
        )

        distance_km = math.hypot(
            north_km,
            east_km,
        )

        return target, distance_km

    def _vector(
        self,
        observation: Observation,
    ) -> np.ndarray:
        unit = self._unit(observation)

        side = observation.side(
            self.config.scenario.player_side
        )

        heading_rad = math.radians(
            unit.heading_deg or 0.0
        )

        target, distance_km = self._nearest_contact(
            observation,
            unit,
        )

        if target is None or distance_km is None:
            contact_state = [
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
            ]
        else:
            north_km, east_km = self._relative_km(
                unit,
                target.latitude,
                target.longitude,
            )

            bearing_rad = math.atan2(
                east_km,
                north_km,
            )

            altitude_difference = (
                (target.altitude_m or 0.0)
                - (unit.altitude_m or 0.0)
            )

            contact_state = [
                float(
                    np.clip(
                        north_km
                        / self.config.rl.max_target_distance_km,
                        -1.0,
                        1.0,
                    )
                ),
                float(
                    np.clip(
                        east_km
                        / self.config.rl.max_target_distance_km,
                        -1.0,
                        1.0,
                    )
                ),
                float(
                    np.clip(
                        altitude_difference / 15000.0,
                        -1.0,
                        1.0,
                    )
                ),
                float(
                    np.clip(
                        distance_km
                        / self.config.rl.max_target_distance_km,
                        0.0,
                        1.0,
                    )
                ),
                math.sin(bearing_rad),
                math.cos(bearing_rad),
                float(
                    np.clip(
                        (target.speed_kts or 0.0)
                        / 1500.0,
                        0.0,
                        1.0,
                    )
                ),
                1.0,
            ]

        state = [
            float(
                np.clip(
                    (unit.altitude_m or 0.0)
                    / 15000.0,
                    -1.0,
                    1.0,
                )
            ),
            float(
                np.clip(
                    (unit.speed_kts or 0.0)
                    / 1500.0,
                    0.0,
                    1.0,
                )
            ),
            math.sin(heading_rad),
            math.cos(heading_rad),
            float(
                np.clip(
                    unit.fuel_ratio or 0.0,
                    0.0,
                    1.0,
                )
            ),
            *contact_state,
            float(
                np.clip(
                    side.total_score / 1000.0,
                    -1.0,
                    1.0,
                )
            ),
        ]

        return np.asarray(
            state,
            dtype=np.float32,
        )

    def reset(
        self,
        *,
        seed=None,
        options=None,
    ):
        super().reset(seed=seed)

        if (
            self.reset_count > 0
            and not self.config.rl.soft_reset
        ):
            raise ManualScenarioResetRequired(
                "CMO 시나리오를 초기 상태로 다시 불러오고 "
                "bootstrap.lua를 실행한 뒤 학습을 재시작하십시오."
            )

        observation, info = self.env.reset()

        self.current_observation = observation
        self.episode_steps = 0
        self.reset_count += 1

        unit = self._unit(observation)

        _, distance_km = self._nearest_contact(
            observation,
            unit,
        )

        self.previous_target_distance_km = (
            distance_km
        )

        self.previous_fuel_ratio = (
            unit.fuel_ratio
        )

        info.update(
            {
                "soft_reset": self.reset_count > 1,
                "target_distance_km": distance_km,
            }
        )

        return self._vector(observation), info

    def _convert_action(
        self,
        action: int,
        unit: UnitState,
    ):
        # 지상에 있는 경우 RL 행동보다 출격을 우선한다.
        if (
            self.config.rl.auto_launch
            and unit.is_operating is False
        ):
            return launch(
                self.config.scenario.player_side,
                unit.name,
            )

        if action == 0:
            return noop()

        # 행동 9: 가장 가까운 contact 공격
        if action == 9:
            if self.current_observation is None:
                return noop()

            target, _ = self._nearest_contact(
                self.current_observation,
                unit,
            )

            if target is None:
                return noop()

            return attack_contact(
                attacker_guid=unit.guid,
                contact_guid=target.guid,
            )

        if (
            unit.latitude is None
            or unit.longitude is None
        ):
            return noop()

        offsets = {
            1: (1, 0),
            2: (1, 1),
            3: (0, 1),
            4: (-1, 1),
            5: (-1, 0),
            6: (-1, -1),
            7: (0, -1),
            8: (1, -1),
        }

        if action not in offsets:
            return noop()

        delta_lat, delta_lon = offsets[action]

        step = self.config.rl.waypoint_step_deg

        return set_course(
            self.config.scenario.player_side,
            unit.name,
            unit.latitude + delta_lat * step,
            unit.longitude + delta_lon * step,
        )

    def step(self, action):
        if self.current_observation is None:
            raise RuntimeError(
                "reset()을 먼저 호출하십시오."
            )

        action_value = int(
            np.asarray(action).item()
        )

        previous_observation = (
            self.current_observation
        )

        previous_unit = self._unit(
            previous_observation
        )

        selected_action = self._convert_action(
            action_value,
            previous_unit,
        )

        result = self.env.step(
            selected_action
        )

        current_observation = (
            result.observation
        )

        current_unit = self._unit(
            current_observation
        )

        _, distance_km = self._nearest_contact(
            current_observation,
            current_unit,
        )

        reward = self.config.reward.step_penalty

        if distance_km is None:
            reward += (
                self.config.rl.no_contact_penalty
            )
        else:
            reward += (
                self.config.rl.contact_reward
            )

            if (
                self.previous_target_distance_km
                is not None
            ):
                progress_km = (
                    self.previous_target_distance_km
                    - distance_km
                )

                progress_km = float(
                    np.clip(
                        progress_km,
                        -10.0,
                        10.0,
                    )
                )

                reward += (
                    self.config.rl.distance_progress_scale
                    * progress_km
                )

            self.previous_target_distance_km = (
                distance_km
            )

        previous_score = previous_observation.side(
            self.config.scenario.player_side
        ).total_score

        current_score = current_observation.side(
            self.config.scenario.player_side
        ).total_score

        score_delta = (
            current_score - previous_score
        )

        reward += (
            self.config.reward.score_delta_scale
            * score_delta
        )

        if (
            self.previous_fuel_ratio is not None
            and current_unit.fuel_ratio is not None
        ):
            fuel_used = max(
                0.0,
                self.previous_fuel_ratio
                - current_unit.fuel_ratio,
            )

            reward -= (
                self.config.rl.fuel_penalty_scale
                * fuel_used
            )

        self.previous_fuel_ratio = (
            current_unit.fuel_ratio
        )

        self.current_observation = (
            current_observation
        )

        self.episode_steps += 1

        success = (
            distance_km is not None
            and distance_km
            <= self.config.rl.target_success_distance_km
        )

        terminated = bool(
            result.terminated or success
        )

        truncated = (
            self.episode_steps
            >= self.config.rl.max_episode_steps
        )

        if success:
            reward += (
                self.config.reward.success_bonus
            )

        info = dict(result.info)

        info.update(
            {
                "raw_action": action_value,
                "selected_action": selected_action.name,
                "target_distance_km": distance_km,
                "success": success,
                "episode_steps": self.episode_steps,
            }
        )

        return (
            self._vector(current_observation),
            float(reward),
            terminated,
            truncated,
            info,
        )