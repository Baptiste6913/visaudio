import { useEffect, useState } from "react";
import type { DiagnosticsPayload } from "../types";
import { getDiagnostics } from "../utils/api";

export function useDiagnostics() {
  const [data, setData] = useState<DiagnosticsPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getDiagnostics()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}
