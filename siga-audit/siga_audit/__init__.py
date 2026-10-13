"""siga-audit — backtest audit engine.

Give it a list of per-trade P&L numbers (chronological). It splits them
into in-sample (first 70%) and out-of-sample (last 30%), judges ONLY the
OOS portion, and prints a verdict: PASS / FAIL / INCONCLUSIVE.

No third kind of talk.
"""

from siga_audit.audit import AuditResult, SampleStats, run_audit

__version__ = "0.1.0"
__all__ = ["AuditResult", "SampleStats", "run_audit", "__version__"]
