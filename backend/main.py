from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
import traceback

from src.data.fetcher import DataFetcher
from src.data.preprocessor import Preprocessor
from src.engine.state_encoder import StateEncoder
from src.engine.matcher import Matcher
from src.engine.distribution import DistributionCalculator
from src.engine.stability import StabilityAnalyzer
from src.part2.position_analyzer import PositionAnalyzer
from src.engine.scanner import EdgeScanner
from src.engine.interpreter import (
    decision_summary, quick_insight, distribution_text, stability_text, action_suggestion
)

app = FastAPI(title="Decision Anchor API", version="1.0.0")

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

        # 1. Fetch & preprocess
        df = fetcher.get_data(ticker)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {req.asset_code}")
        df = preprocessor.calculate_indicators(df)

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

        p25 = round(distribution["P25"], 2)
        p50 = round(distribution["P50"], 2)
        p75 = round(distribution["P75"], 2)
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
                "N": distribution["N"],
                "data_range": distribution["data_range"],
            },
            "stability": stability_result,
            "confidence": _confidence_label(distribution["N"]),
            "decision": decision_summary(p25, p50, stab_label),
            "insight": quick_insight(momentum, trend),
            "distribution_text": distribution_text(p25, p50, p75),
            "stability_text": stability_text(stab_label),
            "action": action_suggestion(p25, p50, stab_label),
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
        df = fetcher.get_data(ticker)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {req.asset_code}")
        df = preprocessor.calculate_indicators(df)
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

        df = fetcher.get_data(ticker)
        if df is None or df.empty:
            raise HTTPException(status_code=404, detail=f"No data found for {req.asset_code}")
        df = preprocessor.calculate_indicators(df)

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


def _confidence_label(n: int) -> str:
    if n >= 100:
        return "high"
    elif n >= 30:
        return "medium"
    else:
        return "low"
