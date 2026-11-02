"""siga-audit — backtest audit engine.

Give it a list of per-trade P&L numbers (chronological). It splits them
into in-sample (first 70%) and out-of-sample (last 30%), judges ONLY the
OOS portion — net of an assumed cost, and on the day rather than the ticket
if you ask it to — and prints a verdict: PASS / FAIL / INCONCLUSIVE.

Ask for a plant and it also tells you the smallest edge that log could prove.

No third kind of talk.
"""

from siga_audit.audit import AuditResult, SampleStats, daily_means, run_audit
from siga_audit.plant import contrast, detectable_delta, ladder

__version__ = "0.2.0"
__all__ = [
    "AuditResult",
    "SampleStats",
    "run_audit",
    "daily_means",
    "contrast",
    "ladder",
    "detectable_delta",
    "__version__",
]
