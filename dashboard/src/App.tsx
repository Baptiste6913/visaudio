import { useState } from "react";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { RoleContext } from "./utils/roles";
import type { Role, StoreName } from "./types";
import Layout from "./components/Layout";
import LandingPage from "./pages/LandingPage";
import StoreDrilldownPage from "./pages/StoreDrilldownPage";
import SimulationPage from "./pages/SimulationPage";

export default function App() {
  const [role, setRole] = useState<Role>("direction");
  const [store, setStore] = useState<StoreName | null>(null);

  return (
    <RoleContext.Provider value={{ role, store, setRole, setStore }}>
      <BrowserRouter>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<LandingPage />} />
            <Route path="/store/:ville" element={<StoreDrilldownPage />} />
            <Route path="/simulation" element={<SimulationPage />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </RoleContext.Provider>
  );
}
