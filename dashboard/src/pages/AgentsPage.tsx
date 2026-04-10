import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";
import type { TooltipProps } from "recharts";
import type { ValueType, NameType } from "recharts/types/component/DefaultTooltipContent";
import { useArchetypes } from "../hooks/useArchetypes";
import { fmtEur, fmtPct, fmtNum } from "../utils/format";

/* ── Palette: 6 color-blind-aware hues, one per archetype ──────────────── */
const ARCHETYPE_COLORS = [
  "#2563eb",
  "#7c3aed",
  "#059669",
  "#d97706",
  "#dc2626",
  "#0891b2",
] as const;

/* ── Derived gamme label ─────────────────────────────────────────────────── */
function deriveGamme(partPremiumPlus: number, panierMoyen: number): string {
  if (partPremiumPlus > 0.3) return "PREMIUM+";
  if (panierMoyen > 150) return "CONFORT";
  return "ESSENTIEL";
}

/* ── Derived fidelite score (0-100) ─────────────────────────────────────── */
function deriveScore(nAchatsTotaux: number): number {
  return Math.min(100, Math.round(nAchatsTotaux * 40));
}

/* ── Types ──────────────────────────────────────────────────────────────── */
interface ArchetypeRow {
  id: number;
  label: string;
  nClients: number;
  shareOfCa: number;
  ageDernierAchat: number;
  panierMoyen: number;
  partPremiumPlus: number;
  nAchatsTotaux: number;
  moisEntreAchats: number;
  conventionnementLibre: number;
  sexeFemme: number;
  sexeHomme: number;
  gamme: string;
  fidelite: number;
  color: string;
}

/* ── Scatter tooltip ─────────────────────────────────────────────────────── */
function BubbleTooltip({
  active,
  payload,
}: TooltipProps<ValueType, NameType>) {
  if (!active || !payload || payload.length === 0) return null;
  const d = payload[0]?.payload as ArchetypeRow | undefined;
  if (!d) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-md px-3 py-2 text-xs max-w-[200px]">
      <p className="font-semibold text-gray-800 mb-1 leading-tight">{d.label}</p>
      <div className="flex flex-col gap-0.5 text-gray-600">
        <span>{fmtNum(d.nClients)} clients</span>
        <span>Panier moyen : {fmtEur(d.panierMoyen)}</span>
        <span>Part PREMIUM+ : {fmtPct(d.partPremiumPlus)}</span>
      </div>
    </div>
  );
}

/* ── Detail panel ─────────────────────────────────────────────────────────── */
interface DetailPanelProps {
  archetype: ArchetypeRow;
}

function DetailPanel({ archetype: a }: DetailPanelProps) {
  const frequence =
    a.moisEntreAchats > 0 ? (12 / a.moisEntreAchats).toFixed(1) : "—";
  const dominantSexe = a.sexeFemme >= a.sexeHomme ? "Femme" : "Homme";
  const femPct = Math.round(a.sexeFemme * 100);
  const homPct = Math.round(a.sexeHomme * 100);
  const conventionnement =
    a.conventionnementLibre > 0.5 ? "LIBRE" : "NON-LIBRE";

  // Build a natural-language description
  const description = [
    `${dominantSexe} d'environ ${Math.round(a.ageDernierAchat)} ans`,
    `conventionnement ${conventionnement.toLowerCase()}`,
    `achète ${a.gamme}`,
    `panier moyen ${fmtEur(a.panierMoyen)}`,
    `fréquence ${frequence} achat${Number(frequence) > 1.1 ? "s" : ""}/an`,
    `fidélité ${a.fidelite}\u202f%`,
  ].join(", ");

  return (
    <div className="animate-slide-up glass-card p-6 mt-4">
      {/* Title row */}
      <div className="flex items-start justify-between gap-4 mb-5">
        <div>
          <h3 className="text-base font-bold text-gray-900">{a.label}</h3>
          <p className="text-sm text-gray-500 mt-0.5 leading-relaxed">
            {description}.
          </p>
        </div>
        <span
          className="inline-flex shrink-0 items-center rounded-full px-2.5 py-0.5 text-xs font-semibold text-white"
          style={{ backgroundColor: a.color }}
        >
          #{a.id}
        </span>
      </div>

      {/* Stats grid */}
      <dl className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-5">
        <StatItem label="Sexe F / H" value={`${femPct}\u202f% / ${homPct}\u202f%`} />
        <StatItem label="Age moyen" value={`${Math.round(a.ageDernierAchat)}\u202fans`} />
        <StatItem label="Panier moyen" value={fmtEur(a.panierMoyen)} />
        <StatItem label="Gamme préférée" value={a.gamme} />
        <StatItem label="Conventionnement" value={conventionnement} />
        <StatItem label="Fréquence" value={`${frequence} / an`} />
        <StatItem label="Score fidélité" value={`${a.fidelite}\u202f%`} />
        <StatItem label="Part CA" value={fmtPct(a.shareOfCa)} />
      </dl>

      {/* CTA */}
      <Link
        to={`/simulation?scenario=SC-L2a`}
        className="inline-flex items-center gap-2 rounded-md bg-brand-600 px-4 py-2 text-sm font-semibold text-white shadow-sm transition-colors hover:bg-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
      >
        Simuler l'impact sur ce segment
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-4 w-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
        </svg>
      </Link>
    </div>
  );
}

interface StatItemProps {
  label: string;
  value: string;
}

function StatItem({ label, value }: StatItemProps) {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className="text-xs font-medium text-gray-400 uppercase tracking-wide">
        {label}
      </dt>
      <dd className="text-sm font-semibold text-gray-800">{value}</dd>
    </div>
  );
}

/* ── Page ──────────────────────────────────────────────────────────────── */
export default function AgentsPage() {
  const { data, loading, error } = useArchetypes();
  const [selectedId, setSelectedId] = useState<number | null>(null);

  /* Transform API payload → typed rows */
  const rows = useMemo<ArchetypeRow[]>(() => {
    if (!data) return [];
    return data.archetypes.map((a, i) => {
      const c = a.centroid;
      const partPremiumPlus = c["part_premium_plus"] ?? 0;
      const panierMoyen = c["panier_moyen"] ?? 0;
      const nAchatsTotaux = c["n_achats_totaux"] ?? 0;
      return {
        id: a.id,
        label: a.label,
        nClients: a.n_clients,
        shareOfCa: a.share_of_ca,
        ageDernierAchat: c["age_dernier_achat"] ?? 0,
        panierMoyen,
        partPremiumPlus,
        nAchatsTotaux,
        moisEntreAchats: c["mois_entre_achats"] ?? 0,
        conventionnementLibre: c["conventionnement_libre"] ?? 0,
        sexeFemme: c["sexe_Femme"] ?? 0,
        sexeHomme: c["sexe_Homme"] ?? 0,
        gamme: deriveGamme(partPremiumPlus, panierMoyen),
        fidelite: deriveScore(nAchatsTotaux),
        color: ARCHETYPE_COLORS[i % ARCHETYPE_COLORS.length],
      };
    });
  }, [data]);

  const totalClients = useMemo(
    () => rows.reduce((sum, r) => sum + r.nClients, 0),
    [rows]
  );

  const selectedArchetype = useMemo(
    () => rows.find((r) => r.id === selectedId) ?? null,
    [rows, selectedId]
  );

  /* ── Loading state ─────────────────────────────────────────────────── */
  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-gray-500 text-sm animate-pulse">
          Chargement des archetypes…
        </p>
      </div>
    );
  }

  /* ── Error state ───────────────────────────────────────────────────── */
  if (error || !data) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-red-500 text-sm">
          {error ?? "Impossible de charger les données."}
        </p>
      </div>
    );
  }

  /* ── Empty state ───────────────────────────────────────────────────── */
  if (rows.length === 0) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <p className="text-gray-400 text-sm">
          Aucun archétype disponible. Importez un fichier Excel pour lancer
          l'analyse.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-8 max-w-5xl mx-auto">
      {/* ── Section 1: Header ──────────────────────────────────────────── */}
      <section>
        <div className="flex items-start justify-between gap-4 flex-wrap">
          <div>
            <h1 className="text-3xl font-extrabold gradient-text leading-tight">
              Agents Clients
            </h1>
            <p className="mt-1 text-sm text-gray-500">
              {data.n_archetypes} archétypes découverts par K-Means sur 20\u202f000+
              clients
            </p>
          </div>
          <span className="inline-flex items-center rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-sm font-semibold text-brand-700">
            {fmtNum(totalClients)} clients
          </span>
        </div>
      </section>

      {/* ── Section 2: Bubble chart ─────────────────────────────────────── */}
      <section className="glass-card p-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-4">
          Positionnement des archétypes — Panier moyen vs Part PREMIUM+
        </h2>
        <ResponsiveContainer width="100%" height={400}>
          <ScatterChart
            margin={{ top: 20, right: 30, bottom: 20, left: 20 }}
            aria-label="Positionnement des archétypes clients"
          >
            <XAxis
              type="number"
              dataKey="panierMoyen"
              name="Panier moyen"
              unit="€"
              tickFormatter={(v: number) => `${v}\u202f€`}
              tick={{ fontSize: 11, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
              label={{
                value: "Panier moyen (€)",
                position: "insideBottomRight",
                offset: -8,
                fontSize: 11,
                fill: "#9ca3af",
              }}
            />
            <YAxis
              type="number"
              dataKey="partPremiumPlus"
              name="Part PREMIUM+"
              tickFormatter={(v: number) =>
                `${Math.round(v * 100)}\u202f%`
              }
              tick={{ fontSize: 11, fill: "#6b7280" }}
              axisLine={{ stroke: "#e5e7eb" }}
              tickLine={false}
              label={{
                value: "Part PREMIUM+ (%)",
                angle: -90,
                position: "insideLeft",
                offset: 8,
                fontSize: 11,
                fill: "#9ca3af",
              }}
            />
            <ZAxis
              type="number"
              dataKey="nClients"
              name="Clients"
              range={[200, 2000]}
            />
            <Tooltip content={<BubbleTooltip />} />
            <Scatter
              data={rows}
              animationDuration={1500}
              animationEasing="ease-out"
            >
              {rows.map((row) => (
                <Cell key={row.id} fill={row.color} fillOpacity={0.85} />
              ))}
            </Scatter>
          </ScatterChart>
        </ResponsiveContainer>

        {/* Legend */}
        <div className="flex flex-wrap gap-3 mt-2">
          {rows.map((row) => (
            <button
              key={row.id}
              type="button"
              onClick={() =>
                setSelectedId((prev) => (prev === row.id ? null : row.id))
              }
              className={[
                "flex items-center gap-1.5 rounded-full px-2.5 py-0.5 text-xs font-medium border transition-colors",
                selectedId === row.id
                  ? "border-gray-400 bg-gray-100 text-gray-700"
                  : "border-gray-200 bg-white text-gray-600 hover:border-gray-300",
              ].join(" ")}
            >
              <span
                className="inline-block h-2 w-2 rounded-full shrink-0"
                style={{ backgroundColor: row.color }}
                aria-hidden="true"
              />
              {row.label.length > 15
                ? `${row.label.slice(0, 15)}\u2026`
                : row.label}
            </button>
          ))}
        </div>
      </section>

      {/* ── Section 3: Archetype table ──────────────────────────────────── */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Tableau des archétypes
        </h2>
        <div className="glass-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-xs">
              <thead>
                <tr className="border-b border-gray-100 text-gray-400 uppercase tracking-wide">
                  <th className="px-4 py-3 text-left font-semibold w-8">
                    ID
                  </th>
                  <th className="px-4 py-3 text-left font-semibold">
                    Archétype
                  </th>
                  <th className="px-4 py-3 text-right font-semibold">
                    Clients
                  </th>
                  <th className="px-4 py-3 text-right font-semibold">
                    Part CA
                  </th>
                  <th className="px-4 py-3 text-right font-semibold">
                    Âge moyen
                  </th>
                  <th className="px-4 py-3 text-right font-semibold">
                    Panier
                  </th>
                  <th className="px-4 py-3 text-center font-semibold">
                    Gamme
                  </th>
                  <th className="px-4 py-3 text-right font-semibold">
                    Fidélité
                  </th>
                </tr>
              </thead>
              <tbody>
                {rows.map((row, i) => {
                  const isSelected = selectedId === row.id;
                  return (
                    <tr
                      key={row.id}
                      onClick={() =>
                        setSelectedId((prev) =>
                          prev === row.id ? null : row.id
                        )
                      }
                      className={[
                        "border-b border-gray-50 cursor-pointer transition-colors",
                        isSelected
                          ? "bg-brand-50"
                          : i % 2 === 0
                          ? "bg-white hover:bg-gray-50"
                          : "bg-gray-50/50 hover:bg-gray-100/60",
                      ].join(" ")}
                      aria-selected={isSelected}
                    >
                      {/* ID */}
                      <td className="px-4 py-3">
                        <span
                          className="inline-flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold text-white"
                          style={{ backgroundColor: row.color }}
                        >
                          {row.id}
                        </span>
                      </td>
                      {/* Label */}
                      <td className="px-4 py-3 font-medium text-gray-800 max-w-[180px] truncate">
                        {row.label}
                      </td>
                      {/* Clients */}
                      <td className="px-4 py-3 text-right text-gray-600 tabular-nums">
                        {fmtNum(row.nClients)}
                      </td>
                      {/* Part CA */}
                      <td className="px-4 py-3 text-right text-gray-600 tabular-nums">
                        {fmtPct(row.shareOfCa)}
                      </td>
                      {/* Age */}
                      <td className="px-4 py-3 text-right text-gray-600 tabular-nums">
                        {Math.round(row.ageDernierAchat)}&nbsp;ans
                      </td>
                      {/* Panier */}
                      <td className="px-4 py-3 text-right text-gray-600 tabular-nums">
                        {fmtEur(row.panierMoyen)}
                      </td>
                      {/* Gamme badge */}
                      <td className="px-4 py-3 text-center">
                        <GammeBadge gamme={row.gamme} />
                      </td>
                      {/* Fidélité */}
                      <td className="px-4 py-3 text-right">
                        <FideliteBar score={row.fidelite} />
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {/* ── Section 4: Detail panel ─────────────────────────────────── */}
        {selectedArchetype && (
          <DetailPanel archetype={selectedArchetype} />
        )}
      </section>
    </div>
  );
}

/* ── Small presentational sub-components ─────────────────────────────────── */

interface GammeBadgeProps {
  gamme: string;
}

function GammeBadge({ gamme }: GammeBadgeProps) {
  const cls =
    gamme === "PREMIUM+"
      ? "bg-violet-100 text-violet-700 border border-violet-200"
      : gamme === "CONFORT"
      ? "bg-blue-100 text-blue-700 border border-blue-200"
      : "bg-gray-100 text-gray-600 border border-gray-200";

  return (
    <span
      className={`inline-flex items-center rounded-full px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide ${cls}`}
    >
      {gamme}
    </span>
  );
}

interface FideliteBarProps {
  score: number;
}

function FideliteBar({ score }: FideliteBarProps) {
  const color =
    score >= 80
      ? "bg-green-500"
      : score >= 50
      ? "bg-brand-500"
      : "bg-gray-300";

  return (
    <div className="flex items-center justify-end gap-1.5">
      <div
        className="h-1.5 w-14 rounded-full bg-gray-100 overflow-hidden"
        aria-hidden="true"
      >
        <div
          className={`h-full rounded-full ${color} transition-all`}
          style={{ width: `${score}%` }}
        />
      </div>
      <span className="text-gray-600 tabular-nums w-8 text-right">
        {score}&nbsp;%
      </span>
    </div>
  );
}
