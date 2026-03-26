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
  const [tab, setTab] = useState<"part1" | "part2">("part1");
  const [code, setCode] = useState("");
  const [days, setDays] = useState(10);

  // Part 2
  const [entryDate, setEntryDate] = useState("");
  const [entryPrice, setEntryPrice] = useState("");
  const [currentPrice, setCurrentPrice] = useState("");

  const pnl =
    entryPrice && currentPrice
      ? ((Number(currentPrice) - Number(entryPrice)) / Number(entryPrice)) * 100
      : null;

  function handleAnalyze() {
    if (!code.trim()) return;
    onNavigate({ name: "analyze", code: code.trim().toUpperCase(), days });
  }

  function handlePosition() {
    if (!code.trim() || !entryDate || !entryPrice || !currentPrice) return;
    onNavigate({
      name: "position",
      code: code.trim().toUpperCase(),
      entryDate,
      entryPrice: Number(entryPrice),
      currentPrice: Number(currentPrice),
    });
  }

  return (
    <div
      className="flex flex-col min-h-dvh bg-[#0D0D0D] px-4 pb-8"
      style={{ paddingTop: "max(24px, env(safe-area-inset-top))" }}
    >
      {/* Header */}
      <div className="mb-8">
        <p className="text-[#555] text-xs tracking-widest uppercase mb-1">Decision Anchor</p>
        <h1 className="text-2xl font-bold tracking-tight">決策錨點</h1>
        <p className="text-[#555] text-sm mt-1">條件報酬分布 · 歷史統計評估</p>
      </div>

      {/* Tab */}
      <div className="flex rounded-xl bg-[#1A1A1A] p-1 mb-5">
        {(["part1", "part2"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all ${
              tab === t ? "bg-[#00D4FF] text-black" : "text-[#666]"
            }`}
          >
            {t === "part1" ? "進場驗證" : "持倉評估"}
          </button>
        ))}
      </div>

      {/* Code Input */}
      <div className="mb-4">
        <label className="text-xs text-[#555] mb-2 block tracking-wide uppercase">股票代碼</label>
        <input
          type="text"
          value={code}
          onChange={(e) => setCode(e.target.value.replace(/\D/g, ""))}
          placeholder="例：2330"
          inputMode="numeric"
          maxLength={6}
          className="w-full bg-[#1A1A1A] border border-[#2A2A2A] rounded-xl px-4 py-4 text-white text-xl font-mono tracking-widest focus:border-[#00D4FF] outline-none"
        />
      </div>

      {/* Popular chips */}
      <div className="flex gap-2 flex-wrap mb-5">
        {POPULAR.map((s) => (
          <button
            key={s.code}
            onClick={() => setCode(s.code)}
            className={`px-3 py-1.5 rounded-lg text-xs border transition-all ${
              code === s.code
                ? "border-[#00D4FF] text-[#00D4FF] bg-[#00D4FF]/10"
                : "border-[#2A2A2A] text-[#777]"
            }`}
          >
            {s.code} {s.name}
          </button>
        ))}
      </div>

      {/* Part 1 */}
      {tab === "part1" && (
        <>
          <div className="mb-6">
            <label className="text-xs text-[#555] mb-3 block uppercase tracking-wide">持有天數</label>
            <div className="flex gap-2">
              {HORIZONS.map((h) => (
                <button
                  key={h}
                  onClick={() => setDays(h)}
                  className={`flex-1 py-3 rounded-xl text-sm font-semibold border transition-all ${
                    days === h
                      ? "border-[#00D4FF] text-[#00D4FF] bg-[#00D4FF]/10"
                      : "border-[#2A2A2A] text-[#666]"
                  }`}
                >
                  {h}日
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={handleAnalyze}
            disabled={!code.trim()}
            className="w-full py-4 rounded-2xl bg-[#00D4FF] text-black font-bold text-base disabled:opacity-30 active:scale-95 transition-all"
          >
            分析歷史分布
          </button>
        </>
      )}

      {/* Part 2 */}
      {tab === "part2" && (
        <>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label className="text-xs text-[#555] mb-2 block">進場日期</label>
              <input
                type="date"
                value={entryDate}
                onChange={(e) => setEntryDate(e.target.value)}
                className="w-full bg-[#1A1A1A] border border-[#2A2A2A] rounded-xl px-3 py-3 text-white text-sm focus:border-[#00D4FF] outline-none"
              />
            </div>
            <div>
              <label className="text-xs text-[#555] mb-2 block">進場價格</label>
              <input
                type="number"
                value={entryPrice}
                onChange={(e) => setEntryPrice(e.target.value)}
                placeholder="0.00"
                inputMode="decimal"
                className="w-full bg-[#1A1A1A] border border-[#2A2A2A] rounded-xl px-3 py-3 text-white text-sm font-mono focus:border-[#00D4FF] outline-none"
              />
            </div>
          </div>

          <div className="mb-5">
            <label className="text-xs text-[#555] mb-2 block">目前價格</label>
            <input
              type="number"
              value={currentPrice}
              onChange={(e) => setCurrentPrice(e.target.value)}
              placeholder="0.00"
              inputMode="decimal"
              className="w-full bg-[#1A1A1A] border border-[#2A2A2A] rounded-xl px-4 py-4 text-white text-xl font-mono focus:border-[#00D4FF] outline-none"
            />
            {pnl !== null && (
              <p className={`text-xs mt-2 font-mono ${pnl >= 0 ? "text-[#00C851]" : "text-[#FF4444]"}`}>
                {pnl > 0 ? "+" : ""}{pnl.toFixed(2)}% 未實現
              </p>
            )}
          </div>

          <button
            onClick={handlePosition}
            disabled={!code.trim() || !entryDate || !entryPrice || !currentPrice}
            className="w-full py-4 rounded-2xl bg-[#00D4FF] text-black font-bold text-base disabled:opacity-30 active:scale-95 transition-all mb-3"
          >
            評估持倉路徑
          </button>

          <div className="px-4 py-3 rounded-xl bg-[#1A1A1A] border border-[#2A2A2A]">
            <p className="text-[#555] text-xs text-center">持倉評估付費功能 · 目前免費體驗</p>
          </div>
        </>
      )}

      <div className="mt-auto pt-8 text-center">
        <p className="text-[#333] text-xs">歷史統計分析 · 非投資建議 · 不預測未來</p>
      </div>
    </div>
  );
}
