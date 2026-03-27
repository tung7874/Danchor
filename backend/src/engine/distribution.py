import numpy as np


class DistributionCalculator:
    def __init__(self, min_samples=5):
        self.min_samples = min_samples

    def calculate(self, df, events, horizon):
        try:
            # === 防呆 ===
            if df is None or len(df) == 0:
                return self._empty_result(0, "no_data")

            if events is None or len(events) == 0:
                return self._empty_result(0, "no_events")

            # === 自動判斷價格欄位 ===
            if "close" in df.columns:
                price_col = "close"
            elif "Close" in df.columns:
                price_col = "Close"
            else:
                return self._empty_result(0, "no_price_column")

            returns = []
            valid_count = 0

            for event in events:
                try:
                    idx = event.get("index")

                    # === 修正 1：index 必須是 int ===
                    if not isinstance(idx, int):
                        try:
                            idx = int(idx)
                        except Exception:
                            continue

                    # === 修正 2：範圍檢查 ===
                    if idx < 0 or idx + horizon >= len(df):
                        continue

                    entry_price = df.iloc[idx][price_col]
                    exit_price = df.iloc[idx + horizon][price_col]

                    # === 修正 3：價格防呆 ===
                    if entry_price is None or entry_price == 0:
                        continue

                    ret = (exit_price - entry_price) / entry_price * 100

                    if not np.isfinite(ret):
                        continue

                    returns.append(ret)
                    valid_count += 1

                except Exception:
                    continue

            returns = np.array(returns, dtype=float)

            n = len(returns)

            # === 核心：樣本不足 ===
            if n < self.min_samples:
                return self._empty_result(n, "insufficient_samples")

            # === 正常統計 ===
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
                "data_range": None,
                "p50_ci_low": None,
                "p50_ci_high": None,
                "profit_factor": None,
            }

        except Exception as e:
            return self._empty_result(0, f"fatal_error: {str(e)}")

    def _empty_result(self, n, reason):
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
            "reason": reason,
        }
