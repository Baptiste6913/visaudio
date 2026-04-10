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
  id: string;
  severity: string;
  message: string;
  recommendation?: string;
}

export interface UploadResult {
  status: string;
  rows_imported: number;
  rows_rejected: number;
  clients: number;
  archetypes: number;
  message: string;
}

/** A recommended action with pre-filled simulation params. */
export interface Recommendation {
  title: string;
  description: string;
  scenario_id: ScenarioId;
  gain_estimate?: string;
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
