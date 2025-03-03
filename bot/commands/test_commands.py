# pylint: disable-all

import pytest
from unittest.mock import MagicMock, patch
from admin import Admin
from character import Character
from creature import Creature
from location import Location
from spell import Spell


def test_true():
    assert True
