from _common import PROJECT_ROOT
import argparse
from stable_baselines3 import PPO
from cmo_tutorial.config import load_config
from cmo_tutorial.gym_env import CMOTutorialGymEnv

def main():
    p=argparse.ArgumentParser(); p.add_argument('--model',default=str(PROJECT_ROOT/'outputs'/'ppo'/'final_model.zip')); p.add_argument('--steps',type=int,default=100); args=p.parse_args()
    env=CMOTutorialGymEnv(load_config(PROJECT_ROOT/'config.yaml')); model=PPO.load(args.model,env=env)
    obs,info=env.reset(); total=0
    for i in range(args.steps):
        action,_=model.predict(obs,deterministic=True); obs,r,t,tr,info=env.step(action); total+=r
        print(f"step={i:03d} action={int(action)} reward={r:.3f} total={total:.3f} distance={info.get('target_distance_km')}")
        if t or tr:break
    env.close()
if __name__=='__main__':main()
