local folder = _scriptfolder_
if folder == nil or folder == '' then error('bootstrap.lua를 절대경로로 실행하십시오.') end
folder = string.gsub(folder, '\\', '/')
if string.sub(folder,-1) ~= '/' then folder=folder .. '/' end
PYCMO_RUNTIME_CONFIG=nil
ScenEdit_RunScript(folder .. 'runtime_config.lua', true)
if PYCMO_RUNTIME_CONFIG==nil then error('PYCMO_RUNTIME_CONFIG가 없습니다.') end
ScenEdit_RunScript(folder .. 'pycmo_lib.lua', true)
ScenEdit_RunScript(folder .. 'init.lua', true)
setup_pycmo_tutorial3({folder=folder, action_filename=PYCMO_RUNTIME_CONFIG.action_filename, action_interval_seconds=PYCMO_RUNTIME_CONFIG.action_interval_seconds, observation_interval_seconds=PYCMO_RUNTIME_CONFIG.observation_interval_seconds, time_compression=PYCMO_RUNTIME_CONFIG.time_compression})
print('PyCMO Tutorial 3 bridge installed: ' .. folder)
