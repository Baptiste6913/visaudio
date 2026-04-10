import React from "react";

export default function KpiRow({ children }: { children: React.ReactNode }) {
  const items = React.Children.toArray(children);
  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
      {items.map((child, i) => (
        <div key={i} className="animate-slide-up" style={{ animationDelay: `${i * 100}ms`, animationFillMode: "both" }}>
          {child}
        </div>
      ))}
    </div>
  );
}
