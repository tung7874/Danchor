import { useEffect, useState } from "react";
import { fetchAnalysis } from "../lib/api";

type AnalysisResult = {
  asset_code: string;
  analysis_date: string;
  holding_horizon_days: number;
  state: {
    state: string;
    actual_date: string;
    components: { relative_position: string; momentum: string; trend: string };
    raw: { close: number; sma_50: number; mom_5_pct: number };
  };
  distribution: { P25: number; P50: number; P75: number; N: number; data_range: string };
  stability: {
    classification: string;
    reason: string;
    cv: number;
    periods: { label: string; mean: number; count: number }[];
  };
  confidence: string;
  decision: string;
  insight: string;
  distribution_text: string[];
  stability_text: string;
  action: string[];
};

interface Props {
  code: string;
  days: number;
  onBack: () => void;
}

export default function AnalyzePage({ code, days, onBack }: Props) {
  const [data, setData] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    setError("");
    fetchAnalysis({ asset_code: code, holding_horizon_days: days })
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [code, days]);

  const p25 = data?.distribution.P25 ?? 0;
  const p50 = data?.distribution.P50 ?? 0;
  const p75 = data?.distribution.P75 ?? 0;
  const n = data?.distribution.N ?? 0;

  const stabilityColor: Record<string, string> = {
    Stable: "#00C851",
    "Regime-Dependent": "#FFB800",
    Unstable: "#FF4444",
  };
  const stabilityLabel: Record<string, string> = {
    Stable: "穩定",
    "Regime-Dependent": "環境相依",
    Unstable: "不穩定",
  };
  const confLabel: Record<string, string> = {
    high: "高信度", medium: "中信度", low: "低信度",
  };
  const confColor: Record<string, string> = {
    high: "#00C851", medium: "#FFB800", low: "#FF4444",
  };

  return (
    <div
      className="flex flex-col min-h-dvh bg-black"
      style={{
        paddingTop: "max(0px, env(safe-area-inset-top))",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
      }}
    >
      {/* Navbar */}
      <div className="flex items-center px-4 py-3 border-b border-white/[0.06]">
        <button
          onClick={onBack}
          className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center mr-3 active:bg-white/20 transition-colors"
        >
          <svg width="9" height="15" fill="none" viewBox="0 0 9 15">
            <path d="M7.5 1.5 1.5 7.5l6 6" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </button>
        <div className="flex-1">
          <p className="text-white font-semibold">{code}</p>
          <p className="text-[#555] text-xs">{days} 日持有分析</p>
        </div>
        {data && (
          <span
            className="text-xs font-semibold px-2.5 py-1 rounded-full"
            style={{
              color: confColor[data.confidence],
              background: confColor[data.confidence] + "22",
              border: `1px solid ${confColor[data.confidence]}44`,
            }}
          >
            {confLabel[data.confidence]}
          </span>
        )}
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
        {loading && (
          <div className="space-y-4">
            {[120, 200, 100, 140].map((h, i) => (
              <div key={i} className="skeleton" style={{ height: h }} />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-2xl bg-[#FF4444]/10 border border-[#FF4444]/30 p-5 text-center">
            <p className="text-[#FF4444] text-sm font-medium mb-1">分析失敗</p>
            <p className="text-[#666] text-xs">{error}</p>
          </div>
        )}

        {data && !loading && (
          <>
            {/* Decision block */}
            <div className="rounded-[14px] bg-[#1C1C1E] px-5 py-4 animate-fade-up">
              <p className="text-white/40 text-[11px] uppercase tracking-wider mb-3">統計分析</p>
              <div className="flex gap-2 flex-wrap">
                {data.action?.map((a) => (
                  <span key={a} className="px-4 py-1.5 rounded-full bg-white/15 text-white text-[13px] font-medium">
                    {a}
                  </span>
                ))}
                {data.distribution_text?.map((t) => (
                  <span key={t} className="px-4 py-1.5 rounded-full bg-white/[0.06] text-white/50 text-[13px]">
                    {t}
                  </span>
                ))}
              </div>
            </div>

            {/* State card */}
            <div className="rounded-2xl bg-[#1C1C1E] p-5 animate-fade-up">
              <div className="flex justify-between items-center mb-3">
                <h2 className="text-white font-semibold">市場狀態</h2>
                <span className="text-[#555] text-xs">{data.state.actual_date}</span>
              </div>
              <div className="flex gap-2 mb-3">
                {[
                  { l: "位置", v: { High: "近高點", Mid: "中性", Low: "近低點" }[data.state.components.relative_position] ?? data.state.components.relative_position },
                  { l: "動能", v: { Strong: "強動能", Neutral: "中性", Weak: "弱動能" }[data.state.components.momentum] ?? data.state.components.momentum },
                  { l: "趨勢", v: { Bull: "多頭", Bear: "空頭" }[data.state.components.trend] ?? data.state.components.trend },
                ].map((item) => (
                  <div key={item.l} className="flex-1 rounded-xl bg-[#2C2C2E] px-2 py-2.5 text-center">
                    <p className="text-[#555] text-[10px] mb-0.5">{item.l}</p>
                    <p className="text-white text-[13px] font-semibold">{item.v}</p>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <p className="text-[#444] text-xs">收盤</p>
                  <p className="text-[#AAA] text-xs font-mono">${data.state.raw.close}</p>
                </div>
                <div>
                  <p className="text-[#444] text-xs">5日動能</p>
                  <p className={`text-xs font-mono ${data.state.raw.mom_5_pct >= 0 ? "text-[#00C851]" : "text-[#FF4444]"}`}>
                    {data.state.raw.mom_5_pct > 0 ? "+" : ""}{data.state.raw.mom_5_pct}%
                  </p>
                </div>
                <div>
                  <p className="text-[#444] text-xs">SMA50</p>
                  <p className="text-[#AAA] text-xs font-mono">${data.state.raw.sma_50}</p>
                </div>
              </div>
            </div>

            {/* Distribution card */}
            <div className="rounded-2xl bg-[#1C1C1E] p-5 animate-fade-up">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-white font-semibold">報酬分布</h2>
                <span className="text-[#555] text-xs font-mono">{data.distribution.data_range}</span>
              </div>

              <DistributionBar p25={p25} p50={p50} p75={p75} />

              <div className="grid grid-cols-3 gap-3 mt-4">
                <StatBox label="P25" sub="較差情況" value={p25} />
                <StatBox label="P50" sub="平均情況" value={p50} highlight />
                <StatBox label="P75" sub="較好情況" value={p75} />
              </div>

              <div className="mt-3 pt-3 border-t border-white/[0.06] flex justify-between">
                <span className="text-[#555] text-xs">樣本數</span>
                <span className={`text-sm font-mono font-bold ${n >= 100 ? "text-[#00C851]" : n >= 30 ? "text-[#FFB800]" : "text-[#FF4444]"}`}>
                  {n} 次
                </span>
              </div>
            </div>

            {/* Stability */}
            <div className="rounded-2xl bg-[#1C1C1E] p-5 animate-fade-up">
              <div className="flex justify-between items-center mb-3">
                <h2 className="text-white font-semibold">穩定性評估</h2>
                <span
                  className="text-xs font-semibold px-2.5 py-1 rounded-full"
                  style={{
                    color: stabilityColor[data.stability.classification],
                    background: stabilityColor[data.stability.classification] + "22",
                    border: `1px solid ${stabilityColor[data.stability.classification]}44`,
                  }}
                >
                  {stabilityLabel[data.stability.classification] ?? data.stability.classification}
                </span>
              </div>
              <p className="text-white/50 text-[13px] leading-relaxed mb-4">{data.stability_text || data.stability.reason}</p>
              {data.stability.cv !== undefined && (
                <div>
                  <div className="flex justify-between text-[11px] text-white/30 mb-1.5">
                    <span>波動</span>
                    <span>穩定</span>
                  </div>
                  <div className="relative h-2 rounded-full bg-white/10">
                    <div
                      className="absolute inset-y-0 left-0 rounded-full bg-gradient-to-r from-[#FF4444] via-[#FFB800] to-[#00C851]"
                      style={{ width: `${Math.max(4, Math.min(100, (1 - data.stability.cv / 2) * 100))}%` }}
                    />
                  </div>
                  <p className="text-white/25 text-[11px] font-mono mt-1.5 text-right">CV = {data.stability.cv}</p>
                </div>
              )}
            </div>

            {/* Periods */}
            {data.stability.periods?.length > 0 && (
              <div className="rounded-2xl bg-[#1C1C1E] p-5 animate-fade-up">
                <h2 className="text-white font-semibold mb-4">分期表現</h2>
                <div className="space-y-3">
                  {data.stability.periods.map((p) => {
                    const max = Math.max(...data.stability.periods.map((x) => Math.abs(x.mean)), 0.1);
                    return (
                      <div key={p.label} className="flex items-center gap-3">
                        <span className="text-[#555] text-xs w-16 shrink-0">{p.label}</span>
                        <div className="flex-1 h-6 rounded-lg bg-[#2C2C2E] relative overflow-hidden">
                          <div
                            className={`absolute top-0 h-full rounded-lg ${p.mean >= 0 ? "bg-[#00C851]/30 left-1/2" : "bg-[#FF4444]/30 right-1/2"}`}
                            style={{ width: `${(Math.abs(p.mean) / max) * 50}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono w-14 text-right" style={{ color: p.mean >= 0 ? "#00C851" : "#FF4444" }}>
                          {p.mean > 0 ? "+" : ""}{p.mean}%
                        </span>
                        <span className="text-[#444] text-xs w-8 text-right">{p.count}次</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="text-center py-4">
              <p className="text-[#2A2A2A] text-xs leading-relaxed">
                歷史統計分析 · 不預測未來 · 不構成投資建議
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function DistributionBar({ p25, p50, p75 }: { p25: number; p50: number; p75: number }) {
  const min = Math.min(p25, -15);
  const max = Math.max(p75, 15);
  const range = max - min;
  const toX = (v: number) => ((v - min) / range) * 100;

  return (
    <div className="relative h-12 flex items-center">
      <div className="absolute inset-x-0 h-2 rounded-full bg-[#2A2A2A]" />
      <div className="absolute h-2 rounded-l-full bg-[#FF4444]/30" style={{ left: `${toX(min)}%`, width: `${toX(0) - toX(min)}%` }} />
      <div className="absolute h-2 rounded-r-full bg-[#00C851]/30" style={{ left: `${toX(0)}%`, width: `${toX(max) - toX(0)}%` }} />
      <div className="absolute h-3 rounded-full bg-white/20" style={{ left: `${toX(p25)}%`, width: `${toX(p75) - toX(p25)}%` }} />
      <div className="absolute w-px h-4 bg-[#444]" style={{ left: `${toX(0)}%` }} />
      <div className="absolute w-2.5 h-2.5 rounded-full bg-[#FF4444]" style={{ left: `${toX(p25)}%`, transform: "translateX(-50%)" }} />
      <div className="absolute w-4 h-4 rounded-full bg-white border-2 border-[#0D0D0D] z-10" style={{ left: `${toX(p50)}%`, transform: "translateX(-50%)" }} />
      <div className="absolute w-2.5 h-2.5 rounded-full bg-[#00C851]" style={{ left: `${toX(p75)}%`, transform: "translateX(-50%)" }} />
    </div>
  );
}

function StatBox({ label, sub, value, highlight }: { label: string; sub?: string; value: number; highlight?: boolean }) {
  const color = value > 0 ? "#00C851" : value < 0 ? "#FF4444" : "#888";
  return (
    <div className={`rounded-xl p-3 text-center ${highlight ? "bg-white/5 border border-white/10" : "bg-[#2C2C2E]"}`}>
      <p className="text-[#555] text-[11px]">{label}</p>
      {sub && <p className="text-white/25 text-[10px] mb-1">{sub}</p>}
      <p className="font-mono font-bold text-base" style={{ color }}>
        {value > 0 ? "+" : ""}{value}%
      </p>
    </div>
  );
}
