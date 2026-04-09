import { useEffect, useState } from "react";
import type { KpisPayload } from "../types";
import { getKpis } from "../utils/api";

export function useKpis() {
  const [data, setData] = useState<KpisPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getKpis()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}
