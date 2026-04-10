import { useMemo } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
} from "recharts";
import { useKpis } from "../hooks/useKpis";
import { useDiagnostics } from "../hooks/useDiagnostics";
import StoreSelector from "../components/StoreSelector";
import KpiRow from "../components/KpiRow";
import KpiCard from "../components/KpiCard";
import FindingList from "../components/FindingList";
import MixPieChart from "../components/charts/MixPieChart";
import RadarStoreChart from "../components/charts/RadarStoreChart";
import type { Finding, StoreDiagnostics, ScenarioId } from "../types";
import { STORE_NAMES } from "../types";
import { fmtEur, fmtKEur, fmtPct } from "../utils/format";

// ─── helpers ─────────────────────────────────────────────────────────────────

function networkAverage(record: Record<string, number>): number {
  const vals = Object.values(record);
  if (vals.length === 0) return 0;
  return vals.reduce((a, b) => a + b, 0) / vals.length;
}

function networkMax(record: Record<string, number>): number {
  const vals = Object.values(record);
  if (vals.length === 0) return 1;
  return Math.max(...vals);
}

// ─── Recommendation card ──────────────────────────────────────────────────────

interface RecommendationCardProps {
  title: string;
  description: string;
  gainLabel: string;
  scenarioId: ScenarioId;
  onSimulate: (scenarioId: ScenarioId) => void;
}

function RecommendationCard({
  title,
  description,
  gainLabel,
  scenarioId,
  onSimulate,
}: RecommendationCardProps) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm border-l-4 border-l-brand-600 p-4 flex flex-col gap-2">
      <p className="font-semibold text-gray-800 text-sm">{title}</p>
      <p className="text-sm text-gray-600">{description}</p>
      <p className="text-xs text-gray-500 italic">{gainLabel}</p>
      <div className="mt-1">
        <button
          type="button"
          onClick={() => onSimulate(scenarioId)}
          className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg bg-brand-600 text-white text-xs font-medium transition-colors hover:bg-brand-700 focus:outline-none focus-visible:ring-2 focus-visible:ring-brand-600 focus-visible:ring-offset-1"
        >
          Simuler l&apos;impact →
        </button>
      </div>
    </div>
  );
}

// ─── Seasonality chart tooltip ────────────────────────────────────────────────

function SeasonTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean;
  payload?: Array<{ value: number }>;
  label?: string;
}) {
  if (!active || !payload || payload.length === 0) return null;
  return (
    <div className="bg-white border border-gray-200 rounded shadow-sm px-3 py-1.5 text-xs">
      <p className="font-medium text-gray-800">{label}</p>
      <p className="text-gray-600">
        Indice :{" "}
        {typeof payload[0].value === "number"
          ? payload[0].value.toFixed(2)
          : "—"}
      </p>
    </div>
  );
}

// ─── Page ─────────────────────────────────────────────────────────────────────

export default function StoreDrilldownPage() {
  const { ville } = useParams<{ ville: string }>();
  const navigate = useNavigate();

  const currentVille = ville ?? STORE_NAMES[0];

  const { data: kpisData, loading: kpisLoading, error: kpisError } = useKpis();
  const {
    data: diagData,
    loading: diagLoading,
    error: diagError,
  } = useDiagnostics();

  // ── Raw KPI maps ─────────────────────────────────────────────────────────────
  const caParMagasin = useMemo(
    () =>
      kpisData?.cadrage?.par_magasin as Record<string, number> | undefined,
    [kpisData]
  );

  const panierMoyenParMagasin = useMemo(
    () =>
      kpisData?.cadrage?.panier_moyen_par_magasin as
        | Record<string, number>
        | undefined,
    [kpisData]
  );

  const h5ParMagasin = useMemo(
    () =>
      kpisData?.hero?.opportunite_par_magasin as
        | Record<string, number>
        | undefined,
    [kpisData]
  );

  const mixGammeParMagasin = useMemo(
    () =>
      kpisData?.hero?.mix_gamme_par_magasin as
        | Record<string, Record<string, number>>
        | undefined,
    [kpisData]
  );

  const partPremiumPlusParMagasin = useMemo(
    () =>
      kpisData?.hero?.mix_premium_plus_par_magasin as
        | Record<string, number>
        | undefined,
    [kpisData]
  );

  const indexSaisonnalite = useMemo(
    () =>
      kpisData?.diagnostic_signals?.index_saisonnalite as
        | Record<string, Record<string, number>>
        | undefined,
    [kpisData]
  );

  const ratioMonturePar = useMemo(
    () =>
      kpisData?.diagnostic_signals?.ratio_monture_verre_eur as
        | Record<string, number>
        | undefined,
    [kpisData]
  );

  // ── Per-store values ─────────────────────────────────────────────────────────
  const caStore = caParMagasin?.[currentVille];
  const panierStore = panierMoyenParMagasin?.[currentVille];
  const h5Store = h5ParMagasin?.[currentVille];
  const partPremiumStore = partPremiumPlusParMagasin?.[currentVille];

  // ── Network averages ─────────────────────────────────────────────────────────
  const caNetworkAvg = useMemo(
    () => (caParMagasin ? networkAverage(caParMagasin) : undefined),
    [caParMagasin]
  );

  const panierNetworkAvg = useMemo(
    () =>
      panierMoyenParMagasin ? networkAverage(panierMoyenParMagasin) : undefined,
    [panierMoyenParMagasin]
  );

  const partPremiumNetworkAvg = useMemo(
    () =>
      partPremiumPlusParMagasin
        ? networkAverage(partPremiumPlusParMagasin)
        : undefined,
    [partPremiumPlusParMagasin]
  );

  // ── Radar chart data ─────────────────────────────────────────────────────────
  const radarData = useMemo(() => {
    if (
      !caParMagasin ||
      !panierMoyenParMagasin ||
      !partPremiumPlusParMagasin
    ) {
      return [];
    }

    const caMax = networkMax(caParMagasin);
    const panierMax = networkMax(panierMoyenParMagasin);
    const premiumMax = networkMax(partPremiumPlusParMagasin);
    const ratioMax = ratioMonturePar ? networkMax(ratioMonturePar) : 1;

    // Normalize to 0–100
    const normalize = (v: number | undefined, max: number): number =>
      max > 0 && v !== undefined ? Math.min(100, (v / max) * 100) : 0;

    // Per-store values
    const caStoreVal = caParMagasin[currentVille];
    const panierStoreVal = panierMoyenParMagasin[currentVille];
    const premiumStoreVal = partPremiumPlusParMagasin[currentVille];
    const ratioStoreVal = ratioMonturePar?.[currentVille];

    // Network averages (already normalized implicitly via avg/max)
    const caNetAvg = networkAverage(caParMagasin);
    const panierNetAvg = networkAverage(panierMoyenParMagasin);
    const premiumNetAvg = networkAverage(partPremiumPlusParMagasin);
    const ratioNetAvg = ratioMonturePar ? networkAverage(ratioMonturePar) : 0;

    return [
      {
        dimension: "Performance CA",
        store: normalize(caStoreVal, caMax),
        network: normalize(caNetAvg, caMax),
      },
      {
        dimension: "Panier moyen",
        store: normalize(panierStoreVal, panierMax),
        network: normalize(panierNetAvg, panierMax),
      },
      {
        dimension: "Mix PREMIUM+",
        store: normalize(premiumStoreVal, premiumMax),
        network: normalize(premiumNetAvg, premiumMax),
      },
      {
        dimension: "Fidélisation",
        // Fallback: use 70 as default fidelisation index when no dormants data
        store: 70,
        network: 70,
      },
      {
        dimension: "Diversification",
        store: normalize(ratioStoreVal, ratioMax),
        network: normalize(ratioNetAvg, ratioMax),
      },
    ];
  }, [
    caParMagasin,
    panierMoyenParMagasin,
    partPremiumPlusParMagasin,
    ratioMonturePar,
    currentVille,
  ]);

  // ── Gamme pie data ────────────────────────────────────────────────────────────
  const gammeData = useMemo<{ name: string; value: number }[]>(() => {
    const mix = mixGammeParMagasin?.[currentVille];
    if (!mix) return [];
    return Object.entries(mix).map(([name, value]) => ({ name, value }));
  }, [mixGammeParMagasin, currentVille]);

  // ── Seasonality line data ─────────────────────────────────────────────────────
  const seasonData = useMemo<{ month: string; value: number }[]>(() => {
    const storeSeason = indexSaisonnalite?.[currentVille];
    if (!storeSeason) return [];
    return Object.entries(storeSeason).map(([month, value]) => ({
      month,
      value,
    }));
  }, [indexSaisonnalite, currentVille]);

  // ── Diagnostics findings ──────────────────────────────────────────────────────
  const findings = useMemo<Finding[]>(() => {
    if (!diagData) return [];
    const storeEntry = diagData[currentVille];
    if (
      !storeEntry ||
      typeof storeEntry !== "object" ||
      !("findings" in storeEntry)
    ) {
      return [];
    }
    return (storeEntry as StoreDiagnostics).findings ?? [];
  }, [diagData, currentVille]);

  // ── Recommendations ───────────────────────────────────────────────────────────
  interface RecommendationItem {
    title: string;
    description: string;
    gainLabel: string;
    scenarioId: ScenarioId;
  }

  const recommendations = useMemo<RecommendationItem[]>(() => {
    const items: RecommendationItem[] = [];
    const gainStr = h5Store !== undefined ? `+${fmtKEur(h5Store)}/an` : "+15K€/an";

    // 1. Below-average PREMIUM+ share
    if (
      partPremiumStore !== undefined &&
      partPremiumNetworkAvg !== undefined &&
      partPremiumStore < partPremiumNetworkAvg
    ) {
      items.push({
        title: "Effort commercial PREMIUM+",
        description:
          "Ce magasin est en dessous de la moyenne réseau sur le mix PREMIUM+. Une montée en gamme ciblée peut améliorer le panier moyen et la marge.",
        gainLabel: `Gain potentiel : ${gainStr}`,
        scenarioId: "SC-L2a",
      });
    }

    // 2. CROSS_SELL finding present
    const hasCrossSell = findings.some(
      (f) => f.id?.includes("CROSS_SELL") || f.message?.toLowerCase().includes("cross")
    );
    if (hasCrossSell) {
      items.push({
        title: "Programme cross-sell monture",
        description:
          "Des opportunités de vente croisée monture/verre ont été détectées. Un programme d'accompagnement vendeur peut convertir ces profils.",
        gainLabel: `Gain potentiel : ${gainStr}`,
        scenarioId: "SC-L2b",
      });
    }

    // 3. Always: réactivation dormants
    items.push({
      title: "Campagne réactivation dormants",
      description:
        "Relancer les clients sans achat depuis 18+ mois via une campagne ciblée (SMS, email) augmente le taux de ré-achat et la LTV.",
      gainLabel: `Gain potentiel : ${gainStr}`,
      scenarioId: "SC-L4a",
    });

    return items;
  }, [partPremiumStore, partPremiumNetworkAvg, findings, h5Store]);

  // ── Navigate to simulation ────────────────────────────────────────────────────
  function handleSimulate(scenarioId: ScenarioId) {
    navigate(`/simulation?scenario=${scenarioId}`);
  }

  // ── Loading / error states ───────────────────────────────────────────────────
  const isLoading = kpisLoading || diagLoading;
  const error = kpisError ?? diagError;

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-gray-400">
        Chargement des données...
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center h-64 text-sm text-red-500">
        Erreur : {error}
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8">
      {/* ── 1. Header ────────────────────────────────────────────────────────── */}
      <div className="flex flex-wrap items-center gap-4">
        <Link
          to="/"
          className="text-sm text-brand-600 hover:underline font-medium"
        >
          &larr; Retour
        </Link>
        <StoreSelector
          value={currentVille}
          onChange={(v) => navigate(`/store/${v}`)}
        />
        <h1 className="text-2xl font-bold text-gray-900">{currentVille}</h1>
      </div>

      {/* ── 2. KPI comparison row ────────────────────────────────────────────── */}
      <KpiRow>
        <KpiCard
          label="CA magasin"
          value={caStore !== undefined ? fmtKEur(caStore) : "—"}
          subtitle={
            caNetworkAvg !== undefined
              ? `vs moyenne réseau : ${fmtKEur(caNetworkAvg)}`
              : "vs moyenne réseau"
          }
          delta={
            caStore !== undefined && caNetworkAvg !== undefined
              ? Math.round((caStore - caNetworkAvg) / 1000)
              : undefined
          }
        />
        <KpiCard
          label="Panier moyen"
          value={panierStore !== undefined ? fmtEur(panierStore) : "—"}
          subtitle={
            panierNetworkAvg !== undefined
              ? `vs moyenne réseau : ${fmtEur(panierNetworkAvg)}`
              : "vs moyenne réseau"
          }
          delta={
            panierStore !== undefined && panierNetworkAvg !== undefined
              ? Math.round(panierStore - panierNetworkAvg)
              : undefined
          }
        />
        <KpiCard
          label="Part PREMIUM+"
          value={
            partPremiumStore !== undefined ? fmtPct(partPremiumStore) : "—"
          }
          subtitle={
            partPremiumNetworkAvg !== undefined
              ? `vs moyenne réseau : ${fmtPct(partPremiumNetworkAvg)}`
              : "vs moyenne réseau"
          }
          delta={
            partPremiumStore !== undefined &&
            partPremiumNetworkAvg !== undefined
              ? Math.round(
                  (partPremiumStore - partPremiumNetworkAvg) * 1000
                ) / 10
              : undefined
          }
        />
        <KpiCard
          label="Opportunité upsell"
          value={h5Store !== undefined ? fmtKEur(h5Store) : "—"}
          subtitle="vs moyenne réseau"
          delta={
            h5Store !== undefined && caNetworkAvg !== undefined
              ? Math.round(
                  (h5Store -
                    (h5ParMagasin ? networkAverage(h5ParMagasin) : 0)) /
                    1000
                )
              : undefined
          }
        />
      </KpiRow>

      {/* ── 3. Radar + Donut grid ────────────────────────────────────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section
          aria-labelledby="radar-heading"
          className="bg-white border border-gray-100 rounded-xl shadow-sm p-5"
        >
          <h2
            id="radar-heading"
            className="text-lg font-semibold text-gray-800 mb-4"
          >
            Performance multidimensionnelle
          </h2>
          <RadarStoreChart storeData={radarData} />
        </section>

        <section
          aria-labelledby="mix-heading"
          className="bg-white border border-gray-100 rounded-xl shadow-sm p-5"
        >
          <h2
            id="mix-heading"
            className="text-lg font-semibold text-gray-800 mb-4"
          >
            Mix gamme — {currentVille}
          </h2>
          <MixPieChart
            data={gammeData}
            title={`Répartition des gammes — ${currentVille}`}
          />
        </section>
      </div>

      {/* ── 4. Seasonality line chart ────────────────────────────────────────── */}
      <section
        aria-labelledby="season-heading"
        className="bg-white border border-gray-100 rounded-xl shadow-sm p-5"
      >
        <h2
          id="season-heading"
          className="text-lg font-semibold text-gray-800 mb-4"
        >
          Saisonnalité mensuelle
        </h2>
        {seasonData.length > 0 ? (
          <ResponsiveContainer width="100%" height={220}>
            <LineChart
              data={seasonData}
              margin={{ top: 4, right: 16, left: 0, bottom: 4 }}
              aria-label="Indice de saisonnalité mensuelle"
            >
              <CartesianGrid stroke="#f3f4f6" vertical={false} />
              <XAxis
                dataKey="month"
                tick={{ fontSize: 11, fill: "#6b7280" }}
                axisLine={false}
                tickLine={false}
              />
              <YAxis
                tick={{ fontSize: 11, fill: "#6b7280" }}
                axisLine={false}
                tickLine={false}
                domain={["auto", "auto"]}
                width={36}
              />
              <Tooltip content={<SeasonTooltip />} />
              <Line
                type="monotone"
                dataKey="value"
                stroke="#1d4ed8"
                strokeWidth={2}
                dot={{ r: 3, fill: "#1d4ed8", strokeWidth: 0 }}
                activeDot={{ r: 5 }}
                name="Indice saisonnalité"
              />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <p className="text-sm text-gray-400 italic h-[220px] flex items-center justify-center">
            Données de saisonnalité non disponibles pour ce magasin.
          </p>
        )}
      </section>

      {/* ── 5. Diagnostics section ───────────────────────────────────────────── */}
      <section aria-labelledby="findings-heading">
        <h2
          id="findings-heading"
          className="text-lg font-semibold text-gray-800 mb-3"
        >
          Diagnostic automatique
        </h2>
        <FindingList findings={findings} />
      </section>

      {/* ── 6. Recommandations IA ────────────────────────────────────────────── */}
      <section aria-labelledby="reco-heading">
        <h2
          id="reco-heading"
          className="text-lg font-semibold text-gray-800 mb-3 flex items-center gap-2"
        >
          <span aria-hidden="true">✦</span> Recommandations
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {recommendations.map((reco) => (
            <RecommendationCard
              key={reco.scenarioId}
              title={reco.title}
              description={reco.description}
              gainLabel={reco.gainLabel}
              scenarioId={reco.scenarioId}
              onSimulate={handleSimulate}
            />
          ))}
        </div>
      </section>
    </div>
  );
}
