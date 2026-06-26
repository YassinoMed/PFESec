/**
 * lib/api.ts — Client typé pour l'API d'inférence SecureRAG Hub.
 *
 * - Appels directs côté client vers l'URL du backend (CORS déjà configuré).
 * - Si le backend est injoignable, on lève une erreur BackendUnreachable
 *   que le hook useQuery traduira en bascule vers les données mock.
 *
 * Variable d'env : NEXT_PUBLIC_BACKEND_URL (défaut http://localhost:8000)
 */

import type {
  GpuStatus,
  LoadModelResponse,
  ModelsResponse,
  PredictAllResponse,
  PredictResponse,
  RunTestsResponse,
  TestScriptView,
  TestScriptsResponse,
} from "@/types/api";

export class BackendUnreachable extends Error {
  constructor() {
    super("Backend d'inférence injoignable");
    this.name = "BackendUnreachable";
  }
}

/** URL de base du backend d'inférence (lisible côté client via NEXT_PUBLIC_). */
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";

async function getJson<T>(path: string, init?: RequestInit): Promise<T> {
  const url = `${BACKEND_URL}${path}`;
  let res: Response;
  try {
    res = await fetch(url, {
      ...init,
      headers: { "Content-Type": "application/json", ...init?.headers },
    });
  } catch {
    // fetch jette sur un échec réseau (backend éteint).
    throw new BackendUnreachable();
  }
  if (res.status === 502 || res.status === 504) {
    throw new BackendUnreachable();
  }
  return res.json() as Promise<T>;
}

/* ─────────────────────── Endpoints GET ───────────────────── */

export const api = {
  ping: () => getJson<ModelsResponse>("/api/models"),

  models: () => getJson<ModelsResponse>("/api/models"),

  gpuStatus: () => getJson<GpuStatus>("/api/gpu-status"),

  testScripts: () => getJson<TestScriptsResponse>("/api/test-scripts"),

  testScriptView: (name: string) =>
    getJson<TestScriptView>(
      `/api/test-scripts/view?name=${encodeURIComponent(name)}`
    ),

  /* ───────────────────── Endpoints POST ──────────────────── */

  predict: (model: string, prompt: string, maxNewTokens = 200) =>
    getJson<PredictResponse>("/api/predict", {
      method: "POST",
      body: JSON.stringify({ model, prompt, max_new_tokens: maxNewTokens }),
    }),

  predictAll: (prompt: string, maxNewTokens = 150) =>
    getJson<PredictAllResponse>("/api/predict-all", {
      method: "POST",
      // L'inférence multi-modèles peut être longue : on laisse le client
      // attendre (le backend n'impose pas de timeout côté inference).
      body: JSON.stringify({ prompt, max_new_tokens: maxNewTokens }),
    }),

  loadModel: (model: string) =>
    getJson<LoadModelResponse>("/api/load-model", {
      method: "POST",
      body: JSON.stringify({ model }),
    }),

  runTests: (model: string, script: string) =>
    getJson<RunTestsResponse>("/api/run-tests", {
      method: "POST",
      body: JSON.stringify({ model, script }),
    }),
};
