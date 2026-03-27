import numpy as np


class DistributionCalculator:
    def __init__(self, min_samples=5):
        self.min_samples = min_samples

    def calculate(self, df, events, horizon):
        try:
            if events is None or len(events) == 0:
                return self._empty_result(0)

            returns = []

            for event in events:
                try:
                    idx = event.get("index")
                    if idx is None or idx + horizon >= len(df):
                        continue

                    entry_price = df.iloc[idx]["close"]
                    exit_price = df.iloc[idx + horizon]["close"]

                    if entry_price == 0:
                        continue

                    ret = (exit_price - entry_price) / entry_price * 100
                    returns.append(ret)

                except Exception:
                    continue

            returns = np.array(returns, dtype=float)
            returns = returns[np.isfinite(returns)]

            n = len(returns)

            # === 核心：樣本不足 ===
            if n < self.min_samples:
                return self._empty_result(n)

            # === 正常計算 ===
            p25 = float(np.percentile(returns, 25))
            p50 = float(np.percentile(returns, 50))
            p75 = float(np.percentile(returns, 75))
            mean = float(np.mean(returns))
            win_rate = float(np.mean(returns > 0))

            return {
                "valid": True,
                "P25": p25,
                "P50": p50,
                "P75": p75,
                "mean": mean,
                "win_rate": win_rate,
                "N": n,
                "events": events,
                "data_range": None,  # 保留欄位
                "p50_ci_low": None,
                "p50_ci_high": None,
                "profit_factor": None,
            }

        except Exception as e:
            return self._empty_result(0, error=str(e))

    def _empty_result(self, n, error=None):
        return {
            "valid": False,
            "P25": None,
            "P50": None,
            "P75": None,
            "mean": None,
            "win_rate": None,
            "N": n,
            "events": [],
            "data_range": None,
            "p50_ci_low": None,
            "p50_ci_high": None,
            "profit_factor": None,
            "reason": "insufficient_samples" if error is None else f"error: {error}"
        }
