from _common import PROJECT_ROOT

import argparse
import csv
from pathlib import Path

from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import (
    BaseCallback,
    CallbackList,
    CheckpointCallback,
)
from stable_baselines3.common.monitor import Monitor

from cmo_tutorial.config import load_config
from cmo_tutorial.gym_env import CMOTutorialGymEnv
import gymnasium as gym

class EpisodeRewardCallback(BaseCallback):
    """Print and persist one row for every completed episode."""

    def __init__(self, csv_path: Path):
        super().__init__(verbose=0)
        self.csv_path = csv_path
        self.episode_number = self._existing_episode_count()

    def _existing_episode_count(self) -> int:
        if not self.csv_path.exists():
            return 0
        with self.csv_path.open(
            "r",
            encoding="utf-8",
            newline="",
        ) as handle:
            return max(sum(1 for _ in csv.DictReader(handle)), 0)

    def _append(
        self,
        reward: float,
        length: int,
        elapsed_seconds: float,
    ) -> None:
        write_header = not self.csv_path.exists()
        self.csv_path.parent.mkdir(parents=True, exist_ok=True)

        with self.csv_path.open(
            "a",
            encoding="utf-8",
            newline="",
        ) as handle:
            writer = csv.writer(handle)
            if write_header:
                writer.writerow(
                    [
                        "episode",
                        "total_timesteps",
                        "reward",
                        "length",
                        "elapsed_seconds",
                    ]
                )
            writer.writerow(
                [
                    self.episode_number,
                    self.num_timesteps,
                    f"{reward:.6f}",
                    length,
                    f"{elapsed_seconds:.6f}",
                ]
            )

    def _on_step(self) -> bool:
        infos = self.locals.get("infos", [])
        dones = self.locals.get("dones", [])

        for done, info in zip(dones, infos):
            episode = info.get("episode") if done else None
            if episode is None:
                continue

            self.episode_number += 1
            reward = float(episode["r"])
            length = int(episode["l"])
            elapsed_seconds = float(episode["t"])
            self._append(reward, length, elapsed_seconds)

            print(
                "[Episode] "
                f"{self.episode_number} | "
                f"reward={reward:.6f} | "
                f"length={length} | "
                f"total_timesteps={self.num_timesteps}"
            )

            self.logger.record("episode/reward", reward)
            self.logger.record("episode/length", length)

        return True


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--timesteps", type=int, default=1000)
    parser.add_argument("--resume", default="")
    args = parser.parse_args()

    config = load_config(PROJECT_ROOT / "config.yaml")
    output_dir = PROJECT_ROOT / "outputs" / "ppo"
    output_dir.mkdir(parents=True, exist_ok=True)

    environment = Monitor(
        CMOTutorialGymEnv(config),
        filename=str(output_dir / "monitor.csv"),
        info_keywords=(
            "success",
            "mission_success",
            "target_reached",
            "enemy_destroyed",
            "ownship_destroyed",
        ),
    )

    if args.resume:
        model = PPO.load(
            args.resume,
            env=environment,
            device="auto",
        )
    else:
        model = PPO(
            "MlpPolicy",
            environment,
            learning_rate=3e-4,
            n_steps=32,
            batch_size=32,
            n_epochs=5,
            gamma=0.99,
            gae_lambda=0.95,
            clip_range=0.2,
            ent_coef=0.01,
            verbose=1,
            tensorboard_log=str(output_dir / "tensorboard"),
            device="auto",
            seed=42,
        )

    callbacks = CallbackList(
        [
            CheckpointCallback(
                save_freq=200,
                save_path=str(output_dir / "checkpoints"),
                name_prefix="cmo_ppo",
            ),
            EpisodeRewardCallback(
                output_dir / "episode_rewards.csv"
            ),
        ]
    )

    try:
        model.learn(
            total_timesteps=args.timesteps,
            callback=callbacks,
            progress_bar=False,
            reset_num_timesteps=not bool(args.resume),
        )
    finally:
        model.save(output_dir / "final_model")
        environment.close()


if __name__ == "__main__":
    main()
