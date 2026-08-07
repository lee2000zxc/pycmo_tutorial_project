from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

from cmo_tutorial.scenario_controller import (
    ScenarioRestartError,
    SteamScenarioController,
)
from cmo_tutorial.window_controller import title_matches
from cmo_tutorial.protocol import ScenarioEnded


def _config():
    return SimpleNamespace(
        auto_reset=SimpleNamespace(
            scenario_window_title="Demo scenario",
            restart_timeout_seconds=12.0,
            menu_delay_seconds=0.5,
            target_time_compression=5,
        )
    )


def test_restart_invokes_powershell_script(tmp_path: Path):
    script = tmp_path / "restart.ps1"
    script.write_text("# test", encoding="utf-8")
    completed = SimpleNamespace(returncode=0, stdout="", stderr="")

    with patch(
        "cmo_tutorial.scenario_controller.subprocess.run",
        return_value=completed,
    ) as run:
        output = SteamScenarioController(_config(), script).restart()

    command = run.call_args.args[0]
    assert command[:2] == ["powershell.exe", "-NoProfile"]
    assert "Demo scenario" in command
    assert "-TargetTimeCompression" in command
    assert "5" in command
    assert output == ""


def test_restart_reports_script_failure(tmp_path: Path):
    script = tmp_path / "restart.ps1"
    script.write_text("# test", encoding="utf-8")
    completed = SimpleNamespace(
        returncode=1,
        stdout="",
        stderr="window not found",
    )

    with patch(
        "cmo_tutorial.scenario_controller.subprocess.run",
        Mock(return_value=completed),
    ):
        with pytest.raises(
            ScenarioRestartError,
            match="window not found",
        ):
            SteamScenarioController(_config(), script).restart()


def test_scenario_end_window_title_matching():
    assert title_matches("Scenario End", "Scenario End")
    assert title_matches("  Scenario   End - CMO  ", "scenario end")
    assert not title_matches("Side selection", "Scenario End")
    assert title_matches(
        "1 new messages of type: Special Messages",
        "Special Messages",
    )


def test_restart_script_handles_player_evaluation_dialog():
    script = (
        Path(__file__).resolve().parents[1]
        / "scripts"
        / "restart_cmo_scenario.ps1"
    ).read_text(encoding="utf-8")

    assert 'AppActivate("Player Evaluation")' in script
    assert script.count('$shell.SendKeys("{TAB}")') >= 3
    assert "$restartedFromEvaluation" in script


def test_scenario_end_can_carry_success_hint():
    error = ScenarioEnded("finished", success_hint=True)

    assert error.success_hint is True
