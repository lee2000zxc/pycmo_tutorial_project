from cmo_tutorial.inst import extract_xml_from_inst_text
from cmo_tutorial.parser import parse_observation_xml


def sample_xml():
    return """<?xml version='1.0' encoding='utf-8'?>
<Scenario>
  <Title>Aircraft Tutorial 3</Title>
  <Time>100</Time>
  <StartTime>0</StartTime>
  <Duration>1000</Duration>
  <Status>Running</Status>
  <TimeCompression>0</TimeCompression>
  <LastActionID>session:7</LastActionID>
  <AttackAssigned>true</AttackAssigned>
  <AssignedWeaponDBID>516</AssignedWeaponDBID>
  <Sides>
    <Side>
      <ID>s1</ID><Name>Blue</Name><TotalScore>10</TotalScore>
      <Contacts><Contact><ID>c1</ID><Name>Bandit</Name><Type>Air</Type>
      <Posture>H</Posture><IdentificationStatus>KnownClass</IdentificationStatus>
      <Lat>36.2</Lat><Lon>127.2</Lon></Contact></Contacts>
    </Side>
  </Sides>
  <ActiveUnits>
    <Aircraft>
      <ID>u1</ID><DBID>1</DBID><Name>Tanker [Wing Drogue &amp; Centerline Boom]</Name>
      <Side>Blue</Side><Lat>36.1</Lat><Lon>127.1</Lon>
      <CA>1000</CA><CH>90</CH><CS>300</CS><Thr>Cruise</Thr>
      <Fuel><FuelRec><CQ>50</CQ><MQ>100</MQ></FuelRec></Fuel>
    </Aircraft>
  </ActiveUnits>
</Scenario>"""


def test_parse_observation():
    obs = parse_observation_xml(sample_xml())
    assert obs.title == "Aircraft Tutorial 3"
    assert obs.last_action_id == "session:7"
    assert obs.attack_assigned is True
    assert obs.assigned_weapon_dbid == 516
    assert obs.side("Blue").total_score == 10
    contact = obs.side("Blue").contacts[0]
    assert contact.is_hostile
    assert contact.identification_status == "KnownClass"
    unit = obs.aircraft("Blue")[0]
    assert unit.name == "Tanker [Wing Drogue & Centerline Boom]"
    assert unit.fuel_ratio == 0.5


def test_extract_and_repair_bare_ampersand():
    bad = sample_xml().replace("&amp;", "&")
    wrapped = f"<Root><Comment>{bad}</Comment></Root>"
    xml = extract_xml_from_inst_text(wrapped)
    obs = parse_observation_xml(xml)
    assert "&" in obs.units[0].name
