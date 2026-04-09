import { useEffect, useState } from "react";
import type { ArchetypesPayload } from "../types";
import { getArchetypes } from "../utils/api";

export function useArchetypes() {
  const [data, setData] = useState<ArchetypesPayload | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    getArchetypes()
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, []);

  return { data, loading, error };
}
