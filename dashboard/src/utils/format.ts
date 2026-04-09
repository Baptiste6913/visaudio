/* Number and date formatters */

const eurFmt = new Intl.NumberFormat("fr-FR", {
  style: "currency", currency: "EUR", maximumFractionDigits: 0,
});
const pctFmt = new Intl.NumberFormat("fr-FR", {
  style: "percent", minimumFractionDigits: 1, maximumFractionDigits: 1,
});
const numFmt = new Intl.NumberFormat("fr-FR", { maximumFractionDigits: 0 });

export const fmtEur = (v: number) => eurFmt.format(v);
export const fmtPct = (v: number) => pctFmt.format(v);
export const fmtNum = (v: number) => numFmt.format(v);
export const fmtKEur = (v: number) =>
  `${numFmt.format(Math.round(v / 1000))} K\u20AC`;
