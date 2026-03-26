import { useEffect, useState } from "react";
import { fetchPosition } from "../lib/api";

type PositionResult = {
  unrealized_pnl_pct: number;
  days_held: number;
  entry_state: { state: string };
  sample_count: number;
  path_analysis: {
    total: number;
    reversal: { count: number; probability: number; avg_return: number; median_return: number };
    continued_loss: { count: number; probability: number; avg_return: number };
  };
  expected_values: { days: number; expected_value: number }[];
  note?: string;
};

interface Props {
  code: string;
  entryDate: string;
  entryPrice: number;
  currentPrice: number;
  onBack: () => void;
}

export default function PositionPage({ code, entryDate, entryPrice, currentPrice, onBack }: Props) {
  const [data, setData] = useState<PositionResult | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    setLoading(true);
    fetchPosition({ asset_code: code, entry_date: entryDate, entry_price: entryPrice, current_price: currentPrice })
      .then(setData)
      .catch((e: Error) => setError(e.message))
      .finally(() => setLoading(false));
  }, [code, entryDate, entryPrice, currentPrice]);

  const pnl = data?.unrealized_pnl_pct ?? ((currentPrice - entryPrice) / entryPrice * 100);
  const pnlColor = pnl >= 0 ? "#00C851" : "#FF4444";

  return (
    <div
      className="flex flex-col min-h-dvh bg-[#0D0D0D]"
      style={{ paddingTop: "env(safe-area-inset-top)" }}
    >
      {/* Navbar */}
      <div className="flex items-center px-4 py-3 border-b border-[#1A1A1A]">
        <button onClick={onBack} className="w-9 h-9 flex items-center justify-center rounded-full bg-[#1A1A1A] mr-3">
          <svg width="18" height="18" fill="none" stroke="white" strokeWidth="2.5">
            <path d="M11 4l-7 5 7 5" />
          </svg>
        </button>
        <div>
          <p className="text-white font-semibold">{code} 持倉評估</p>
          <p className="text-[#555] text-xs">條件概率分析</p>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-5 space-y-4">
        {/* PnL card */}
        <div className="rounded-2xl bg-[#1A1A1A] p-5">
          <p className="text-[#555] text-xs mb-2 uppercase tracking-wide">未實現損益</p>
          <div className="flex items-end gap-3 mb-3">
            <p className="text-4xl font-bold font-mono" style={{ color: pnlColor }}>
              {pnl > 0 ? "+" : ""}{pnl.toFixed(2)}%
            </p>
            {data && <p className="text-[#555] text-sm mb-1">持有 {data.days_held} 天</p>}
          </div>
          <div className="flex gap-5">
            <div><p className="text-[#444] text-xs">進場</p><p className="text-white text-sm font-mono">${entryPrice}</p></div>
            <div><p className="text-[#444] text-xs">現在</p><p className="text-white text-sm font-mono">${currentPrice}</p></div>
            <div><p className="text-[#444] text-xs">進場日</p><p className="text-white text-sm">{entryDate}</p></div>
          </div>
        </div>

        {loading && (
          <div className="space-y-4">
            {[140, 180].map((h, i) => <div key={i} className="skeleton" style={{ height: h }} />)}
          </div>
        )}

        {error && (
          <div className="rounded-2xl bg-[#FF4444]/10 border border-[#FF4444]/30 p-5 text-center">
            <p className="text-[#FF4444] text-sm">{error}</p>
          </div>
        )}

        {data && !loading && (
          <>
            {data.note && (
              <div className="rounded-2xl bg-[#FFB800]/10 border border-[#FFB800]/30 p-4">
                <p className="text-[#FFB800] text-sm">{data.note}</p>
              </div>
            )}

            {data.path_analysis?.reversal && (
              <div className="rounded-2xl bg-[#1A1A1A] p-5 animate-fade-up">
                <div className="flex justify-between items-center mb-4">
                  <h2 className="text-white font-semibold">路徑概率</h2>
                  <span className="text-[#555] text-xs">N={data.sample_count}</span>
                </div>
                <PathBar label="反轉回正" prob={data.path_analysis.reversal.probability} avg={data.path_analysis.reversal.avg_return} color="#00C851" />
                <div className="my-3" />
                <PathBar label="持續虧損" prob={data.path_analysis.continued_loss.probability} avg={data.path_analysis.continued_loss.avg_return} color="#FF4444" />
                <div className="mt-4 pt-3 border-t border-[#222]">
                  <p className="text-[#666] text-xs">
                    反轉中位數：
                    <span className="text-[#00C851] font-mono ml-1">+{data.path_analysis.reversal.median_return}%</span>
                  </p>
                </div>
              </div>
            )}

            {data.expected_values?.length > 0 && (
              <div className="rounded-2xl bg-[#1A1A1A] p-5 animate-fade-up">
                <h2 className="text-white font-semibold mb-4">期望值預估</h2>
                <div className="space-y-2">
                  {data.expected_values.map((ev) => (
                    <div key={ev.days} className="flex justify-between py-2 border-b border-[#1E1E1E] last:border-0">
                      <span className="text-[#888] text-sm">T+{ev.days} 天</span>
                      <span className="font-mono font-semibold text-sm" style={{ color: ev.expected_value >= 0 ? "#00C851" : "#FF4444" }}>
                        {ev.expected_value > 0 ? "+" : ""}{ev.expected_value}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="text-center py-4">
              <p className="text-[#2A2A2A] text-xs">歷史統計分析 · 不構成投資建議</p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function PathBar({ label, prob, avg, color }: { label: string; prob: number; avg: number; color: string }) {
  return (
    <div>
      <div className="flex justify-between mb-1.5">
        <span className="text-[#AAA] text-sm">{label}</span>
        <span className="font-mono text-sm font-bold" style={{ color }}>{prob}%</span>
      </div>
      <div className="h-2 rounded-full bg-[#2A2A2A] overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${prob}%`, background: color }} />
      </div>
      <p className="text-[#444] text-xs mt-1">
        平均報酬：<span className="font-mono" style={{ color }}>{avg > 0 ? "+" : ""}{avg}%</span>
      </p>
    </div>
  );
}
