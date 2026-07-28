from _common import PROJECT_ROOT
from cmo_tutorial.config import load_config
import shutil

def main():
    cfg=load_config(PROJECT_ROOT/'config.yaml'); source=PROJECT_ROOT/'lua'; target=cfg.cmo.lua_dir/'pycmo_tutorial3'; target.mkdir(parents=True,exist_ok=True)
    for f in source.glob('*.lua'): shutil.copy2(f,target/f.name); print('Installed:',target/f.name)
    name=cfg.protocol.action_filename.replace('\\\\','\\\\\\\\').replace('"','\\\\"')
    text=f'''PYCMO_RUNTIME_CONFIG = {{\n  action_filename = "{name}",\n  action_interval_seconds = {cfg.protocol.action_interval_seconds},\n  observation_interval_seconds = {cfg.protocol.observation_interval_seconds},\n  time_compression = {cfg.protocol.time_compression}\n}}\nprint("PyCMO runtime config loaded.")\n'''
    (target/'runtime_config.lua').write_text(text,encoding='utf-8'); print('Generated:',target/'runtime_config.lua')
if __name__=='__main__':main()
