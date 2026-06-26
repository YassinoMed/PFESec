#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
test_runner.py — Exécuteur automatisé de tests pour les modèles de sécurité SecureRAG Hub.

Lit un fichier .txt de tests, exécute chaque test sur le modèle spécifié,
et génère un rapport JSON + console avec les résultats (pass/fail, métriques).

Usage :
    python test_runner.py --test-file tests/test_phishing_emails.txt --model cysecbert --report
    python test_runner.py --test-file tests/test_bert_robustness.txt --model secbert --report
    python test_runner.py --test-file tests/test_cyber_defense.txt --model securityllm
    python test_runner.py --test-file tests/test_phishing_emails.txt --model phishsense
"""

import os
import re
import json
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

import torch
import numpy as np

os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

BASE_DIR = Path(__file__).resolve().parent

MODEL_PATHS = {
    "cysecbert": BASE_DIR / "outputs" / "cysecbert-phishing",
    "secbert": BASE_DIR / "outputs" / "secbert-phishing",
    "securityllm": BASE_DIR / "outputs" / "securityllm-targeted-lora",
    "securityllm-merged": BASE_DIR / "outputs" / "securityllm-merged",
    "phishsense": BASE_DIR / "outputs" / "phishsense-targeted-lora",
    "phishsense-merged": BASE_DIR / "outputs" / "phishsense-merged",
}

BASE_MODELS = {
    "securityllm": BASE_DIR / "models" / "SecurityLLM",
    "phishsense": BASE_DIR / "models" / "Llama-Phishsense-1B",
}


# ============================================================
# Parsing du fichier de test
# ============================================================

def parse_test_file(filepath: Path) -> List[Dict[str, Any]]:
    """Parse un fichier .txt de tests structuré."""
    tests = []
    content = filepath.read_text(encoding="utf-8")

    # Pattern pour capturer les blocs de test
    # Format : [TEST-ID] Description\n---\nCONTENU\n---\nMETADATA
    blocks = re.split(r'\n\[TEST-', content)

    for block in blocks[1:]:  # Skip header
        test = {}

        # Extraire l'ID
        id_match = re.match(r'([A-Z]+-\d+)\]\s*(.*)', block)
        if not id_match:
            continue

        test["id"] = f"TEST-{id_match.group(1)}"
        test["title"] = id_match.group(2).strip()

        # Extraire le contenu entre ---
        content_match = re.search(r'---\n(.*?)\n---', block, re.DOTALL)
        if content_match:
            raw_content = content_match.group(1).strip()

            # Déterminer si c'est un PROMPT ou un EMAIL
            if raw_content.startswith("PROMPT:"):
                test["type"] = "generative"
                test["text"] = raw_content[7:].strip()
            elif raw_content.startswith("TEXT:"):
                test["type"] = "classification"
                test["text"] = raw_content[5:].strip()
            elif "Subject:" in raw_content:
                test["type"] = "classification"
                test["text"] = raw_content
            else:
                test["type"] = "generative"
                test["text"] = raw_content

        # Extraire le label attendu
        label_match = re.search(r'LABEL_ATTENDU:\s*(.+)', block)
        if label_match:
            test["expected_label"] = label_match.group(1).strip()

        # Extraire le type de test
        type_match = re.search(r'TYPE:\s*(.+)', block)
        if type_match:
            test["test_type"] = type_match.group(1).strip()

        # Extraire la réponse attendue
        resp_match = re.search(r'RÉPONSE_ATTENDUE:\s*(.+)', block)
        if resp_match:
            test["expected_keywords"] = resp_match.group(1).strip()

        if "text" in test:
            tests.append(test)

    # Parser aussi les tests BATCH (format compact)
    batch_blocks = re.findall(
        r'\[TEST-(BATCH-\d+)\]\s*\nTEXT:\s*(.+?)\nLABEL_ATTENDU:\s*(.+)',
        content
    )
    for bid, text, label in batch_blocks:
        # Éviter les doublons
        test_id = f"TEST-{bid}"
        if not any(t["id"] == test_id for t in tests):
            tests.append({
                "id": test_id,
                "title": f"Batch test {bid}",
                "type": "classification",
                "text": text.strip(),
                "expected_label": label.strip(),
                "test_type": "batch",
            })

    return tests


# ============================================================
# Inférence BERT Classifier
# ============================================================

def load_bert_classifier(model_path: Path):
    """Charge un classifier BERT fine-tuné."""
    from transformers import AutoTokenizer, AutoModelForSequenceClassification

    print(f"[+] Chargement classifier BERT : {model_path.name}")

    tokenizer = AutoTokenizer.from_pretrained(
        str(model_path), local_files_only=True, trust_remote_code=True,
    )
    model = AutoModelForSequenceClassification.from_pretrained(
        str(model_path), local_files_only=True, trust_remote_code=True,
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()

    # Charger le mapping de labels
    label_mapping = None
    mapping_path = model_path / "label_mapping.json"
    if mapping_path.exists():
        with open(mapping_path, "r") as f:
            label_mapping = json.load(f)
    else:
        # Fallback : lire depuis config.json
        config_path = model_path / "config.json"
        if config_path.exists():
            with open(config_path, "r") as f:
                cfg = json.load(f)
            if "id2label" in cfg:
                label_mapping = cfg["id2label"]

    return tokenizer, model, device, label_mapping


def predict_bert(tokenizer, model, device, text: str, label_mapping=None) -> Dict[str, Any]:
    """Inférence sur un classifier BERT."""
    inputs = tokenizer(
        text, return_tensors="pt", truncation=True,
        padding=True, max_length=512,
    )
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    logits = outputs.logits
    probs = torch.softmax(logits, dim=-1)[0]
    pred_idx = torch.argmax(probs).item()
    confidence = probs[pred_idx].item()

    label = str(pred_idx)
    if label_mapping:
        if isinstance(label_mapping, dict):
            label = label_mapping.get(str(pred_idx), str(pred_idx))

    all_probs = {
        (label_mapping.get(str(i), str(i)) if label_mapping else str(i)): round(p.item(), 4)
        for i, p in enumerate(probs)
    }

    return {
        "predicted_label": label,
        "confidence": round(confidence, 4),
        "all_probabilities": all_probs,
    }


# ============================================================
# Inférence LLM (LoRA ou Merged)
# ============================================================

def load_llm(model_name: str):
    """Charge un LLM (merged ou base+adapter)."""
    from transformers import AutoTokenizer, AutoModelForCausalLM

    model_path = MODEL_PATHS.get(model_name)
    if model_path is None or not model_path.exists():
        # Essayer la version merged
        merged_name = f"{model_name}-merged"
        model_path = MODEL_PATHS.get(merged_name)

    if model_path is None or not model_path.exists():
        raise FileNotFoundError(f"Modèle introuvable : {model_name}")

    print(f"[+] Chargement LLM : {model_path}")

    # Vérifier si c'est un adapter LoRA ou un modèle complet
    is_adapter = (model_path / "adapter_config.json").exists()

    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    device_map = "auto" if torch.cuda.is_available() else None

    def load_base_model(path: Path):
        try:
            return AutoModelForCausalLM.from_pretrained(
                str(path), local_files_only=True, trust_remote_code=True,
                torch_dtype=dtype, device_map=device_map,
            )
        except Exception as e:
            print(f"[WARN] Chargement avec device_map={device_map} a échoué ({e}). Fallback sans device_map...")
            m = AutoModelForCausalLM.from_pretrained(
                str(path), local_files_only=True, trust_remote_code=True,
                torch_dtype=dtype,
            )
            if torch.cuda.is_available():
                try:
                    m = m.to("cuda")
                except Exception as cuda_err:
                    print(f"[WARN] Impossible de déplacer sur GPU : {cuda_err}")
            return m

    if is_adapter:
        from peft import PeftModel

        base_name = model_name.replace("-merged", "")
        base_path = BASE_MODELS.get(base_name)
        if base_path is None or not base_path.exists():
            raise FileNotFoundError(f"Base model introuvable pour {model_name}")

        print(f"    Base model : {base_path}")
        tokenizer = AutoTokenizer.from_pretrained(
            str(base_path), local_files_only=True, trust_remote_code=True,
        )
        model = load_base_model(base_path)
        model = PeftModel.from_pretrained(model, str(model_path))
        model.eval()
    else:
        tokenizer = AutoTokenizer.from_pretrained(
            str(model_path), local_files_only=True, trust_remote_code=True,
        )
        model = load_base_model(model_path)
        model.eval()

    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    return tokenizer, model


def predict_llm(tokenizer, model, text: str, max_new_tokens: int = 300) -> Dict[str, Any]:
    """Inférence générative sur un LLM."""
    device = next(model.parameters()).device
    inputs = tokenizer(text, return_tensors="pt", truncation=True, max_length=1024)
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            temperature=0.3,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
            repetition_penalty=1.2,
        )

    generated = tokenizer.decode(output[0], skip_special_tokens=True)

    # Supprimer le prompt du début de la réponse
    if generated.startswith(text):
        generated = generated[len(text):].strip()

    return {
        "generated_text": generated,
        "input_tokens": len(inputs["input_ids"][0]),
        "output_tokens": len(output[0]),
    }


# ============================================================
# Exécution des tests
# ============================================================

def run_tests(
    tests: List[Dict[str, Any]],
    model_name: str,
    generate_report: bool = False,
) -> Dict[str, Any]:
    """Exécute tous les tests et retourne les résultats."""

    results = {
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "total_tests": len(tests),
        "passed": 0,
        "failed": 0,
        "errors": 0,
        "accuracy": 0.0,
        "test_results": [],
    }

    # Déterminer le type de modèle
    is_bert = model_name in ["cysecbert", "secbert"]

    if is_bert:
        model_path = MODEL_PATHS[model_name]
        if not model_path.exists():
            print(f"[ERREUR] Modèle introuvable : {model_path}")
            return results

        tokenizer, model, device, label_mapping = load_bert_classifier(model_path)
    else:
        tokenizer, model = load_llm(model_name)

    print(f"\n{'='*80}")
    print(f"  EXÉCUTION DES TESTS — {model_name.upper()}")
    print(f"  {len(tests)} tests à exécuter")
    print(f"{'='*80}\n")

    for i, test in enumerate(tests):
        test_result = {
            "id": test["id"],
            "title": test.get("title", ""),
            "status": "unknown",
        }

        try:
            print(f"[{i+1}/{len(tests)}] {test['id']} — {test.get('title', '')[:60]}")

            if is_bert:
                prediction = predict_bert(tokenizer, model, device, test["text"], label_mapping)
                test_result["prediction"] = prediction

                # Vérifier le résultat
                if "expected_label" in test:
                    expected = test["expected_label"].strip().lower()
                    predicted = prediction["predicted_label"].strip().lower()

                    # Mapping flexible
                    phishing_labels = {"phishing email", "phishing", "1", "unsafe"}
                    safe_labels = {"safe email", "safe", "0", "legitimate", "ham"}

                    expected_is_phishing = expected in phishing_labels
                    predicted_is_phishing = predicted in phishing_labels

                    if expected_is_phishing == predicted_is_phishing:
                        test_result["status"] = "PASS"
                        results["passed"] += 1
                    else:
                        test_result["status"] = "FAIL"
                        results["failed"] += 1

                    test_result["expected"] = test["expected_label"]
                    print(f"  → Prédit: {prediction['predicted_label']} "
                          f"(conf: {prediction['confidence']:.1%}) | "
                          f"Attendu: {test['expected_label']} | "
                          f"{'✓ PASS' if test_result['status'] == 'PASS' else '✗ FAIL'}")
                else:
                    test_result["status"] = "INFO"
                    print(f"  → Prédit: {prediction['predicted_label']} "
                          f"(conf: {prediction['confidence']:.1%})")

            else:
                # LLM génératif
                prediction = predict_llm(tokenizer, model, test["text"])
                test_result["prediction"] = {
                    "generated_text": prediction["generated_text"][:500],
                    "input_tokens": prediction["input_tokens"],
                    "output_tokens": prediction["output_tokens"],
                }
                test_result["status"] = "GENERATED"
                print(f"  → Réponse ({prediction['output_tokens']} tokens) :")
                print(f"    {prediction['generated_text'][:200]}...")

        except Exception as e:
            test_result["status"] = "ERROR"
            test_result["error"] = str(e)
            results["errors"] += 1
            print(f"  → ERREUR: {e}")

        results["test_results"].append(test_result)
        print()

    # Calculer l'accuracy globale
    n_evaluated = results["passed"] + results["failed"]
    if n_evaluated > 0:
        results["accuracy"] = round(results["passed"] / n_evaluated, 4)

    # Résumé
    print(f"\n{'='*80}")
    print(f"  RÉSUMÉ — {model_name.upper()}")
    print(f"{'='*80}")
    print(f"  Total tests     : {results['total_tests']}")
    print(f"  Réussis (PASS)  : {results['passed']}")
    print(f"  Échoués (FAIL)  : {results['failed']}")
    print(f"  Erreurs         : {results['errors']}")
    if n_evaluated > 0:
        print(f"  Accuracy        : {results['accuracy']:.1%}")
    print(f"{'='*80}\n")

    # Sauvegarder le rapport
    if generate_report:
        reports_dir = BASE_DIR / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        report_path = reports_dir / f"test_report_{model_name}_{datetime.now():%Y%m%d_%H%M%S}.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(results, f, ensure_ascii=False, indent=2, default=str)
        print(f"[OK] Rapport sauvegardé : {report_path}")

    return results


# ============================================================
# Main
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="Exécuteur automatisé de tests pour les modèles de sécurité"
    )
    parser.add_argument(
        "--test-file", required=True,
        help="Fichier .txt contenant les tests"
    )
    parser.add_argument(
        "--model", required=True,
        choices=["cysecbert", "secbert", "securityllm", "securityllm-merged",
                 "phishsense", "phishsense-merged"],
        help="Modèle à tester"
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Générer un rapport JSON"
    )
    parser.add_argument(
        "--max-tests", type=int, default=0,
        help="Nombre maximum de tests à exécuter (0 = tous)"
    )
    parser.add_argument(
        "--filter-id", type=str, default="",
        help="Filtrer par ID de test (ex: PHISH, SOC, ADV)"
    )

    args = parser.parse_args()

    test_file = Path(args.test_file)
    if not test_file.is_absolute():
        test_file = BASE_DIR / test_file

    if not test_file.exists():
        print(f"[ERREUR] Fichier de test introuvable : {test_file}")
        sys.exit(1)

    tests = parse_test_file(test_file)
    print(f"[OK] {len(tests)} tests chargés depuis {test_file.name}")

    # Filtrer si demandé
    if args.filter_id:
        tests = [t for t in tests if args.filter_id.upper() in t["id"].upper()]
        print(f"[OK] {len(tests)} tests après filtre '{args.filter_id}'")

    # Limiter si demandé
    if args.max_tests > 0:
        tests = tests[:args.max_tests]
        print(f"[OK] Limité à {len(tests)} tests")

    if not tests:
        print("[ERREUR] Aucun test à exécuter.")
        sys.exit(1)

    run_tests(tests, args.model, generate_report=args.report)


if __name__ == "__main__":
    main()
