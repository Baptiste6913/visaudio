export interface HeroCardProps {
  value: string;
  label: string;
  subtitle?: string;
}

export default function HeroCard({ value, label, subtitle }: HeroCardProps) {
  return (
    <div className="animate-fade-in relative rounded-2xl bg-gradient-to-br from-brand-600 via-brand-700 to-brand-900 text-white p-6 shadow-md overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_30%_20%,rgba(255,255,255,0.15),transparent)]" />
      <div className="relative">
        <p className="text-5xl font-extrabold leading-tight tracking-tight">
          {value}
        </p>
        <p className="mt-1 text-base font-medium text-white/90">{label}</p>
        {subtitle && (
          <p className="mt-1 text-sm text-white/70">{subtitle}</p>
        )}
      </div>
    </div>
  );
}
