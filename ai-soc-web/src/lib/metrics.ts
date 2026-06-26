/**
 * lib/metrics.ts — Calcule precision/recall/F1/confusion matrix côté client.
 *
 * Le backend (test_runner.py) ne fournit QUE l'accuracy. Pour enrichir le
 * tableau de bord SOC, on dérive ces métriques depuis `test_results[]` :
 *  - On ne garde que les cas évaluables (BERT, status PASS/FAIL).
 *  - On compare prediction.predicted_label vs expected.
 *  - La "catégorie" est extraite du préfixe de l'id (PHISH, SAFE, ADV…).
 */

import type {
  ComputedMetrics,
  ConfusionCell,
  TestReport,
  TestResultItem,
} from "@/types/api";

/** Extrait la catégorie depuis un id de test : "TEST-PHISH-001" → "PHISH". */
export function categoryFromId(id: string): string {
  const m = id.match(/TEST-([A-Z]+)-\d+/i);
  return m ? m[1].toUpperCase() : "AUTRE";
}

/** Vrai label positif = contenu dans predicted_label ? (insensible à la casse). */
function isPhishLabel(label: string): boolean {
  const l = label.toLowerCase();
  return l.includes("phish") || l.includes("malicious") || l.includes("spam");
}

/**
 * Calcule le jeu complet de métriques depuis un rapport de test.
 * Renvoie des zéros si aucune prédiction BERT évaluable n'est présente
 * (cas des modèles génératifs purs).
 */
export function computeMetrics(report: TestReport): ComputedMetrics {
  const evaluable: TestResultItem[] = report.test_results.filter(
    (t) =>
      t.status === "PASS" ||
      (t.status === "FAIL" &&
        t.prediction &&
        "predicted_label" in t.prediction &&
        t.expected !== undefined)
  );

  const labelsSet = new Set<string>();
  const confusionMap = new Map<string, number>();
  const perCat = new Map<
    string,
    { total: number; passed: number; failed: number }
  >();

  let tp = 0; // phishing correctement détecté
  let fp = 0; // safe classé phishing
  let fn = 0; // phishing classé safe
  let tn = 0; // safe correctement classé

  for (const t of evaluable) {
    const pred = (t.prediction as { predicted_label?: string })
      ?.predicted_label;
    if (!pred || t.expected === undefined) continue;

    const expectedPhish = isPhishLabel(t.expected);
    const predictedPhish = isPhishLabel(pred);

    labelsSet.add(t.expected);
    labelsSet.add(pred);

    const key = `${t.expected}__${pred}`;
    confusionMap.set(key, (confusionMap.get(key) ?? 0) + 1);

    const cat = categoryFromId(t.id);
    const c = perCat.get(cat) ?? { total: 0, passed: 0, failed: 0 };
    c.total += 1;
    if (t.status === "PASS") c.passed += 1;
    else c.failed += 1;
    perCat.set(cat, c);

    if (expectedPhish && predictedPhish) tp += 1;
    else if (!expectedPhish && predictedPhish) fp += 1;
    else if (expectedPhish && !predictedPhish) fn += 1;
    else tn += 1;
  }

  const precision = tp + fp > 0 ? tp / (tp + fp) : 0;
  const recall = tp + fn > 0 ? tp / (tp + fn) : 0;
  const f1 = precision + recall > 0 ? (2 * precision * recall) / (precision + recall) : 0;

  const confusion: ConfusionCell[] = Array.from(confusionMap.entries()).map(
    ([k, count]) => {
      const [expected, predicted] = k.split("__");
      return { expected, predicted, count };
    }
  );

  const perCategory = Array.from(perCat.entries()).map(([category, c]) => ({
    category,
    total: c.total,
    passed: c.passed,
    failed: c.failed,
    accuracy: c.total > 0 ? c.passed / c.total : 0,
  }));

  return {
    accuracy: report.accuracy,
    precision: round4(precision),
    recall: round4(recall),
    f1: round4(f1),
    confusion,
    perCategory,
    evaluated: evaluable.length,
    labels: Array.from(labelsSet),
  };
}

function round4(n: number): number {
  return Math.round(n * 10000) / 10000;
}

/** Formate un 0..1 en pourcentage lisible. */
export function pct(n: number): string {
  return `${(n * 100).toFixed(1)}%`;
}
