/* Unified API client — spec §10.2 */

import type {
  KpisPayload,
  ArchetypesPayload,
  DiagnosticsPayload,
  ScenarioInfo,
  SimulateRequest,
  SimulateResponse,
} from "../types";

const BASE = "/api";

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) throw new Error(`API ${resp.status}: ${resp.statusText}`);
  return resp.json() as Promise<T>;
}

export const getKpis = () => fetchJson<KpisPayload>("/kpis");
export const getArchetypes = () => fetchJson<ArchetypesPayload>("/archetypes");
export const getDiagnostics = () => fetchJson<DiagnosticsPayload>("/diagnostics");
export const getScenarios = () => fetchJson<ScenarioInfo[]>("/scenarios");

export const simulate = (req: SimulateRequest) =>
  fetchJson<SimulateResponse>("/simulate", {
    method: "POST",
    body: JSON.stringify(req),
  });
