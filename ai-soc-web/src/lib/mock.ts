/**
 * lib/mock.ts — Données simulées réalistes pour le mode démo.
 *
 * Quand inference_server.py n'est pas lancé, le dashboard bascule
 * automatiquement sur ces données afin de rester vivant pour la démo.
 * Les structures respectent strictement les types de l'API réelle.
 */

import type {
  GpuStatus,
  ModelsResponse,
  PredictAllResponse,
  TestScriptsResponse,
} from "@/types/api";

export const mockModels: ModelsResponse = {
  models: [
    {
      id: "cysecbert",
      name: "CySecBERT Classifier",
      type: "bert",
      description: "BERT fine-tuné — détection phishing / email malveillant",
      task: "phishing",
      status: "READY",
      loaded: true,
      icon: "🛡️",
      path: "outputs/cysecbert-phishing",
    },
    {
      id: "phishsense",
      name: "Llama PhishSense (LoRA)",
      type: "lora",
      description: "Llama 1B + LoRA — analyse sémantique phishing",
      task: "phishing",
      status: "READY",
      loaded: true,
      icon: "🎣",
      path: "outputs/phishsense-targeted-lora",
    },
    {
      id: "qwen2_5_1_5b",
      name: "Qwen2.5-1.5B-Instruct",
      type: "llm",
      description: "LLM 1.5B — raisonnement, synthèse et décision SOC",
      task: "soc",
      status: "READY",
      loaded: true,
      icon: "🧠",
      path: "outputs/qwen2.5-1.5b",
    },
    {
      id: "smollm2_1_7b",
      name: "SmolLM2-1.7B-Instruct",
      type: "llm",
      description: "LLM 1.7B — synthèse rapide d'alertes et playbooks",
      task: "soc",
      status: "READY",
      loaded: true,
      icon: "⚡",
      path: "outputs/smollm2-1.7b",
    },
  ],
};

export const mockGpu: GpuStatus = {
  available: true,
  devices: [
    {
      index: 0,
      name: "NVIDIA GeForce RTX 3060",
      total_gb: 12.0,
      allocated_gb: 7.42,
      reserved_gb: 7.58,
      free_gb: 4.42,
      utilization_pct: 63.2,
    },
  ],
  loaded_models: ["cysecbert", "phishsense", "qwen2_5_1_5b", "smollm2_1_7b"],
  cuda_version: "12.1",
};

export const mockScripts: TestScriptsResponse = {
  scripts: [
    {
      name: "test_phishing_emails.txt",
      path: "tests/test_phishing_emails.txt",
      category: "Détection Phishing",
      size_bytes: 8421,
    },
    {
      name: "test_bert_robustness.txt",
      path: "tests/test_bert_robustness.txt",
      category: "Robustesse & Adversarial",
      size_bytes: 6210,
    },
    {
      name: "test_cyber_defense.txt",
      path: "tests/test_cyber_defense.txt",
      category: "Analyse SOC",
      size_bytes: 7980,
    },
  ],
};

/**
 * Génère une analyse multi-modèles simulée à partir d'un prompt.
 * Le verdict dépend de la présence de mots-clés suspects → démo crédible.
 */
export function mockPredictAll(prompt: string): PredictAllResponse {
  const suspicious = /urgent|password|verify|account|click|bank|suspend|prize|bitcoin|login/i.test(
    prompt
  );
  const verdict = suspicious ? "BLOCK" : "ACCEPT";
  const threat = suspicious ? 80 + Math.random() * 15 : 12 + Math.random() * 20;
  const score = Math.round(threat * 10) / 10;

  return {
    text_preview: prompt.slice(0, 120) + (prompt.length > 120 ? "…" : ""),
    timestamp: new Date().toISOString(),
    consensus: {
      verdict: suspicious ? "BLOCK" : "ACCEPT",
      block_votes: suspicious ? 3 : 0,
      accept_votes: suspicious ? 1 : 4,
      total_votes: 4,
      confidence_pct: suspicious ? 75 : 100,
    },
    results: mockModels.models.map((m, i) => ({
      model_id: m.id,
      model_name: m.name,
      model_type: m.type,
      elapsed_s: Math.round((0.05 + Math.random() * 1.4) * 100) / 100,
      icon: m.icon,
      predicted: true,
      prediction: verdict,
      threat_score: Math.max(
        0,
        Math.min(100, score + (i - 2) * 6 + (Math.random() * 8 - 4))
      ),
      verdict,
      type: m.type === "bert" ? "classification" : "generative",
      ...(m.type === "bert"
        ? {
            confidence: suspicious ? 0.82 + Math.random() * 0.15 : 0.9 + Math.random() * 0.09,
            probabilities: {
              "Phishing Email": suspicious ? 0.88 : 0.05,
              "Safe Email": suspicious ? 0.12 : 0.95,
            },
          }
        : { confidence: null }),
    })) as PredictAllResponse["results"],
  };
}
