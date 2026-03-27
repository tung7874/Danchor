import numpy as np


class DistributionCalculator:
    """
    向下相容舊系統接口：
    main.py 仍可使用 DistributionCalculator().calculate()
    """

    def __init__(self, min_samples=5):
        self.min_samples = min_samples

    def calculate(self, returns):
        return analyze_distribution(returns, self.min_samples)


def analyze_distribution(returns, min_samples=5):
    """
    returns: list[float] | np.ndarray
    永不 crash，保證回傳結構
    """

    # === 1️⃣ 基本防呆 ===
    if returns is None:
        returns = []

    try:
        returns = np.array(returns, dtype=float)
    except Exception:
        returns = np.array([])

    # 移除 NaN / inf
    returns = returns[np.isfinite(returns)]

    sample_size = len(returns)

    # === 2️⃣ 樣本不足 ===
    if sample_size < min_samples:
        return {
            "valid": False,
            "confidence": "low",
            "reason": "insufficient_samples",
            "sample_size": sample_size,
            "p25": None,
            "p50": None,
            "p75": None,
            "mean": None,
            "win_rate": None,
        }

    # === 3️⃣ 正常統計 ===
    try:
        p25 = float(np.percentile(returns, 25))
        p50 = float(np.percentile(returns, 50))
        p75 = float(np.percentile(returns, 75))
        mean = float(np.mean(returns))

        wins = np.sum(returns > 0)
        win_rate = float(wins / sample_size)

        return {
            "valid": True,
            "confidence": "low" if sample_size < 50 else "medium",
            "sample_size": sample_size,
            "p25": p25,
            "p50": p50,
            "p75": p75,
            "mean": mean,
            "win_rate": win_rate,
        }

    except Exception as e:
        # === 4️⃣ 最終保險 ===
        return {
            "valid": False,
            "confidence": "low",
            "reason": f"calculation_error: {str(e)}",
            "sample_size": sample_size,
            "p25": None,
            "p50": None,
            "p75": None,
            "mean": None,
            "win_rate": None,
        }
