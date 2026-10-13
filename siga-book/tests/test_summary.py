"""Regression + boundary tests for siga_book.summary.

Numeric expectations ported from c1m/tests/test_briefing.py::TestTickSource
(mocked ccxt book). No network, no ccxt, no mocks — fake fetchers only.
"""

from siga_book import fetch_summary, summarize_book

BOOK = {
    "bids": [["100.0", "10.0"], ["99.5", "5.0"]],
    "asks": [["100.5", "8.0"], ["101.0", "3.0"]],
}


def fake_fetcher(book):
    def fetch(symbol, depth):
        assert isinstance(symbol, str) and depth > 0
        return book

    return fetch


def test_regression_math_matches_c1m():
    result = fetch_summary(fake_fetcher(BOOK), "SOL/USDC", depth=2)
    assert result["symbol"] == "SOL/USDC"
    assert result["bid_price"] == 100.0
    assert result["ask_price"] == 100.5
    assert result["mid_price"] == 100.25
    assert result["spread"] == 0.5
    assert result["spread_pct"] == round(0.5 / 100.25 * 100, 4)
    assert result["error"] is None


def test_empty_book_reports_error():
    result = fetch_summary(fake_fetcher({"bids": [], "asks": []}), "SOL/USDC")
    assert result["error"] == "Empty order book"


def test_one_sided_book_reports_error():
    assert summarize_book({"bids": [[1.0, 2.0]], "asks": []})["error"] == "Empty order book"
    assert summarize_book({"bids": [], "asks": [[1.0, 2.0]]})["error"] == "Empty order book"


def test_zero_volume_falls_back_to_half():
    book = {"bids": [["100.0", "0.0"]], "asks": [["100.5", "0.0"]]}
    result = summarize_book(book, depth=1)
    assert result["bid_imbalance"] == 0.5
    assert result["ask_imbalance"] == 0.5
    assert result["error"] is None


def test_imbalance_math():
    # bids 10+5=15, asks 8+3=11 → bid 15/26, ask 11/26
    result = summarize_book(BOOK, depth=2)
    assert result["bid_imbalance"] == round(15 / 26, 3)
    assert result["ask_imbalance"] == round(11 / 26, 3)
    assert result["bid_depth"] == 15.0
    assert result["ask_depth"] == 11.0


def test_sell_wall_needs_strictly_over_2x():
    # avg ask = (8+3)/2 = 5.5; 8.0/5.5 = 1.45x → no wall
    assert summarize_book(BOOK, depth=2)["sell_wall_levels"] == []
    # avg ask = (20+1+1+1+1)/5 = 4.8; 20/4.8 = 4.2x → wall
    book = {
        "bids": [["100.0", "5.0"]],
        "asks": [["100.5", "20.0"], ["101.0", "1.0"], ["101.5", "1.0"], ["102.0", "1.0"], ["102.5", "1.0"]],
    }
    walls = summarize_book(book, depth=5)["sell_wall_levels"]
    assert len(walls) == 1
    assert walls[0]["price"] == 100.5
    assert walls[0]["multiple"] == round(20.0 / 4.8, 1)


def test_exactly_2x_is_not_a_wall():
    # avg = (3+1+1+1)/4 = 1.5; 3.0/1.5 = exactly 2.0x → not > 2 → no wall
    book = {"bids": [["100.0", "1.0"]], "asks": [["100.5", "3.0"], ["101.0", "1.0"], ["101.5", "1.0"], ["102.0", "1.0"]]}
    assert summarize_book(book, depth=4)["sell_wall_levels"] == []


def test_fetcher_exception_becomes_error():
    def boom(symbol, depth):
        raise ConnectionError("exchange down")

    result = fetch_summary(boom, "SOL/USDC")
    assert result == {"symbol": "SOL/USDC", "error": "exchange down"}
