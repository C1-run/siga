"""Tests for CSV loading, CLI wiring, and output formats."""

import argparse
import json

from siga_audit.cli import add_audit_parser, load_trades_csv, run_audit_cli


def _make_args(csv_path, **over):
    parser = argparse.ArgumentParser(prog="siga")
    subs = parser.add_subparsers(dest="command")
    add_audit_parser(subs)
    argv = ["audit", str(csv_path)]
    for k, v in over.items():
        flag = "--" + k.replace("_", "-")
        if isinstance(v, bool):
            if v:
                argv.append(flag)
        else:
            argv += [flag, str(v)]
    return parser.parse_args(argv)


def _write_csv(tmp_path, rows, header="ts,pnl\n"):
    p = tmp_path / "trades.csv"
    p.write_text(header + "\n".join(rows) + "\n")
    return p


def test_load_detects_pnl_column(tmp_path):
    p = _write_csv(tmp_path, ["2026-01-01,10.5"] * 12)
    pnl, notional = load_trades_csv(str(p))
    assert len(pnl) == 12 and notional is None


def test_load_parses_currency_and_commas(tmp_path):
    p = _write_csv(tmp_path, ['t,"$1,234.50"'] + ["t,10"] * 11)
    pnl, _ = load_trades_csv(str(p))
    assert pnl[0] == 1234.50


def test_load_explicit_column(tmp_path):
    p = _write_csv(tmp_path, ["t,7.5"] * 12, header="ts,my_profit\n")
    pnl, _ = load_trades_csv(str(p), column="my_profit")
    assert pnl[0] == 7.5


def test_load_missing_pnl_column_errors(tmp_path):
    p = _write_csv(tmp_path, ["t,1"] * 12, header="ts,foo\n")
    try:
        load_trades_csv(str(p))
        assert False, "should have raised"
    except ValueError as e:
        assert "no P&L column" in str(e)


def test_load_bad_value_reports_line(tmp_path):
    p = _write_csv(tmp_path, ["t,1"] * 5 + ["t,oops"] + ["t,1"] * 6)
    try:
        load_trades_csv(str(p))
        assert False, "should have raised"
    except ValueError as e:
        assert "line 7" in str(e)


def test_load_requires_ten_trades(tmp_path):
    p = _write_csv(tmp_path, ["t,1"] * 9)
    try:
        load_trades_csv(str(p))
        assert False, "should have raised"
    except ValueError as e:
        assert "at least 10" in str(e)


def test_cli_verdict_line(tmp_path, capsys):
    oos = ["t,25" if i % 3 else "t,-10" for i in range(36)]
    p = _write_csv(tmp_path, ["t,5", "t,-5"] * 42 + oos)
    rc = run_audit_cli(_make_args(p))
    out = capsys.readouterr().out
    assert rc == 0
    assert "VERDICT: PASS" in out
    assert "CHECK 01" in out and "CHECK 03" in out


def test_cli_json(tmp_path, capsys):
    p = _write_csv(tmp_path, ["t,5", "t,-5"] * 30)
    rc = run_audit_cli(_make_args(p, json=True))
    data = json.loads(capsys.readouterr().out)
    assert rc == 0
    assert data["verdict"] == "INCONCLUSIVE"  # OOS n=18 < 30
    assert data["oos"]["n"] == 18


def test_cli_cost_bps_requires_notional(tmp_path, capsys):
    p = _write_csv(tmp_path, ["t,10"] * 20)
    rc = run_audit_cli(_make_args(p, cost_bps=10))
    assert rc == 2
    assert "notional" in capsys.readouterr().err


def test_cli_cost_bps_with_notional(tmp_path, capsys):
    rows = [f"t,100,10000"] * 120  # 10bps of 10000 = 10 -> net 90
    p = _write_csv(tmp_path, rows, header="ts,pnl,notional\n")
    rc = run_audit_cli(_make_args(p, cost_bps=10))
    out = capsys.readouterr().out
    assert rc == 0
    assert "VERDICT: PASS" in out  # still profitable after cost


def test_cli_missing_file(capsys):
    rc = run_audit_cli(_make_args("/nonexistent/trades.csv"))
    assert rc == 2
    assert "not found" in capsys.readouterr().err
