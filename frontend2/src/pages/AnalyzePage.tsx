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
  distribution: {
    P25: number; P50: number; P75: number; net_p50: number; N: number;
    win_rate: number; p50_ci_low: number; p50_ci_high: number;
    profit_factor: number | null; data_range: string;
  };
  stability: {
    classification: string;
    reason: string;
    cv: number;
    consistency: number;
    positive_years: number;
    total_years: number;
    periods: { label: string; mean: number; count: number }[];
  };
  confidence: string;
  confidence_text: string;
  decision: string;
  insight: string;
  distribution_text: string[];
  stability_text: string;
  analysis_text: string;
  action: string[];
  state_dependency: {
    label: string;
    diff: number;
    direction: string;
    up_return: number;
    down_return: number;
    up_count: number;
    down_count: number;
    text: string;
  } | null;
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
  const netP50 = data?.distribution.net_p50 ?? 0;
  const ciLow = data?.distribution.p50_ci_low ?? 0;
  const ciHigh = data?.distribution.p50_ci_high ?? 0;
  const profitFactor = data?.distribution.profit_factor ?? null;

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
          className="w-9 h-9 rounded-full bg-white/10 flex items-center justify-center mr-3 active:bg-white/20 transition-colors"
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
            {/* Analysis text block */}
            <div className="rounded-2xl bg-[#1C1C1E] p-5 animate-fade-up">
              <p className="text-[#8E8E93] text-[11px] uppercase tracking-wider mb-3">統計分析</p>
              {data.analysis_text && (
                <p className="text-white/85 text-[14px] leading-relaxed mb-4">{data.analysis_text}</p>
              )}
              <div className="pt-3 border-t border-white/[0.06]">
                <div className="flex items-center gap-2 mb-1.5">
                  <span className="text-[#8E8E93] text-[11px]">可信度</span>
                  <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                    data.confidence === "high"
                      ? "bg-[#00C851]/20 text-[#00C851]"
                      : data.confidence === "medium"
                      ? "bg-[#FFB800]/20 text-[#FFB800]"
                      : "bg-[#FF4444]/20 text-[#FF4444]"
                  }`}>
                    {{ high: "高", medium: "中", low: "低" }[data.confidence] ?? data.confidence}
                  </span>
                </div>
                <p className="text-[#636366] text-[12px] leading-relaxed">{data.confidence_text}</p>
              </div>
            </div>

            {/* State card */}
            <div className="rounded-2xl bg-[#1C1C1E] p-5 animate-fade-up">
              <div className="flex justify-between items-center mb-3">
                <h2 className="text-white font-semibold">市場狀態</h2>
                <span className="text-[#8E8E93] text-xs">{data.state.actual_date}</span>
              </div>
              <div className="flex gap-2 mb-3">
                {[
                  { l: "位置", v: { High: "近高點", Mid: "中性", Low: "近低點" }[data.state.components.relative_position] ?? data.state.components.relative_position },
                  { l: "動能", v: { Strong: "強動能", Neutral: "中性", Weak: "弱動能" }[data.state.components.momentum] ?? data.state.components.momentum },
                  { l: "趨勢", v: { Bull: "多頭", Bear: "空頭" }[data.state.components.trend] ?? data.state.components.trend },
                ].map((item) => (
                  <div key={item.l} className="flex-1 rounded-xl bg-[#2C2C2E] px-2 py-2.5 text-center">
                    <p className="text-[#8E8E93] text-[10px] mb-0.5">{item.l}</p>
                    <p className="text-white text-[13px] font-semibold">{item.v}</p>
                  </div>
                ))}
              </div>
              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <p className="text-[#8E8E93] text-xs">收盤</p>
                  <p className="text-white/70 text-xs font-mono">${data.state.raw.close}</p>
                </div>
                <div>
                  <p className="text-[#8E8E93] text-xs">5日動能</p>
                  <p className={`text-xs font-mono ${data.state.raw.mom_5_pct >= 0 ? "text-[#00C851]" : "text-[#FF4444]"}`}>
                    {data.state.raw.mom_5_pct > 0 ? "+" : ""}{data.state.raw.mom_5_pct}%
                  </p>
                </div>
                <div>
                  <p className="text-[#8E8E93] text-xs">SMA50</p>
                  <p className="text-white/70 text-xs font-mono">${data.state.raw.sma_50}</p>
                </div>
              </div>
            </div>

            {/* N warning */}
            {n < 50 && (
              <div className={`rounded-2xl p-4 border animate-fade-up ${n < 30 ? "bg-[#FF4444]/10 border-[#FF4444]/30" : "bg-[#FFB800]/10 border-[#FFB800]/30"}`}>
                <p className={`text-xs font-medium ${n < 30 ? "text-[#FF4444]" : "text-[#FFB800]"}`}>
                  {n < 30
                    ? `樣本不足（N=${n}），統計結果可靠度低，僅供參考`
                    : `樣本偏少（N=${n}），建議謹慎參考`}
                </p>
              </div>
            )}

            {/* Distribution card */}
            <div className="rounded-2xl bg-[#1C1C1E] p-5 animate-fade-up">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-white font-semibold">報酬分布</h2>
                <span className="text-[#8E8E93] text-xs font-mono">{data.distribution.data_range}</span>
              </div>

              <DistributionBar p25={p25} p50={p50} p75={p75} />

              <div className="grid grid-cols-3 gap-3 mt-4">
                <StatBox label="P25" sub="較差情況" value={p25} />
                <StatBox label="P50" sub="中位報酬" value={p50} highlight ciLow={ciLow} ciHigh={ciHigh} />
                <StatBox label="P75" sub="較好情況" value={p75} />
              </div>

              <div className="mt-3 pt-3 border-t border-white/[0.06] space-y-2">
                <div className="flex justify-between">
                  <span className="text-[#8E8E93] text-xs">樣本數</span>
                  <span className={`text-sm font-mono font-bold ${n >= 100 ? "text-[#00C851]" : n >= 30 ? "text-[#FFB800]" : "text-[#FF4444]"}`}>
                    {n} 次
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-[#8E8E93] text-xs">扣費後中位數</span>
                  <span className={`text-sm font-mono font-bold ${netP50 >= 0 ? "text-[#00C851]" : "text-[#FF4444]"}`}>
                    {netP50 > 0 ? "+" : ""}{netP50}%
                  </span>
                </div>
                {profitFactor !== null && (
                  <div className="flex justify-between">
                    <span className="text-[#8E8E93] text-xs">盈虧比</span>
                    <span className={`text-sm font-mono font-bold ${profitFactor >= 1 ? "text-[#00C851]" : "text-[#FF4444]"}`}>
                      {profitFactor}
                    </span>
                  </div>
                )}
                <div className="flex justify-between">
                  <span className="text-[#8E8E93] text-xs">結果一致性</span>
                  <span className="text-sm font-mono font-bold text-white/70">
                    {data.stability.consistency}%
                    <span className="text-[#636366] text-[10px] ml-1">
                      （{data.stability.positive_years}/{data.stability.total_years} 年正報酬）
                    </span>
                  </span>
                </div>
              </div>
            </div>

            {/* Stability */}
            {data.state_dependency && (
              <div className="rounded-2xl bg-[#1C1C1E] p-5 animate-fade-up">
                <div className="flex justify-between items-center mb-3">
                  <h2 className="text-white font-semibold">市場依賴程度</h2>
                  <span className={`text-xs font-semibold px-2.5 py-1 rounded-full ${
                    data.state_dependency.label === "高度依賴"
                      ? "bg-[#FF4444]/20 text-[#FF4444]"
                      : data.state_dependency.label === "中度依賴"
                      ? "bg-[#FFB800]/20 text-[#FFB800]"
                      : "bg-[#00C851]/20 text-[#00C851]"
                  }`}>
                    {data.state_dependency.label}
                    {data.state_dependency.label !== "低依賴" && (
                      `（偏${data.state_dependency.direction}）`
                    )}
                  </span>
                </div>
                <p className="text-[#8E8E93] text-[13px] leading-relaxed mb-4">{data.state_dependency.text}</p>
                <div className="grid grid-cols-2 gap-3">
                  <div className="bg-[#2C2C2E] rounded-xl p-3 text-center">
                    <p className="text-[#8E8E93] text-[11px] mb-1">上升市場均值</p>
                    <p className={`text-[17px] font-bold font-mono ${data.state_dependency.up_return >= 0 ? "text-[#00C851]" : "text-[#FF4444]"}`}>
                      {data.state_dependency.up_return > 0 ? "+" : ""}{data.state_dependency.up_return}%
                    </p>
                    <p className="text-[#636366] text-[10px] mt-0.5">N={data.state_dependency.up_count}</p>
                  </div>
                  <div className="bg-[#2C2C2E] rounded-xl p-3 text-center">
                    <p className="text-[#8E8E93] text-[11px] mb-1">下跌市場均值</p>
                    <p className={`text-[17px] font-bold font-mono ${data.state_dependency.down_return >= 0 ? "text-[#00C851]" : "text-[#FF4444]"}`}>
                      {data.state_dependency.down_return > 0 ? "+" : ""}{data.state_dependency.down_return}%
                    </p>
                    <p className="text-[#636366] text-[10px] mt-0.5">N={data.state_dependency.down_count}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Periods */}
            {data.stability.periods?.length > 0 && (
              <div className="rounded-2xl bg-[#1C1C1E] p-5 animate-fade-up">
                <h2 className="text-white font-semibold mb-4">分期表現</h2>
                <div className="space-y-3">
                  {data.stability.periods.map((p) => {
                    return (
                      <div key={p.label} className="flex items-center justify-between">
                        <span className="text-[#8E8E93] text-[13px] w-20">{p.label}</span>
                        <span className="text-[13px] font-mono font-semibold" style={{ color: p.mean >= 0 ? "#00C851" : "#FF4444" }}>
                          {p.mean > 0 ? "+" : ""}{p.mean}%
                        </span>
                        <span className="text-[#636366] text-[11px] w-12 text-right">{p.count} 次</span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            <div className="text-center py-4 space-y-1">
              <p className="text-[#3A3A3C] text-xs">歷史統計分析 · 不預測未來 · 不構成投資建議</p>
              <p className="text-[#2A2A2A] text-[10px]">適用大型流動性股票 · 中小型股存活者偏差較大</p>
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

function StatBox({ label, sub, value, highlight, ciLow, ciHigh }: {
  label: string; sub?: string; value: number; highlight?: boolean;
  ciLow?: number; ciHigh?: number;
}) {
  const color = value > 0 ? "#00C851" : value < 0 ? "#FF4444" : "#888";
  return (
    <div className={`rounded-xl p-3 text-center ${highlight ? "bg-white/5 border border-white/10" : "bg-[#2C2C2E]"}`}>
      <p className="text-[#8E8E93] text-[11px]">{label}</p>
      {sub && <p className="text-[#636366] text-[10px] mb-1">{sub}</p>}
      <p className="font-mono font-bold text-base" style={{ color }}>
        {value > 0 ? "+" : ""}{value}%
      </p>
      {ciLow !== undefined && ciHigh !== undefined && (
        <p className="text-[#636366] text-[9px] mt-0.5 font-mono">
          {ciLow > 0 ? "+" : ""}{ciLow} ~ {ciHigh > 0 ? "+" : ""}{ciHigh}%
        </p>
      )}
    </div>
  );
}
