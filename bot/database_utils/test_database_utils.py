import pytest
from unittest.mock import MagicMock, patch
from fetch_queries import DatabaseMapper, DatabaseIDFetch, InventoryDatabase


@pytest.fixture
def mock_connection():
    """Creates a mock database connection with a cursor mock."""
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cursor
    return mock_conn, mock_cursor

class FetchQueries:
    """This is a base class for all tests happening to the fetch_queries.py file"""
    pass

class TestDatabaseMaps(FetchQueries):
    """Defines all the tests that check
    the DatabaseMapper methods."""

    def test_get_player_mapping(self, mock_connection):
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.return_value = [
            {'player_name': 'Alice', 'player_id': 1}, {'player_name': 'Bob', 'player_id': 2}]

        result = DatabaseMapper.get_player_mapping(mock_conn, 12345)
        assert result == {'Alice': 1, 'Bob': 2}
    

    def test_get_location_mapping(self, mock_connection):
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.return_value = [
            {'channel_id': 1, 'location_id': 1}, {'channel_id': 1, 'location_id': 2}]

        result = DatabaseMapper.get_location_mapping(mock_conn, 12345)
        assert result == {1: 1, 1: 2}
    

    def test_get_character_mapping(self, mock_connection):
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.return_value = [
            {'character_name': 'Hero', 'character_id': 999}]

        result = DatabaseMapper.get_character_mapping(mock_conn, 1)
        assert result == {'Hero': 999}

    def test_get_race_map(self, mock_connection):
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.return_value = [
            {'race_name': 'Elf', 'race_id': 5}, {'race_name': 'Orc', 'race_id': 8}]

        result = DatabaseMapper.get_race_map(mock_conn, 12345)
        assert result == {'Elf': 5, 'Orc': 8}


class TestIDFetcher(FetchQueries):
    def test_get_player_id(self, mock_connection):
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = {'player_id': 7}

        result = DatabaseIDFetch.get_player_id(mock_conn, 'Test', 12345)
        assert result == 7


    def test_get_selected_character_id(self, mock_connection):
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = {'character_id': 42}

        result = DatabaseIDFetch.get_selected_character_id(mock_conn, 1)
        assert result == 42


    def test_get_inventory_id(self, mock_connection):
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchone.return_value = {'inventory_id': 500}

        result = DatabaseIDFetch.get_inventory_id(mock_conn, 42)
        assert result == 500


class TestInventoryDatabase(FetchQueries):
    def test_get_items_in_inventory(self, mock_connection):
        mock_conn, mock_cursor = mock_connection
        mock_cursor.fetchall.return_value = [{'item_id' : 1,'item_name' : 'Excalibur', 'Value' : 500},
                                             {'item_id' : 2, 'item_name': 'Lance of Longinus', 'Value' : 200},
                                             {'item_id' : 3, 'item_name': 'Mjolnir', 'Value': 350}]
        result = InventoryDatabase.get_items_in_inventory(mock_conn, 42)
        assert result == [{'item_id': 1, 'item_name': 'Excalibur', 'Value': 500},
                          {'item_id': 2, 'item_name': 'Lance of Longinus', 'Value': 200},
                          {'item_id': 3, 'item_name': 'Mjolnir', 'Value': 350}]
