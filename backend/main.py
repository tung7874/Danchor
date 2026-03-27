from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
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
    action_suggestion, generate_analysis_text, state_dependency_text
)
from src.engine.state_dependency import StateDependencyAnalyzer

app = FastAPI(title="Decision Anchor API", version="1.0.0")


@app.on_event("startup")
async def startup_warmup():
    def warm():
        for ticker in _POPULAR_TICKERS:
            try:
                _get_df(ticker)
                print(f"[Warmup] {ticker} ready")
            except Exception as e:
                print(f"[Warmup] {ticker} failed: {e}")
    threading.Thread(target=warm, daemon=True).start()


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

# In-memory DataFrame cache: {ticker: (date_str, preprocessed_df)}
# Keyed by today's date — auto-invalidates next trading day
_df_cache: dict = {}
_cache_lock = threading.Lock()

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
    if df is None or df.empty:
        return pd.DataFrame()
    df = preprocessor.calculate_indicators(df)
    with _cache_lock:
        _df_cache[ticker] = (today, df)
    return df


class AnalyzeRequest(BaseModel):
    asset_code: str
    analysis_date: Optional[str] = None  # YYYY-MM-DD, defaults to today
    holding_horizon_days: int = 10


class ScanRequest(BaseModel):
    asset_code: str
    holding_horizon_days: int = 10


class PositionRequest(BaseModel):
    asset_code: str
    entry_date: str       # YYYY-MM-DD
    entry_price: float
    current_date: Optional[str] = None  # defaults to today
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

        # 1. Fetch & preprocess (memory-cached)
        df = _get_df(ticker)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {req.asset_code}")

        # 2. Encode current state
        state_info = encoder.encode_for_date(df, analysis_date)
        if state_info is None:
            raise HTTPException(status_code=400, detail="Not enough historical data to encode state for this date")

        # 3. Find similar historical states
        similar_events = matcher.find_similar(df, state_info["state"], analysis_date)

        # 4. Calculate return distribution
        distribution = dist_calc.calculate(df, similar_events, req.holding_horizon_days)
        if distribution is None:
            raise HTTPException(status_code=400, detail="Not enough similar historical events found")

        # 5. Stability analysis
        stability_result = stability.analyze(distribution["events"])

        TRADE_COST = 0.7  # 手續費(0.285%) + 交易稅(0.3%) + 滑點(0.1%) 大型股估計

        p25 = round(distribution["P25"], 2)
        p50 = round(distribution["P50"], 2)
        p75 = round(distribution["P75"], 2)
        net_p50 = round(p50 - TRADE_COST, 2)
        stab_label = stability_result["classification"]
        momentum = state_info["components"]["momentum"]
        trend = state_info["components"]["trend"]

        return {
            "asset_code": req.asset_code,
            "analysis_date": analysis_date,
            "holding_horizon_days": req.holding_horizon_days,
            "state": state_info,
            "distribution": {
                "P25": p25,
                "P50": p50,
                "P75": p75,
                "net_p50": net_p50,
                "N": distribution["N"],
                "win_rate": distribution.get("win_rate", 0),
                "p50_ci_low": distribution.get("p50_ci_low"),
                "p50_ci_high": distribution.get("p50_ci_high"),
                "profit_factor": distribution.get("profit_factor"),
                "data_range": distribution["data_range"],
            },
            "stability": stability_result,
            "confidence": _confidence_label(distribution["N"]),
            "decision": decision_summary(p25, p50, stab_label),
            "insight": quick_insight(momentum, trend, distribution.get("win_rate", 0)),
            "distribution_text": distribution_text(p25, p50, p75),
            "stability_text": stability_text(stab_label),
            "action": action_suggestion(p25, p50, stab_label),
            "analysis_text": generate_analysis_text(p25, p50, p75, stability_result.get("cv", 1.0)),
            "state_dependency": _build_dependency(df, state_info["state"], req.holding_horizon_days),
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/scan")
def scan_states(req: ScanRequest):
    try:
        ticker = req.asset_code.strip() + ".TW"
        df = _get_df(ticker)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {req.asset_code}")
        states = edge_scanner.scan(df, req.holding_horizon_days)
        return {
            "asset_code": req.asset_code,
            "holding_horizon_days": req.holding_horizon_days,
            "states": states,
        }
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/position")
def position(req: PositionRequest):
    try:
        current_date = req.current_date or date.today().isoformat()
        ticker = req.asset_code.strip() + ".TW"

        df = _get_df(ticker)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {req.asset_code}")

        result = position_analyzer.analyze(
            df=df,
            entry_date=req.entry_date,
            entry_price=req.entry_price,
            current_date=current_date,
            current_price=req.current_price,
            position_type=req.position_type,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/assets")
def list_assets():
    popular = [
        {"code": "2330", "name": "台積電"},
        {"code": "2317", "name": "鴻海"},
        {"code": "2454", "name": "聯發科"},
        {"code": "2382", "name": "廣達"},
        {"code": "2308", "name": "台達電"},
        {"code": "2881", "name": "富邦金"},
        {"code": "2882", "name": "國泰金"},
        {"code": "0050", "name": "元大台灣50"},
        {"code": "0056", "name": "元大高股息"},
        {"code": "2412", "name": "中華電"},
    ]
    return {"assets": popular}


def _build_dependency(df, state: str, horizon: int) -> dict | None:
    result = dep_analyzer.analyze(df, state, horizon)
    if result is None:
        return None
    result["text"] = state_dependency_text(result["label"])
    return result


def _confidence_label(n: int) -> str:
    if n >= 100:
        return "high"
    elif n >= 30:
        return "medium"
    else:
        return "low"
