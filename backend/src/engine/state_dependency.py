import numpy as np
import pandas as pd


class StateDependencyAnalyzer:
    def analyze(self, df: pd.DataFrame, state: str, horizon_days: int) -> dict | None:
        events = df[df["state"] == state]
        if len(events) < 50:
            return None

        df_index = {date: i for i, date in enumerate(df.index)}
        records = []

        for event_date in events.index:
            loc = df_index.get(event_date)
            if loc is None:
                continue
            future_loc = loc + horizon_days
            if future_loc >= len(df):
                continue
            entry = float(df.iloc[loc]["Close"])
            future = float(df.iloc[future_loc]["Close"])
            if entry <= 0:
                continue
            ret = (future - entry) / entry * 100
            market = df.iloc[loc].get("market_trend", "up")
            records.append({"return": ret, "market_trend": market})

        if len(records) < 50:
            return None

        rec = pd.DataFrame(records)
        up = rec[rec["market_trend"] == "up"]["return"]
        down = rec[rec["market_trend"] == "down"]["return"]

        if len(up) < 30 or len(down) < 30:
            return None

        # Use median + winsorize to resist outliers
        def winsorize(s):
            return s.clip(lower=s.quantile(0.05), upper=s.quantile(0.95))

        up_ret = round(float(winsorize(up).median()), 2)
        down_ret = round(float(winsorize(down).median()), 2)
        diff = round(up_ret - down_ret, 2)
        strength = abs(diff)

        if strength > 1.5:
            label = "高度依賴"
        elif strength > 0.5:
            label = "中度依賴"
        else:
            label = "低依賴"

        return {
            "label": label,
            "diff": diff,
            "direction": "多" if diff > 0 else "空",
            "strength": round(strength, 2),
            "up_return": up_ret,
            "down_return": down_ret,
            "up_count": len(up),
            "down_count": len(down),
        }
