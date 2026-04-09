import type { ReactNode } from "react";

export interface KpiRowProps {
  children: ReactNode;
}

export default function KpiRow({ children }: KpiRowProps) {
  return (
    <div className="flex flex-wrap gap-4">
      {children}
    </div>
  );
}
