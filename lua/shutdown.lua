local function remove_event(name)
    pcall(function()
        ScenEdit_SetEvent(name, {mode='remove'})
    end)
end

local function remove_trigger(name)
    pcall(function()
        ScenEdit_SetTrigger({description=name, mode='remove'})
    end)
end

local function remove_action(name)
    pcall(function()
        ScenEdit_SetAction({description=name, mode='remove'})
    end)
end

remove_event('PyCMO Export observation')
remove_event('PyCMO Execute agent action')
remove_trigger('PyCMO Export observation trigger')
remove_trigger('PyCMO Execute agent action trigger')
remove_action('PyCMO Export observation action')
remove_action('PyCMO Execute agent action action')

PYCMO_LAST_ACTION_ID = nil
PYCMO_LAST_ACTION_RESULT_ID = nil
PYCMO_LAST_ATTACK_ASSIGNED = nil
PYCMO_LAST_ASSIGNED_WEAPON_DBID = nil

print('PyCMO Tutorial 3 bridge stopped')
