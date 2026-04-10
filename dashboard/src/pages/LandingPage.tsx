import { useMemo } from "react";
import { Link } from "react-router-dom";
import HeroCard from "../components/HeroCard";
import KpiRow from "../components/KpiRow";
import KpiCard from "../components/KpiCard";
import RevenueBarChart from "../components/charts/RevenueBarChart";
import { useKpis } from "../hooks/useKpis";
import { fmtEur, fmtKEur, fmtNum, fmtPct } from "../utils/format";

function recordToChartData(
  rec: Record<string, unknown>
): { name: string; value: number }[] {
  return Object.entries(rec).map(([name, value]) => ({
    name,
    value: value as number,
  }));
}

interface StoreCardProps {
  name: string;
  ca: number;
  panierMoyen: number;
  opportunite: number;
}

function StoreCard({ name, ca, panierMoyen, opportunite }: StoreCardProps) {
  return (
    <Link
      to={`/store/${encodeURIComponent(name)}`}
      className="group block bg-white rounded-xl border border-gray-100 shadow-sm p-4 transition-all duration-200 hover:shadow-md hover:border-brand-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-600"
    >
      <p className="text-sm font-semibold text-gray-800 truncate group-hover:text-brand-600 transition-colors">
        {name}
      </p>
      <div className="mt-3 flex flex-col gap-1.5">
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">CA</span>
          <span className="text-sm font-bold text-gray-900">{fmtKEur(ca)}</span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">Panier moyen</span>
          <span className="text-sm font-medium text-gray-700">
            {fmtEur(panierMoyen)}
          </span>
        </div>
        <div className="flex items-center justify-between">
          <span className="text-xs text-gray-400">Opportunité upsell</span>
          <span className="text-sm font-medium text-green-600">
            {fmtKEur(opportunite)}
          </span>
        </div>
      </div>
    </Link>
  );
}

function SectionSeparator() {
  return <hr className="border-gray-100" />;
}

export default function LandingPage() {
  const { data, loading, error } = useKpis();

  const magasinData = useMemo(() => {
    if (!data) return [];
    const rec = data.hero.opportunite_par_magasin as
      | Record<string, number>
      | undefined;
    return rec ? recordToChartData(rec) : [];
  }, [data]);

  const segmentData = useMemo(() => {
    if (!data) return [];
    const list = data.hero.opportunite_par_segment as
      | { segment: string; opportunite: number }[]
      | undefined;
    return list
      ? list.map((s) => ({ name: `Segment ${s.segment}`, value: s.opportunite }))
      : [];
  }, [data]);

  const storeCards = useMemo(() => {
    if (!data) return [];
    const caMap = data.cadrage.par_magasin as
      | Record<string, number>
      | undefined;
    const panierMap = data.cadrage.panier_moyen_par_magasin as
      | Record<string, number>
      | undefined;
    const oppMap = data.hero.opportunite_par_magasin as
      | Record<string, number>
      | undefined;

    if (!caMap) return [];

    return Object.keys(caMap).map((name) => ({
      name,
      ca: caMap[name] ?? 0,
      panierMoyen: panierMap?.[name] ?? 0,
      opportunite: oppMap?.[name] ?? 0,
    }));
  }, [data]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-gray-500 text-sm animate-pulse">Chargement...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-red-500 text-sm">
          {error ?? "Impossible de charger les données."}
        </p>
      </div>
    );
  }

  const opportuniteUpsell = data.hero.opportunite_upsell_annuelle as number;
  const caTotal = data.cadrage.ca_total as number;
  const panierMoyen = data.cadrage.panier_moyen as number;
  const clientsUniques = data.cadrage.clients_uniques as number;

  const mixPremium = data.hero.mix_premium_plus_par_magasin as
    | Record<string, number>
    | undefined;
  const partPremiumPlus = mixPremium
    ? Object.values(mixPremium).reduce((a, b) => a + b, 0) /
      Math.max(Object.keys(mixPremium).length, 1)
    : 0;

  return (
    <main className="flex flex-col gap-8 p-6 max-w-5xl mx-auto">
      {/* Hero section */}
      <section>
        <HeroCard
          value={fmtEur(opportuniteUpsell)}
          label="Opportunité upsell annuelle"
          subtitle="Écart au top-quartile par segment × volume"
        />
        <p className="mt-3 text-sm text-gray-500">
          Vue consolidée du réseau — 6 magasins en Normandie
        </p>
      </section>

      <SectionSeparator />

      {/* KPI row */}
      <section>
        <KpiRow>
          <KpiCard
            label="CA total réseau"
            value={fmtEur(caTotal)}
          />
          <KpiCard
            label="Panier moyen réseau"
            value={fmtEur(panierMoyen)}
          />
          <KpiCard
            label="Clients uniques"
            value={fmtNum(clientsUniques)}
          />
          <KpiCard
            label="Part PREMIUM+"
            value={fmtPct(partPremiumPlus)}
          />
        </KpiRow>
      </section>

      <SectionSeparator />

      {/* Charts */}
      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Opportunité par magasin
        </h2>
        <RevenueBarChart
          data={magasinData}
          label="Opportunité upsell (K€)"
          color="#1d4ed8"
        />
      </section>

      <section>
        <h2 className="text-lg font-semibold text-gray-800 mb-4">
          Opportunité par segment
        </h2>
        <RevenueBarChart
          data={segmentData}
          label="Opportunité upsell (K€)"
          color="#7c3aed"
        />
      </section>

      <SectionSeparator />

      {/* Store cards */}
      {storeCards.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-gray-800 mb-1">
            Magasins
          </h2>
          <p className="text-sm text-gray-400 mb-4">
            Cliquez sur un magasin pour accéder à son tableau de bord détaillé.
          </p>
          <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
            {storeCards.map((store) => (
              <StoreCard
                key={store.name}
                name={store.name}
                ca={store.ca}
                panierMoyen={store.panierMoyen}
                opportunite={store.opportunite}
              />
            ))}
          </div>
        </section>
      )}
    </main>
  );
}
