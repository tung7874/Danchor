import { useState } from "react";
import type { Route } from "../App";

const POPULAR = [
  { code: "2330", name: "台積電" },
  { code: "2317", name: "鴻海" },
  { code: "2454", name: "聯發科" },
  { code: "0050", name: "台灣50" },
  { code: "0056", name: "高股息" },
  { code: "2882", name: "國泰金" },
];

const HORIZONS = [5, 10, 20, 30];

interface Props {
  onNavigate: (r: Route) => void;
}

export default function HomePage({ onNavigate }: Props) {
  const [tab, setTab] = useState<"analyze" | "coming">("analyze");
  const [code, setCode] = useState("");
  const [days, setDays] = useState(10);

  function handleAnalyze() {
    if (!code.trim()) return;
    onNavigate({ name: "analyze", code: code.trim().toUpperCase(), days });
  }

  function handleScan() {
    if (!code.trim()) return;
    onNavigate({ name: "scan", code: code.trim().toUpperCase(), days });
  }

  return (
    <div
      className="flex flex-col min-h-dvh bg-black px-4 pb-10"
      style={{
        paddingTop: "max(20px, env(safe-area-inset-top))",
        fontFamily: "-apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif",
      }}
    >
      {/* Header */}
      <div className="mb-7">
        <p className="text-white/30 text-[11px] tracking-widest uppercase mb-1">Decision Anchor</p>
        <h1 className="text-[28px] font-bold tracking-tight text-white">決策錨點</h1>
        <p className="text-white/40 text-[13px] mt-0.5">條件報酬分布 · 歷史統計</p>
      </div>

      {/* Segmented Control */}
      <div className="flex rounded-[10px] bg-[#1C1C1E] p-[3px] mb-6 gap-[3px]">
        {([
          { key: "analyze", label: "進場驗證" },
          { key: "coming", label: "持倉評估" },
        ] as const).map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            className={`flex-1 py-[7px] rounded-[8px] text-[13px] font-medium transition-all duration-200 ${
              tab === t.key
                ? "bg-[#2C2C2E] text-white shadow-sm"
                : "text-white/40"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === "coming" ? (
        <div className="flex-1 flex flex-col items-center justify-center pb-20">
          <div className="w-16 h-16 rounded-2xl bg-[#1C1C1E] flex items-center justify-center mb-5">
            <svg width="28" height="28" fill="none" viewBox="0 0 24 24">
              <rect x="3" y="11" width="18" height="11" rx="2" stroke="white" strokeOpacity="0.3" strokeWidth="1.8" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" stroke="white" strokeOpacity="0.3" strokeWidth="1.8" strokeLinecap="round" />
            </svg>
          </div>
          <p className="text-white font-semibold text-[17px] mb-2">持倉評估</p>
          <p className="text-white/40 text-[14px] text-center leading-relaxed">
            功能開發中<br />敬請期待
          </p>
        </div>
      ) : (
        <>
          {/* Stock Input */}
          <div className="mb-4">
            <label className="text-white/40 text-[12px] mb-2 block uppercase tracking-wider">股票代碼</label>
            <input
              type="text"
              value={code}
              onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
              placeholder="例：2330"
              inputMode="numeric"
              maxLength={6}
              className="w-full bg-[#1C1C1E] rounded-[12px] px-4 py-[14px] text-white text-[22px] font-mono tracking-widest focus:ring-1 focus:ring-[#00D4FF] outline-none border border-transparent focus:border-[#00D4FF]/30 transition-all"
            />
          </div>

          {/* Popular chips */}
          <div className="flex gap-2 flex-wrap items-center mb-6">
            <span className="text-white/50 text-[12px] font-medium mr-1">熱門:</span>
            {POPULAR.map((s) => (
              <button
                key={s.code}
                onClick={() => setCode(s.code)}
                className={`px-3 py-[7px] rounded-[8px] text-[12px] font-medium transition-all duration-150 ${
                  code === s.code
                    ? "bg-[#00D4FF]/15 text-[#00D4FF] border border-[#00D4FF]/40"
                    : "bg-[#1C1C1E] text-white/40 border border-transparent"
                }`}
              >
                {s.code} {s.name}
              </button>
            ))}
          </div>

          {/* Horizon */}
          <div className="mb-7">
            <label className="text-white/40 text-[12px] mb-3 block uppercase tracking-wider">持有天數</label>
            <div className="flex gap-2">
              {HORIZONS.map((h) => (
                <button
                  key={h}
                  onClick={() => setDays(h)}
                  className={`flex-1 py-[12px] rounded-[12px] text-[14px] font-semibold transition-all duration-150 ${
                    days === h
                      ? "bg-white/15 text-white border border-white/30"
                      : "bg-[#1C1C1E] text-white/40 border border-transparent"
                  }`}
                >
                  {h}日
                </button>
              ))}
            </div>
          </div>

          {/* Primary action */}
          <button
            onClick={handleAnalyze}
            disabled={!code.trim()}
            className="w-full py-[16px] rounded-[14px] bg-white text-black font-bold text-[16px] disabled:opacity-25 active:scale-[0.98] transition-all duration-100 mb-3"
          >
            分析歷史分布
          </button>

          {/* Secondary: Edge Scanner */}
          <button
            onClick={handleScan}
            disabled={!code.trim()}
            className="w-full py-[14px] rounded-[14px] bg-[#1C1C1E] text-white/70 font-semibold text-[15px] disabled:opacity-25 active:scale-[0.98] transition-all duration-100 border border-white/[0.08]"
          >
            掃描全部狀態 Edge Scanner
          </button>
        </>
      )}

      <div className="mt-auto pt-8 text-center">
        <p className="text-white/15 text-[11px]">歷史統計分析 · 非投資建議 · 不預測未來</p>
      </div>
    </div>
  );
}
