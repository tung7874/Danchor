import time
import threading
import requests
import urllib3
import yfinance as yf
import pandas as pd
import sqlite3
import os
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# Suppress SSL warnings for TWSE/TPEx certificates (they have known cert issues)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_yf_lock = threading.Lock()
_START_YEAR = datetime.now().year - 8  # rolling 8-year window

_data_dir = os.environ.get("DATA_DIR", os.path.join(os.path.dirname(__file__), "../../data/processed"))
DB_PATH = os.path.join(_data_dir, "market_data.db")

_TWSE_SESSION = requests.Session()
_TWSE_SESSION.headers.update({
    "Accept": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://www.twse.com.tw/",
})
_TWSE_SESSION.verify = False  # TWSE/TPEx certs have Missing Subject Key Identifier issues


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

    # ── FinMind REST API (primary — single request, all history) ─
    def _fetch_finmind_rest(self, ticker: str) -> pd.DataFrame:
        stock_id = self._stock_id(ticker)
        print(f"[Fetcher] FinMind downloading {stock_id}...")
        params = {
            "dataset": "TaiwanStockPrice",
            "data_id": stock_id,
            "start_date": f"{_START_YEAR}-01-01",
        }
        token = os.environ.get("FINMIND_TOKEN")
        if token:
            params["token"] = token
            print(f"[Fetcher] FinMind using token (user: tung7874)")
        else:
            print("[Fetcher] FinMind using anonymous (no token)")
        try:
            r = requests.get(
                "https://api.finmindtrade.com/api/v4/data",
                params=params,
                timeout=10,
            )
            data = r.json()
            if data.get("status") != 200 or not data.get("data"):
                print(f"[Fetcher] FinMind no data: status={data.get('status')}")
                return pd.DataFrame()
            df = pd.DataFrame(data["data"])
            df["date"] = pd.to_datetime(df["date"])
            df = df.rename(columns={"max": "high", "min": "low", "Trading_Volume": "volume"})
            df = df[["date", "open", "high", "low", "close", "volume"]].set_index("date").sort_index()
            df = df[df["close"] > 0].dropna()
            print(f"[Fetcher] FinMind OK: {len(df)} rows")
            return df
        except Exception as e:
            print(f"[Fetcher] FinMind REST failed: {e}")
            return pd.DataFrame()

    # ── TWSE (上市) — 使用舊版穩定 API ──────────────────────────
    def _fetch_twse(self, ticker: str) -> pd.DataFrame:
        stock_id = self._stock_id(ticker)
        print(f"[Fetcher] TWSE downloading {stock_id}...")

        def fetch_month(ym):
            y, m = ym
            for attempt in range(3):
                try:
                    r = _TWSE_SESSION.get(
                        "https://www.twse.com.tw/exchangeReport/STOCK_DAY",
                        params={"response": "json", "date": f"{y}{m:02d}01", "stockNo": stock_id},
                        timeout=15,
                    )
                    if r.ok:
                        data = r.json()
                        if data.get("stat") == "OK":
                            return data.get("data", [])
                        return []  # stat != OK means no data for that month
                    time.sleep(1 + attempt)
                except Exception:
                    if attempt < 2:
                        time.sleep(2 + attempt * 2)
            return []

        months = _gen_months(_START_YEAR)
        with ThreadPoolExecutor(max_workers=4) as pool:
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

    # ── TPEx (上櫃) — POST API (GET endpoint redirects, new response format) ──
    def _fetch_tpex(self, ticker: str) -> pd.DataFrame:
        stock_id = self._stock_id(ticker)
        print(f"[Fetcher] TPEx downloading {stock_id}...")

        def fetch_month(ym):
            y, m = ym
            roc = y - 1911
            for attempt in range(3):
                try:
                    # Must use POST; GET 302-redirects to non-functional URL
                    # New response format: {"tables": [{"data": [...]}], ...}
                    # Old aaData format no longer returned
                    r = _TWSE_SESSION.post(
                        "https://www.tpex.org.tw/web/stock/aftertrading/daily_trading_info/st43_download.php",
                        data={"l": "zh-tw", "d": f"{roc}/{m:02d}", "s": stock_id, "download": "json"},
                        timeout=15,
                    )
                    if r.ok:
                        data = r.json()
                        # Try new format first: tables[0].data
                        tables = data.get("tables", [])
                        if tables and tables[0].get("data"):
                            return tables[0]["data"]
                        # Legacy format fallback
                        if data.get("aaData"):
                            return data["aaData"]
                        return []
                    time.sleep(1 + attempt)
                except Exception:
                    if attempt < 2:
                        time.sleep(2 + attempt * 2)
            return []

        months = _gen_months(_START_YEAR)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(fetch_month, months))

        rows = []
        for month_data in results:
            for row in month_data:
                try:
                    # New format fields: [日期, 成交張數, 成交仟元, ?, 開盤, 最高, 最低, 收盤, 漲跌, 筆數]
                    # Old aaData fields: [日期, 成交股數, 成交金額, ?, 開盤, 最高, 最低, 收盤, 漲跌, 筆數]
                    # Both formats share the same column positions
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
        # FinMind REST: single request, fast (~1-2s if reachable)
        if is_tw or is_otc:
            df = self._fetch_finmind_rest(ticker)
        # yfinance: single request fallback (much faster than TWSE monthly)
        if not self._is_valid_df(df):
            df = self._fetch_yfinance(ticker)
        # TWSE monthly: last resort for listed stocks (slow, 30+ requests)
        if not self._is_valid_df(df) and is_tw:
            df = self._fetch_twse(ticker)
        # TPEx monthly: last resort for OTC stocks
        if not self._is_valid_df(df) and is_otc:
            df = self._fetch_tpex(ticker)
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
