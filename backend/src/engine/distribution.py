import pandas as pd
import numpy as np
from typing import Optional


class DistributionCalculator:
    def calculate(
        self,
        df: pd.DataFrame,
        similar_events: pd.DataFrame,
        horizon_days: int,
    ) -> Optional[dict]:
        if similar_events.empty:
            return None

        records = []
        df_index = list(df.index)

        for event_date in similar_events.index:
            try:
                loc = df_index.index(event_date)
            except ValueError:
                continue

            future_loc = loc + horizon_days
            if future_loc >= len(df):
                continue

            entry_price = df.iloc[loc]["Close"]
            future_price = df.iloc[future_loc]["Close"]

            if entry_price <= 0:
                continue

            ret = (future_price - entry_price) / entry_price * 100
            records.append({
                "date": event_date,
                "year": event_date.year,
                "entry_price": round(float(entry_price), 2),
                "future_price": round(float(future_price), 2),
                "return_pct": round(float(ret), 2),
            })

        if not records:
            return None

        returns = [r["return_pct"] for r in records]
        arr = np.array(returns)

        # Bootstrap P50 confidence interval (100 iterations)
        boots = [float(np.median(np.random.choice(arr, len(arr), replace=True))) for _ in range(100)]
        p50_ci_low = round(float(np.percentile(boots, 5)), 2)
        p50_ci_high = round(float(np.percentile(boots, 95)), 2)

        # Profit factor
        wins = arr[arr > 0]
        losses = arr[arr < 0]
        if len(wins) > 0 and len(losses) > 0:
            avg_win = float(np.mean(wins))
            avg_loss = abs(float(np.mean(losses)))
            w = len(wins) / len(arr)
            profit_factor = round(w * avg_win / ((1 - w) * avg_loss), 2)
        else:
            profit_factor = None

        return {
            "P10": round(float(np.percentile(arr, 10)), 2),
            "P25": round(float(np.percentile(arr, 25)), 2),
            "P50": round(float(np.percentile(arr, 50)), 2),
            "P75": round(float(np.percentile(arr, 75)), 2),
            "P90": round(float(np.percentile(arr, 90)), 2),
            "mean": round(float(np.mean(arr)), 2),
            "N": len(records),
            "win_rate": round(float(np.mean(arr > 0) * 100), 1),
            "p50_ci_low": p50_ci_low,
            "p50_ci_high": p50_ci_high,
            "profit_factor": profit_factor,
            "data_range": f"{min(r['year'] for r in records)}–{max(r['year'] for r in records)}",
            "events": records,
        }
