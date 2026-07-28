from _common import PROJECT_ROOT
from cmo_tutorial.config import load_config
import psutil


def main():
    cfg = load_config(PROJECT_ROOT / "config.yaml")
    checks = {
        "CMO install": cfg.cmo.install_dir.exists(),
        "ImportExport": cfg.cmo.import_export_dir.exists(),
        "Lua": cfg.cmo.lua_dir.exists(),
        "Observation": cfg.observation_path.exists(),
        "Action folder": cfg.action_path.parent.exists(),
    }
    process_found = any(
        (proc.info.get("name") or "").lower() == cfg.cmo.process_name.lower()
        for proc in psutil.process_iter(["name"])
    )
    checks[f"Process {cfg.cmo.process_name}"] = process_found

    print("=== PyCMO Tutorial 3 진단 ===")
    for name, ok in checks.items():
        print(f"[{'OK' if ok else 'FAIL'}] {name}")

    print(f"Observation path: {cfg.observation_path}")
    print(f"Action path:      {cfg.action_path}")


if __name__ == "__main__":
    main()
