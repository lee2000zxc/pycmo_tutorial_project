from _common import PROJECT_ROOT
from stable_baselines3.common.env_checker import check_env
from cmo_tutorial.config import load_config
from cmo_tutorial.gym_env import CMOTutorialGymEnv

def main():
    env=CMOTutorialGymEnv(load_config(PROJECT_ROOT/'config.yaml'))
    check_env(env,warn=True,skip_render_check=True)
    print('SB3 environment check completed.')
if __name__=='__main__':main()
