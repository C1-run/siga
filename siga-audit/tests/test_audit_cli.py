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
    log = load_trades_csv(str(p))
    assert len(log.pnl) == 12 and log.notional is None


def test_load_parses_currency_and_commas(tmp_path):
    p = _write_csv(tmp_path, ['t,"$1,234.50"'] + ["t,10"] * 11)
    log = load_trades_csv(str(p))
    assert log.pnl[0] == 1234.50


def test_load_explicit_column(tmp_path):
    p = _write_csv(tmp_path, ["t,7.5"] * 12, header="ts,my_profit\n")
    log = load_trades_csv(str(p), column="my_profit")
    assert log.pnl[0] == 7.5


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


def test_cli_trail_records_verdict(tmp_path, capsys):
    import json as _json

    oos = ["t,-25" if i % 3 else "t,10" for i in range(36)]
    p = _write_csv(tmp_path, ["t,5", "t,-5"] * 42 + oos)
    trail_path = str(tmp_path / "trail.jsonl")
    rc = run_audit_cli(_make_args(p, trail=trail_path))
    assert rc == 0
    with open(trail_path) as f:
        entry = _json.loads(f.readline())
    assert entry["action"] == "audit"
    assert entry["outcome"] == "FAIL"
    assert entry["payload"]["n"] == 120
    assert entry["payload"]["oos_t"] < 0


def test_cli_cluster_days_needs_a_time_column(tmp_path, capsys):
    p = _write_csv(tmp_path, ["10"] * 40, header="pnl\n")
    assert run_audit_cli(_make_args(p, cluster_days=True)) == 2
    assert "time column" in capsys.readouterr().err


def test_cli_verdict_moves_when_the_unit_becomes_the_day(tmp_path, capsys):
    # 20 days x 50 trades, every win inside one day: tickets say PASS, days say nothing.
    rows = [f"2026-01-{i // 50 + 1:02d},{2.0 if i >= 950 else 0.0}" for i in range(1000)]
    p = _write_csv(tmp_path, rows)
    assert run_audit_cli(_make_args(p)) == 0
    assert "VERDICT: PASS" in capsys.readouterr().out
    assert run_audit_cli(_make_args(p, cluster_days=True)) == 0
    out = capsys.readouterr().out
    assert "daily means" in out
    assert "VERDICT: INCONCLUSIVE" in out


def test_cli_plant_ladder_is_printed(tmp_path, capsys):
    rows = []
    for i in range(1000):
        day = i // 25 + 1
        pnl = 100.0 if i % 2 == 0 else -100.0
        arm = "A" if i % 3 == 0 else "B"
        rows.append(f"2026-01-{day:02d},{arm},{pnl:+.1f}")
    p = _write_csv(tmp_path, rows, header="ts,arm,pnl\n")
    rc = run_audit_cli(_make_args(p, plant=True, stratum="A", deltas="0,50,300"))
    out = capsys.readouterr().out
    assert rc == 0
    assert "PLANT" in out
    assert "control: the contrast leaves the whole-log mean where it found it" in out
    assert "smallest planted edge" in out or "cannot prove an edge" in out


def test_cli_plant_needs_a_stratum(tmp_path, capsys):
    p = _write_csv(tmp_path, ["t,10"] * 40)
    assert run_audit_cli(_make_args(p, plant=True)) == 2
    assert "--stratum" in capsys.readouterr().err


def test_cli_json_carries_the_plant_ladder(tmp_path, capsys):
    rows = [f"2026-01-{i // 25 + 1:02d},{'A' if i % 3 == 0 else 'B'},"
            f"{100.0 if i % 2 == 0 else -100.0:+.1f}" for i in range(1000)]
    p = _write_csv(tmp_path, rows, header="ts,arm,pnl\n")
    assert run_audit_cli(_make_args(p, plant=True, stratum="A", json=True)) == 0
    d = json.loads(capsys.readouterr().out)
    assert [r["delta"] for r in d["plant"]] == [0.0, 0.05, 0.1, 0.25, 0.5]
    assert d["clustered"] is False
