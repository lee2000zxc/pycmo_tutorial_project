import pytest
from cmo_tutorial.actions import lua_quote, set_course


def test_lua_quote():
    assert lua_quote("O'Brien") == "'O\\'Brien'"


def test_set_course_validation():
    with pytest.raises(ValueError):
        set_course("Blue", "A", 100, 0)
