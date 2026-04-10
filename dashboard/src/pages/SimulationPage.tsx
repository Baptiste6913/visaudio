import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import CiCurveChart from "../components/charts/CiCurveChart";
import { useSimulate } from "../hooks/useSimulate";
import { fmtKEur } from "../utils/format";
import type { ScenarioId } from "../types";

const SCENARIO_LABELS: Record<ScenarioId, string> = {
  "SC-BASE": "Baseline (pas d'intervention)",
  "SC-L2a": "Effort commercial ciblé (HERO)",
  "SC-L2b": "Best-in-class effort",
  "SC-L1a": "Baisse PREMIUM -10%",
  "SC-L4a": "Campagne réactivation dormants",
  "SC-L5a": "Santéclair -10% (défensif)",
};

const SCENARIO_DESCRIPTIONS: Record<ScenarioId, string> = {
  "SC-BASE":
    "Trajectoire de référence sans aucune action commerciale. Sert d'ancrage pour mesurer l'impact des leviers.",
  "SC-L2a":
    "Activation ciblée des clients HERO identifiés par l'analyse archétype — upsell verre PREMIUM+ sur le top 20 % porteurs.",
  "SC-L2b":
    "Effort commercial maximal aligné sur les pratiques best-in-class du réseau. Borne haute de l'ambition.",
  "SC-L1a":
    "Réduction de 10 % du tarif PREMIUM pour évaluer l'élasticité-prix et l'impact sur le mix produit.",
  "SC-L4a":
    "Campagne de réactivation SMS/email auprès des clients dormants (dernière visite > 24 mois).",
  "SC-L5a":
    "Réponse défensive à une baisse tarifaire Santéclair : réduction de 10 % pour maintenir le volume réseau.",
};

const SCENARIO_IDS: ScenarioId[] = [
  "SC-BASE",
  "SC-L2a",
  "SC-L2b",
  "SC-L1a",
  "SC-L4a",
  "SC-L5a",
];

export default function SimulationPage() {
  const [searchParams] = useSearchParams();
  const initialScenario = (searchParams.get("scenario") as ScenarioId) || "SC-L2a";
  const [selectedScenario, setSelectedScenario] = useState<ScenarioId>(initialScenario);
  const { data, loading, error, run } = useSimulate();

  // Interactive defaults — keep fast for the demo
  const N_STEPS = 12;
  const N_REPS = 3;

  // Auto-trigger the scenario from URL params (or SC-L2a) on mount
  useEffect(() => {
    run({ scenario_id: initialScenario, n_steps: N_STEPS, n_replications: N_REPS });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  function handleRun() {
    run({ scenario_id: selectedScenario, n_steps: N_STEPS, n_replications: N_REPS });
  }

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto">
      {/* Header: scenario selector */}
      <section className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-4">
          Simulation de scénarios
        </h1>

        <div className="flex flex-col sm:flex-row sm:items-end gap-4">
          <div className="flex flex-col gap-1 flex-1">
            <label
              htmlFor="scenario-select"
              className="text-sm font-medium text-gray-700"
            >
              Scénario
            </label>
            <select
              id="scenario-select"
              value={selectedScenario}
              onChange={(e) => setSelectedScenario(e.target.value as ScenarioId)}
              className="rounded-md border border-gray-300 bg-white px-3 py-2 text-sm text-gray-900 shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/30"
            >
              {SCENARIO_IDS.map((id) => (
                <option key={id} value={id}>
                  {id} — {SCENARIO_LABELS[id]}
                </option>
              ))}
            </select>
          </div>

          <button
            type="button"
            onClick={handleRun}
            disabled={loading}
            className="inline-flex items-center gap-2 rounded-md bg-brand-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
          >
            {loading ? (
              <>
                <span
                  className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white border-t-transparent"
                  aria-hidden="true"
                />
                Simulation en cours...
              </>
            ) : (
              "Lancer la simulation"
            )}
          </button>
        </div>

        {/* Scenario description */}
        <p className="mt-3 text-sm text-gray-500 leading-relaxed">
          {SCENARIO_DESCRIPTIONS[selectedScenario]}
        </p>
      </section>

      {/* Error state */}
      {error && (
        <div
          role="alert"
          className="rounded-md border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700"
        >
          Erreur : {error}
        </div>
      )}

      {/* Loading overlay (first load — no data yet) */}
      {loading && !data && (
        <div className="flex items-center justify-center min-h-[400px]">
          <div className="flex flex-col items-center gap-3 text-gray-500">
            <span
              className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-brand-600"
              aria-hidden="true"
            />
            <span className="text-sm">Simulation en cours...</span>
          </div>
        </div>
      )}

      {/* Chart + results */}
      {data && (
        <>
          <section className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
            <CiCurveChart
              baseline={data.baseline}
              intervention={data.intervention}
              title={`${data.scenario_id} — ${SCENARIO_LABELS[data.scenario_id as ScenarioId] ?? data.scenario_id}`}
            />
          </section>

          {/* Result box */}
          <section className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex flex-col gap-1">
                <span className="text-sm font-medium text-gray-500 uppercase tracking-wide">
                  ΔCA cumulé 36 mois
                </span>
                <span
                  className={[
                    "text-4xl font-extrabold leading-tight",
                    data.delta_ca_cumul_36m >= 0
                      ? "text-green-600"
                      : "text-red-600",
                  ].join(" ")}
                >
                  {data.delta_ca_cumul_36m >= 0 ? "+" : ""}
                  {fmtKEur(data.delta_ca_cumul_36m)}
                </span>
                <span className="text-sm text-gray-400">
                  IC 90 % : [{data.delta_ca_ci_low >= 0 ? "+" : ""}
                  {fmtKEur(data.delta_ca_ci_low)} —{" "}
                  {data.delta_ca_ci_high >= 0 ? "+" : ""}
                  {fmtKEur(data.delta_ca_ci_high)}]
                </span>
              </div>

              <div className="flex items-center gap-3">
                <span
                  className={[
                    "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold",
                    data.from_cache
                      ? "bg-gray-100 text-gray-600"
                      : "bg-brand-50 text-brand-700 border border-brand-200",
                  ].join(" ")}
                >
                  {data.from_cache ? "depuis le cache" : "calculé"}
                </span>
                <span className="text-xs text-gray-400">
                  {data.n_replications} réplications
                </span>
              </div>
            </div>
          </section>
        </>
      )}
    </div>
  );
}
