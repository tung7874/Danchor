TEXT_MAP = {
    "expectancy": {
        "high": "報酬分布呈現正向偏態，歷史樣本中錄得正報酬之頻率與幅度均佔優勢，整體結構具備延續性",
        "mid":  "整體報酬結構略偏正向，顯示歷史環境中具備一定的上行機會，但優勢幅度與一致性仍有限",
        "low":  "報酬分布未呈現明顯正向特徵，歷史樣本中上漲優勢不足，整體報酬結構偏弱",
    },
    "risk": {
        "low":  "下行波動相對收斂，報酬分布集中度較高，極端值出現之頻率與幅度均相對有限",
        "high": "報酬分布離散程度較高，波動幅度明顯擴大，需留意尾部風險帶來的潛在影響",
    },
    "stability": {
        "stable":   "不同時間區間之報酬表現具備一致性，統計特徵展現良好的穩健性",
        "unstable": "報酬結構隨時間序列變化明顯，不同時期表現差異較大，統計一致性偏低",
    },
    "dependency": {
        "high": "此統計結果與市場趨勢呈現高度連動，於市場轉弱時表現可能同步轉差，受整體環境影響較為顯著",
        "mid":  "報酬表現與市場整體走勢存在一定關聯，不同市場環境下表現可能有所差異",
        "low":  "報酬表現對市場整體走勢依賴程度較低，在不同環境下維持相對獨立且一致的表現",
    },
}


# ─── 分類輔助 ───────────────────────────────────────────────

def _classify_exp(p25: float, p50: float) -> str:
    if p25 > 0:
        return "high"
    elif p50 > 0:
        return "mid"
    return "low"


def _classify_risk(p25: float) -> str:
    return "low" if p25 > -2 else "high"


def _classify_stability(label: str) -> str:
    return "stable" if label == "Stable" else "unstable"


def _classify_dependency(label: str) -> str:
    if label == "高度依賴":
        return "high"
    elif label == "中度依賴":
        return "mid"
    return "low"


# ─── 語意衝突處理 ────────────────────────────────────────────

def resolve_conflict(exp: str, risk: str, stability: str, dependency: str):
    # 高風險壓制樂觀語氣
    if risk == "high" and exp == "high":
        exp = "mid"
    # 高依賴不應同時 stable
    if dependency == "high" and stability == "stable":
        stability = "unstable"
    return exp, risk, stability, dependency


# ─── 可信度模組 ─────────────────────────────────────────────

def compute_confidence(N: int, p25: float, p75: float, dependency_label: str) -> str:
    # 樣本數（調整為台股實際區間）
    if N > 150:
        n_score = 2
    elif N > 80:
        n_score = 1
    else:
        n_score = 0

    # 分布穩定性（IQR）
    iqr = p75 - p25
    if iqr < 3:
        stability_score = 2
    elif iqr < 6:
        stability_score = 1
    else:
        stability_score = 0

    # 市場依賴
    dep_score = {"低依賴": 2, "中度依賴": 1, "高度依賴": 0}.get(dependency_label, 1)

    total = n_score + stability_score + dep_score
    if total >= 5:
        return "high"
    elif total >= 3:
        return "medium"
    return "low"


def confidence_text(level: str) -> str:
    return {
        "high":   "樣本數充足且報酬分布穩定，統計結果具備較高參考價值。",
        "medium": "樣本數與分布穩定性屬中等，結果具一定參考性，但仍存在不確定性。",
        "low":    "樣本數或分布穩定性不足，統計結果參考性有限。",
    }.get(level, "")


# ─── 句型引擎 ────────────────────────────────────────────────

def generate_analysis_text(
    p25: float, p50: float, p75: float,
    stability_label: str,
    dependency_label: str,
    N: int,
    direction: str = "多",
) -> str:
    exp        = _classify_exp(p25, p50)
    risk       = _classify_risk(p25)
    stability  = _classify_stability(stability_label)
    dependency = _classify_dependency(dependency_label)

    exp, risk, stability, dependency = resolve_conflict(exp, risk, stability, dependency)

    exp_text  = TEXT_MAP["expectancy"][exp]
    risk_text = TEXT_MAP["risk"][risk]

    # 依賴文案加入方向資訊
    if dependency == "low":
        dep_text = TEXT_MAP["dependency"]["low"]
    elif direction == "空":
        dep_text = {
            "high": "此統計結果在市場轉弱時表現明顯較佳，於上升環境中優勢可能減弱，受整體環境影響顯著",
            "mid":  "此條件在市場轉弱時表現相對較佳，於上升環境中優勢較不明顯",
        }.get(dependency, TEXT_MAP["dependency"][dependency])
    else:
        dep_text = {
            "high": "此統計結果與市場走勢具有明顯關聯，在上升環境中表現較佳，於轉弱環境中效果可能降低",
            "mid":  "此結果在市場上升時表現相對較佳，於下跌環境中優勢較不明顯",
        }.get(dependency, TEXT_MAP["dependency"][dependency])

    # 右尾不對稱特徵（P75 明顯大於 |P25|）
    right_skew = p75 > abs(p25) * 1.5 and p75 > 3
    skew_text = "報酬分布呈現右側延伸特性，具備較大上行空間，但同時伴隨明顯的波動風險。" if (right_skew and risk == "high") else ""

    # 句號分隔各邏輯段
    if risk == "high":
        base = f"{exp_text}。{risk_text}。{dep_text}。"
    elif dependency == "high":
        base = f"{exp_text}。{dep_text}。{risk_text}。"
    elif dependency == "mid":
        base = f"{exp_text}。{dep_text}。{risk_text}。"
    else:
        base = f"{exp_text}。{risk_text}。{dep_text}。"

    return base + skew_text if skew_text else base


# ─── 其他輸出函數（維持原有）────────────────────────────────

def decision_summary(p25: float, p50: float, stability_label: str) -> str:
    if p25 > 0:
        level = "偏強"
    elif p50 > 0.8:
        level = "中性偏多"
    elif p50 > 0:
        level = "中性"
    else:
        level = "偏弱"
    p50_str = f"+{p50}%" if p50 > 0 else f"{p50}%"
    return f"歷史分布：{level} · 中位 {p50_str}"


def quick_insight(momentum: str, trend: str, win_rate: float) -> str:
    mom  = {"Strong": "動能強勁", "Neutral": "動能平穩", "Weak": "動能偏弱"}.get(momentum, momentum)
    trnd = "多頭結構" if trend == "Bull" else "空頭環境"
    return f"{mom}，{trnd} · 歷史勝率 {win_rate}%"


def distribution_text(p25: float, p50: float, p75: float) -> list:
    texts = []
    texts.append("小幅正期望" if p50 > 0 else "偏負期望")
    if p75 > abs(p25):
        texts.append("右尾機會存在")
    texts.append("下行風險可控" if p25 > -2 else "下行風險偏高")
    return texts


def stability_text(label: str) -> str:
    return {
        "Stable":           "報酬在不同時期表現一致，穩定性高",
        "Regime-Dependent": "在上升環境中表現較佳，於轉弱環境中效果可能降低",
        "Unstable":         "報酬分布不穩定，歷史參考價值低",
    }.get(label, "")


def state_dependency_text(label: str, direction: str = "多") -> str:
    if label == "低依賴":
        return "此條件在不同市場環境下表現相對一致，未明顯依賴市場方向"
    if direction == "多":
        return {
            "高度依賴": "此統計結果與市場走勢具有明顯關聯，在上升環境中表現較佳，於轉弱環境中效果可能降低",
            "中度依賴": "此結果在市場上升時表現相對較佳，於下跌環境中優勢較不明顯",
        }.get(label, "")
    else:  # direction == "空"：下跌市場表現更好
        return {
            "高度依賴": "此統計結果在市場轉弱時表現明顯較佳，於上升環境中優勢可能減弱，受整體環境影響顯著",
            "中度依賴": "此條件在市場轉弱時表現相對較佳，於上升環境中優勢較不明顯",
        }.get(label, "")


def action_suggestion(p25: float, p50: float, stability_label: str) -> list:
    if p25 > 0 and stability_label == "Stable":
        return ["整體具備穩定正報酬特性", "在不同市場環境下表現相對一致"]
    elif p50 > 0:
        return ["目前條件尚未呈現明確優勢，可持續觀察後續變化"]
    else:
        return ["整體報酬表現偏弱", "不同時期表現差異較大，結果一致性較低"]
