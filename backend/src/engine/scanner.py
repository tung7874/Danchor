import math
import numpy as np
import pandas as pd
from typing import List


class EdgeScanner:
    ALL_STATES = [
        f"{pos}_{mom}_{trend}"
        for pos in ["High", "Mid", "Low"]
        for mom in ["Strong", "Neutral", "Weak"]
        for trend in ["Bull", "Bear"]
    ]

    _POS = {"High": "近高點", "Mid": "中性", "Low": "近低點"}
    _MOM = {"Strong": "強勁", "Neutral": "中性", "Weak": "疲弱"}
    _TRD = {"Bull": "多頭", "Bear": "空頭"}

    def scan(self, df: pd.DataFrame, holding_horizon_days: int, min_n: int = 30) -> List[dict]:
        df_index = list(df.index)
        results = []

        for state in self.ALL_STATES:
            similar = df[df["state"] == state]
            records = []

            for event_date in similar.index:
                try:
                    loc = df_index.index(event_date)
                except ValueError:
                    continue
                future_loc = loc + holding_horizon_days
                if future_loc >= len(df):
                    continue
                entry = float(df.iloc[loc]["Close"])
                future = float(df.iloc[future_loc]["Close"])
                if entry <= 0:
                    continue
                records.append((future - entry) / entry * 100)

            if len(records) < min_n:
                continue

            arr = np.array(records)
            p25 = round(float(np.percentile(arr, 25)), 2)
            p50 = round(float(np.percentile(arr, 50)), 2)
            p75 = round(float(np.percentile(arr, 75)), 2)
            n = len(records)
            win_rate = round(float(np.mean(arr > 0) * 100), 1)

            penalty = max(0.0, -p25)
            score = (p50 * 0.5 + (p75 - p25) * 0.2 + (win_rate / 100) * 3) * math.log(max(n, 2)) - penalty * 0.5

            parts = state.split("_")
            results.append({
                "state": state,
                "label": f"{self._POS[parts[0]]} · {self._MOM[parts[1]]} · {self._TRD[parts[2]]}",
                "score": round(score, 3),
                "quality": self._grade(p25, p50, win_rate),
                "P25": p25,
                "P50": p50,
                "P75": p75,
                "N": n,
                "win_rate": win_rate,
            })

        return sorted(results, key=lambda x: x["score"], reverse=True)

    def _grade(self, p25: float, p50: float, win_rate: float) -> str:
        if p25 > 0 and p50 > 1.5:
            return "A"
        elif p50 > 0.8 and win_rate > 55:
            return "B"
        elif p50 > 0:
            return "C"
        else:
            return "D"
