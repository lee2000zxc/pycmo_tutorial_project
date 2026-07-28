from _common import PROJECT_ROOT
import argparse
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import CheckpointCallback
from stable_baselines3.common.monitor import Monitor
from cmo_tutorial.config import load_config
from cmo_tutorial.gym_env import CMOTutorialGymEnv

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--timesteps',type=int,default=1000)
    p.add_argument('--resume',default=''); args=p.parse_args()
    cfg=load_config(PROJECT_ROOT/'config.yaml')

    out=PROJECT_ROOT/'outputs'/'ppo'
    out.mkdir(parents=True,exist_ok=True)
    env=Monitor(CMOTutorialGymEnv(cfg),filename=str(out/'monitor.csv'))

    if args.resume:
        model=PPO.load(args.resume,env=env,device='auto')
    else: 
        model=PPO('MlpPolicy',env,learning_rate=3e-4,n_steps=32,batch_size=32,n_epochs=5,gamma=0.99,gae_lambda=0.95,clip_range=0.2,ent_coef=0.01,verbose=1,tensorboard_log=str(out/'tensorboard'),device='auto',seed=42)
    cb=CheckpointCallback(save_freq=200,save_path=str(out/'checkpoints'),name_prefix='cmo_ppo')

    try:
        model.learn(total_timesteps=args.timesteps,callback=cb,progress_bar=False,reset_num_timesteps=not bool(args.resume))
    finally:
        model.save(out/'final_model'); env.close()
if __name__=='__main__':main()
