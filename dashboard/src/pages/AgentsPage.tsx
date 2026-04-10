import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useArchetypes } from "../hooks/useArchetypes";
import { fmtEur, fmtPct, fmtNum } from "../utils/format";
import type { ArchetypesPayload } from "../types";

/* ── Palette: 10 color-blind-aware hues ─────────────────────────────────── */
const ARCHETYPE_COLORS = [
  "#2563eb",
  "#7c3aed",
  "#059669",
  "#d97706",
  "#dc2626",
  "#0891b2",
  "#4f46e5",
  "#16a34a",
  "#ca8a04",
  "#be185d",
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

/* ── CountUp animated number ─────────────────────────────────────────────── */
interface CountUpProps {
  target: number;
}

function CountUp({ target }: CountUpProps) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    const start = performance.now();
    const tick = (now: number) => {
      const p = Math.min((now - start) / 1200, 1);
      setVal(Math.round(target * (1 - Math.pow(1 - p, 3))));
      if (p < 1) requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }, [target]);
  return <>{val.toLocaleString("fr-FR")}</>;
}

/* ── Network graph ───────────────────────────────────────────────────────── */
interface NetworkNode {
  id: number;
  label: string;
  n_clients: number;
  ageDernierAchat: number;
  x: number;
  y: number;
  r: number;
  color: string;
}

interface NetworkEdge {
  from: number;
  to: number;
  opacity: number;
}

interface NetworkGraphProps {
  archetypes: ArchetypesPayload["archetypes"];
  selectedId: number | null;
  onSelect: (id: number | null) => void;
}

function NetworkGraph({ archetypes, selectedId, onSelect }: NetworkGraphProps) {
  const [hoveredId, setHoveredId] = useState<number | null>(null);
  const width = 600;
  const height = 400;

  const nodes = useMemo<NetworkNode[]>(
    () =>
      archetypes.map((a, i) => {
        const angle = (2 * Math.PI * i) / archetypes.length;
        const radius = 150;
        return {
          id: a.id,
          label: a.label,
          n_clients: a.n_clients,
          ageDernierAchat: a.centroid["age_dernier_achat"] ?? 0,
          x: width / 2 + radius * Math.cos(angle),
          y: height / 2 + radius * Math.sin(angle),
          r: Math.max(15, Math.sqrt(a.n_clients) * 1.5),
          color: ARCHETYPE_COLORS[i % ARCHETYPE_COLORS.length],
        };
      }),
    [archetypes]
  );

  const edges = useMemo<NetworkEdge[]>(() => {
    const result: NetworkEdge[] = [];
    for (let i = 0; i < nodes.length; i++) {
      for (let j = i + 1; j < nodes.length; j++) {
        const ageDiff = Math.abs(
          nodes[i].ageDernierAchat - nodes[j].ageDernierAchat
        );
        if (ageDiff <= 15) {
          result.push({
            from: i,
            to: j,
            opacity: Math.max(0.1, 1 - ageDiff / 15),
          });
        }
      }
    }
    return result;
  }, [nodes]);

  const activeId = hoveredId ?? selectedId;

  const connectedIds = useMemo<Set<number>>(() => {
    if (activeId === null) return new Set();
    const s = new Set<number>();
    s.add(activeId);
    for (const e of edges) {
      if (nodes[e.from].id === activeId) s.add(nodes[e.to].id);
      if (nodes[e.to].id === activeId) s.add(nodes[e.from].id);
    }
    return s;
  }, [activeId, edges, nodes]);

  return (
    <svg
      viewBox={`0 0 ${width} ${height}`}
      className="w-full max-w-2xl mx-auto"
      aria-label="Graphe de réseau des archétypes clients"
      role="img"
    >
      {/* Edges */}
      {edges.map((e, i) => {
        const fromNode = nodes[e.from];
        const toNode = nodes[e.to];
        const isHighlighted =
          activeId !== null &&
          (fromNode.id === activeId || toNode.id === activeId);
        const dimmed = activeId !== null && !isHighlighted;
        return (
          <line
            key={i}
            x1={fromNode.x}
            y1={fromNode.y}
            x2={toNode.x}
            y2={toNode.y}
            stroke={isHighlighted ? "#6366f1" : "#94a3b8"}
            strokeWidth={isHighlighted ? 2 : 1.5}
            opacity={dimmed ? 0.05 : e.opacity}
            strokeDasharray="4 2"
            style={{
              transition: "opacity 0.25s, stroke 0.25s, stroke-width 0.25s",
            }}
          />
        );
      })}

      {/* Nodes */}
      {nodes.map((n, i) => {
        const isActive = activeId === n.id;
        const dimmed = activeId !== null && !connectedIds.has(n.id);
        return (
          <g
            key={n.id}
            style={{ cursor: "pointer" }}
            onClick={() => onSelect(selectedId === n.id ? null : n.id)}
            onMouseEnter={() => setHoveredId(n.id)}
            onMouseLeave={() => setHoveredId(null)}
            role="button"
            aria-label={`Archétype ${n.label}, ${fmtNum(n.n_clients)} clients`}
            tabIndex={0}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") {
                onSelect(selectedId === n.id ? null : n.id);
              }
            }}
          >
            <circle
              cx={n.x}
              cy={n.y}
              r={n.r}
              fill={n.color}
              opacity={dimmed ? 0.2 : isActive ? 1 : 0.8}
              style={{
                animation: `pulse-node 3s ease-in-out ${i * 0.3}s infinite`,
                transformOrigin: `${n.x}px ${n.y}px`,
                filter: isActive
                  ? "drop-shadow(0 0 8px rgba(0,0,0,0.3))"
                  : "none",
                transition: "opacity 0.25s, filter 0.25s",
              }}
            />
            <text
              x={n.x}
              y={n.y + n.r + 14}
              textAnchor="middle"
              fontSize={10}
              fill="#4b5563"
              fontWeight="500"
              pointerEvents="none"
            >
              {n.label.slice(0, 18)}
            </text>
            <text
              x={n.x}
              y={n.y + 4}
              textAnchor="middle"
              fontSize={11}
              fill="white"
              fontWeight="700"
              pointerEvents="none"
            >
              {fmtNum(n.n_clients)}
            </text>
          </g>
        );
      })}
    </svg>
  );
}

/* ── Simulation log ──────────────────────────────────────────────────────── */
interface SimulationLogProps {
  archetypes: ArchetypesPayload["archetypes"];
}

function SimulationLog({ archetypes }: SimulationLogProps) {
  const entries = useMemo(
    () =>
      archetypes.slice(0, 5).flatMap((a, i) => [
        {
          month: i * 2 + 1,
          text: `${fmtNum(a.n_clients)} clients archétype "${a.label.slice(0, 25)}" évalués`,
          type: "info" as const,
        },
        {
          month: i * 2 + 2,
          text: `${fmtNum(Math.round(a.n_clients * 0.12))} montent en gamme → influencent ${fmtNum(Math.round(a.n_clients * 0.04))} contacts`,
          type: "success" as const,
        },
      ]),
    [archetypes]
  );

  return (
    <div className="bg-gray-900 rounded-xl p-4 font-mono text-xs max-h-60 overflow-y-auto">
      {entries.map((e, i) => (
        <div
          key={i}
          className="flex gap-2 py-0.5 animate-slide-up"
          style={{ animationDelay: `${i * 150}ms`, animationFillMode: "both" }}
        >
          <span className="text-gray-500 shrink-0">
            Mois {String(e.month).padStart(2, "0")}
          </span>
          <span
            className={
              e.type === "success" ? "text-green-400" : "text-blue-400"
            }
          >
            {e.text}
          </span>
        </div>
      ))}
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

  const description = [
    `${dominantSexe} d'environ ${Math.round(a.ageDernierAchat)} ans`,
    `conventionnement ${conventionnement.toLowerCase()}`,
    `achète ${a.gamme}`,
    `panier moyen ${fmtEur(a.panierMoyen)}`,
    `fréquence ${frequence} achat${Number(frequence) > 1.1 ? "s" : ""}/an`,
    `fidélité ${a.fidelite} %`,
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
        <StatItem label="Sexe F / H" value={`${femPct} % / ${homPct} %`} />
        <StatItem
          label="Age moyen"
          value={`${Math.round(a.ageDernierAchat)} ans`}
        />
        <StatItem label="Panier moyen" value={fmtEur(a.panierMoyen)} />
        <StatItem label="Gamme préférée" value={a.gamme} />
        <StatItem label="Conventionnement" value={conventionnement} />
        <StatItem label="Fréquence" value={`${frequence} / an`} />
        <StatItem label="Score fidélité" value={`${a.fidelite} %`} />
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
          Chargement des archetypes...
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
              {data.n_archetypes} archétypes découverts par K-Means sur 20 000+
              clients
            </p>
          </div>
          {/* Animated counters */}
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex flex-col items-end">
              <span className="text-xs text-gray-400 uppercase tracking-wide font-medium">
                Total clients
              </span>
              <span className="text-2xl font-extrabold text-brand-700 tabular-nums">
                <CountUp target={totalClients} />
              </span>
            </div>
            <div className="w-px h-8 bg-gray-200" aria-hidden="true" />
            <div className="flex flex-col items-end">
              <span className="text-xs text-gray-400 uppercase tracking-wide font-medium">
                Archétypes
              </span>
              <span className="text-2xl font-extrabold text-brand-700 tabular-nums">
                <CountUp target={data.n_archetypes} />
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ── Section 2: Network graph ────────────────────────────────────── */}
      <section className="glass-card p-6">
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-1">
          Réseau d'influence entre archétypes
        </h2>
        <p className="text-xs text-gray-400 mb-4">
          Les connexions relient les archétypes dont l'âge moyen est proche
          (&lt; 15 ans d'écart). L'opacité reflète la probabilité d'influence
          bouche-à-oreille.
        </p>
        <NetworkGraph
          archetypes={data.archetypes}
          selectedId={selectedId}
          onSelect={setSelectedId}
        />

        {/* Legend */}
        <div className="flex flex-wrap gap-3 mt-4">
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
                    Age moyen
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
                      {/* Fidelite */}
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
        {selectedArchetype && <DetailPanel archetype={selectedArchetype} />}
      </section>

      {/* ── Section 5: Simulation log ───────────────────────────────────── */}
      <section>
        <h2 className="text-sm font-semibold text-gray-500 uppercase tracking-wide mb-3">
          Journal de simulation
        </h2>
        <SimulationLog archetypes={data.archetypes} />
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
