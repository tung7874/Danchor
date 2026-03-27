import numpy as np
import pandas as pd
from typing import Union


class DistributionCalculator:
    def __init__(self, min_samples: int = 15):
        self.min_samples = min_samples

    def calculate(self, df: pd.DataFrame, similar_events: Union[pd.DataFrame, None], horizon: int) -> dict:
        # --- guard: empty input ---
        if df is None or df.empty:
            return self._empty(0, "no_data")
        if similar_events is None or (hasattr(similar_events, "__len__") and len(similar_events) == 0):
            return self._empty(0, "no_events")

        # --- price column (preprocessor outputs uppercase Close) ---
        price_col = "Close" if "Close" in df.columns else "close"
        if price_col not in df.columns:
            return self._empty(0, "no_price_column")

        # --- O(1) date → integer position lookup ---
        df_index = {date: i for i, date in enumerate(df.index)}

        records = []  # {"return_pct": float, "year": int}

        # similar_events is a DataFrame slice with DatetimeIndex (from Matcher)
        event_dates = similar_events.index if isinstance(similar_events, pd.DataFrame) else []

        for event_date in event_dates:
            loc = df_index.get(event_date)
            if loc is None:
                continue
            future_loc = loc + horizon
            if future_loc >= len(df):
                continue
            entry = float(df.iloc[loc][price_col])
            future = float(df.iloc[future_loc][price_col])
            if entry <= 0:
                continue
            ret = (future - entry) / entry * 100
            if not np.isfinite(ret):
                continue
            records.append({
                "return_pct": round(ret, 4),
                "year": event_date.year,
            })

        n = len(records)
        if n < self.min_samples:
            return self._empty(n, "insufficient_samples")

        arr = np.array([r["return_pct"] for r in records], dtype=float)

        # --- percentiles ---
        p25 = round(float(np.percentile(arr, 25)), 2)
        p50 = round(float(np.percentile(arr, 50)), 2)
        p75 = round(float(np.percentile(arr, 75)), 2)
        win_rate = round(float(np.mean(arr > 0) * 100), 1)

        # --- bootstrap CI on median (100 iterations) ---
        np.random.seed(42)
        boots = [float(np.median(np.random.choice(arr, len(arr), replace=True))) for _ in range(100)]
        p50_ci_low  = round(float(np.percentile(boots, 5)),  2)
        p50_ci_high = round(float(np.percentile(boots, 95)), 2)

        # --- profit factor ---
        wins   = arr[arr > 0]
        losses = arr[arr < 0]
        profit_factor = None
        if len(wins) > 0 and len(losses) > 0:
            w        = len(wins) / n
            avg_win  = float(np.mean(wins))
            avg_loss = abs(float(np.mean(losses)))
            if avg_loss > 0:
                profit_factor = round(w * avg_win / ((1 - w) * avg_loss), 2)

        # --- data_range label ---
        years = sorted(set(r["year"] for r in records))
        data_range = f"{years[0]}–{years[-1]}" if years else ""

        return {
            "valid":        True,
            "P25":          p25,
            "P50":          p50,
            "P75":          p75,
            "N":            n,
            "win_rate":     win_rate,
            "p50_ci_low":   p50_ci_low,
            "p50_ci_high":  p50_ci_high,
            "profit_factor": profit_factor,
            "data_range":   data_range,
            "events":       records,
        }

    def _empty(self, n: int, reason: str) -> dict:
        return {
            "valid":         False,
            "P25":           None,
            "P50":           None,
            "P75":           None,
            "N":             n,
            "win_rate":      None,
            "p50_ci_low":    None,
            "p50_ci_high":   None,
            "profit_factor": None,
            "data_range":    None,
            "events":        [],
            "reason":        reason,
        }
