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

        # Consistency: % of years with positive mean return (easier to understand than CV)
        positive_years = int(np.sum(means > 0))
        total_years = len(means)
        consistency = round(float(positive_years / total_years * 100), 1) if total_years > 0 else 0.0

        # Period breakdown (group into 2-year buckets for visual clarity)
        periods = self._build_periods(df)

        return {
            "classification": classification,
            "reason": reason,
            "cv": cv,
            "consistency": consistency,
            "positive_years": positive_years,
            "total_years": total_years,
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

        best = round(float(np.max(means)), 2)
        worst = round(float(np.min(means)), 2)
        neg_years = int(total_years - positive_years)

        if cv < 0.6 and sign_ratio >= 0.75:
            reason = f"各年份報酬一致（CV={cv_r}），最佳 +{best}% / 最差 {worst}%，{neg_years} 個負報酬年"
            return "Stable", reason, cv_r
        elif cv < 1.5 or sign_ratio >= 0.6:
            reason = f"報酬隨市場環境波動（CV={cv_r}），最佳 +{best}% / 最差 {worst}%，{neg_years} 個負報酬年"
            return "Regime-Dependent", reason, cv_r
        else:
            reason = f"報酬高度不穩定（CV={cv_r}），最佳 +{best}% / 最差 {worst}%，{neg_years} 個負報酬年"
            return "Unstable", reason, cv_r

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
