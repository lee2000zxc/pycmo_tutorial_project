local function rm_event(n) pcall(function() ScenEdit_SetEvent(n,{mode='remove'}) end) end
local function rm_trigger(n) pcall(function() ScenEdit_SetTrigger({description=n,mode='remove'}) end) end
local function rm_action(n) pcall(function() ScenEdit_SetAction({description=n,mode='remove'}) end) end
local function remove_all(e,t,a) rm_event(e);rm_trigger(t);rm_action(a) end
local function interval_code(seconds)
  local map={[1]='0',[5]='1',[15]='2',[30]='3',[60]='4',[300]='5',[900]='6',[1800]='7',[3600]='8'}
  local code=map[tonumber(seconds)]
  if code==nil then print('Unsupported interval; using 5 sec'); code='1' end
  return code
end
local function add_regular(e,t,a,seconds,script)
  remove_all(e,t,a)
  local ev=ScenEdit_SetEvent(e,{mode='add',IsActive=true,IsRepeatable=true,IsShown=false})
  ScenEdit_SetTrigger({mode='add',type='RegularTime',Interval=interval_code(seconds),description=t})
  ScenEdit_SetAction({mode='add',type='LuaScript',description=a,ScriptText=script})
  ScenEdit_SetEventTrigger(ev.guid,{mode='add',description=t})
  ScenEdit_SetEventAction(ev.guid,{mode='add',description=a})
end
function setup_pycmo_tutorial3(o)
  local folder=string.gsub(o.folder,'\\','/'); if string.sub(folder,-1)~='/' then folder=folder..'/' end
  local runtime=folder..'runtime_config.lua'; local lib=folder..'pycmo_lib.lua'; local af=folder..o.action_filename
  -- Persisted while the scenario is running. Generated action files use this
  -- sequence to guarantee at-most-once execution across RegularTime ticks.
  PYCMO_LAST_ACTION_ID = nil
  local observation_setup="ScenEdit_RunScript('"..runtime.."', true)\r\nScenEdit_RunScript('"..lib.."', true)\r\n"
  add_regular('PyCMO Execute agent action','PyCMO Execute agent action trigger','PyCMO Execute agent action action',o.action_interval_seconds,"local ok,err=pcall(function() ScenEdit_RunScript('"..af.."',true) end)\r\nif not ok then print(err) end")
  add_regular('PyCMO Export observation','PyCMO Export observation trigger','PyCMO Export observation action',o.observation_interval_seconds,observation_setup..'PycmoExportScenarioToXML()')
  PycmoScenarioHasEnded(false); PycmoExportScenarioToXML(); VP_SetTimeCompression(o.time_compression or 0)
end
