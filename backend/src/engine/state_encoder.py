import pandas as pd
from typing import Optional


class StateEncoder:
    VALID_STATES = [
        f"{pos}_{mom}_{trend}"
        for pos in ["High", "Mid", "Low"]
        for mom in ["Strong", "Neutral", "Weak"]
        for trend in ["Bull", "Bear"]
    ]  # 18 states total

    def encode_for_date(self, df: pd.DataFrame, analysis_date: str) -> Optional[dict]:
        target = pd.Timestamp(analysis_date)

        # Find the closest available trading day on or before analysis_date
        available = df[df.index <= target]
        if available.empty:
            return None

        row = available.iloc[-1]
        actual_date = available.index[-1]

        state = row.get("state", None)
        if not state or state == "nan_nan_nan":
            return None

        return {
            "state": state,
            "actual_date": actual_date.strftime("%Y-%m-%d"),
            "components": {
                "relative_position": str(row.get("pos_t", "?")),
                "momentum": str(row.get("mom_t", "?")),
                "trend": str(row.get("trend_t", "?")),
            },
            "raw": {
                "close": round(float(row["Close"]), 2),
                "sma_50": round(float(row["SMA_50"]), 2) if pd.notna(row.get("SMA_50")) else None,
                "mom_5_pct": round(float(row["Mom_5"]), 2) if pd.notna(row.get("Mom_5")) else None,
                "rel_pos_20": round(float(row["RelPos_20"]), 3) if pd.notna(row.get("RelPos_20")) else None,
            }
        }
