local function xml_escape(value)
    if value == nil then return "" end
    local s = tostring(value)
    s = string.gsub(s, "&", "&amp;")
    s = string.gsub(s, "<", "&lt;")
    s = string.gsub(s, ">", "&gt;")
    s = string.gsub(s, '"', "&quot;")
    s = string.gsub(s, "'", "&apos;")
    return s
end

local function wrap_xml(value, tag)
    return "<" .. tag .. ">" .. xml_escape(value) .. "</" .. tag .. ">"
end

local function write_data(data, filename)
    local sides = VP_GetSides()
    if sides == nil or #sides == 0 then
        error("No valid side is available for ScenEdit_ExportInst")
    end
    ScenEdit_ExportInst(sides[1].name, {}, {
        filename=filename,
        comment=data
    })
end

local function export_contact(contact)
    local xml = ""
    xml = xml .. wrap_xml(contact.guid, "ID")
    xml = xml .. wrap_xml(contact.name, "Name")
    xml = xml .. wrap_xml(contact.type, "Type")
    if contact.altitude ~= nil then xml = xml .. wrap_xml(contact.altitude, "CA") end
    if contact.speed ~= nil then xml = xml .. wrap_xml(contact.speed, "CS") end
    if contact.latitude ~= nil then xml = xml .. wrap_xml(contact.latitude, "Lat") end
    if contact.longitude ~= nil then xml = xml .. wrap_xml(contact.longitude, "Lon") end
    return "<Contact>" .. xml .. "</Contact>"
end

local function export_contacts(side_name)
    local contacts = ScenEdit_GetContacts(side_name)
    local xml = ""
    if contacts ~= nil then
        for i = 1, #contacts do
            xml = xml .. export_contact(contacts[i])
        end
    end
    return "<Contacts>" .. xml .. "</Contacts>"
end

local function export_sides()
    local sides = VP_GetSides()
    local xml = ""
    for i = 1, #sides do
        local side = sides[i]
        local item = ""
        item = item .. wrap_xml(side.guid, "ID")
        item = item .. wrap_xml(side.name, "Name")
        item = item .. wrap_xml(ScenEdit_GetScore(side.name), "TotalScore")
        item = item .. export_contacts(side.name)
        xml = xml .. "<Side>" .. item .. "</Side>"
    end
    return xml
end

local function export_fuel(unit)
    if unit.fuel == nil then return "" end
    local records = ""
    for _, fuel in pairs(unit.fuel) do
        local item = ""
        item = item .. wrap_xml(fuel.type, "FT")
        item = item .. wrap_xml(fuel.current, "CQ")
        item = item .. wrap_xml(fuel.max, "MQ")
        records = records .. "<FuelRec>" .. item .. "</FuelRec>"
    end
    if records == "" then return "" end
    return "<Fuel>" .. records .. "</Fuel>"
end

local function export_unit(guid)
    local unit = ScenEdit_GetUnit({guid=guid})
    if unit == nil or unit.type == "Facility" then return "" end

    local xml = ""
    xml = xml .. wrap_xml(unit.guid, "ID")
    xml = xml .. wrap_xml(unit.dbid, "DBID")
    xml = xml .. wrap_xml(unit.name, "Name")
    xml = xml .. wrap_xml(unit.side, "Side")
    xml = xml .. wrap_xml(unit.classname, "ClassName")
    xml = xml .. wrap_xml(unit.latitude, "Lat")
    xml = xml .. wrap_xml(unit.longitude, "Lon")
    xml = xml .. wrap_xml(unit.altitude, "CA")
    xml = xml .. wrap_xml(unit.heading, "CH")
    xml = xml .. wrap_xml(unit.speed, "CS")
    xml = xml .. wrap_xml(unit.throttle, "Thr")
    xml = xml .. wrap_xml(tostring(unit.isOperating), "IsOperating")
    xml = xml .. wrap_xml(unit.condition, "Condition")
    if unit.hostFacility ~= nil then xml = xml .. wrap_xml(unit.hostFacility.name, "HostFacility") end
    xml = xml .. export_fuel(unit)
    return "<" .. unit.type .. ">" .. xml .. "</" .. unit.type .. ">"
end

local function export_units()
    local sides = VP_GetSides()
    local xml = ""
    for i = 1, #sides do
        local units = sides[i].units
        if units ~= nil then
            for j = 1, #units do
                local ok, result = pcall(function()
                    return export_unit(units[j].guid)
                end)
                if ok then
                    xml = xml .. result
                else
                    print("PyCMO skipped unit: " .. tostring(result))
                end
            end
        end
    end
    return xml
end

function PycmoScenarioHasEnded(ended)
    local scenario = VP_GetScenario()
    write_data(tostring(ended), scenario.Title .. "_scen_has_ended.inst")
end

function PycmoExportScenarioToXML()
    local scenario = VP_GetScenario()
    local xml = "<?xml version='1.0' encoding='utf-8'?><Scenario>"
    xml = xml .. wrap_xml(scenario.Title, "Title")
    xml = xml .. wrap_xml(scenario.FileName, "FileName")
    xml = xml .. wrap_xml(scenario.CurrentTimeNum, "Time")
    xml = xml .. wrap_xml(scenario.StartTimeNum, "StartTime")
    xml = xml .. wrap_xml(scenario.DurationNum, "Duration")
    xml = xml .. wrap_xml(scenario.Status, "Status")
    xml = xml .. wrap_xml(scenario.TimeCompression, "TimeCompression")
    xml = xml .. "<Sides>" .. export_sides() .. "</Sides>"
    xml = xml .. "<ActiveUnits>" .. export_units() .. "</ActiveUnits>"
    xml = xml .. "</Scenario>"
    write_data(xml, scenario.Title .. ".inst")
end
