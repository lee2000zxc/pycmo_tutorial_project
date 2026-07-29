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
    fire_first_available_weapon,
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
        self.previous_action: int | None = None
        self.previous_contact_exists = False

        self.last_attack_step: int | None = None
        self.valid_attack = False
        self.invalid_attack = False
        self.invalid_attack_reason: str | None = None

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
        return self.env.select_controlled_unit(observation)

    @staticmethod
    def _relative_km(
        unit: UnitState,
        latitude: float,
        longitude: float,
    ) -> tuple[float, float]:
        if unit.latitude is None or unit.longitude is None:
            return 0.0, 0.0

        north_km = (latitude - unit.latitude) * 111.0
        east_km = (
            (longitude - unit.longitude)
            * 111.0
            * math.cos(math.radians(unit.latitude))
        )
        return north_km, east_km

    def _nearest_contact(
        self,
        observation: Observation,
        unit: UnitState,
    ) -> tuple[ContactState | None, float | None]:
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
            return north_km * north_km + east_km * east_km

        target = min(valid_contacts, key=distance_squared)
        north_km, east_km = self._relative_km(
            unit,
            target.latitude,
            target.longitude,
        )
        return target, math.hypot(north_km, east_km)

    @staticmethod
    def _unit_exists(
        observation: Observation,
        guid: str,
    ) -> bool:
        return any(
            unit.guid == guid
            for unit in observation.units
        )

    def _heading_alignment(
        self,
        observation: Observation,
        unit: UnitState,
    ) -> float:
        target, _ = self._nearest_contact(observation, unit)

        if (
            target is None
            or target.latitude is None
            or target.longitude is None
        ):
            return 0.0

        north_km, east_km = self._relative_km(
            unit,
            target.latitude,
            target.longitude,
        )

        target_bearing = math.atan2(east_km, north_km)
        heading_rad = math.radians(unit.heading_deg or 0.0)
        heading_error = math.atan2(
            math.sin(target_bearing - heading_rad),
            math.cos(target_bearing - heading_rad),
        )
        return math.cos(heading_error)

    def _vector(
        self,
        observation: Observation,
    ) -> np.ndarray:
        unit = self._unit(observation)
        side = observation.side(
            self.config.scenario.player_side
        )
        heading_rad = math.radians(unit.heading_deg or 0.0)
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
            bearing_rad = math.atan2(east_km, north_km)
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
                        (target.speed_kts or 0.0) / 1500.0,
                        0.0,
                        1.0,
                    )
                ),
                1.0,
            ]

        state = [
            float(
                np.clip(
                    (unit.altitude_m or 0.0) / 15000.0,
                    -1.0,
                    1.0,
                )
            ),
            float(
                np.clip(
                    (unit.speed_kts or 0.0) / 1500.0,
                    0.0,
                    1.0,
                )
            ),
            math.sin(heading_rad),
            math.cos(heading_rad),
            float(
                np.clip(unit.fuel_ratio or 0.0, 0.0, 1.0)
            ),
            *contact_state,
            float(
                np.clip(side.total_score / 1000.0, -1.0, 1.0)
            ),
        ]

        return np.asarray(state, dtype=np.float32)

    def reset(
        self,
        *,
        seed=None,
        options=None,
    ):
        super().reset(seed=seed)

        if (
            self.config.auto_reset.enabled
            and (
                self.reset_count > 0
                or self.config.auto_reset.reload_on_first_reset
            )
        ):
            self.env.restart_scenario()
        elif (
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

        self.valid_attack = False
        self.invalid_attack = False
        self.invalid_attack_reason = None
        self.previous_action = None
        self.last_attack_step = None

        unit = self._unit(observation)
        _, distance_km = self._nearest_contact(
            observation,
            unit,
        )

        self.previous_target_distance_km = distance_km
        self.previous_contact_exists = distance_km is not None
        self.previous_fuel_ratio = unit.fuel_ratio

        info.update(
            {
                "soft_reset": (
                    self.reset_count > 1
                    and not self.config.auto_reset.enabled
                ),
                "scenario_restarted": (
                    self.config.auto_reset.enabled
                    and (
                        self.reset_count > 1
                        or self.config.auto_reset.reload_on_first_reset
                    )
                ),
                "target_distance_km": distance_km,
                "controlled_unit": unit.name,
            }
        )
        return self._vector(observation), info

    def _mark_invalid_attack(self, reason: str):
        self.invalid_attack = True
        self.invalid_attack_reason = reason
        return noop()

    def _convert_action(
        self,
        action: int,
        unit: UnitState,
    ):
        self.valid_attack = False
        self.invalid_attack = False
        self.invalid_attack_reason = None

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

        if action == 9:
            if self.current_observation is None:
                return self._mark_invalid_attack(
                    "observation_not_available"
                )

            target, distance_km = self._nearest_contact(
                self.current_observation,
                unit,
            )

            if target is None or distance_km is None:
                return self._mark_invalid_attack(
                    "target_not_available"
                )

            if not (
                self.config.rl.attack_min_distance_km
                <= distance_km
                <= self.config.rl.attack_max_distance_km
            ):
                return self._mark_invalid_attack(
                    "target_out_of_attack_range"
                )

            if self.last_attack_step is not None:
                elapsed_steps = (
                    self.episode_steps
                    - self.last_attack_step
                )

                if (
                    elapsed_steps
                    < self.config.rl.attack_cooldown_steps
                ):
                    return self._mark_invalid_attack(
                        "attack_cooldown"
                    )

            if not self.config.rl.attack_weapon_candidates:
                return self._mark_invalid_attack(
                    "weapon_candidates_empty"
                )

            self.valid_attack = True
            self.last_attack_step = self.episode_steps

            return fire_first_available_weapon(
                attacker_guid=unit.guid,
                contact_guid=target.guid,
                candidate_dbids=(
                    self.config.rl.attack_weapon_candidates
                ),
                quantity=(
                    self.config.rl.attack_weapon_quantity
                ),
            )

        if unit.latitude is None or unit.longitude is None:
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
            raise RuntimeError("reset()을 먼저 호출하십시오.")

        action_value = int(np.asarray(action).item())
        previous_observation = self.current_observation
        previous_unit = self._unit(previous_observation)

        selected_action = self._convert_action(
            action_value,
            previous_unit,
        )
        result = self.env.step(selected_action)
        current_observation = result.observation

        ownship_destroyed = not self._unit_exists(
            current_observation,
            previous_unit.guid,
        )

        if ownship_destroyed:
            reward = (
                self.config.reward.step_penalty
                + self.config.reward.ownship_loss_penalty
            )
            reward = float(
                np.clip(
                    reward,
                    self.config.rl.reward_clip_min,
                    self.config.rl.reward_clip_max,
                )
            )
            self.current_observation = current_observation
            self.episode_steps += 1

            info = dict(result.info)
            info.update(
                {
                    "raw_action": action_value,
                    "selected_action": selected_action.name,
                    "target_distance_km": None,
                    "success": False,
                    "episode_steps": self.episode_steps,
                    "ownship_destroyed": True,
                    "invalid_attack": self.invalid_attack,
                    "invalid_attack_reason": self.invalid_attack_reason,
                }
            )

            return (
                self._vector(previous_observation),
                reward,
                True,
                False,
                info,
            )

        current_unit = self._unit(current_observation)
        _, distance_km = self._nearest_contact(
            current_observation,
            current_unit,
        )

        previous_score = previous_observation.side(
            self.config.scenario.player_side
        ).total_score
        current_score = current_observation.side(
            self.config.scenario.player_side
        ).total_score
        score_delta = current_score - previous_score

        reward = self.config.reward.step_penalty
        current_contact_exists = distance_km is not None

        if current_contact_exists and not self.previous_contact_exists:
            reward += self.config.rl.contact_acquired_reward
        elif current_contact_exists:
            reward += self.config.rl.contact_maintain_reward
        elif score_delta <= 0:
            reward += self.config.rl.no_contact_penalty

        if (
            self.previous_target_distance_km is not None
            and distance_km is not None
        ):
            max_distance = max(
                self.config.rl.max_target_distance_km,
                1.0,
            )
            previous_potential = (
                -self.previous_target_distance_km / max_distance
            )
            current_potential = -distance_km / max_distance
            distance_reward = (
                0.99 * current_potential - previous_potential
            )
            reward += (
                self.config.rl.distance_progress_scale
                * distance_reward
            )

        if distance_km is not None:
            if (
                self.config.rl.preferred_attack_min_km
                <= distance_km
                <= self.config.rl.preferred_attack_max_km
            ):
                reward += self.config.rl.preferred_range_reward
            elif distance_km < self.config.rl.too_close_distance_km:
                reward += self.config.rl.too_close_penalty

        alignment = self._heading_alignment(
            current_observation,
            current_unit,
        )
        reward += (
            self.config.rl.heading_alignment_scale * alignment
        )

        if self.invalid_attack:
            reward += self.config.rl.invalid_attack_penalty

        if self.valid_attack:
            reward += self.config.rl.valid_attack_reward

        if action_value == 9:
            reward += self.config.rl.attack_request_cost

        if (
            self.previous_action is not None
            and action_value != self.previous_action
        ):
            reward += self.config.rl.action_change_penalty

        score_reward = float(
            np.clip(
                self.config.reward.score_delta_scale * score_delta,
                -100.0,
                100.0,
            )
        )
        reward += score_reward

        enemy_destroyed = score_delta > 0
        if enemy_destroyed:
            reward += self.config.reward.kill_reward

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
                self.config.rl.fuel_penalty_scale * fuel_used
            )

        self.previous_target_distance_km = distance_km
        self.previous_contact_exists = current_contact_exists
        self.previous_fuel_ratio = current_unit.fuel_ratio
        self.previous_action = action_value
        self.current_observation = current_observation
        self.episode_steps += 1

        mission_success = bool(
            result.terminated and current_score > 0
        )
        success = bool(
            enemy_destroyed
            or mission_success
        )
        terminated = bool(
            result.terminated
            or enemy_destroyed
        )
        truncated = (
            self.episode_steps
            >= self.config.rl.max_episode_steps
        )

        if mission_success:
            reward += self.config.reward.mission_success_reward

        if result.terminated and not mission_success:
            reward += self.config.reward.failure_penalty

        reward = float(
            np.clip(
                reward,
                self.config.rl.reward_clip_min,
                self.config.rl.reward_clip_max,
            )
        )

        info = dict(result.info)
        info.update(
            {
                "raw_action": action_value,
                "selected_action": selected_action.name,
                "target_distance_km": distance_km,
                "success": success,
                "enemy_destroyed": enemy_destroyed,
                "mission_success": mission_success,
                "ownship_destroyed": ownship_destroyed,
                "episode_steps": self.episode_steps,
                "invalid_attack": self.invalid_attack,
                "invalid_attack_reason": self.invalid_attack_reason,
                "valid_attack": self.valid_attack,
                "last_attack_step": self.last_attack_step,
                "heading_alignment": alignment,
                "score_delta": score_delta,
            }
        )

        return (
            self._vector(current_observation),
            reward,
            terminated,
            truncated,
            info,
        )

