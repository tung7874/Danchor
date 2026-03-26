import pandas as pd
from typing import List


class Matcher:
    def find_similar(
        self,
        df: pd.DataFrame,
        target_state: str,
        analysis_date: str,
        lookback_years: int = 10,
    ) -> pd.DataFrame:
        cutoff = pd.Timestamp(analysis_date) - pd.DateOffset(days=1)

        # Only look at history before analysis_date
        hist = df[df.index < cutoff].copy()

        # Optional: limit lookback window
        if lookback_years:
            start = cutoff - pd.DateOffset(years=lookback_years)
            hist = hist[hist.index >= start]

        similar = hist[hist["state"] == target_state]
        return similar
