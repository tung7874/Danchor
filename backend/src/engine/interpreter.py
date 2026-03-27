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
    mom = {"Strong": "動能強勁", "Neutral": "動能平穩", "Weak": "動能偏弱"}.get(momentum, momentum)
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
        "Stable": "報酬在不同時期表現一致，穩定性高",
        "Regime-Dependent": "在上升環境中表現較佳，於轉弱環境中效果可能降低",
        "Unstable": "報酬分布不穩定，歷史參考價值低",
    }.get(label, "")


def state_dependency_text(label: str) -> str:
    return {
        "高度依賴": "此統計結果與市場走勢具有明顯關聯，在上升環境中表現較佳，於轉弱環境中效果可能降低",
        "中度依賴": "此結果在市場上升時表現較佳，市場轉弱時效果可能下降",
        "低依賴": "此條件在不同市場環境下表現相對一致，未明顯依賴市場方向",
    }.get(label, "資料不足，無法判斷")


def action_suggestion(p25: float, p50: float, stability_label: str) -> list:
    if p25 > 0 and stability_label == "Stable":
        return ["整體具備穩定正報酬特性", "在不同市場環境下表現相對一致"]
    elif p50 > 0:
        return ["目前條件尚未呈現明確優勢，可持續觀察後續變化"]
    else:
        return ["整體報酬表現偏弱", "不同時期表現差異較大，結果一致性較低"]


def generate_analysis_text(p25: float, p50: float, p75: float, cv: float) -> str:
    # ① 期望（3類）
    if p25 > 0:
        exp = "整體具備穩定正報酬特性"
    elif p50 > 0:
        exp = "整體呈現小幅正報酬傾向"
    else:
        exp = "整體報酬表現偏弱"

    # ② 穩定性（3類，依 CV）
    if cv < 0.5:
        stability = "且在不同市場環境下表現相對一致"
    elif cv < 1.5:
        stability = "但表現會隨市場變化而有所差異"
    else:
        stability = "且不同時期結果差異較大"

    # ③+④ 風險與上行合併（4類，避免矛盾）
    if p25 < -2 and p75 > abs(p25):
        risk_upside = "報酬分布波動較大，上下幅度均寬"
    elif p25 < -2:
        risk_upside = "下行風險偏高，上行空間亦相對有限"
    elif p75 > abs(p25):
        risk_upside = "下行風險相對可控，上行空間較寬"
    else:
        risk_upside = "下行風險可控，但上行空間有限"

    return f"{exp}，{stability}，{risk_upside}。"
