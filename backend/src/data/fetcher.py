import yfinance as yf
import pandas as pd
import sqlite3
import os
from datetime import datetime, timedelta

_data_dir = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "../../data/processed"))
DB_PATH = os.path.join(_data_dir, "market_data.db")


class DataFetcher:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_prices (
                    ticker TEXT,
                    date TEXT,
                    open REAL,
                    high REAL,
                    low REAL,
                    close REAL,
                    volume INTEGER,
                    PRIMARY KEY (ticker, date)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fetch_log (
                    ticker TEXT PRIMARY KEY,
                    last_fetched TEXT
                )
            """)

    def get_data(self, ticker: str, force_refresh: bool = False) -> pd.DataFrame:
        if not force_refresh and self._is_fresh(ticker):
            return self._load_from_db(ticker)
        return self._download_and_store(ticker)

    def _is_fresh(self, ticker: str) -> bool:
        with sqlite3.connect(DB_PATH) as conn:
            row = conn.execute(
                "SELECT last_fetched FROM fetch_log WHERE ticker = ?", (ticker,)
            ).fetchone()
            if not row:
                return False
            last = datetime.fromisoformat(row[0])
            # Refresh if data is older than 1 day
            return (datetime.now() - last).total_seconds() < 86400

    def _download_and_store(self, ticker: str) -> pd.DataFrame:
        print(f"[Fetcher] Downloading {ticker} from yfinance...")
        df = yf.download(ticker, start="2015-01-01", auto_adjust=True, progress=False)

        if df.empty:
            print(f"[Fetcher] No data for {ticker}")
            return pd.DataFrame()

        # yfinance multi-level columns fix
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[["Open", "High", "Low", "Close", "Volume"]].copy()
        df.index = pd.to_datetime(df.index)
        df.index.name = "date"
        df.reset_index(inplace=True)
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        df["ticker"] = ticker

        with sqlite3.connect(DB_PATH) as conn:
            df.rename(columns={"Open": "open", "High": "high", "Low": "low",
                                "Close": "close", "Volume": "volume"}, inplace=True)
            df[["ticker", "date", "open", "high", "low", "close", "volume"]].to_sql(
                "daily_prices", conn, if_exists="replace", index=False,
                method="multi"
            )
            conn.execute(
                "INSERT OR REPLACE INTO fetch_log (ticker, last_fetched) VALUES (?, ?)",
                (ticker, datetime.now().isoformat())
            )

        return self._load_from_db(ticker)

    def _load_from_db(self, ticker: str) -> pd.DataFrame:
        with sqlite3.connect(DB_PATH) as conn:
            df = pd.read_sql(
                "SELECT date, open, high, low, close, volume FROM daily_prices WHERE ticker = ? ORDER BY date",
                conn,
                params=(ticker,),
                parse_dates=["date"],
                index_col="date",
            )
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        return df
