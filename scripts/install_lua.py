from _common import PROJECT_ROOT
from cmo_tutorial.config import load_config
import shutil


def lua_string(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"') + '"'

def main():
    cfg=load_config(PROJECT_ROOT/'config.yaml'); source=PROJECT_ROOT/'lua'; target=cfg.cmo.lua_dir/'pycmo_tutorial3'; target.mkdir(parents=True,exist_ok=True)
    for f in source.glob('*.lua'): shutil.copy2(f,target/f.name); print('Installed:',target/f.name)
    contact_types = ", ".join(
        lua_string(value) for value in cfg.rl.target_contact_types
    )
    text=f'''PYCMO_RUNTIME_CONFIG = {{
  action_filename = {lua_string(cfg.protocol.action_filename)},
  action_interval_seconds = {cfg.protocol.action_interval_seconds},
  observation_interval_seconds = {cfg.protocol.observation_interval_seconds},
  time_compression = {cfg.protocol.time_compression},
  player_side = {lua_string(cfg.scenario.player_side)},
  controlled_unit = {lua_string(cfg.scenario.controlled_unit)},
  target_contact_types = {{{contact_types}}}
}}
print("PyCMO runtime config loaded.")
'''
    (target/'runtime_config.lua').write_text(text,encoding='utf-8'); print('Generated:',target/'runtime_config.lua')
if __name__=='__main__':main()
