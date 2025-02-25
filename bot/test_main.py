# pylint: skip-file
import pytest
import unittest
from unittest.mock import MagicMock, patch

from main import *
from validation import is_valid_class
from db_function import generate_class


@pytest.mark.parametrize(
    "class_name, is_playable, expected",
    [
        ("", True, False),  # Empty string, invalid class name
        ("Cleric", True, True),  # Valid name and playable
        ("qwertyuiopasdfghjklzxcvbnmqwertyuiopasdfghjklzxcvbnm", True, False),  # Too long
        ("ValidClass", False, True),  # Valid name but not playable
        ("Cleric", "False", False),  # Doesn't accept string as bool
    ]
)
def test_is_valid_class(class_name, is_playable, expected):
    assert is_valid_class(class_name, is_playable) == expected


@patch('db_function.connection')
@patch('db_function.discord.Guild')
def test_generate_class(MockGuild, MockConnection):
    """Tests the generate class function"""
    mock_guild = MagicMock()
    mock_guild.id = 12345

    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    assert generate_class(mock_guild, "Warrior", True,
                          mock_conn) == "Class (Warrior) has been added to the database."

    mock_conn.cursor.assert_called_once()
    mock_conn.commit.assert_called_once()

