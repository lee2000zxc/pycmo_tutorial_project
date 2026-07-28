from _common import PROJECT_ROOT
from cmo_tutorial.config import load_config
from cmo_tutorial.protocol import FileProtocol


def fmt(value, digits=2):
    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def main():
    cfg = load_config(PROJECT_ROOT / "config.yaml")
    protocol = FileProtocol(cfg)
    obs = protocol.wait_for_new(allow_existing_first=True)

    print(f"Scenario: {obs.title}")
    print(f"Time: {obs.scenario_time}, status={obs.status}, compression={obs.time_compression}")
    for side in obs.sides:
        print(f"Side: {side.name}, score={side.total_score}, contacts={len(side.contacts)}")

    print("\n=== Player units ===")
    for unit in obs.controllable_units(cfg.scenario.player_side):
        print(
            f"[{unit.unit_type}] {unit.name}\n"
            f"  GUID={unit.guid}\n"
            f"  lat/lon={fmt(unit.latitude, 6)}, {fmt(unit.longitude, 6)}\n"
            f"  alt={fmt(unit.altitude_m)} m, speed={fmt(unit.speed_kts)} kt, "
            f"heading={fmt(unit.heading_deg)} deg, fuel={fmt(unit.fuel_ratio, 3)}"
        )


if __name__ == "__main__":
    main()
