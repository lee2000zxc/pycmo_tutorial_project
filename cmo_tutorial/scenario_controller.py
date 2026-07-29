from __future__ import annotations

from pathlib import Path
import subprocess

from .config import AppConfig


class ScenarioRestartError(RuntimeError):
    """Raised when the CMO Steam UI could not restart the scenario."""


class SteamScenarioController:
    """Reload the first recent Steam scenario through the CMO UI."""

    def __init__(
        self,
        config: AppConfig,
        script_path: Path | None = None,
    ):
        self.config = config
        self.script_path = script_path or (
            Path(__file__).resolve().parents[1]
            / "scripts"
            / "restart_cmo_scenario.ps1"
        )

    def restart(self) -> str:
        if not self.script_path.is_file():
            raise ScenarioRestartError(
                f"시나리오 재시작 스크립트가 없습니다: {self.script_path}"
            )

        reset = self.config.auto_reset
        command = [
            "powershell.exe",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(self.script_path),
            "-ScenarioWindowTitle",
            reset.scenario_window_title,
            "-TimeoutSeconds",
            str(reset.restart_timeout_seconds),
            "-MenuDelaySeconds",
            str(reset.menu_delay_seconds),
            "-TargetTimeCompression",
            str(reset.target_time_compression),
        ]

        try:
            result = subprocess.run(
                command,
                check=False,
                capture_output=True,
                text=True,
                errors="replace",
                timeout=reset.restart_timeout_seconds + 10.0,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ScenarioRestartError(
                "CMO 최근 시나리오 불러오기 자동화를 실행하지 못했습니다."
            ) from exc

        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise ScenarioRestartError(
                "CMO의 File > Load Recent에서 첫 시나리오를 "
                "불러오지 못했습니다."
                + (f"\n{detail}" if detail else "")
            )

        return result.stdout.strip()
