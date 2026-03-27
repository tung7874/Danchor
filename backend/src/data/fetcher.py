import time
import yfinance as yf
import pandas as pd
import sqlite3
import os
from datetime import datetime

# Rolling 8-year window — recalculated at import time
_START_DATE = f"{datetime.now().year - 8}-01-01"

try:
    from FinMind.data import DataLoader as _FinMindLoader
    _FINMIND_AVAILABLE = True
except ImportError:
    _FINMIND_AVAILABLE = False

_data_dir = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "../../data/processed"))
DB_PATH = os.path.join(_data_dir, "market_data.db")
_FINMIND_TOKEN = os.environ.get("FINMIND_TOKEN", "")


class DataFetcher:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()
        self._finmind = None
        if _FINMIND_AVAILABLE:
            try:
                self._finmind = _FinMindLoader()
                if _FINMIND_TOKEN:
                    self._finmind.login_by_token(api_token=_FINMIND_TOKEN)
                    print("[Fetcher] FinMind logged in with token")
                else:
                    print("[Fetcher] FinMind ready (no token, free tier)")
            except Exception as e:
                print(f"[Fetcher] FinMind init failed: {e}")
                self._finmind = None

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
            return (datetime.now() - last).total_seconds() < 86400

    def _stock_id(self, ticker: str) -> str:
        return ticker.split(".")[0]

    def _is_valid_df(self, df: pd.DataFrame) -> bool:
        if df is None or df.empty:
            return False
        if len(df) < 100:
            return False
        required_cols = ["open", "high", "low", "close", "volume"]
        for col in required_cols:
            if col not in df.columns:
                return False
        return True

    def _fetch_finmind(self, ticker: str) -> pd.DataFrame:
        stock_id = self._stock_id(ticker)
        try:
            print(f"[Fetcher] FinMind downloading {stock_id}...")
            raw = self._finmind.taiwan_stock_daily(stock_id=stock_id, start_date=_START_DATE)
            if raw is None or raw.empty:
                return pd.DataFrame()
            raw = raw[["date", "open", "max", "min", "close", "Trading Volume"]].copy()
            raw.columns = ["date", "open", "high", "low", "close", "volume"]
            raw["date"] = pd.to_datetime(raw["date"])
            raw = raw.set_index("date").sort_index()
            raw = raw.dropna()
            print(f"[Fetcher] FinMind OK: {len(raw)} rows")
            return raw
        except Exception as e:
            print(f"[Fetcher] FinMind failed for {stock_id}: {e}")
            return pd.DataFrame()

    def _fetch_yfinance(self, ticker: str) -> pd.DataFrame:
        print(f"[Fetcher] yfinance downloading {ticker}...")
        raw = pd.DataFrame()
        for attempt in range(3):
            try:
                t = yf.Ticker(ticker)
                raw = t.history(start=_START_DATE, auto_adjust=True, timeout=10)
                break  # empty = ticker not found, no point retrying
            except Exception as e:
                print(f"[Fetcher] yfinance attempt {attempt + 1} failed: {e}")
                if attempt < 2:
                    time.sleep(attempt + 1)
                else:
                    raise

        if raw.empty:
            return pd.DataFrame()

        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)

        raw = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
        raw.columns = ["open", "high", "low", "close", "volume"]
        raw.index = pd.to_datetime(raw.index)
        raw.index.name = "date"
        raw = raw.dropna()
        print(f"[Fetcher] yfinance OK: {len(raw)} rows")
        return raw

    def _download_and_store(self, ticker: str) -> pd.DataFrame:
        df = pd.DataFrame()
        if self._finmind is not None:
            df = self._fetch_finmind(ticker)
        if not self._is_valid_df(df):
            print(f"[Fetcher] FinMind invalid → fallback to yfinance ({ticker})")
            df = self._fetch_yfinance(ticker)
        if not self._is_valid_df(df):
            print(f"[Fetcher] No valid data for {ticker}")
            return pd.DataFrame()

        df = df.copy()
        df.reset_index(inplace=True)
        df["date"] = df["date"].dt.strftime("%Y-%m-%d")
        df["ticker"] = ticker

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("DELETE FROM daily_prices WHERE ticker = ?", (ticker,))
            df[["ticker", "date", "open", "high", "low", "close", "volume"]].to_sql(
                "daily_prices", conn, if_exists="append", index=False, method="multi"
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
