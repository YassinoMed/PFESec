/**
 * types/api.ts — Types TypeScript pour l'API d'inférence SecureRAG Hub.
 *
 * Ces types reproduisent fidèlement les schémas JSON réellement renvoyés
 * par inference_server.py (port 8000). Beaucoup sont des "discriminated
 * unions" — il faut d'abord tester le discriminant (error, available, type…).
 */

/* ───────────────────────── Modèles ───────────────────────── */

export type ModelType = "bert" | "lora" | "llm";
export type ModelStatus = "READY" | "NOT_TRAINED" | "UNKNOWN";

export interface ModelInfo {
  id: string;
  name: string;
  type: ModelType;
  description: string;
  /** "phishing" | "soc" | … ; "unknown" par défaut. */
  task: string;
  status: ModelStatus;
  loaded: boolean;
  /** Emoji défini dans MODEL_REGISTRY. */
  icon: string;
  /** Chemin absolu vers le dossier du modèle. */
  path: string;
}

export interface ModelsResponse {
  models: ModelInfo[];
}

/* ─────────────────────── Inférence ───────────────────────── */

export type Verdict = "ACCEPT" | "BLOCK";
export type ConsensusVerdict = "ACCEPT" | "BLOCK" | "UNCERTAIN";

/** Champs communs à tout résultat d'inférence réussi. */
export interface InferenceCommon {
  model_id: string;
  model_name: string;
  model_type: ModelType;
  elapsed_s: number;
  icon: string;
  predicted: boolean;
  prediction: string;
  /** 0..100, 1 décimale. */
  threat_score: number;
  /** "ACCEPT" | "BLOCK" pour BERT ; peut être "UNKNOWN" pour les LLM. */
  verdict: Verdict | "UNKNOWN";
}

/** Résultat d'un classifieur BERT (CySecBERT, SecBERT). */
export interface ClassificationResult extends InferenceCommon {
  type: "classification";
  /** 0..1. */
  confidence: number;
  /** Toutes les classes → probabilité. */
  probabilities: Record<string, number>;
}

/** Résultat d'un LLM / LoRA génératif (PhishSense, SecurityLLM). */
export interface GenerativeResult extends InferenceCommon {
  type: "generative";
  /** Toujours null pour les modèles génératifs. */
  confidence: null;
}

export type InferenceResult = ClassificationResult | GenerativeResult;

/** Variante d'erreur (renvoyée avec HTTP 200, testez `error` en premier). */
export interface InferenceError {
  error: string;
  model_id?: string;
  status?: string;
  elapsed_s?: number;
}

export type PredictResponse = InferenceResult | InferenceError;

/* ──────────────────── Consensus multi-modèles ────────────── */

export interface Consensus {
  verdict: ConsensusVerdict;
  block_votes: number;
  accept_votes: number;
  total_votes: number;
  /** 0..100, 1 décimale. */
  confidence_pct: number;
}

export interface PredictAllResponse {
  results: PredictResponse[];
  consensus: Consensus;
  text_preview: string;
  timestamp: string;
}

/* ───────────────────────── GPU ───────────────────────────── */

export interface GpuDevice {
  index: number;
  name: string;
  total_gb: number;
  allocated_gb: number;
  reserved_gb: number;
  free_gb: number;
  utilization_pct: number;
}

export interface GpuStatusAvailable {
  available: true;
  devices: GpuDevice[];
  loaded_models: string[];
  cuda_version: string | null;
}

export interface GpuStatusUnavailable {
  available: false;
  message: string;
}

export type GpuStatus = GpuStatusAvailable | GpuStatusUnavailable;

/* ─────────────────── Tests & rapports ────────────────────── */

export interface TestScriptInfo {
  name: string;
  path: string;
  category: string;
  size_bytes: number;
}

export interface TestScriptsResponse {
  scripts: TestScriptInfo[];
}

export interface TestCase {
  id: string;
  title: string;
  type: "classification" | "generative";
  text: string;
  expected_label?: string;
  test_type?: string;
  expected_keywords?: string;
}

export interface TestScriptView {
  script_name: string;
  total_tests: number;
  tests: TestCase[];
}

export type TestStatus =
  | "unknown"
  | "PASS"
  | "FAIL"
  | "INFO"
  | "GENERATED"
  | "ERROR";

export interface BertTestPrediction {
  predicted_label: string;
  confidence: number;
  all_probabilities: Record<string, number>;
}

export interface LlmTestPrediction {
  generated_text: string;
  input_tokens: number;
  output_tokens: number;
}

export interface TestResultItem {
  id: string;
  title: string;
  status: TestStatus;
  prediction?: BertTestPrediction | LlmTestPrediction;
  /** Présent uniquement pour les cas BERT PASS/FAIL. */
  expected?: string;
  error?: string;
}

export interface TestReport {
  model: string;
  timestamp: string;
  total_tests: number;
  passed: number;
  failed: number;
  errors: number;
  accuracy: number;
  test_results: TestResultItem[];
}

export interface RunTestsResponse {
  success: boolean;
  stdout: string;
  stderr: string;
  report: TestReport | Record<string, never>;
}

export interface LoadModelResponse {
  success: boolean;
  model_id: string;
  message?: string;
  error?: string;
}

/* ─────────────────── Métriques calculées ─────────────────── */
/* Le backend ne fournit QUE l'accuracy. Ces structures sont */
/* calculées côté client (lib/metrics.ts) depuis test_results. */

export interface ConfusionCell {
  expected: string;
  predicted: string;
  count: number;
}

export interface CategoryMetric {
  category: string;
  total: number;
  passed: number;
  failed: number;
  accuracy: number;
}

export interface ComputedMetrics {
  accuracy: number;
  precision: number;
  recall: number;
  f1: number;
  confusion: ConfusionCell[];
  perCategory: CategoryMetric[];
  evaluated: number;
  /** Classes distinctes rencontrées. */
  labels: string[];
}
