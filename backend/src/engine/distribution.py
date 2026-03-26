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

        return {
            "P10": round(float(np.percentile(arr, 10)), 2),
            "P25": round(float(np.percentile(arr, 25)), 2),
            "P50": round(float(np.percentile(arr, 50)), 2),
            "P75": round(float(np.percentile(arr, 75)), 2),
            "P90": round(float(np.percentile(arr, 90)), 2),
            "mean": round(float(np.mean(arr)), 2),
            "N": len(records),
            "win_rate": round(float(np.mean(arr > 0) * 100), 1),
            "data_range": f"{min(r['year'] for r in records)}–{max(r['year'] for r in records)}",
            "events": records,
        }
