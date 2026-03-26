def decision_summary(p25: float, p50: float, stability_label: str) -> str:
    if p25 > 0:
        level = "強正期望"
    elif p50 > 0:
        level = "弱正期望"
    else:
        level = "負期望"
    stab = {"Stable": "穩定", "Regime-Dependent": "環境相依", "Unstable": "不穩定"}.get(
        stability_label, stability_label
    )
    return f"{level}（{stab}）"


def quick_insight(momentum: str, trend: str) -> str:
    mom = {"Strong": "動能強勁", "Neutral": "動能平穩", "Weak": "動能偏弱"}.get(momentum, momentum)
    trnd = "多頭結構" if trend == "Bull" else "空頭環境"
    return f"{mom}，目前處於{trnd}"


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
        return ["可考慮進場", "具備穩定優勢"]
    elif p50 > 0:
        return ["可觀察", "需搭配趨勢"]
    else:
        return ["不建議進場", "風險高於報酬"]
