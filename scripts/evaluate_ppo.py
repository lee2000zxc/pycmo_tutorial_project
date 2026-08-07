from _common import PROJECT_ROOT

import argparse

import numpy as np
from stable_baselines3 import PPO

from cmo_tutorial.config import load_config
from cmo_tutorial.gym_env import CMOTutorialGymEnv


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--model",
        default=str(PROJECT_ROOT / "outputs" / "ppo" / "final_model.zip"),
    )
    parser.add_argument("--episodes", type=int, default=10)
    parser.add_argument("--steps", type=int, default=100)
    args = parser.parse_args()

    if args.episodes <= 0 or args.steps <= 0:
        parser.error("--episodes and --steps must be positive")

    env = CMOTutorialGymEnv(load_config(PROJECT_ROOT / "config.yaml"))
    model = PPO.load(args.model, env=env)
    successes = 0
    ownship_losses = 0
    episode_rewards: list[float] = []

    try:
        for episode in range(1, args.episodes + 1):
            observation, _ = env.reset()
            total_reward = 0.0
            final_info: dict[str, object] = {}

            for step in range(1, args.steps + 1):
                action, _ = model.predict(observation, deterministic=True)
                observation, reward, terminated, truncated, info = env.step(
                    action
                )
                total_reward += float(reward)
                final_info = info

                print(
                    f"episode={episode:03d} step={step:03d} "
                    f"action={int(np.asarray(action).item())} "
                    f"reward={reward:.3f} total={total_reward:.3f} "
                    f"distance={info.get('target_distance_km')}"
                )

                if terminated or truncated:
                    break

            success = bool(final_info.get("success", False))
            ownship_destroyed = bool(
                final_info.get("ownship_destroyed", False)
            )
            successes += int(success)
            ownship_losses += int(ownship_destroyed)
            episode_rewards.append(total_reward)
            print(
                f"[Evaluation] episode={episode} reward={total_reward:.3f} "
                f"success={success} ownship_destroyed={ownship_destroyed}"
            )
    finally:
        env.close()

    mean_reward = float(np.mean(episode_rewards))
    print(
        "[Evaluation summary] "
        f"episodes={args.episodes} "
        f"success_rate={successes / args.episodes:.3f} "
        f"ownship_loss_rate={ownship_losses / args.episodes:.3f} "
        f"mean_reward={mean_reward:.3f}"
    )


if __name__ == "__main__":
    main()
