def decision_summary(p25: float, p50: float, stability_label: str) -> str:
    if p25 > 0:
        level = "強正期望"
    elif p50 > 0.8:
        level = "正期望"
    elif p50 > 0:
        level = "弱正期望"
    else:
        level = "負期望"
    stab = {"Stable": "穩定", "Regime-Dependent": "環境相依", "Unstable": "不穩定"}.get(
        stability_label, stability_label
    )
    p50_str = f"+{p50}%" if p50 > 0 else f"{p50}%"
    return f"{level} · 中位 {p50_str}（{stab}）"


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
        "Regime-Dependent": "報酬高度依賴市場環境，需搭配趨勢判斷",
        "Unstable": "報酬分布不穩定，歷史參考價值低",
    }.get(label, "")


def action_suggestion(p25: float, p50: float, stability_label: str) -> list:
    if p25 > 0 and stability_label == "Stable":
        return ["統計上呈穩定正報酬", "各市場環境表現一致"]
    elif p50 > 0:
        return ["統計上偏正報酬", "受市場環境影響較明顯"]
    else:
        return ["統計上報酬偏弱", "歷史參考價值有限"]


def generate_analysis_text(p25: float, p50: float, p75: float, cv: float) -> str:
    # ① 期望（3類）
    if p25 > 0:
        exp = "整體呈現穩定正報酬特性"
    elif p50 > 0:
        exp = "整體呈現小幅正報酬傾向"
    else:
        exp = "整體報酬表現偏弱"

    # ② 穩定性（3類，依 CV）
    if cv < 0.5:
        stability = "且在不同市場階段表現一致"
    elif cv < 1.5:
        stability = "但報酬表現受市場環境影響較大"
    else:
        stability = "且歷史報酬分布差異較大"

    # ③ 風險（2類）
    risk = "整體下行風險相對可控" if p25 > -2 else "需留意潛在下行風險"

    # ④ 上行（2類）
    upside = "並具備一定上行延伸空間" if p75 > abs(p25) else "上行空間相對有限"

    return f"{exp}，{stability}，{risk}，{upside}。"
