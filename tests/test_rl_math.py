import pytest; pytest.importorskip("gymnasium")
from cmo_tutorial.gym_env import CMOTutorialGymEnv
from cmo_tutorial.models import UnitState

def test_relative_km():
    u=UnitState('1','a','Blue','Aircraft',None,36.0,127.0,0,0,0,None,None,None)
    n,e=CMOTutorialGymEnv._relative_km(u,37.0,127.0)
    assert 110<n<112 and abs(e)<1e-6
