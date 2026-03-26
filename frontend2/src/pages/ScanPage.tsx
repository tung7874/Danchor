import { useEffect, useState } from "react";
import { fetchScan } from "../lib/api";

type StateResult = {
  state: string;
  label: string;
  score: number;
  quality: "A" | "B" | "C" | "D";
  P25: number;
  P50: number;
  P75: number;
  N: number;
  win_rate: number;
};

const GRADE_STYLE: Record<string, { bg: string; text: string; label: string }> = {
  A: { bg: "bg-[#FFD60A]/15", text: "text-[#FFD60A]", label: "A" },
  B: { bg: "bg-[#00D4FF]/15", text: "text-[#00D4FF]", label: "B" },
  C: { bg: "bg-white/10", text: "text-white/60", label: "C" },
  D: { bg: "bg-[#FF4444]/10", text: "text-[#FF4444]", label: "D" },
};

interface Props {
  code: string;
  days: number;
  onBack: () => void;
}

export default function ScanPage({ code, days, onBack }: Props) {
  const [data, setData] = useState<StateResult[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    fetchScan({ asset_code: code, holding_horizon_days: days })
      .then((r) => setData(r.states))
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [code, days]);

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
          <p className="text-white font-semibold text-[17px]">{code} · Edge Scanner</p>
          <p className="text-white/40 text-[12px]">{days} 日持有 · 全狀態掃描</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-5">
        {loading && (
          <div className="space-y-3">
            {Array.from({ length: 8 }).map((_, i) => (
              <div key={i} className="skeleton rounded-[14px]" style={{ height: 80 }} />
            ))}
          </div>
        )}

        {error && (
          <div className="rounded-[14px] bg-[#FF4444]/10 border border-[#FF4444]/20 p-5 text-center mt-4">
            <p className="text-[#FF4444] text-[14px] font-medium mb-1">掃描失敗</p>
            <p className="text-white/40 text-[12px]">{error}</p>
          </div>
        )}

        {data && !loading && (
          <>
            <p className="text-white/30 text-[12px] mb-4 uppercase tracking-wide">
              找到 {data.length} 個有效狀態 · 按 Edge Score 排序
            </p>

            <div className="space-y-2">
              {data.map((s, i) => {
                const g = GRADE_STYLE[s.quality];
                const p50Color = s.P50 > 0 ? "#00C851" : "#FF4444";
                return (
                  <div
                    key={s.state}
                    className="bg-[#1C1C1E] rounded-[14px] px-4 py-4 flex items-center gap-4"
                  >
                    {/* Rank */}
                    <span className="text-white/20 text-[13px] font-mono w-5 shrink-0 text-center">
                      {i + 1}
                    </span>

                    {/* Grade */}
                    <span className={`w-8 h-8 rounded-[8px] flex items-center justify-center text-[13px] font-bold shrink-0 ${g.bg} ${g.text}`}>
                      {g.label}
                    </span>

                    {/* Label */}
                    <div className="flex-1 min-w-0">
                      <p className="text-white text-[13px] font-medium leading-snug">{s.label}</p>
                      <p className="text-white/30 text-[11px] mt-0.5">
                        勝率 {s.win_rate}% · N={s.N}
                      </p>
                    </div>

                    {/* P50 */}
                    <div className="text-right shrink-0">
                      <p
                        className="text-[17px] font-bold font-mono"
                        style={{ color: p50Color }}
                      >
                        {s.P50 > 0 ? "+" : ""}{s.P50}%
                      </p>
                      <p className="text-white/25 text-[10px] font-mono">
                        {s.P25 > 0 ? "+" : ""}{s.P25} / {s.P75 > 0 ? "+" : ""}{s.P75}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>

            <div className="mt-6 bg-[#1C1C1E] rounded-[14px] px-4 py-4 space-y-2">
              <p className="text-white/40 text-[12px] font-semibold uppercase tracking-wide">評級說明</p>
              {[
                { g: "A", desc: "P25 > 0 且 P50 > 1.5% · 穩定正期望" },
                { g: "B", desc: "P50 > 0.8% 且勝率 > 55% · 有效 Edge" },
                { g: "C", desc: "P50 > 0 · 弱正期望" },
                { g: "D", desc: "P50 ≤ 0 · 無明顯優勢" },
              ].map(({ g, desc }) => {
                const gs = GRADE_STYLE[g];
                return (
                  <div key={g} className="flex items-center gap-3">
                    <span className={`w-6 h-6 rounded-[6px] flex items-center justify-center text-[11px] font-bold ${gs.bg} ${gs.text}`}>{g}</span>
                    <p className="text-white/40 text-[12px]">{desc}</p>
                  </div>
                );
              })}
            </div>

            <p className="text-white/15 text-[11px] text-center mt-6 mb-2">
              歷史統計分析 · 非投資建議 · 不預測未來
            </p>
          </>
        )}
      </div>
    </div>
  );
}
