import pandas as pd
import numpy as np
from typing import List


class StabilityAnalyzer:
    def analyze(self, events: List[dict]) -> dict:
        if not events:
            return {"classification": "Unstable", "yearly": [], "reason": "No events"}

        df = pd.DataFrame(events)

        yearly = (
            df.groupby("year")["return_pct"]
            .agg(mean="mean", median="median", count="count", std="std")
            .reset_index()
        )
        yearly["mean"] = yearly["mean"].round(2)
        yearly["median"] = yearly["median"].round(2)
        yearly["std"] = yearly["std"].round(2)

        means = yearly["mean"].values
        classification, reason, cv = self._classify(means, yearly["count"].values)

        # Period breakdown (group into 2-year buckets for visual clarity)
        periods = self._build_periods(df)

        return {
            "classification": classification,
            "reason": reason,
            "cv": cv,
            "yearly": yearly.to_dict("records"),
            "periods": periods,
        }

    def _classify(self, means: np.ndarray, counts: np.ndarray) -> tuple:
        if len(means) < 2:
            return "Regime-Dependent", "樣本年份不足，無法評估穩定性", 0.0

        overall_mean = np.mean(means)

        # Coefficient of variation (CV) on yearly means
        if abs(overall_mean) < 0.5:
            cv = float(np.std(means))
        else:
            cv = float(abs(np.std(means) / overall_mean))

        cv_r = round(cv, 2)

        # Check sign consistency
        positive_years = np.sum(means > 0)
        total_years = len(means)
        sign_ratio = max(positive_years, total_years - positive_years) / total_years

        if cv < 0.6 and sign_ratio >= 0.75:
            return "Stable", "各年份報酬分布一致，歷史表現穩定", cv_r
        elif cv < 1.5 or sign_ratio >= 0.6:
            return "Regime-Dependent", "報酬特徵與市場環境高度相關，需評估當前環境適配度", cv_r
        else:
            return "Unstable", "歷史表現高度波動，過去統計特徵在未來可能不可靠", cv_r

    def _build_periods(self, df: pd.DataFrame) -> list:
        df = df.copy()
        df["period"] = (df["year"] // 2) * 2  # 2-year buckets: 2016, 2018, 2020...
        periods = (
            df.groupby("period")["return_pct"]
            .agg(mean="mean", count="count")
            .reset_index()
        )
        periods["mean"] = periods["mean"].round(2)
        result = []
        for _, row in periods.iterrows():
            result.append({
                "label": f"{int(row['period'])}–{int(row['period'])+1}",
                "mean": row["mean"],
                "count": int(row["count"]),
            })
        return result
