import pandas as pd
import numpy as np


class Preprocessor:
    def calculate_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()

        # SMA 50 — trend indicator (used in state)
        df["SMA_50"] = df["Close"].rolling(window=50, min_periods=50).mean()

        # SMA 200 — long-term market trend (used in dependency, independent of state)
        df["SMA_200"] = df["Close"].rolling(window=200, min_periods=150).mean()
        df["market_trend"] = np.where(df["Close"] > df["SMA_200"], "up", "down")

        # 20-day high/low for relative position
        df["High_20"] = df["High"].rolling(window=20, min_periods=20).max()
        df["Low_20"] = df["Low"].rolling(window=20, min_periods=20).min()

        # 5-day momentum
        df["Mom_5"] = (df["Close"] - df["Close"].shift(5)) / df["Close"].shift(5) * 100

        # Relative position in 20-day range (0 to 1)
        range_20 = df["High_20"] - df["Low_20"]
        df["RelPos_20"] = np.where(
            range_20 > 0,
            (df["Close"] - df["Low_20"]) / range_20,
            0.5
        )

        # State components
        df["pos_t"] = pd.cut(
            df["RelPos_20"],
            bins=[-0.001, 0.25, 0.75, 1.001],
            labels=["Low", "Mid", "High"]
        )
        df["mom_t"] = pd.cut(
            df["Mom_5"],
            bins=[-999, -3, 3, 999],
            labels=["Weak", "Neutral", "Strong"]
        )
        df["trend_t"] = np.where(df["Close"] > df["SMA_50"], "Bull", "Bear")

        # Combined state code
        df["state"] = (
            df["pos_t"].astype(str) + "_" +
            df["mom_t"].astype(str) + "_" +
            df["trend_t"].astype(str)
        )

        # Drop rows with NaN state components
        df = df.dropna(subset=["SMA_50", "Mom_5", "High_20"])

        return df
