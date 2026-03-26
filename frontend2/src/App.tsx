import { useState } from "react";
import HomePage from "./pages/HomePage";
import AnalyzePage from "./pages/AnalyzePage";
import ScanPage from "./pages/ScanPage";

export type Route =
  | { name: "home" }
  | { name: "analyze"; code: string; days: number }
  | { name: "scan"; code: string; days: number };

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

  if (route.name === "scan") {
    return (
      <ScanPage
        code={route.code}
        days={route.days}
        onBack={() => setRoute({ name: "home" })}
      />
    );
  }

  return <HomePage onNavigate={setRoute} />;
}
