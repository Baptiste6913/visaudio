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
  const headers: Record<string, string> = {};
  if (init?.body) headers["Content-Type"] = "application/json";

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 30_000);

  try {
    const resp = await fetch(`${BASE}${path}`, {
      ...init,
      headers: { ...headers, ...(init?.headers as Record<string, string>) },
      signal: controller.signal,
    });
    if (!resp.ok) throw new Error(`API ${resp.status}: ${resp.statusText}`);
    return (await resp.json()) as T;
  } catch (e) {
    if (e instanceof DOMException && e.name === "AbortError") {
      throw new Error(
        `Timeout sur ${path} — le backend (localhost:8000) ne répond pas. ` +
          `Lancez : python -m src.cli serve --no-prewarm`
      );
    }
    throw e;
  } finally {
    clearTimeout(timeout);
  }
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
