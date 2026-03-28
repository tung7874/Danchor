import time
import threading
import requests
import yfinance as yf
import pandas as pd
import sqlite3
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

_yf_lock = threading.Lock()
_START_YEAR = datetime.now().year - 8  # rolling 8-year window

_data_dir = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "../../data/processed"))
DB_PATH = os.path.join(_data_dir, "market_data.db")

_TWSE_SESSION = requests.Session()
_TWSE_SESSION.headers.update({"Accept": "application/json", "User-Agent": "Mozilla/5.0"})


def _gen_months(start_year: int) -> list:
    now = datetime.now()
    months = []
    y, m = start_year, 1
    while (y, m) <= (now.year, now.month):
        months.append((y, m))
        m += 1
        if m > 12:
            m, y = 1, y + 1
    return months


class DataFetcher:
    def __init__(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS daily_prices (
                    ticker TEXT, date TEXT,
                    open REAL, high REAL, low REAL, close REAL, volume INTEGER,
                    PRIMARY KEY (ticker, date)
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS fetch_log (
                    ticker TEXT PRIMARY KEY, last_fetched TEXT
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
            return (datetime.now() - datetime.fromisoformat(row[0])).total_seconds() < 86400

    def _stock_id(self, ticker: str) -> str:
        return ticker.split(".")[0]

    def _is_valid_df(self, df: pd.DataFrame) -> bool:
        if df is None or df.empty or len(df) < 100:
            return False
        return all(c in df.columns for c in ["open", "high", "low", "close", "volume"])

    # ── TWSE (上市) — 使用舊版穩定 API ──────────────────────────
    def _fetch_twse(self, ticker: str) -> pd.DataFrame:
        stock_id = self._stock_id(ticker)
        print(f"[Fetcher] TWSE downloading {stock_id}...")

        def fetch_month(ym):
            y, m = ym
            try:
                r = _TWSE_SESSION.get(
                    "https://www.twse.com.tw/exchangeReport/STOCK_DAY",
                    params={"response": "json", "date": f"{y}{m:02d}01", "stockNo": stock_id},
                    timeout=10,
                )
                if r.ok:
                    data = r.json()
                    if data.get("stat") == "OK":
                        return data.get("data", [])
            except Exception:
                pass
            return []

        months = _gen_months(_START_YEAR)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(fetch_month, months))

        rows = []
        for month_data in results:
            for row in month_data:
                try:
                    # row: [民國日期, 成交股數, 成交金額, 開盤, 最高, 最低, 收盤, 漲跌, 成交筆數]
                    parts = row[0].split("/")
                    date = pd.Timestamp(f"{int(parts[0]) + 1911}-{parts[1]}-{parts[2]}")
                    def clean(v): return float(str(v).replace(",", "").replace("--", "0") or 0)
                    rows.append({
                        "date":   date,
                        "open":   clean(row[3]),
                        "high":   clean(row[4]),
                        "low":    clean(row[5]),
                        "close":  clean(row[6]),
                        "volume": int(str(row[1]).replace(",", "") or 0),
                    })
                except Exception:
                    continue

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows).set_index("date").sort_index()
        df = df[df["close"] > 0].dropna()
        print(f"[Fetcher] TWSE OK: {len(df)} rows")
        return df

    # ── TPEx (上櫃) — 舊版穩定 API ───────────────────────────────
    def _fetch_tpex(self, ticker: str) -> pd.DataFrame:
        stock_id = self._stock_id(ticker)
        print(f"[Fetcher] TPEx downloading {stock_id}...")

        def fetch_month(ym):
            y, m = ym
            roc = y - 1911
            try:
                r = _TWSE_SESSION.get(
                    "https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_download.php",
                    params={"l": "zh-tw", "d": f"{roc}/{m:02d}", "s": stock_id, "download": "json"},
                    timeout=10,
                )
                if r.ok:
                    data = r.json()
                    return data.get("aaData", [])
            except Exception:
                pass
            return []

        months = _gen_months(_START_YEAR)
        with ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(fetch_month, months))

        rows = []
        for month_data in results:
            for row in month_data:
                try:
                    parts = row[0].split("/")
                    date = pd.Timestamp(f"{int(parts[0]) + 1911}-{parts[1]}-{parts[2]}")
                    def clean(v): return float(str(v).replace(",", "").replace("--", "0") or 0)
                    rows.append({
                        "date":   date,
                        "open":   clean(row[4]),
                        "high":   clean(row[5]),
                        "low":    clean(row[6]),
                        "close":  clean(row[7]),
                        "volume": int(str(row[1]).replace(",", "") or 0),
                    })
                except Exception:
                    continue

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows).set_index("date").sort_index()
        df = df[df["close"] > 0].dropna()
        print(f"[Fetcher] TPEx OK: {len(df)} rows")
        return df

    # ── yfinance fallback ────────────────────────────────────────
    def _fetch_yfinance(self, ticker: str) -> pd.DataFrame:
        print(f"[Fetcher] yfinance downloading {ticker}...")
        start_date = f"{_START_YEAR}-01-01"
        with _yf_lock:
            for attempt in range(3):
                try:
                    raw = yf.Ticker(ticker).history(start=start_date, auto_adjust=True, timeout=15)
                    break
                except Exception as e:
                    wait = (attempt + 1) * 5
                    print(f"[Fetcher] yfinance attempt {attempt + 1} failed: {e} — retry in {wait}s")
                    if attempt < 2:
                        time.sleep(wait)
                    else:
                        return pd.DataFrame()

        if raw.empty:
            return pd.DataFrame()
        if isinstance(raw.columns, pd.MultiIndex):
            raw.columns = raw.columns.get_level_values(0)
        raw = raw[["Open", "High", "Low", "Close", "Volume"]].copy()
        raw.columns = ["open", "high", "low", "close", "volume"]
        raw.index = pd.to_datetime(raw.index)
        raw.index.name = "date"
        print(f"[Fetcher] yfinance OK: {len(raw)} rows")
        return raw.dropna()

    # ── orchestrator ─────────────────────────────────────────────
    def _download_and_store(self, ticker: str) -> pd.DataFrame:
        is_otc = ticker.endswith(".TWO")
        is_tw  = ticker.endswith(".TW") and not is_otc

        df = pd.DataFrame()
        if is_tw:
            df = self._fetch_twse(ticker)
        if not self._is_valid_df(df) and is_otc:
            df = self._fetch_tpex(ticker)
        if not self._is_valid_df(df):
            df = self._fetch_yfinance(ticker)
        if not self._is_valid_df(df):
            print(f"[Fetcher] No valid data for {ticker}")
            return pd.DataFrame()

        df = df.copy()
        df.reset_index(inplace=True)
        df["date"]   = df["date"].dt.strftime("%Y-%m-%d")
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
                "SELECT date, open, high, low, close, volume FROM daily_prices "
                "WHERE ticker = ? ORDER BY date",
                conn, params=(ticker,), parse_dates=["date"], index_col="date",
            )
        df.columns = ["Open", "High", "Low", "Close", "Volume"]
        return df
