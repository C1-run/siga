"""Portfolio model and storage for siga-briefing."""
from __future__ import annotations


import csv
import json
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterator


DEFAULT_PATH = Path.home() / ".siga" / "portfolio.json"


@dataclass
class Holding:
    """A single position. cost_basis is per-unit (not total). Optional — 0 means unknown."""
    symbol: str
    quantity: float
    cost_basis: float = 0.0
    acquired_at: date = field(default_factory=date.today)
    notes: str = ""

    def __post_init__(self) -> None:
        self.symbol = self.symbol.upper().strip()
        if not self.symbol:
            raise ValueError("symbol cannot be empty")
        if self.quantity <= 0:
            raise ValueError(f"quantity must be positive, got {self.quantity}")
        if self.cost_basis < 0:
            raise ValueError(f"cost_basis must be non-negative, got {self.cost_basis}")
        if isinstance(self.acquired_at, str):
            try:
                self.acquired_at = date.fromisoformat(self.acquired_at)
            except ValueError as e:
                raise ValueError(f"acquired_at must be YYYY-MM-DD: {e}") from e

    @property
    def has_cost(self) -> bool:
        return self.cost_basis > 0

    @property
    def cost_total(self) -> float:
        return self.quantity * self.cost_basis

    def value(self, price: float) -> float:
        return self.quantity * price

    def pnl(self, price: float) -> float:
        return self.value(price) - self.cost_total

    def pnl_pct(self, price: float) -> float:
        if self.cost_basis == 0:
            return 0.0
        return (price - self.cost_basis) / self.cost_basis * 100


@dataclass
class Portfolio:
    holdings: list[Holding] = field(default_factory=list)
    base_currency: str = "USD"

    # ---------- constructors ----------

    @classmethod
    def from_csv(cls, path: str | Path) -> Portfolio:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"CSV not found: {path}")
        holdings: list[Holding] = []
        with path.open(newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            required = {"symbol", "quantity"}
            missing = required - set(reader.fieldnames or [])
            if missing:
                raise ValueError(f"CSV missing columns: {sorted(missing)}")
            for i, row in enumerate(reader, start=2):
                try:
                    cost_str = row.get("cost_basis", "").strip()
                    holdings.append(Holding(
                        symbol=row["symbol"],
                        quantity=float(row["quantity"]),
                        cost_basis=float(cost_str) if cost_str else 0.0,
                        acquired_at=date.fromisoformat(row["acquired_at"]) if row.get("acquired_at") else date.today(),
                        notes=row.get("notes", "") or "",
                    ))
                except (ValueError, KeyError) as e:
                    raise ValueError(f"CSV row {i} invalid: {e}") from e
        return cls(holdings=holdings)

    @classmethod
    def from_dict(cls, d: dict) -> Portfolio:
        return cls(
            holdings=[Holding(**h) for h in d.get("holdings", [])],
            base_currency=d.get("base_currency", "USD"),
        )

    @classmethod
    def load(cls, path: str | Path = DEFAULT_PATH) -> Portfolio:
        """Load from disk. Missing file -> empty Portfolio (does not create file)."""
        path = Path(path)
        if not path.exists():
            return cls()
        with path.open(encoding="utf-8") as f:
            return cls.from_dict(json.load(f))

    # ---------- persistence ----------

    def save(self, path: str | Path = DEFAULT_PATH) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "base_currency": self.base_currency,
            "holdings": [
                {**asdict(h), "acquired_at": h.acquired_at.isoformat()}
                for h in self.holdings
            ],
        }
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    # ---------- mutations ----------

    def add(self, holding: Holding) -> None:
        """Add, or merge with existing position using weighted-average cost."""
        for existing in self.holdings:
            if existing.symbol == holding.symbol:
                total_qty = existing.quantity + holding.quantity
                total_cost = existing.cost_total + holding.cost_total
                existing.quantity = total_qty
                existing.cost_basis = total_cost / total_qty
                return
        self.holdings.append(holding)

    def remove(self, symbol: str) -> Holding | None:
        """Remove and return the holding, or None if not found."""
        symbol = symbol.upper()
        for i, h in enumerate(self.holdings):
            if h.symbol == symbol:
                return self.holdings.pop(i)
        return None

    # ---------- views ----------

    def find(self, symbol: str) -> Holding | None:
        symbol = symbol.upper()
        for h in self.holdings:
            if h.symbol == symbol:
                return h
        return None

    def symbols(self) -> list[str]:
        return [h.symbol for h in self.holdings]

    def total_cost(self) -> float:
        return sum(h.cost_total for h in self.holdings)

    def total_value(self, prices: dict[str, float]) -> float:
        return sum(h.value(prices.get(h.symbol, 0.0)) for h in self.holdings)

    def pnl(self, prices: dict[str, float]) -> dict:
        """Returns:
        {
          "total": {"cost": float, "value": float, "pnl": float, "pnl_pct": float},
          "per_symbol": {
            "SOL": {"cost": ..., "value": ..., "pnl": ..., "pnl_pct": ...},
            ...
          }
        }
        """
        per_symbol = {}
        total_cost = 0.0
        total_value = 0.0
        for h in self.holdings:
            price = prices.get(h.symbol, 0.0)
            v = h.value(price)
            c = h.cost_total
            total_cost += c
            total_value += v
            per_symbol[h.symbol] = {
                "cost": c,
                "value": v,
                "pnl": v - c,
                "pnl_pct": h.pnl_pct(price),
            }
        total_pnl = total_value - total_cost
        return {
            "total": {
                "cost": total_cost,
                "value": total_value,
                "pnl": total_pnl,
                "pnl_pct": (total_pnl / total_cost * 100) if total_cost else 0.0,
            },
            "per_symbol": per_symbol,
        }

    def allocation(self, prices: dict[str, float]) -> dict[str, float]:
        total = self.total_value(prices)
        if total == 0:
            return {}
        return {
            h.symbol: h.value(prices.get(h.symbol, 0.0)) / total * 100
            for h in self.holdings
        }

    def __len__(self) -> int:
        return len(self.holdings)

    def __iter__(self) -> Iterator[Holding]:
        return iter(self.holdings)
