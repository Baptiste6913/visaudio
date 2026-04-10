import type { Finding } from "../types";

export interface FindingListProps {
  findings: Finding[];
}

const SEVERITY_BADGE: Record<string, string> = {
  critical: "bg-red-100 text-red-700 border border-red-200",
  warning: "bg-amber-100 text-amber-700 border border-amber-200",
  info: "bg-blue-100 text-blue-700 border border-blue-200",
};

const SEVERITY_LABEL: Record<string, string> = {
  critical: "Critique",
  warning: "Attention",
  info: "Info",
};

function severityClass(severity: string): string {
  return (
    SEVERITY_BADGE[severity] ??
    "bg-gray-100 text-gray-700 border border-gray-200"
  );
}

function severityLabel(severity: string): string {
  return SEVERITY_LABEL[severity] ?? severity;
}

export default function FindingList({ findings }: FindingListProps) {
  if (findings.length === 0) {
    return (
      <p className="text-sm text-gray-400 italic">Aucune anomalie détectée.</p>
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {findings.map((f) => (
        <li
          key={f.id}
          className="bg-white border border-gray-100 rounded-lg p-4 shadow-sm"
        >
          <div className="flex items-start gap-3">
            <span
              className={[
                "shrink-0 mt-0.5 px-2 py-0.5 rounded text-xs font-semibold uppercase tracking-wide",
                severityClass(f.severity),
              ].join(" ")}
            >
              {severityLabel(f.severity)}
            </span>
            <div className="flex flex-col gap-1 min-w-0">
              <p className="text-sm text-gray-600">{f.message}</p>
              {f.recommendation && (
                <p className="text-xs text-gray-500 italic">
                  {f.recommendation}
                </p>
              )}
            </div>
          </div>
        </li>
      ))}
    </ul>
  );
}
