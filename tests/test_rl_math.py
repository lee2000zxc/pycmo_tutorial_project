import pytest; pytest.importorskip("gymnasium")
from cmo_tutorial.gym_env import CMOTutorialGymEnv
from cmo_tutorial.models import UnitState
from cmo_tutorial.models import ContactState, Observation, SideState
from types import SimpleNamespace

def test_relative_km():
    u=UnitState('1','a','Blue','Aircraft',None,36.0,127.0,0,0,0,None,None,None)
    n,e=CMOTutorialGymEnv._relative_km(u,37.0,127.0)
    assert 110<n<112 and abs(e)<1e-6


def test_nearest_contact_prefers_hostile_when_posture_is_available():
    env = object.__new__(CMOTutorialGymEnv)
    env.config = SimpleNamespace(
        scenario=SimpleNamespace(player_side="Blue"),
        rl=SimpleNamespace(target_contact_types=("air", "aircraft")),
    )
    unit = UnitState('1','a','Blue','Aircraft',None,36.0,127.0,0,0,0,None,None,None)
    friendly = ContactState('f','Friendly','Air',36.01,127.0,0,0,posture='F')
    hostile = ContactState('h','Hostile','Air',36.10,127.0,0,0,posture='H')
    facility = ContactState(
        'x', 'Facility', 'Fixed Facility', 36.001, 127.0, 0, 0, posture='H'
    )
    observation = Observation(
        'Demo', 0, 0, 100, 'Running', 1,
        (SideState('s', 'Blue', 0, (friendly, hostile, facility)),),
        (unit,),
    )

    target, _ = env._nearest_contact(observation, unit)
    assert target == hostile
