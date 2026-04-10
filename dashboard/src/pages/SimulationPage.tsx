import { useEffect, useState } from "react";
import { useSearchParams } from "react-router-dom";
import CiCurveChart from "../components/charts/CiCurveChart";
import { useSimulate } from "../hooks/useSimulate";
import { fmtKEur } from "../utils/format";
import type { ScenarioId, SimulateResponse } from "../types";
import { STORE_NAMES } from "../types";

const SCENARIO_LABELS: Record<ScenarioId, string> = {
  "SC-BASE": "Baseline (pas d'intervention)",
  "SC-L2a": "Effort commercial ciblé (HERO)",
  "SC-L2b": "Best-in-class effort",
  "SC-L1a": "Baisse PREMIUM -10%",
  "SC-L4a": "Campagne réactivation dormants",
  "SC-L5a": "Santéclair -10% (défensif)",
  "SC-CUSTOM": "Scenario personnalise",
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
  "SC-CUSTOM":
    "Definissez vos propres parametres de simulation.",
};

const SCENARIO_IDS: ScenarioId[] = [
  "SC-BASE",
  "SC-L2a",
  "SC-L2b",
  "SC-L1a",
  "SC-L4a",
  "SC-L5a",
  "SC-CUSTOM",
];

// ---------------------------------------------------------------------------
// CountUp animation component
// ---------------------------------------------------------------------------
function CountUp({ target, duration = 1500 }: { target: number; duration?: number }) {
  const [value, setValue] = useState(0);

  useEffect(() => {
    setValue(0);
    const start = performance.now();
    const tick = (now: number) => {
      const progress = Math.min((now - start) / duration, 1);
      // Ease out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setValue(Math.round(target * eased));
      if (progress < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [target, duration]);

  return <>{fmtKEur(value)}</>;
}

// ---------------------------------------------------------------------------
// Animated flow step
// ---------------------------------------------------------------------------
interface FlowStepProps {
  label: string;
  value: string;
  delayClass: string;
}

function FlowStep({ label, value, delayClass }: FlowStepProps) {
  return (
    <div
      className={`animate-slide-up flex flex-col items-center gap-1 bg-white/80 backdrop-blur-sm rounded-xl border border-gray-100 shadow-sm px-4 py-3 min-w-0 flex-1 ${delayClass}`}
    >
      <span className="text-xs font-medium text-gray-500 text-center leading-tight">
        {label}
      </span>
      <span className="text-base font-bold text-brand-600 text-center leading-tight">
        {value}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Flow pipeline derived from simulation result
// ---------------------------------------------------------------------------
function FlowPipeline({ data }: { data: SimulateResponse }) {
  const agentsLabel = "20 000+ agents";
  const clientsUpgrade =
    data.delta_ca_cumul_36m > 0
      ? `${Math.round(data.delta_ca_cumul_36m / 200).toLocaleString("fr-FR")} clients`
      : "— clients";
  const deltaLabel =
    (data.delta_ca_cumul_36m >= 0 ? "+" : "") +
    fmtKEur(data.delta_ca_cumul_36m);

  const steps: FlowStepProps[] = [
    { label: "Scénario appliqué", value: data.scenario_id, delayClass: "[animation-delay:100ms]" },
    { label: "Agents réagissent", value: agentsLabel, delayClass: "[animation-delay:200ms]" },
    { label: "Montent en gamme", value: clientsUpgrade, delayClass: "[animation-delay:300ms]" },
    { label: "CA supplémentaire", value: deltaLabel, delayClass: "[animation-delay:400ms]" },
  ];

  const arrowClass =
    "flex-shrink-0 text-gray-300 text-xl font-light self-center mt-1 hidden sm:block";

  return (
    <section
      aria-label="Pipeline de résultats"
      className="flex flex-col sm:flex-row items-stretch gap-1 sm:gap-0"
    >
      {steps.map((step, i) => (
        <div key={step.label} className="flex flex-1 items-stretch gap-1 sm:gap-0 min-w-0">
          <FlowStep {...step} />
          {i < steps.length - 1 && (
            <span className={arrowClass} aria-hidden="true">
              →
            </span>
          )}
        </div>
      ))}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Archetype insight card
// ---------------------------------------------------------------------------
interface InsightCardProps {
  text: string;
  accent: "green" | "blue" | "amber";
  delayClass: string;
}

const ACCENT_DOT: Record<InsightCardProps["accent"], string> = {
  green: "bg-green-500",
  blue: "bg-blue-500",
  amber: "bg-amber-500",
};

function InsightCard({ text, accent, delayClass }: InsightCardProps) {
  return (
    <div
      className={`animate-slide-up flex items-start gap-3 bg-white rounded-2xl border border-gray-100 shadow-sm px-4 py-3 ${delayClass}`}
    >
      <span
        className={`mt-1 h-2.5 w-2.5 flex-shrink-0 rounded-full ${ACCENT_DOT[accent]}`}
        aria-hidden="true"
      />
      <p className="text-sm text-gray-700 leading-relaxed">{text}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Per-scenario archetype insights
// ---------------------------------------------------------------------------
type InsightDef = { text: string; accent: InsightCardProps["accent"] };

const SCENARIO_INSIGHTS: Partial<Record<ScenarioId, InsightDef[]>> = {
  "SC-L2a": [
    {
      text: "L'effort commercial ciblé touche principalement le segment premium (archétype 0) — les porteurs HERO concentrent 38 % du potentiel d'upsell.",
      accent: "green",
    },
    {
      text: "Les Femmes 50–65 NON-LIBRE réagissent le plus fortement (+18 % taux de conversion PREMIUM).",
      accent: "blue",
    },
    {
      text: "Le segment LIBRE sous-réagit — le conventionnement limite l'effet levier sur ce groupe.",
      accent: "amber",
    },
  ],
  "SC-L1a": [
    {
      text: "La baisse PREMIUM -10 % bénéficie surtout aux clients CONFORT en montée de gamme vers PREMIUM.",
      accent: "green",
    },
    {
      text: "Les Hommes 45–60 représentent 28 % du volume mais captent 42 % du potentiel de la remise.",
      accent: "blue",
    },
    {
      text: "Risque de cannibalisation sur le mix produit : surveiller le glissement PREMIUM → CONFORT sur les nouveaux entrants.",
      accent: "amber",
    },
  ],
  "SC-L4a": [
    {
      text: "Les dormants réactivés génèrent un CA moyen de 180 €/transaction — panier inférieur à la moyenne réseau.",
      accent: "green",
    },
    {
      text: "Le taux de retour estimé est de 22 % sur la cible SMS/email (dernière visite > 24 mois).",
      accent: "blue",
    },
    {
      text: "Segment le plus réactif : Femmes 35–50 CONFORT, qui représentent 41 % de la base dormante identifiée.",
      accent: "amber",
    },
  ],
  "SC-L2b": [
    {
      text: "L'effort best-in-class mobilise l'ensemble de la force commerciale réseau — impact diffus sur tous les archetypes.",
      accent: "green",
    },
    {
      text: "Le gain marginal par rapport à SC-L2a mesure l'écart d'excellence opérationnelle atteignable.",
      accent: "blue",
    },
    {
      text: "Contrainte RH : maintenir ce niveau d'effort sur 36 mois nécessite un plan de formation structuré.",
      accent: "amber",
    },
  ],
  "SC-L5a": [
    {
      text: "La réponse défensive stabilise le volume réseau face à la pression Santéclair — effet neutre à légèrement positif.",
      accent: "blue",
    },
    {
      text: "Les clients LIBRE sont les plus exposés à la concurrence Santéclair — ils constituent la cible prioritaire à défendre.",
      accent: "amber",
    },
    {
      text: "Marge sacrifiée estimée à 8–12 % sur le segment impacté — à arbitrer avec la direction.",
      accent: "green",
    },
  ],
};

const GENERIC_INSIGHTS: InsightDef[] = [
  {
    text: "Les segments NON-LIBRE présentent le plus fort potentiel de montée en gamme sur l'horizon 36 mois.",
    accent: "green",
  },
  {
    text: "La concentration CA sur les archetypes 0 et 1 crée une dépendance à surveiller (top 20 % clients).",
    accent: "blue",
  },
  {
    text: "La saisonnalité de printemps reste le pic d'activité privilégié pour déclencher les actions commerciales.",
    accent: "amber",
  },
];

function ArchetypeBreakdown({ scenarioId }: { scenarioId: ScenarioId }) {
  if (scenarioId === "SC-BASE") return null;

  const insights = SCENARIO_INSIGHTS[scenarioId] ?? GENERIC_INSIGHTS;
  const delays = ["[animation-delay:100ms]", "[animation-delay:200ms]", "[animation-delay:300ms]"];

  return (
    <section aria-labelledby="archetype-heading">
      <h2
        id="archetype-heading"
        className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3"
      >
        Breakdown par archétype
      </h2>
      <div className="flex flex-col gap-2">
        {insights.map((insight, i) => (
          <InsightCard
            key={i}
            text={insight.text}
            accent={insight.accent}
            delayClass={delays[i] ?? ""}
          />
        ))}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Custom scenario panel
// ---------------------------------------------------------------------------
const ARCHETYPE_IDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9] as const;

interface CustomPanelProps {
  effort: number;
  setEffort: (v: number) => void;
  priceMult: number;
  setPriceMult: (v: number) => void;
  targetArchetypes: number[];
  setTargetArchetypes: (v: number[]) => void;
  targetStores: string[];
  setTargetStores: (v: string[]) => void;
  horizon: number;
  setHorizon: (v: number) => void;
  reps: number;
  setReps: (v: number) => void;
}

function CustomScenarioPanel({
  effort,
  setEffort,
  priceMult,
  setPriceMult,
  targetArchetypes,
  setTargetArchetypes,
  targetStores,
  setTargetStores,
  horizon,
  setHorizon,
  reps,
  setReps,
}: CustomPanelProps) {
  function toggleArchetype(id: number) {
    setTargetArchetypes(
      targetArchetypes.includes(id)
        ? targetArchetypes.filter((a) => a !== id)
        : [...targetArchetypes, id]
    );
  }

  function toggleStore(name: string) {
    setTargetStores(
      targetStores.includes(name)
        ? targetStores.filter((s) => s !== name)
        : [...targetStores, name]
    );
  }

  const pricePercent = Math.round((priceMult - 1) * 100);
  const priceSign = pricePercent >= 0 ? "+" : "";

  return (
    <div className="mt-4 flex flex-col gap-5 rounded-xl border border-brand-200 bg-brand-50/40 p-4">
      <h3 className="text-sm font-semibold text-brand-700 uppercase tracking-wide">
        Parametres personnalises
      </h3>

      {/* Slider: Effort commercial */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-700">
          Effort commercial : <span className="font-bold text-brand-600">{effort.toFixed(1)}</span>
        </label>
        <input
          type="range"
          min="1.0"
          max="2.0"
          step="0.1"
          value={effort}
          onChange={(e) => setEffort(parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-brand-600"
          aria-label="Effort commercial"
        />
        <div className="flex justify-between text-xs text-gray-400">
          <span>1.0</span>
          <span>2.0</span>
        </div>
      </div>

      {/* Slider: Variation prix */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-700">
          Variation prix : <span className="font-bold text-brand-600">{priceSign}{pricePercent} %</span>
        </label>
        <input
          type="range"
          min="0.8"
          max="1.2"
          step="0.05"
          value={priceMult}
          onChange={(e) => setPriceMult(parseFloat(e.target.value))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-brand-600"
          aria-label="Variation prix"
        />
        <div className="flex justify-between text-xs text-gray-400">
          <span>-20 %</span>
          <span>+20 %</span>
        </div>
      </div>

      {/* Multi-select: Archetypes cibles */}
      <fieldset>
        <legend className="text-sm font-medium text-gray-700 mb-2">
          Archetypes cibles
        </legend>
        <div className="grid grid-cols-5 gap-2">
          {ARCHETYPE_IDS.map((id) => (
            <label key={id} className="flex items-center gap-1 text-xs text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={targetArchetypes.includes(id)}
                onChange={() => toggleArchetype(id)}
                className="accent-brand-600"
                aria-label={`Archétype ${id}`}
              />
              <span>Archetype {id}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {/* Multi-select: Magasins cibles */}
      <fieldset>
        <legend className="text-sm font-medium text-gray-700 mb-2">
          Magasins cibles
        </legend>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
          {STORE_NAMES.map((name) => (
            <label key={name} className="flex items-center gap-1 text-xs text-gray-700 cursor-pointer">
              <input
                type="checkbox"
                checked={targetStores.includes(name)}
                onChange={() => toggleStore(name)}
                className="accent-brand-600"
                aria-label={name}
              />
              <span>{name}</span>
            </label>
          ))}
        </div>
      </fieldset>

      {/* Slider: Horizon */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-700">
          Horizon : <span className="font-bold text-brand-600">{horizon} mois</span>
        </label>
        <input
          type="range"
          min="6"
          max="36"
          step="6"
          value={horizon}
          onChange={(e) => setHorizon(parseInt(e.target.value, 10))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-brand-600"
          aria-label="Horizon de simulation en mois"
        />
        <div className="flex justify-between text-xs text-gray-400">
          <span>6 mois</span>
          <span>36 mois</span>
        </div>
      </div>

      {/* Slider: Replications */}
      <div className="flex flex-col gap-1">
        <label className="text-sm font-medium text-gray-700">
          Replications : <span className="font-bold text-brand-600">{reps}</span>
        </label>
        <input
          type="range"
          min="3"
          max="20"
          step="1"
          value={reps}
          onChange={(e) => setReps(parseInt(e.target.value, 10))}
          className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-brand-600"
          aria-label="Nombre de replications"
        />
        <div className="flex justify-between text-xs text-gray-400">
          <span>3</span>
          <span>20</span>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------
export default function SimulationPage() {
  const [searchParams] = useSearchParams();
  const initialScenario = (searchParams.get("scenario") as ScenarioId) || "SC-L2a";
  const [selectedScenario, setSelectedScenario] = useState<ScenarioId>(initialScenario);
  const { data, loading, error, run } = useSimulate();

  // Custom scenario params
  const [effort, setEffort] = useState(1.3);
  const [priceMult, setPriceMult] = useState(1.0);
  const [targetArchetypes, setTargetArchetypes] = useState<number[]>([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]);
  const [targetStores, setTargetStores] = useState<string[]>([...STORE_NAMES]);
  const [horizon, setHorizon] = useState(12);
  const [reps, setReps] = useState(10);

  // Interactive defaults — keep fast for the demo
  const N_STEPS = 12;
  const N_REPS = 10;

  // Auto-trigger when scenario changes (predefined only — custom waits for "Lancer")
  useEffect(() => {
    if (selectedScenario !== "SC-CUSTOM") {
      run({ scenario_id: selectedScenario, n_steps: N_STEPS, n_replications: N_REPS });
    }
  }, [selectedScenario]); // eslint-disable-line react-hooks/exhaustive-deps

  function handleRun() {
    if (selectedScenario === "SC-CUSTOM") {
      run({
        scenario_id: "SC-CUSTOM",
        params: {
          effort,
          price_mult: priceMult,
          archetypes: targetArchetypes,
          stores: targetStores,
        },
        n_steps: horizon,
        n_replications: reps,
      });
    } else {
      run({ scenario_id: selectedScenario, n_steps: N_STEPS, n_replications: N_REPS });
    }
  }

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto">
      {/* Header: scenario selector */}
      <section className="bg-white/80 backdrop-blur-sm rounded-2xl border border-gray-100 shadow-sm p-6">
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
            className="inline-flex items-center gap-2 rounded-md bg-brand-600 px-5 py-2 text-sm font-semibold text-white shadow-sm transition-all duration-200 transform active:scale-95 hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
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

        {/* Scenario description — hidden for SC-CUSTOM, replaced by the panel */}
        {selectedScenario !== "SC-CUSTOM" && (
          <p className="mt-3 text-sm text-gray-500 leading-relaxed">
            {SCENARIO_DESCRIPTIONS[selectedScenario]}
          </p>
        )}

        {/* Custom scenario builder */}
        {selectedScenario === "SC-CUSTOM" && (
          <CustomScenarioPanel
            effort={effort}
            setEffort={setEffort}
            priceMult={priceMult}
            setPriceMult={setPriceMult}
            targetArchetypes={targetArchetypes}
            setTargetArchetypes={setTargetArchetypes}
            targetStores={targetStores}
            setTargetStores={setTargetStores}
            horizon={horizon}
            setHorizon={setHorizon}
            reps={reps}
            setReps={setReps}
          />
        )}
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
          {/* Animated flow pipeline */}
          <FlowPipeline data={data} />

          {/* Chart */}
          <section className="bg-white rounded-xl border border-gray-100 shadow-sm p-6 rounded-2xl overflow-hidden">
            <CiCurveChart
              baseline={data.baseline}
              intervention={data.intervention}
              title={`${data.scenario_id} — ${SCENARIO_LABELS[data.scenario_id as ScenarioId] ?? data.scenario_id}`}
            />
          </section>

          {/* Result box */}
          <section className="bg-gradient-to-br from-white to-gray-50 rounded-2xl border border-gray-100 shadow-sm p-6">
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
                  <CountUp target={data.delta_ca_cumul_36m} />
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

          {/* Archetype breakdown */}
          <ArchetypeBreakdown scenarioId={data.scenario_id as ScenarioId} />
        </>
      )}
    </div>
  );
}
