from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
import time
import traceback
import threading
import pandas as pd

from src.data.fetcher import DataFetcher
from src.data.preprocessor import Preprocessor
from src.engine.state_encoder import StateEncoder
from src.engine.matcher import Matcher
from src.engine.distribution import DistributionCalculator
from src.engine.stability import StabilityAnalyzer
from src.part2.position_analyzer import PositionAnalyzer
from src.engine.scanner import EdgeScanner
from src.engine.interpreter import (
    decision_summary, quick_insight, distribution_text, stability_text,
    action_suggestion, generate_analysis_text, state_dependency_text,
    compute_confidence, confidence_text,
)
from src.engine.state_dependency import StateDependencyAnalyzer

app = FastAPI(title="Decision Anchor API", version="1.0.0")


@app.on_event("startup")
async def startup_warmup():
    def warm_one(ticker):
        try:
            _get_df(ticker)
            code = ticker.replace(".TW", "")
            for horizon in [5, 10, 20]:
                try:
                    analyze(AnalyzeRequest(asset_code=code, holding_horizon_days=horizon))
                except Exception:
                    pass
            print(f"[Warmup] {ticker} ready")
        except Exception as e:
            print(f"[Warmup] {ticker} failed: {e}")

    def warm_all():
        for ticker in _POPULAR_TICKERS:
            warm_one(ticker)
            time.sleep(1.5)  # avoid yfinance rate limit during warmup

    threading.Thread(target=warm_all, daemon=True).start()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

fetcher = DataFetcher()
preprocessor = Preprocessor()
encoder = StateEncoder()
matcher = Matcher()
dist_calc = DistributionCalculator()
stability = StabilityAnalyzer()
position_analyzer = PositionAnalyzer()
edge_scanner = EdgeScanner()
dep_analyzer = StateDependencyAnalyzer()

_df_cache = {}
_cache_lock = threading.Lock()

_result_cache = {}
_result_lock = threading.Lock()

_POPULAR_TICKERS = [
    "2330.TW", "2317.TW", "2454.TW", "2382.TW", "2308.TW",
    "2881.TW", "2882.TW", "0050.TW", "0056.TW", "2412.TW",
]


def _get_df(ticker: str) -> pd.DataFrame:
    today = date.today().isoformat()
    with _cache_lock:
        cached = _df_cache.get(ticker)
        if cached and cached[0] == today:
            return cached[1]

    df = fetcher.get_data(ticker)

    if (df is None or df.empty) and ticker.endswith(".TW") and not ticker.endswith(".TWO"):
        df = fetcher.get_data(ticker[:-3] + ".TWO")

    if df is None or df.empty:
        return pd.DataFrame()

    df = preprocessor.calculate_indicators(df)

    with _cache_lock:
        _df_cache[ticker] = (today, df)

    return df


class AnalyzeRequest(BaseModel):
    asset_code: str
    analysis_date: Optional[str] = None
    holding_horizon_days: int = 10


class ScanRequest(BaseModel):
    asset_code: str
    holding_horizon_days: int = 10


class PositionRequest(BaseModel):
    asset_code: str
    entry_date: str
    entry_price: float
    current_date: Optional[str] = None
    current_price: float
    position_type: str = "LONG"


@app.get("/")
def root():
    return {"status": "ok", "service": "Decision Anchor API"}


@app.get("/api/v1/health")
def health():
    return {"status": "healthy"}


@app.post("/api/v1/analyze")
def analyze(req: AnalyzeRequest):
    try:
        analysis_date = req.analysis_date or date.today().isoformat()
        ticker = req.asset_code.strip() + ".TW"

        rkey = (ticker, analysis_date, req.holding_horizon_days)
        with _result_lock:
            cached = _result_cache.get(rkey)
            if cached and cached[0] == analysis_date:
                return cached[1]

        df = _get_df(ticker)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {req.asset_code}")

        state_info = encoder.encode_for_date(df, analysis_date)
        if state_info is None:
            raise HTTPException(status_code=400, detail="Not enough historical data")

        similar_events = matcher.find_similar(df, state_info["state"], analysis_date)

        # ===== 🔥 修補開始 =====
        distribution = dist_calc.calculate(df, similar_events, req.holding_horizon_days)

        if distribution is None or not distribution.get("valid", True):
            p25 = p50 = p75 = None
            net_p50 = None
            n = distribution.get("N", 0) if distribution else 0
            win_rate = None
        else:
            p25 = round(distribution.get("P25", 0), 2)
            p50 = round(distribution.get("P50", 0), 2)
            p75 = round(distribution.get("P75", 0), 2)
            net_p50 = round(p50 - 0.7, 2)
            n = distribution.get("N", 0)
            win_rate = distribution.get("win_rate", 0)
        # ===== 🔥 修補結束 =====

        stability_result = stability.analyze(distribution.get("events", []))

        dep_result = _build_dependency(df, state_info["state"], req.holding_horizon_days)
        dep_label = dep_result["label"] if dep_result else "低依賴"
        dep_direction = dep_result.get("direction", "多") if dep_result else "多"

        stab_label = stability_result.get("classification", "Unstable")
        consistency = stability_result.get("consistency", 0.0)

        if not distribution or not distribution.get("valid", True):
            conf_level = "low"
        else:
            conf_level = compute_confidence(n, p25 or 0, p75 or 0, dep_label)

        result = {
            "asset_code": req.asset_code,
            "analysis_date": analysis_date,
            "holding_horizon_days": req.holding_horizon_days,
            "state": state_info,
            "distribution": {
                "P25": p25,
                "P50": p50,
                "P75": p75,
                "net_p50": net_p50,
                "N": n,
                "win_rate": win_rate,
                "p50_ci_low": distribution.get("p50_ci_low"),
                "p50_ci_high": distribution.get("p50_ci_high"),
                "profit_factor": distribution.get("profit_factor"),
                "data_range": distribution.get("data_range"),
            },
            "stability": stability_result,
            "confidence": conf_level,
            "confidence_text": confidence_text(conf_level),
            "decision": decision_summary(p25 or 0, p50 or 0, stab_label),
            "insight": quick_insight(
                state_info["components"]["momentum"],
                state_info["components"]["trend"],
                win_rate or 0,
            ),
            "distribution_text": distribution_text(p25 or 0, p50 or 0, p75 or 0),
            "stability_text": stability_text(stab_label),
            "action": action_suggestion(p25 or 0, p50 or 0, stab_label),
            "analysis_text": generate_analysis_text(
                p25 or 0, p50 or 0, p75 or 0,
                stab_label, dep_label, n,
                direction=dep_direction,
                consistency=consistency,
            ),
            "state_dependency": dep_result,
        }

        with _result_lock:
            _result_cache[rkey] = (analysis_date, result)

        return result

    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.post("/api/v1/scan")
def scan_states(req: ScanRequest):
    try:
        df = _get_df(req.asset_code.strip() + ".TW")
        states = edge_scanner.scan(df, req.holding_horizon_days)
        return {"states": states}
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


@app.post("/api/v1/position")
def position(req: PositionRequest):
    try:
        df = _get_df(req.asset_code.strip() + ".TW")
        return position_analyzer.analyze(
            df,
            req.entry_date,
            req.entry_price,
            req.current_date or date.today().isoformat(),
            req.current_price,
            req.position_type,
        )
    except Exception as e:
        traceback.print_exc()
        return {"status": "error", "message": str(e)}


def _build_dependency(df, state: str, horizon: int):
    result = dep_analyzer.analyze(df, state, horizon)
    if result:
        result["text"] = state_dependency_text(result["label"], result.get("direction", "多"))
    return result
