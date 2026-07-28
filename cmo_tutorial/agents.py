from __future__ import annotations

from dataclasses import dataclass
import math
import random

from .actions import Action, noop, rtb, set_course_speed_altitude
from .config import AppConfig
from .environment import CMOEnvironment
from .models import Observation, UnitState


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius_km = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * radius_km * math.asin(math.sqrt(a))


class RandomWaypointAgent:
    def __init__(self, config: AppConfig, radius_deg: float = 0.03, seed: int = 0):
        self.config = config
        self.radius_deg = radius_deg
        self.random = random.Random(seed)

    def act(self, unit: UnitState, observation: Observation) -> Action:
        if unit.latitude is None or unit.longitude is None:
            return noop()
        angle = self.random.uniform(0.0, 2.0 * math.pi)
        lat = unit.latitude + self.radius_deg * math.cos(angle)
        lon = unit.longitude + self.radius_deg * math.sin(angle)
        return set_course_speed_altitude(
            self.config.scenario.player_side,
            unit.name,
            lat,
            lon,
            self.config.tutorial3.default_speed_kts,
            self.config.tutorial3.default_altitude_m,
        )


@dataclass
class Tutorial3RouteAgent:
    config: AppConfig
    waypoint_index: int = 0

    def act(self, unit: UnitState, observation: Observation) -> Action:
        route = self.config.tutorial3.route
        if not route:
            raise RuntimeError(
                "config.yaml의 tutorial3.route가 비어 있습니다. Tutorial #3 목표점을 입력하십시오."
            )

        if self.waypoint_index >= len(route):
            return rtb(self.config.scenario.player_side, unit.name)

        target_lat, target_lon = route[self.waypoint_index]
        if unit.latitude is not None and unit.longitude is not None:
            distance = haversine_km(
                unit.latitude, unit.longitude, target_lat, target_lon
            )
            if distance <= self.config.tutorial3.waypoint_reached_km:
                self.waypoint_index += 1
                if self.waypoint_index >= len(route):
                    return rtb(self.config.scenario.player_side, unit.name)
                target_lat, target_lon = route[self.waypoint_index]

        return set_course_speed_altitude(
            self.config.scenario.player_side,
            unit.name,
            target_lat,
            target_lon,
            self.config.tutorial3.default_speed_kts,
            self.config.tutorial3.default_altitude_m,
        )
