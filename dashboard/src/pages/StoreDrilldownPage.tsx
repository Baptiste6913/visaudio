import { useMemo } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { useKpis } from "../hooks/useKpis";
import { useDiagnostics } from "../hooks/useDiagnostics";
import StoreSelector from "../components/StoreSelector";
import KpiRow from "../components/KpiRow";
import KpiCard from "../components/KpiCard";
import FindingList from "../components/FindingList";
import WaterfallChart from "../components/charts/WaterfallChart";
import MixPieChart from "../components/charts/MixPieChart";
import type { Finding, StoreDiagnostics } from "../types";
import { STORE_NAMES } from "../types";
import { fmtEur, fmtKEur, fmtPct } from "../utils/format";

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

  // --- KPI extraction ---
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
      kpisData?.hero?.opportunite_par_magasin as Record<string, number> | undefined,
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

  // --- Per-store values ---
  const caStore = caParMagasin?.[currentVille];
  const panierStore = panierMoyenParMagasin?.[currentVille];
  const h5Store = h5ParMagasin?.[currentVille];
  const partPremiumStore = partPremiumPlusParMagasin?.[currentVille];

  // --- Network medians for deltas ---
  const caMedian = useMemo(() => {
    if (!caParMagasin) return undefined;
    const vals = Object.values(caParMagasin).sort((a, b) => a - b);
    if (vals.length === 0) return undefined;
    const mid = Math.floor(vals.length / 2);
    return vals.length % 2 === 0
      ? (vals[mid - 1] + vals[mid]) / 2
      : vals[mid];
  }, [caParMagasin]);

  const panierMedian = useMemo(() => {
    if (!panierMoyenParMagasin) return undefined;
    const vals = Object.values(panierMoyenParMagasin).sort((a, b) => a - b);
    if (vals.length === 0) return undefined;
    const mid = Math.floor(vals.length / 2);
    return vals.length % 2 === 0
      ? (vals[mid - 1] + vals[mid]) / 2
      : vals[mid];
  }, [panierMoyenParMagasin]);

  const partPremiumMedian = useMemo(() => {
    if (!partPremiumPlusParMagasin) return undefined;
    const vals = Object.values(partPremiumPlusParMagasin).sort(
      (a, b) => a - b
    );
    if (vals.length === 0) return undefined;
    const mid = Math.floor(vals.length / 2);
    return vals.length % 2 === 0
      ? (vals[mid - 1] + vals[mid]) / 2
      : vals[mid];
  }, [partPremiumPlusParMagasin]);

  // --- Gamme mix pie data ---
  const gammeData = useMemo<{ name: string; value: number }[]>(() => {
    const mix = mixGammeParMagasin?.[currentVille];
    if (!mix) return [];
    return Object.entries(mix).map(([name, value]) => ({ name, value }));
  }, [mixGammeParMagasin, currentVille]);

  // --- Waterfall: opportunity by segment from h5 across all stores ---
  const waterfallData = useMemo<{ name: string; value: number }[]>(() => {
    if (!h5ParMagasin) return [];
    return Object.entries(h5ParMagasin).map(([name, value]) => ({
      name,
      value,
    }));
  }, [h5ParMagasin]);

  // --- Diagnostics findings for this store ---
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

  // --- Loading / error states ---
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
    <div className="flex flex-col gap-6">
      {/* Header */}
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
        <h1 className="text-xl font-bold text-gray-900">{currentVille}</h1>
      </div>

      {/* KPI row */}
      <KpiRow>
        <KpiCard
          label="CA magasin"
          value={caStore !== undefined ? fmtKEur(caStore) : "—"}
          subtitle={
            caMedian !== undefined
              ? `Médiane réseau : ${fmtKEur(caMedian)}`
              : undefined
          }
          delta={
            caStore !== undefined && caMedian !== undefined
              ? Math.round((caStore - caMedian) / 1000)
              : undefined
          }
        />
        <KpiCard
          label="Panier moyen magasin"
          value={panierStore !== undefined ? fmtEur(panierStore) : "—"}
          subtitle={
            panierMedian !== undefined
              ? `Médiane réseau : ${fmtEur(panierMedian)}`
              : undefined
          }
          delta={
            panierStore !== undefined && panierMedian !== undefined
              ? Math.round(panierStore - panierMedian)
              : undefined
          }
        />
        <KpiCard
          label="Opportunité upsell magasin"
          value={h5Store !== undefined ? fmtKEur(h5Store) : "—"}
          subtitle="Potentiel upsell H5"
        />
        <KpiCard
          label="Part PREMIUM+"
          value={partPremiumStore !== undefined ? fmtPct(partPremiumStore) : "—"}
          subtitle={
            partPremiumMedian !== undefined
              ? `Médiane réseau : ${fmtPct(partPremiumMedian)}`
              : undefined
          }
          delta={
            partPremiumStore !== undefined && partPremiumMedian !== undefined
              ? Math.round((partPremiumStore - partPremiumMedian) * 1000) / 10
              : undefined
          }
        />
      </KpiRow>

      {/* Diagnostics findings */}
      <section aria-labelledby="findings-heading">
        <h2
          id="findings-heading"
          className="text-base font-semibold text-gray-800 mb-3"
        >
          Diagnostics — {currentVille}
        </h2>
        <FindingList findings={findings} />
      </section>

      {/* Charts grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <section
          aria-labelledby="mix-heading"
          className="bg-white border border-gray-100 rounded-lg shadow-sm p-4"
        >
          <h2
            id="mix-heading"
            className="text-sm font-semibold text-gray-700 mb-3"
          >
            Mix gamme — {currentVille}
          </h2>
          <MixPieChart
            data={gammeData}
            title={`Répartition des gammes — ${currentVille}`}
          />
        </section>

        <section
          aria-labelledby="waterfall-heading"
          className="bg-white border border-gray-100 rounded-lg shadow-sm p-4"
        >
          <h2
            id="waterfall-heading"
            className="text-sm font-semibold text-gray-700 mb-3"
          >
            Opportunité upsell par magasin
          </h2>
          <WaterfallChart data={waterfallData} />
        </section>
      </div>
    </div>
  );
}
