"""Unit tests for the monie-briefing CLI entrypoint."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

import pytest

import monie_briefing.cli as cli


# ---------------------------------------------------------------------------
# Top-level alias tests (use default path, isolated by conftest)
# ---------------------------------------------------------------------------


class TestTopLevelAliases:
    def test_add_and_list(self, capsys):
        rc = cli.main(["add", "SOL", "10", "--cost", "150"])
        assert rc == 0
        assert "Added SOL" in capsys.readouterr().out

        rc = cli.main(["list"])
        assert rc == 0
        assert "SOL" in capsys.readouterr().out

    def test_add_without_cost(self, capsys):
        rc = cli.main(["add", "BTC", "0.5"])
        assert rc == 0
        assert "Added BTC" in capsys.readouterr().out

    def test_empty_state_guidance(self, capsys):
        rc = cli.main(["list"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "No holdings yet" in out
        assert "monie add" in out

    def test_brief_empty_guidance(self, capsys):
        rc = cli.main(["brief"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "No holdings yet" in out
        assert "monie add" in out

    def test_value(self, monkeypatch, capsys):
        cli.main(["add", "SOL", "10", "--cost", "150"])
        import monie_briefing.prices as prices_mod
        monkeypatch.setattr(prices_mod, "_default", None)
        monkeypatch.setattr(cli, "get_prices", lambda syms: {s: 150.0 for s in syms})
        rc = cli.main(["value"])
        assert rc == 0
        assert "1,500" in capsys.readouterr().out

    def test_remove(self, capsys):
        cli.main(["add", "SOL", "10", "--cost", "150"])
        rc = cli.main(["remove", "SOL"])
        assert rc == 0
        assert "Removed SOL" in capsys.readouterr().out

    def test_import_csv(self, tmp_path, capsys):
        csv_file = tmp_path / "portfolio.csv"
        csv_file.write_text(
            "symbol,quantity\nSOL,100\nBTC,0.5\n",
            encoding="utf-8",
        )
        rc = cli.main(["import", str(csv_file)])
        assert rc == 0
        assert "Imported 2" in capsys.readouterr().out

    def test_brief_with_holdings(self, monkeypatch, capsys):
        cli.main(["add", "SOL", "100", "--cost", "150"])
        import monie_briefing.prices as prices_mod
        monkeypatch.setattr(prices_mod, "_default", prices_mod.StubPriceSource())
        rc = cli.main(["brief"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "# Brief" in out
        assert "SOL" in out


# ---------------------------------------------------------------------------
# Portfolio subcommand tests (with --file)
# ---------------------------------------------------------------------------


class TestPortfolioCli:
    def test_cli_portfolio_add(self, tmp_path, capsys):
        from monie_briefing.portfolio import Portfolio
        pf_file = tmp_path / "p.json"
        rc = cli.main(["portfolio", "--file", str(pf_file), "add", "SOL", "10",
                        "--cost", "150.00", "--date", "2025-01-15"])
        assert rc == 0
        pf = Portfolio.load(pf_file)
        h = pf.find("SOL")
        assert h is not None
        assert h.quantity == 10
        assert h.cost_basis == 150.0

    def test_cli_portfolio_list(self, tmp_path, capsys):
        from monie_briefing.portfolio import Holding, Portfolio
        from datetime import date as _date
        pf_file = tmp_path / "p.json"
        Portfolio(holdings=[
            Holding("SOL", 10, 150.0, _date(2025, 1, 1)),
            Holding("BTC", 0.5, 60000.0, _date(2025, 1, 1)),
        ]).save(pf_file)
        rc = cli.main(["portfolio", "--file", str(pf_file), "list"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "SOL" in out
        assert "BTC" in out

    def test_cli_portfolio_value(self, tmp_path, monkeypatch, capsys):
        from monie_briefing.portfolio import Holding, Portfolio
        from datetime import date as _date
        pf_file = tmp_path / "p.json"
        Portfolio(holdings=[
            Holding("SOL", 10, 100.0, _date(2025, 1, 1)),
        ]).save(pf_file)
        import monie_briefing.prices as prices_mod
        monkeypatch.setattr(prices_mod, "_default", None)
        monkeypatch.setattr(
            cli, "get_prices", lambda syms: {s: 150.0 for s in syms}
        )
        rc = cli.main(["portfolio", "--file", str(pf_file), "value"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "1,500" in out
        assert "+50.0%" in out

    def test_cli_portfolio_import(self, tmp_path, capsys):
        from monie_briefing.portfolio import Portfolio
        pf_file = tmp_path / "p.json"
        csv_file = tmp_path / "portfolio.csv"
        csv_file.write_text(
            "symbol,quantity,cost_basis,acquired_at,notes\n"
            "SOL,100,150.00,2025-01-15,early\n"
            "BTC,0.5,62000.00,2024-11-20,\n",
            encoding="utf-8",
        )
        rc = cli.main(["portfolio", "--file", str(pf_file), "import", str(csv_file)])
        assert rc == 0
        pf = Portfolio.load(pf_file)
        assert len(pf) == 2
        assert pf.find("SOL").notes == "early"


# ---------------------------------------------------------------------------
# Briefing CLI tests (with --file)
# ---------------------------------------------------------------------------


class TestBriefingCli:
    def test_brief_prints_markdown(self, tmp_path, monkeypatch, capsys):
        from monie_briefing.portfolio import Holding, Portfolio
        from datetime import date as _date
        pf_file = tmp_path / "p.json"
        Portfolio(holdings=[
            Holding("SOL", 100, 150.0, _date(2025, 1, 1)),
        ]).save(pf_file)
        import monie_briefing.prices as prices_mod
        monkeypatch.setattr(prices_mod, "_default", prices_mod.StubPriceSource())
        # Use top-level brief with --file via portfolio subcommand
        rc = cli.main(["portfolio", "--file", str(pf_file), "brief"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "# Brief" in out
        assert "SOL" in out

    def test_brief_writes_file(self, tmp_path, monkeypatch):
        from monie_briefing.portfolio import Holding, Portfolio
        from datetime import date as _date
        pf_file = tmp_path / "p.json"
        Portfolio(holdings=[
            Holding("SOL", 100, 150.0, _date(2025, 1, 1)),
        ]).save(pf_file)
        import monie_briefing.prices as prices_mod
        monkeypatch.setattr(prices_mod, "_default", prices_mod.StubPriceSource())
        out_dir = tmp_path / "briefings"
        rc = cli.main(["portfolio", "--file", str(pf_file), "brief", "--out-dir", str(out_dir)])
        assert rc == 0
        files = list(out_dir.iterdir())
        assert len(files) == 1
        assert "briefing-" in files[0].name

    def test_brief_empty_portfolio(self, tmp_path, monkeypatch, capsys):
        import monie_briefing.prices as prices_mod
        monkeypatch.setattr(prices_mod, "_default", prices_mod.StubPriceSource())
        rc = cli.main(["portfolio", "--file", str(tmp_path / "empty.json"), "brief"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "No holdings yet" in out
        assert "monie add" in out
