"""Tests for history retrieval tools (history_orders_get, history_deals_get).

The MT5 Python API takes the history date range positionally and only accepts
group/ticket/position as keyword arguments, so these tests pin down the exact
call made into MetaTrader5.
"""

from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

import pytest

from mcp_mt5.main import history_deals_get, history_orders_get

DEAL = {
    "ticket": 1001,
    "order": 2001,
    "time": 1714557600,
    "time_msc": 1714557600000,
    "type": 0,
    "entry": 0,
    "magic": 0,
    "position_id": 3001,
    "reason": 0,
    "volume": 0.1,
    "price": 1.1,
    "commission": 0.0,
    "swap": 0.0,
    "profit": 5.0,
    "fee": 0.0,
    "symbol": "EURUSD",
    "comment": "",
    "external_id": "",
}

HISTORY_ORDER = {
    "ticket": 2001,
    "time_setup": 1714557600,
    "time_setup_msc": 1714557600000,
    "time_expiration": 0,
    "type": 0,
    "type_time": 0,
    "type_filling": 0,
    "state": 4,
    "magic": 0,
    "position_id": 3001,
    "position_by_id": 0,
    "reason": 0,
    "volume_initial": 0.1,
    "volume_current": 0.0,
    "price_open": 1.1,
    "sl": 0.0,
    "tp": 0.0,
    "price_current": 1.1,
    "price_stoplimit": 0.0,
    "symbol": "EURUSD",
    "comment": "",
    "external_id": "",
}


def _record(fields):
    record = Mock()
    record._asdict.return_value = dict(fields)
    return record


@pytest.fixture
def mock_history():
    """Patch the MT5 module with a mock returning one deal and one order."""
    mock = MagicMock()
    mock.history_deals_get.return_value = (_record(DEAL),)
    mock.history_orders_get.return_value = (_record(HISTORY_ORDER),)
    mock.last_error.return_value = (1, "Success")
    with patch("mcp_mt5.main.mt5", mock):
        yield mock


@pytest.mark.unit
def test_history_deals_get_passes_dates_positionally(mock_history):
    from_date = datetime(2020, 1, 1)
    to_date = datetime(2026, 1, 1)

    deals = history_deals_get(from_date=from_date, to_date=to_date)

    mock_history.history_deals_get.assert_called_once_with(from_date, to_date)
    assert len(deals) == 1
    assert deals[0].ticket == 1001


@pytest.mark.unit
def test_history_orders_get_passes_dates_positionally(mock_history):
    from_date = datetime(2020, 1, 1)
    to_date = datetime(2026, 1, 1)

    orders = history_orders_get(from_date=from_date, to_date=to_date)

    mock_history.history_orders_get.assert_called_once_with(from_date, to_date)
    assert len(orders) == 1
    assert orders[0].ticket == 2001


@pytest.mark.unit
def test_history_deals_get_without_dates_uses_full_range(mock_history):
    history_deals_get()

    args, kwargs = mock_history.history_deals_get.call_args
    assert kwargs == {}
    date_from, date_to = args
    assert date_from == datetime(1970, 1, 1)
    assert date_to > datetime.now()


@pytest.mark.unit
def test_history_deals_get_symbol_becomes_group_filter(mock_history):
    from_date = datetime(2020, 1, 1)
    to_date = datetime(2026, 1, 1)

    history_deals_get(symbol="EURUSD", from_date=from_date, to_date=to_date)

    mock_history.history_deals_get.assert_called_once_with(from_date, to_date, group="EURUSD")


@pytest.mark.unit
def test_history_deals_get_group_takes_precedence_over_symbol(mock_history):
    from_date = datetime(2020, 1, 1)
    to_date = datetime(2026, 1, 1)

    history_deals_get(symbol="EURUSD", group="USD*", from_date=from_date, to_date=to_date)

    mock_history.history_deals_get.assert_called_once_with(from_date, to_date, group="USD*")


@pytest.mark.unit
def test_history_deals_get_by_ticket_ignores_other_filters(mock_history):
    history_deals_get(
        ticket=1001,
        symbol="EURUSD",
        from_date=datetime(2020, 1, 1),
        to_date=datetime(2026, 1, 1),
    )

    mock_history.history_deals_get.assert_called_once_with(ticket=1001)


@pytest.mark.unit
def test_history_deals_get_by_position_ignores_other_filters(mock_history):
    history_deals_get(position=3001, group="USD*", from_date=datetime(2020, 1, 1))

    mock_history.history_deals_get.assert_called_once_with(position=3001)


@pytest.mark.unit
def test_history_orders_get_by_ticket_ignores_other_filters(mock_history):
    history_orders_get(ticket=2001, from_date=datetime(2020, 1, 1))

    mock_history.history_orders_get.assert_called_once_with(ticket=2001)


@pytest.mark.unit
def test_history_deals_get_returns_empty_list_on_failure(mock_history):
    mock_history.history_deals_get.return_value = None
    mock_history.last_error.return_value = (-2, "Invalid parameters")

    assert history_deals_get(from_date=datetime(2020, 1, 1)) == []


@pytest.mark.unit
def test_history_orders_get_returns_empty_list_on_failure(mock_history):
    mock_history.history_orders_get.return_value = None
    mock_history.last_error.return_value = (-2, "Invalid parameters")

    assert history_orders_get() == []
