import { useState } from "react";
import HomePage from "./pages/HomePage";
import AnalyzePage from "./pages/AnalyzePage";
import PositionPage from "./pages/PositionPage";

export type Route =
  | { name: "home" }
  | { name: "analyze"; code: string; days: number }
  | { name: "position"; code: string; entryDate: string; entryPrice: number; currentPrice: number };

export default function App() {
  const [route, setRoute] = useState<Route>({ name: "home" });

  if (route.name === "analyze") {
    return (
      <AnalyzePage
        code={route.code}
        days={route.days}
        onBack={() => setRoute({ name: "home" })}
      />
    );
  }

  if (route.name === "position") {
    return (
      <PositionPage
        code={route.code}
        entryDate={route.entryDate}
        entryPrice={route.entryPrice}
        currentPrice={route.currentPrice}
        onBack={() => setRoute({ name: "home" })}
      />
    );
  }

  return <HomePage onNavigate={setRoute} />;
}
