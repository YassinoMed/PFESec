export interface ModelInfo {
  model_id: string;
  name: string;
  category: string;
  version: string;
  framework: string;
  hf_id: string;
  local_path: string;
  size: string;
  param_count_b: number;
  memory_mb: number;
  gpu_required: boolean;
  description: string;
  task: string;
  icon: string;
  repo_available: boolean;
  status: string;
  loaded_at: string | null;
  load_time_ms: number | null;
  memory_usage_mb: number | null;
  gpu_usage_pct: number | null;
  cpu_usage_pct: number | null;
  avg_inference_ms: number | null;
  total_predictions: number;
  total_errors: number;
  last_used: string | null;
  download_progress: number;
  download_speed: string;
  error_message: string;
}

export interface FleetSummary {
  total_models: number;
  loaded: number;
  available: number;
  error: number;
  unloaded: number;
  total_predictions: number;
  total_errors: number;
  avg_inference_ms: number;
  estimated_gpu_memory_mb: number;
  estimated_cpu_memory_mb: number;
  categories: Record<string, { total: number; loaded: number }>;
  health: string;
}

function getOrchestratorUrl(): string {
  const envUrl = process.env.NEXT_PUBLIC_ORCHESTRATOR_URL;
  if (envUrl) return envUrl.trim();
  if (typeof window !== "undefined") {
    return `${window.location.protocol}//${window.location.hostname}:8080`;
  }
  return "http://localhost:8080";
}

async function getJson<T>(path: string): Promise<T> {
  const url = `${getOrchestratorUrl()}${path}`;
  const res = await fetch(url, { headers: { "Content-Type": "application/json" } });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

async function postJson<T>(path: string, body: unknown): Promise<T> {
  const url = `${getOrchestratorUrl()}${path}`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export const registryApi = {
  listModels: () => getJson<{ models: ModelInfo[]; total: number }>("/api/v1/models"),
  getSummary: () => getJson<FleetSummary>("/api/v1/models/summary"),
  getModelStatus: (modelId: string) => getJson<ModelInfo>(`/api/v1/models/${modelId}/status`),
  loadModel: (modelId: string) => postJson<{ success: boolean; model_id: string; status: string }>(`/api/v1/models/${modelId}/load`, {}),
  unloadModel: (modelId: string) => postJson<{ success: boolean; model_id: string; status: string }>(`/api/v1/models/${modelId}/unload`, {}),
  predictModel: (modelId: string, input: Record<string, unknown>) => postJson<Record<string, unknown>>(`/api/v1/models/${modelId}/predict`, input),
  downloadModel: (modelId: string) => postJson<{ success: boolean; model_id: string; progress: Record<string, unknown> }>("/api/v1/models/download", { model_id: modelId }),
};
