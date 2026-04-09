import { useCallback, useState } from "react";
import type { SimulateRequest, SimulateResponse } from "../types";
import { simulate } from "../utils/api";

export function useSimulate() {
  const [data, setData] = useState<SimulateResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const run = useCallback(async (req: SimulateRequest) => {
    setLoading(true);
    setError(null);
    try {
      const result = await simulate(req);
      setData(result);
      return result;
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  return { data, loading, error, run };
}
