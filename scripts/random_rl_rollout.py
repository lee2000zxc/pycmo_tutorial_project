from _common import PROJECT_ROOT
import argparse
from cmo_tutorial.config import load_config
from cmo_tutorial.gym_env import CMOTutorialGymEnv

def main():
    p=argparse.ArgumentParser(); p.add_argument('--steps',type=int,default=20); args=p.parse_args()
    env=CMOTutorialGymEnv(load_config(PROJECT_ROOT/'config.yaml')); obs,info=env.reset(); print('initial:',obs,info)
    for i in range(args.steps):
        a=env.action_space.sample(); obs,r,t,tr,info=env.step(a); print(i,a,r,info)
        if t or tr:break
if __name__=='__main__':main()
