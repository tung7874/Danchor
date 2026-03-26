import pandas as pd
import numpy as np
from typing import Optional

from src.engine.state_encoder import StateEncoder
from src.engine.matcher import Matcher
from src.engine.distribution import DistributionCalculator


class PositionAnalyzer:
    def __init__(self):
        self.encoder = StateEncoder()
        self.matcher = Matcher()
        self.dist_calc = DistributionCalculator()

    def analyze(
        self,
        df: pd.DataFrame,
        entry_date: str,
        entry_price: float,
        current_date: str,
        current_price: float,
        position_type: str = "LONG",
    ) -> dict:
        # Current P&L
        if position_type == "LONG":
            unrealized_pnl_pct = (current_price - entry_price) / entry_price * 100
        else:
            unrealized_pnl_pct = (entry_price - current_price) / entry_price * 100

        days_held = (pd.Timestamp(current_date) - pd.Timestamp(entry_date)).days

        # Recover entry state
        entry_state_info = self.encoder.encode_for_date(df, entry_date)
        if entry_state_info is None:
            return {"error": "Cannot encode state for entry date"}

        entry_state = entry_state_info["state"]

        # Find similar historical entry events
        similar_entries = self.matcher.find_similar(df, entry_state, current_date)

        if similar_entries.empty:
            return self._no_data_response(unrealized_pnl_pct, days_held, entry_state_info)

        # Among similar entries, find those that also experienced similar drawdown at similar holding period
        loss_threshold = unrealized_pnl_pct * 0.7  # within 70% of current loss level
        matching_scenarios = self._find_matching_drawdown(
            df, similar_entries, days_held, unrealized_pnl_pct, position_type
        )

        if not matching_scenarios:
            # Fall back to all similar entries
            matching_scenarios = self._all_entry_paths(df, similar_entries, position_type)

        path_analysis = self._analyze_paths(matching_scenarios)
        expected_values = self._calculate_expected_values(path_analysis, [9, 16, 30])

        return {
            "entry_date": entry_date,
            "entry_price": entry_price,
            "current_date": current_date,
            "current_price": current_price,
            "position_type": position_type,
            "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
            "days_held": days_held,
            "entry_state": entry_state_info,
            "sample_count": len(matching_scenarios),
            "path_analysis": path_analysis,
            "expected_values": expected_values,
        }

    def _find_matching_drawdown(
        self,
        df: pd.DataFrame,
        similar_entries: pd.DataFrame,
        days_held: int,
        current_pnl: float,
        position_type: str,
    ) -> list:
        results = []
        df_index = list(df.index)

        for entry_date in similar_entries.index:
            try:
                loc = df_index.index(entry_date)
            except ValueError:
                continue

            future_loc = loc + days_held
            if future_loc >= len(df):
                continue

            entry_price = df.iloc[loc]["Close"]
            price_at_held = df.iloc[future_loc]["Close"]

            if position_type == "LONG":
                pnl_at_held = (price_at_held - entry_price) / entry_price * 100
            else:
                pnl_at_held = (entry_price - price_at_held) / entry_price * 100

            # Match: similar P&L direction (both in loss, or pnl within 30% of current)
            if current_pnl < 0 and pnl_at_held < 0:
                results.append({
                    "entry_date": entry_date,
                    "entry_price": float(entry_price),
                    "pnl_at_match": round(float(pnl_at_held), 2),
                    "future_prices": self._get_future_prices(df, loc, [5, 10, 20, 30]),
                })

        return results

    def _all_entry_paths(self, df: pd.DataFrame, similar_entries: pd.DataFrame, position_type: str) -> list:
        results = []
        df_index = list(df.index)

        for entry_date in similar_entries.index:
            try:
                loc = df_index.index(entry_date)
            except ValueError:
                continue

            entry_price = float(df.iloc[loc]["Close"])
            results.append({
                "entry_date": entry_date,
                "entry_price": entry_price,
                "pnl_at_match": 0.0,
                "future_prices": self._get_future_prices(df, loc, [5, 10, 20, 30]),
            })

        return results

    def _get_future_prices(self, df: pd.DataFrame, start_loc: int, horizons: list) -> dict:
        prices = {}
        for h in horizons:
            future_loc = start_loc + h
            if future_loc < len(df):
                prices[f"d{h}"] = round(float(df.iloc[future_loc]["Close"]), 2)
        return prices

    def _analyze_paths(self, scenarios: list) -> dict:
        if not scenarios:
            return {}

        reversal_count = 0
        continued_loss_count = 0
        reversal_returns = []
        loss_returns = []

        for s in scenarios:
            entry_p = s["entry_price"]
            fp = s.get("future_prices", {})

            # Check d10 or d20 outcome
            future_key = "d10" if "d10" in fp else ("d20" if "d20" in fp else None)
            if not future_key:
                continue

            future_return = (fp[future_key] - entry_p) / entry_p * 100

            if future_return > 0:
                reversal_count += 1
                reversal_returns.append(future_return)
            else:
                continued_loss_count += 1
                loss_returns.append(future_return)

        total = reversal_count + continued_loss_count
        if total == 0:
            return {}

        return {
            "total": total,
            "reversal": {
                "count": reversal_count,
                "probability": round(reversal_count / total * 100, 1),
                "avg_return": round(float(np.mean(reversal_returns)), 2) if reversal_returns else 0,
                "median_return": round(float(np.median(reversal_returns)), 2) if reversal_returns else 0,
            },
            "continued_loss": {
                "count": continued_loss_count,
                "probability": round(continued_loss_count / total * 100, 1),
                "avg_return": round(float(np.mean(loss_returns)), 2) if loss_returns else 0,
            },
        }

    def _calculate_expected_values(self, path_analysis: dict, horizons: list) -> list:
        if not path_analysis or "reversal" not in path_analysis:
            return []

        rev_prob = path_analysis["reversal"]["probability"] / 100
        rev_ret = path_analysis["reversal"]["avg_return"]
        loss_prob = path_analysis["continued_loss"]["probability"] / 100
        loss_ret = path_analysis["continued_loss"]["avg_return"]

        results = []
        for h in horizons:
            ev = rev_prob * rev_ret + loss_prob * loss_ret
            results.append({
                "days": h,
                "expected_value": round(ev, 2),
            })
        return results

    def _no_data_response(self, unrealized_pnl_pct: float, days_held: int, entry_state_info: dict) -> dict:
        return {
            "unrealized_pnl_pct": round(unrealized_pnl_pct, 2),
            "days_held": days_held,
            "entry_state": entry_state_info,
            "sample_count": 0,
            "path_analysis": {},
            "expected_values": [],
            "note": "歷史資料中無足夠相似案例",
        }
