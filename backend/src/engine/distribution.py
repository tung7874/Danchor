import numpy as np


def analyze_distribution(returns):
    """
    returns: list[float]
    永不 crash，保證回傳結構
    """

    # 🔥 1️⃣ 基本防呆
    if returns is None:
        returns = []

    # 轉 numpy
    returns = np.array(returns, dtype=float)

    # 移除 NaN / inf
    returns = returns[np.isfinite(returns)]

    sample_size = len(returns)

    # 🔥 2️⃣ 樣本不足（核心）
    if sample_size < 5:
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

    # 🔥 3️⃣ 正常計算（安全）
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
        # 🔥 4️⃣ 最終保險（永不 crash）
        return {
            "valid": False,
            "confidence": "low",
            "reason": f"calculation_error: {str(e)}",
            "sample_size": sample_size,
        }
