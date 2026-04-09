import { useMemo } from "react";
import HeroCard from "../components/HeroCard";
import KpiRow from "../components/KpiRow";
import KpiCard from "../components/KpiCard";
import RevenueBarChart from "../components/charts/RevenueBarChart";
import { useKpis } from "../hooks/useKpis";
import { fmtEur, fmtNum, fmtPct } from "../utils/format";

function recordToChartData(
  rec: Record<string, unknown>
): { name: string; value: number }[] {
  return Object.entries(rec).map(([name, value]) => ({
    name,
    value: value as number,
  }));
}

export default function LandingPage() {
  const { data, loading, error } = useKpis();

  const magasinData = useMemo(() => {
    if (!data) return [];
    return recordToChartData(
      data.hero.h5_par_magasin as Record<string, unknown>
    );
  }, [data]);

  const segmentData = useMemo(() => {
    if (!data) return [];
    return recordToChartData(
      data.hero.h5_par_segment as Record<string, unknown>
    );
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
  const panierMoyen = data.cadrage.panier_moyen_reseau as number;
  const clientsUniques = data.cadrage.clients_uniques as number;
  const partPremiumPlus = data.hero.part_premium_plus_reseau as number;

  return (
    <main className="flex flex-col gap-8 p-6 max-w-5xl mx-auto">
      <HeroCard
        value={fmtEur(opportuniteUpsell)}
        label="Opportunité upsell annuelle"
        subtitle="Écart au top-quartile par segment × volume"
      />

      <KpiRow>
        <KpiCard label="CA total réseau" value={fmtEur(caTotal)} />
        <KpiCard label="Panier moyen réseau" value={fmtEur(panierMoyen)} />
        <KpiCard label="Clients uniques" value={fmtNum(clientsUniques)} />
        <KpiCard
          label="Part PREMIUM+"
          value={fmtPct(partPremiumPlus)}
        />
      </KpiRow>

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
    </main>
  );
}
