export interface HeroCardProps {
  value: string;
  label: string;
  subtitle?: string;
}

export default function HeroCard({ value, label, subtitle }: HeroCardProps) {
  return (
    <div className="rounded-xl bg-gradient-to-br from-brand-600 to-brand-700 text-white p-6 shadow-md">
      <p className="text-4xl font-extrabold leading-tight tracking-tight">
        {value}
      </p>
      <p className="mt-1 text-base font-medium text-white/90">{label}</p>
      {subtitle && (
        <p className="mt-1 text-sm text-white/70">{subtitle}</p>
      )}
    </div>
  );
}
