from pathlib import Path

from cmo_tutorial.config import load_config


def test_project_config_loads_scenario_end_dialog_settings():
    config = load_config(Path(__file__).parents[1] / "config.yaml")
    assert config.auto_reset.dismiss_scenario_end_dialog is True
    assert config.auto_reset.scenario_end_window_title == "Scenario End"
    assert config.auto_reset.dismiss_special_messages_dialog is True
    assert config.auto_reset.special_messages_window_title == "Special Messages"
    assert config.reward.timeout_penalty == -2.0
    assert config.rl.contact_maintain_reward == 0.0
    assert config.rl.preferred_range_reward == 0.02
    assert config.scenario.start_position_enabled is True
    assert config.scenario.start_heading == 90.0
    assert config.scenario.randomize_start_position is True
    assert config.scenario.start_position_random_radius_km == 10.0
    assert config.scenario.randomize_start_heading is True
