# P5 — Dashboard React — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a 3-page React dashboard (Direction landing, Store drill-down, Simulation "wow" page) with multi-role switching, consuming the FastAPI backend (P4) and displaying KPIs, diagnostics, and Mesa simulation results with interactive charts.

**Architecture:** Vite + React 18 + TypeScript + Tailwind CSS + Recharts. A unified `api.ts` client hides the backend origin. Custom hooks (`useKpis`, `useSimulate`) manage fetch + loading states. Pages are routed via react-router-dom. The `<RoleSwitcher>` in the header controls Direction vs Manager view.

**Tech Stack:** React 18, TypeScript 5, Vite 5, Tailwind CSS 3.4, Recharts 2.12, react-router-dom 6, shadcn/ui primitives (manual — no CLI dependency).

**Source spec:** `docs/specs/architecture-spec.md` §10 (Dashboard), §10.1-10.6.

---

## Prerequisites (one-time, before Task 1)

```bash
cd dashboard
npm install
```

Verify:

```bash
npx tsc --version   # Expected: 5.x
npx vite --version  # Expected: 5.x
```

---

## File structure produced by this plan

```
dashboard/
├── index.html                          (NEW — Vite entry point)
├── vite.config.ts                      (NEW — Vite + React plugin + proxy)
├── tsconfig.json                       (NEW — strict TS config)
├── tsconfig.node.json                  (NEW — for vite config)
├── tailwind.config.js                  (NEW — Tailwind config)
├── postcss.config.js                   (NEW — PostCSS + Tailwind)
├── src/
│   ├── main.tsx                        (NEW — React entry)
│   ├── App.tsx                         (NEW — routes + layout)
│   ├── index.css                       (NEW — Tailwind directives)
│   ├── types.ts                        (NEW — shared TypeScript types)
│   ├── utils/
│   │   ├── api.ts                      (NEW — unified API client)
│   │   ├── format.ts                   (NEW — € / % / date formatters)
│   │   └── roles.ts                    (NEW — role context)
│   ├── hooks/
│   │   ├── useKpis.ts                  (NEW — fetch + cache KPIs)
│   │   ├── useDiagnostics.ts           (NEW — fetch diagnostics)
│   │   ├── useArchetypes.ts            (NEW — fetch archetypes)
│   │   └── useSimulate.ts              (NEW — POST /simulate with loading)
│   ├── components/
│   │   ├── Layout.tsx                  (NEW — header + nav + role switcher)
│   │   ├── KpiCard.tsx                 (NEW — single KPI display card)
│   │   ├── KpiRow.tsx                  (NEW — row of KPI cards)
│   │   ├── HeroCard.tsx                (NEW — big hero number)
│   │   ├── FindingList.tsx             (NEW — diagnostic findings)
│   │   ├── RoleSwitcher.tsx            (NEW — Direction / Manager toggle)
│   │   ├── StoreSelector.tsx           (NEW — dropdown to pick a store)
│   │   └── charts/
│   │       ├── RevenueBarChart.tsx     (NEW — horizontal bar chart)
│   │       ├── MixPieChart.tsx         (NEW — gamme mix donut)
│   │       ├── CiCurveChart.tsx        (NEW — twin curves + CI band)
│   │       └── WaterfallChart.tsx      (NEW — waterfall opportunity)
│   └── pages/
│       ├── LandingPage.tsx             (NEW — Page 1 Direction)
│       ├── StoreDrilldownPage.tsx      (NEW — Page 2 Magasin)
│       └── SimulationPage.tsx          (NEW — Page 3 Wow)
```

---

# Part A — Project Scaffolding

## Task 1 — Vite + Tailwind + TypeScript setup

Bootstrap the project: config files, entry HTML, CSS with Tailwind directives, and a "Hello Visaudio" App to verify the dev server works.

**Files:**
- Create: `dashboard/index.html`
- Create: `dashboard/vite.config.ts`
- Create: `dashboard/tsconfig.json`
- Create: `dashboard/tsconfig.node.json`
- Create: `dashboard/tailwind.config.js`
- Create: `dashboard/postcss.config.js`
- Create: `dashboard/src/main.tsx`
- Create: `dashboard/src/index.css`
- Create: `dashboard/src/App.tsx`
- Create: `dashboard/src/vite-env.d.ts`

- [ ] **Step 1.1 — Create config files**

`dashboard/index.html`:
```html
<!DOCTYPE html>
<html lang="fr">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Visaudio Optique Analytics</title>
  </head>
  <body class="bg-gray-50 text-gray-900 antialiased">
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

`dashboard/vite.config.ts`:
```typescript
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8000",
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
});
```

`dashboard/tsconfig.json`:
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": false,
    "noUnusedParameters": false,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

`dashboard/tsconfig.node.json`:
```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

`dashboard/tailwind.config.js`:
```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: { 500: "#2563eb", 600: "#1d4ed8", 700: "#1e40af" },
      },
    },
  },
  plugins: [],
};
```

`dashboard/postcss.config.js`:
```javascript
export default {
  plugins: {
    tailwindcss: {},
    autoprefixer: {},
  },
};
```

`dashboard/src/vite-env.d.ts`:
```typescript
/// <reference types="vite/client" />
```

- [ ] **Step 1.2 — Create React entry + App**

`dashboard/src/index.css`:
```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

`dashboard/src/main.tsx`:
```typescript
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./index.css";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

`dashboard/src/App.tsx`:
```typescript
export default function App() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <h1 className="text-3xl font-bold text-brand-600">
        Visaudio Optique Analytics
      </h1>
    </div>
  );
}
```

- [ ] **Step 1.3 — Install deps and verify**

```bash
cd dashboard && npm install
npx vite build 2>&1 | tail -5
```

Expected: build succeeds with no errors.

- [ ] **Step 1.4 — Commit**

```bash
git add dashboard/index.html dashboard/vite.config.ts dashboard/tsconfig.json dashboard/tsconfig.node.json dashboard/tailwind.config.js dashboard/postcss.config.js dashboard/src/main.tsx dashboard/src/index.css dashboard/src/App.tsx dashboard/src/vite-env.d.ts
git commit -m "feat(dashboard): Vite + Tailwind + TS scaffold — P5 Task 1"
```

---

# Part B — Types, API Client, Utils

## Task 2 — Shared types + API client + formatters

Define TypeScript types matching the backend pydantic models, a unified `api.ts` client, formatters, and the role context.

**Files:**
- Create: `dashboard/src/types.ts`
- Create: `dashboard/src/utils/api.ts`
- Create: `dashboard/src/utils/format.ts`
- Create: `dashboard/src/utils/roles.ts`

- [ ] **Step 2.1 — Create types**

`dashboard/src/types.ts`:
```typescript
/* Shared TypeScript types — mirrors backend pydantic models */

export type ScenarioId =
  | "SC-BASE" | "SC-L2a" | "SC-L2b" | "SC-L1a" | "SC-L4a" | "SC-L5a";

export interface Trajectory {
  months: number[];
  ca_mean: number[];
  ca_lower: number[];
  ca_upper: number[];
}

export interface SimulateRequest {
  scenario_id: ScenarioId;
  params?: Record<string, unknown>;
  n_steps?: number;
  n_replications?: number;
}

export interface SimulateResponse {
  scenario_id: string;
  params: Record<string, unknown>;
  baseline: Trajectory;
  intervention: Trajectory;
  delta_ca_cumul_36m: number;
  delta_ca_ci_low: number;
  delta_ca_ci_high: number;
  n_replications: number;
  from_cache: boolean;
}

export interface ScenarioInfo {
  scenario_id: string;
  name: string;
  levier: string;
  description: string;
}

export interface KpisPayload {
  meta: { generated_at: string };
  cadrage: Record<string, unknown>;
  hero: Record<string, unknown>;
  retention: Record<string, unknown>;
  benchmark: Record<string, unknown>;
  conventionnement: Record<string, unknown>;
  signals: Record<string, unknown>;
}

export interface ArchetypesPayload {
  generated_at: string;
  n_archetypes: number;
  archetypes: Array<{
    id: number;
    label: string;
    n_clients: number;
    share_of_clients: number;
    share_of_ca: number;
    centroid: Record<string, number>;
  }>;
}

export interface DiagnosticsPayload {
  generated_at: string;
  [store: string]: unknown;
}

export interface Finding {
  rule_id: string;
  severity: string;
  title: string;
  message: string;
  recommendation?: string;
  value?: number;
  threshold?: number;
}

export interface StoreDiagnostics {
  findings: Finding[];
}

export type Role = "direction" | "manager";

export const STORE_NAMES = [
  "Avranches",
  "Carentan-les-Marais",
  "Cherbourg-en-Cotentin",
  "Coutances",
  "Rampan",
  "Yquelon",
] as const;

export type StoreName = (typeof STORE_NAMES)[number];
```

- [ ] **Step 2.2 — Create API client**

`dashboard/src/utils/api.ts`:
```typescript
/* Unified API client — spec §10.2 */

const BASE = "/api";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) throw new Error(`API ${resp.status}: ${resp.statusText}`);
  return resp.json() as Promise<T>;
}

export async function getKpis() {
  return fetchJson<import("../types").KpisPayload>("/kpis");
}

export async function getArchetypes() {
  return fetchJson<import("../types").ArchetypesPayload>("/archetypes");
}

export async function getDiagnostics() {
  return fetchJson<import("../types").DiagnosticsPayload>("/diagnostics");
}

export async function getScenarios() {
  return fetchJson<import("../types").ScenarioInfo[]>("/scenarios");
}

export async function simulate(req: import("../types").SimulateRequest) {
  return fetchJson<import("../types").SimulateResponse>("/simulate", {
    method: "POST",
    body: JSON.stringify(req),
  });
}
```

- [ ] **Step 2.3 — Create formatters**

`dashboard/src/utils/format.ts`:
```typescript
/* Number and date formatters */

const eurFmt = new Intl.NumberFormat("fr-FR", {
  style: "currency", currency: "EUR", maximumFractionDigits: 0,
});
const pctFmt = new Intl.NumberFormat("fr-FR", {
  style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1,
});
const numFmt = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });

export const fmtEur = (v: number) => eurFmt.format(v);
export const fmtPct = (v: number) => pctFmt.format(v);
export const fmtNum = (v: number) => numFmt.format(v);
export const fmtKEur = (v: number) =>
  `${numFmt.format(Math.round(v / 1000))} K€`;
```

- [ ] **Step 2.4 — Create role context**

`dashboard/src/utils/roles.ts`:
```typescript
import { createContext, useContext } from "react";
import type { Role, StoreName } from "../types";

export interface RoleState {
  role: Role;
  store: StoreName | null;
  setRole: (r: Role) => void;
  setStore: (s: StoreName | null) => void;
}

export const RoleContext = createContext<RoleState>({
  role: "direction",
  store: null,
  setRole: () => {},
  setStore: () => {},
});

export const useRole = () => useContext(RoleContext);
```

- [ ] **Step 2.5 — Verify build**

```bash
cd dashboard && npx vite build 2>&1 | tail -5
```

Expected: build succeeds.

- [ ] **Step 2.6 — Commit**

```bash
git add dashboard/src/types.ts dashboard/src/utils/
git commit -m "feat(dashboard): types + API client + formatters + role context — P5 Task 2"
```

---

## Task 3 — Data hooks

Custom React hooks wrapping the API client with loading/error states.

**Files:**
- Create: `dashboard/src/hooks/useKpis.ts`
- Create: `dashboard/src/hooks/useDiagnostics.ts`
- Create: `dashboard/src/hooks/useArchetypes.ts`
- Create: `dashboard/src/hooks/useSimulate.ts`

- [ ] **Step 3.1 — Implement hooks**

`dashboard/src/hooks/useKpis.ts`:
```typescript
import { useEffect, useState } from "react";
import type { KpisPayload } from "../types";
import { getKpis } from "../utils/api";

export function useKpis() {
  const [data, setData] = useState<KpisPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getKpis()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}
```

`dashboard/src/hooks/useDiagnostics.ts`:
```typescript
import { useEffect, useState } from "react";
import type { DiagnosticsPayload } from "../types";
import { getDiagnostics } from "../utils/api";

export function useDiagnostics() {
  const [data, setData] = useState<DiagnosticsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDiagnostics()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}
```

`dashboard/src/hooks/useArchetypes.ts`:
```typescript
import { useEffect, useState } from "react";
import type { ArchetypesPayload } from "../types";
import { getArchetypes } from "../utils/api";

export function useArchetypes() {
  const [data, setData] = useState<ArchetypesPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getArchetypes()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}
```

`dashboard/src/hooks/useSimulate.ts`:
```typescript
import { useCallback, useState } from "react";
import type { SimulateRequest, SimulateResponse } from "../types";
import { simulate } from "../utils/api";

export function useSimulate() {
  const [data, setData] = useState<SimulateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (req: SimulateRequest) => {
    setLoading(true);
    setError(null);
    try {
      const result = await simulate(req);
      setData(result);
      return result;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, run };
}
```

- [ ] **Step 3.2 — Verify build**

```bash
cd dashboard && npx vite build 2>&1 | tail -5
```

- [ ] **Step 3.3 — Commit**

```bash
git add dashboard/src/hooks/
git commit -m "feat(dashboard): data hooks (useKpis, useDiagnostics, useArchetypes, useSimulate) — P5 Task 3"
```

---

# Part C — Shared Components

## Task 4 — Layout + shared UI components

Header with nav, role switcher, KPI cards, hero card, finding list, store selector.

**Files:**
- Create: `dashboard/src/components/Layout.tsx`
- Create: `dashboard/src/components/RoleSwitcher.tsx`
- Create: `dashboard/src/components/KpiCard.tsx`
- Create: `dashboard/src/components/KpiRow.tsx`
- Create: `dashboard/src/components/HeroCard.tsx`
- Create: `dashboard/src/components/FindingList.tsx`
- Create: `dashboard/src/components/StoreSelector.tsx`

- [ ] **Step 4.1 — Implement all shared components**

Each component is a focused file. The full code for each is provided to the implementing agent.

Key components:
- `Layout.tsx`: wraps children with header (title, nav links, RoleSwitcher), renders `<Outlet />` from react-router
- `RoleSwitcher.tsx`: two buttons (Direction / Manager), uses `useRole()` context
- `KpiCard.tsx`: props `{ label, value, subtitle?, delta? }`, colored card with optional green/red delta indicator
- `KpiRow.tsx`: props `{ children }`, flex row of KPI cards
- `HeroCard.tsx`: props `{ value, label, subtitle }`, big prominent number card with gradient background
- `FindingList.tsx`: props `{ findings: Finding[] }`, list of diagnostic findings with severity badges
- `StoreSelector.tsx`: props `{ value, onChange }`, dropdown of 6 store names

- [ ] **Step 4.2 — Verify build**

- [ ] **Step 4.3 — Commit**

```bash
git add dashboard/src/components/
git commit -m "feat(dashboard): shared UI components — P5 Task 4"
```

---

## Task 5 — Chart components

Recharts wrappers for the 4 chart types used across pages.

**Files:**
- Create: `dashboard/src/components/charts/RevenueBarChart.tsx`
- Create: `dashboard/src/components/charts/MixPieChart.tsx`
- Create: `dashboard/src/components/charts/CiCurveChart.tsx`
- Create: `dashboard/src/components/charts/WaterfallChart.tsx`

- [ ] **Step 5.1 — Implement chart components**

- `RevenueBarChart`: horizontal bar chart, props `{ data: {name, value}[], label, color? }`, uses `BarChart` + `Bar` + `XAxis` + `YAxis` from recharts
- `MixPieChart`: donut chart for gamme mix, props `{ data: {name, value}[], title }`, uses `PieChart` + `Pie` + `Cell` + `Legend`
- `CiCurveChart`: twin line chart with CI shaded area, props `{ baseline: Trajectory, intervention: Trajectory, title }`, uses `LineChart` + `Line` + `Area` + `Tooltip` + `Legend`
- `WaterfallChart`: bar chart showing opportunity per segment/store, props `{ data: {name, value}[] }`, uses `BarChart` + colored bars (positive green, negative red)

- [ ] **Step 5.2 — Verify build**

- [ ] **Step 5.3 — Commit**

```bash
git add dashboard/src/components/charts/
git commit -m "feat(dashboard): Recharts chart components — P5 Task 5"
```

---

# Part D — Pages + Routing

## Task 6 — Page 1 — Landing (Direction réseau)

The main landing page showing the hero number, KPI row, and opportunity charts.

**Files:**
- Create: `dashboard/src/pages/LandingPage.tsx`

- [ ] **Step 6.1 — Implement LandingPage**

Components used: `HeroCard`, `KpiRow`, `KpiCard`, `RevenueBarChart`.
Data: `useKpis()`.

Layout:
1. `<HeroCard>` with H5 opportunité upsell
2. `<KpiRow>` with 4 cards: CA total, panier moyen, clients uniques, part PREMIUM
3. `<RevenueBarChart>` "Opportunité upsell par magasin"
4. `<RevenueBarChart>` "Opportunité upsell par segment"

All values extracted from `kpis.data.hero` and `kpis.data.cadrage`.

- [ ] **Step 6.2 — Verify build**

- [ ] **Step 6.3 — Commit**

```bash
git add dashboard/src/pages/LandingPage.tsx
git commit -m "feat(dashboard): Page 1 Landing — P5 Task 6"
```

---

## Task 7 — Page 2 — Store drill-down

Per-store detail page with KPIs, diagnostics, and tabbed charts.

**Files:**
- Create: `dashboard/src/pages/StoreDrilldownPage.tsx`

- [ ] **Step 7.1 — Implement StoreDrilldownPage**

Components: `StoreSelector`, `KpiRow`, `KpiCard`, `FindingList`, `WaterfallChart`, `MixPieChart`.
Data: `useKpis()`, `useDiagnostics()`.
Route: `/store/:ville` (ville from URL params).

Layout:
1. Header with store selector + back link
2. `<KpiRow>` with 4 store-specific KPIs (CA magasin, panier moyen magasin, clients magasin, part PREMIUM magasin) with delta vs median
3. `<WaterfallChart>` "Opportunité locale par segment"
4. `<FindingList>` from diagnostics for selected store
5. Tabs: Mix gamme | Conventionnement (each with relevant chart)

- [ ] **Step 7.2 — Verify build**

- [ ] **Step 7.3 — Commit**

```bash
git add dashboard/src/pages/StoreDrilldownPage.tsx
git commit -m "feat(dashboard): Page 2 Store drill-down — P5 Task 7"
```

---

## Task 8 — Page 3 — Simulation (page "wow")

Interactive simulation page with scenario selector, parameter sliders, and twin-curve CI chart.

**Files:**
- Create: `dashboard/src/pages/SimulationPage.tsx`

- [ ] **Step 8.1 — Implement SimulationPage**

Components: `CiCurveChart`.
Data: `useSimulate()`.

Layout:
1. Header with scenario dropdown (6 options)
2. Left panel: scenario description, parameter display, "Lancer la simulation" button
3. Right panel: `<CiCurveChart>` showing baseline vs intervention with CI bands
4. Result box: ΔCA cumulé 36 mois with CI range
5. Loading state: spinner when simulation is running
6. On mount: auto-load SC-L2a (the hero scenario)

- [ ] **Step 8.2 — Verify build**

- [ ] **Step 8.3 — Commit**

```bash
git add dashboard/src/pages/SimulationPage.tsx
git commit -m "feat(dashboard): Page 3 Simulation — P5 Task 8"
```

---

## Task 9 — App routing + role provider

Wire up react-router with all 3 pages, Layout wrapper, and RoleContext provider.

**Files:**
- Modify: `dashboard/src/App.tsx`

- [ ] **Step 9.1 — Implement routing**

`dashboard/src/App.tsx`:
```typescript
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
```

- [ ] **Step 9.2 — Verify build**

```bash
cd dashboard && npx vite build 2>&1 | tail -5
```

Expected: build succeeds with no TS errors.

- [ ] **Step 9.3 — Commit**

```bash
git add dashboard/src/App.tsx
git commit -m "feat(dashboard): App routing + role provider — P5 Task 9"
```

---

## Summary of commits

| # | Message | Files |
|---|---|---|
| 1 | `feat(dashboard): Vite + Tailwind + TS scaffold — P5 Task 1` | Config files, entry points |
| 2 | `feat(dashboard): types + API client + formatters + role context — P5 Task 2` | `types.ts`, `utils/` |
| 3 | `feat(dashboard): data hooks — P5 Task 3` | `hooks/` |
| 4 | `feat(dashboard): shared UI components — P5 Task 4` | `components/*.tsx` |
| 5 | `feat(dashboard): Recharts chart components — P5 Task 5` | `components/charts/*.tsx` |
| 6 | `feat(dashboard): Page 1 Landing — P5 Task 6` | `pages/LandingPage.tsx` |
| 7 | `feat(dashboard): Page 2 Store drill-down — P5 Task 7` | `pages/StoreDrilldownPage.tsx` |
| 8 | `feat(dashboard): Page 3 Simulation — P5 Task 8` | `pages/SimulationPage.tsx` |
| 9 | `feat(dashboard): App routing + role provider — P5 Task 9` | `App.tsx` |
