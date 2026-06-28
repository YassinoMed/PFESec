#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
train_adaptive_pipeline.py

Pipeline adaptatif pour SecureRAG Hub.

Sous-commandes :
    holdout    : construit le holdout d'évaluation (Phase 0)
    baseline   : évalue les modèles non fine-tunés sur le holdout
    train      : entraîne les modèles sélectionnés (LoRA pour LLM, classif pour BERT)
    eval       : évalue les modèles entraînés sur le holdout
    decide     : génère un rapport de recommandation (qui garder, qui jeter)
    merge      : fusionne un adapter LoRA dans son base model (un seul fichier final)
    predict    : inférence rapide sur un modèle fusionné ou un classifier
    test       : tests d'inférence rapides sur les adapters

Philosophie :
    - Holdout d'évaluation construit AVANT tout entraînement
    - Early stopping basé sur eval split
    - Décisions go/no-go avec delta minimal vs baseline
    - Pas d'entraînement aveugle sur 10 datasets : datasets ciblés par tâche
"""

import os
import gc
import json
import argparse
import inspect
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime
from collections import Counter

import numpy as np
import torch

from datasets import load_dataset, Dataset, concatenate_datasets

from transformers import (
    AutoConfig,
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    EarlyStoppingCallback,
)

from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    PeftModel,
)

from sklearn.metrics import accuracy_score, precision_recall_fscore_support


# ============================================================
# Configuration
# ============================================================

BASE_DIR = Path(__file__).resolve().parent

DEFAULT_MODELS = {
    "phishsense": BASE_DIR / "models" / "Llama-Phishsense-1B",
    "cysecbert": BASE_DIR / "models" / "CySecBERT",
}

DEFAULT_OUTPUT_DIR = BASE_DIR / "outputs"
DEFAULT_HOLDOUT_DIR = BASE_DIR / "holdout"
DEFAULT_REPORTS_DIR = BASE_DIR / "reports"

# Catégorisation des datasets par tâche
DATASETS_BY_TASK = {
    "phishing": [
        {
            "name": "phishing_email_dataset",
            "dataset": "zefang-liu/phishing-email-dataset",
            "max_samples": 0,
            "type": "classification",
        },
    ],
    "cyber_general": [
        {
            "name": "local_cybersecurity_rules",
            "dataset": str(BASE_DIR / "datasets" / "cybersecurity-rules"),
            "max_samples": 0,
            "type": "sft",
        },
        {
            "name": "trendyol_cybersecurity_instruction",
            "dataset": "Trendyol/Trendyol-Cybersecurity-Instruction-Tuning-Dataset",
            "max_samples": 15000,
            "type": "sft",
        },
        {
            "name": "cybersecurity_32k_instruction",
            "dataset": "Vanessasml/cybersecurity_32k_instruction_input_output",
            "max_samples": 10000,
            "type": "sft",
        },
        {
            "name": "cybersecurity_sharegpt",
            "dataset": "ChaoticNeutrals/Cybersecurity-ShareGPT",
            "max_samples": 10000,
            "type": "sft",
        },
    ],
    "cve_analysis": [
        {
            "name": "cybersecurity_llm_cve",
            "dataset": "Bouquets/Cybersecurity-LLM-CVE",
            "max_samples": 10000,
            "type": "sft",
        },
        {
            "name": "cve_llm_training",
            "dataset": "morpheuslord/cve-llm-training",
            "max_samples": 10000,
            "type": "sft",
        },
    ],
    "eval_only": [
        {
            "name": "cybersecurity_eval",
            "dataset": "CyberNative/CyberSecurityEval",
            "max_samples": 1000,
            "type": "sft",
        },
    ],
}

MODEL_TASK_MAPPING = {
    "phishsense": ["phishing"],
    "cysecbert": ["phishing"],
}

MIN_IMPROVEMENT_DELTA = 0.03


# ============================================================
# Utilitaires
# ============================================================

def log(title: str):
    print("\n" + "=" * 100)
    print(title)
    print("=" * 100)


def set_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)


def cleanup_memory():
    gc.collect()
    if torch.cuda.is_available():
        torch.cuda.empty_cache()


def check_path(path: Path, name: str):
    if not path.exists():
        raise FileNotFoundError(f"{name} introuvable : {path}")


def make_training_args(**kwargs):
    """Compatibilité multi-versions transformers (eval_strategy vs evaluation_strategy)."""
    sig = inspect.signature(TrainingArguments.__init__)
    allowed = set(sig.parameters.keys())
    clean = {}
    for k, v in kwargs.items():
        if k in allowed:
            clean[k] = v
    if "evaluation_strategy" in kwargs and "eval_strategy" in allowed and "evaluation_strategy" not in allowed:
        clean["eval_strategy"] = kwargs["evaluation_strategy"]
    return TrainingArguments(**clean)


def reduce_dataset(ds: Dataset, max_samples: int = 0) -> Dataset:
    if max_samples and max_samples > 0 and len(ds) > max_samples:
        return ds.select(range(max_samples))
    return ds


def save_json(data: Any, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2, default=str)


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_str(x) -> str:
    if x is None:
        return ""
    return str(x).strip()


def detect_dtype():
    """BF16 si supporté, sinon FP16 si CUDA, sinon FP32."""
    if torch.cuda.is_available():
        try:
            if torch.cuda.is_bf16_supported():
                return torch.bfloat16, False, True  # dtype, use_fp16, use_bf16
        except Exception:
            pass
        return torch.float16, True, False
    return torch.float32, False, False


def enforce_gpu(allow_cpu: bool = False):
    """
    Vérifie qu'un GPU CUDA est disponible avant tout entraînement.
    Plante avec un message clair si non, sauf si allow_cpu=True.

    Active aussi les optimisations CUDA standard.
    """
    if allow_cpu:
        print("[INFO] Mode CPU autorisé (--allow-cpu).")
        return

    if not torch.cuda.is_available():
        msg = [
            "",
            "=" * 100,
            "[ERREUR] Aucun GPU CUDA disponible.",
            "=" * 100,
            "",
            "L'entraînement est forcé sur GPU pour des raisons de performance.",
            "Sur ce poste, torch.cuda.is_available() = False.",
            "",
            "Causes possibles :",
            "  1. Pas de GPU NVIDIA sur cette machine.",
            "  2. PyTorch installé en version CPU au lieu de CUDA.",
            "  3. Drivers NVIDIA / CUDA Toolkit non installés.",
            "",
            "Solutions :",
            "  - Vérifie : nvidia-smi (doit lister ta GPU)",
            "  - Vérifie torch CUDA : python -c \"import torch; print(torch.version.cuda)\"",
            "  - Réinstalle torch avec CUDA :",
            "      pip uninstall torch torchvision torchaudio",
            "      pip install torch --index-url https://download.pytorch.org/whl/cu121",
            "",
            "Pour entraîner quand même sur CPU (très lent, déconseillé pour LLM) :",
            "  Ajoute le flag --allow-cpu à ta commande.",
            "",
            "=" * 100,
        ]
        print("\n".join(msg))
        raise SystemExit(1)

    # GPU disponible : log et optimisations
    n_gpu = torch.cuda.device_count()
    gpu_name = torch.cuda.get_device_name(0)
    total_mem_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
    cuda_version = torch.version.cuda
    bf16_ok = False
    try:
        bf16_ok = torch.cuda.is_bf16_supported()
    except Exception:
        pass

    print("=" * 100)
    print("[GPU] CUDA disponible — entraînement forcé sur GPU.")
    print(f"      Devices         : {n_gpu}")
    print(f"      Device 0        : {gpu_name}")
    print(f"      VRAM            : {total_mem_gb:.1f} GB")
    print(f"      CUDA toolkit    : {cuda_version}")
    print(f"      BF16 supporté   : {bf16_ok}")
    print("=" * 100)

    # Optimisations CUDA standard
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
    torch.backends.cudnn.benchmark = True

    # Vide le cache au démarrage
    torch.cuda.empty_cache()


# ============================================================
# Chargement dataset local ou HF
# ============================================================

def load_local_or_hf_dataset(dataset_ref: str, split: str = "train") -> Dataset:
    path = Path(dataset_ref)
    if path.exists():
        if path.is_file():
            suffix = path.suffix.lower()
            files = [str(path)]
            if suffix in [".json", ".jsonl"]:
                return load_dataset("json", data_files=files, split=split)
            if suffix == ".csv":
                return load_dataset("csv", data_files=files, split=split)
            if suffix == ".parquet":
                return load_dataset("parquet", data_files=files, split=split)
            raise RuntimeError(f"Format fichier non supporté : {path}")

        for ext, fmt in [("*.jsonl", "json"), ("*.json", "json"),
                         ("*.csv", "csv"), ("*.parquet", "parquet")]:
            files = list(path.rglob(ext))
            if files:
                return load_dataset(fmt, data_files=[str(f) for f in files], split=split)

        raise RuntimeError(f"Aucun fichier dataset lisible trouvé dans : {path}")

    return load_dataset(dataset_ref, split=split)


# ============================================================
# Conversion SFT unifiée
# ============================================================

def row_to_unified_sft_text(row: Dict[str, Any]) -> str:
    """Convertit n'importe quelle ligne en format SFT unifié."""

    # 1. messages
    if "messages" in row and row["messages"]:
        try:
            parts = []
            for msg in row["messages"]:
                if isinstance(msg, dict):
                    role = safe_str(msg.get("role", "user")).upper()
                    content = safe_str(msg.get("content", ""))
                    if content:
                        parts.append(f"{role}:\n{content}")
            if parts:
                return "\n\n".join(parts)
        except Exception:
            pass

    # 2. system/user/assistant
    system = safe_str(row.get("system", ""))
    user = safe_str(row.get("user", ""))
    assistant = safe_str(row.get("assistant", ""))
    if user and assistant:
        if not system:
            system = "Tu es un assistant cybersécurité défensif."
        return f"### System:\n{system}\n\n### User:\n{user}\n\n### Assistant:\n{assistant}"

    # 3. instruction/input/output
    instruction = safe_str(row.get("instruction", ""))
    input_text = safe_str(row.get("input", ""))
    output = safe_str(row.get("output", ""))
    if instruction and output:
        user_content = instruction
        if input_text:
            user_content += "\n\nContexte :\n" + input_text
        return (
            "### System:\nTu es un assistant cybersécurité défensif.\n\n"
            f"### User:\n{user_content}\n\n### Assistant:\n{output}"
        )

    # 4. prompt/response
    prompt_keys = ["prompt", "Prompt", "query", "question", "Question", "problem"]
    answer_keys = ["response", "Response", "completion", "answer", "Answer", "solution"]
    prompt, answer = "", ""
    for k in prompt_keys:
        if k in row and safe_str(row.get(k)):
            prompt = safe_str(row.get(k))
            break
    for k in answer_keys:
        if k in row and safe_str(row.get(k)):
            answer = safe_str(row.get(k))
            break
    if prompt and answer:
        return (
            "### System:\nTu es un assistant cybersécurité défensif.\n\n"
            f"### User:\n{prompt}\n\n### Assistant:\n{answer}"
        )

    # 5. CVE-like
    cve_keys = ["cve", "CVE", "cve_id", "CVE_ID", "id"]
    desc_keys = ["description", "Description", "details", "summary"]
    cve_id, desc = "", ""
    for k in cve_keys:
        if k in row and safe_str(row.get(k)):
            cve_id = safe_str(row.get(k))
            break
    for k in desc_keys:
        if k in row and safe_str(row.get(k)):
            desc = safe_str(row.get(k))
            break
    if cve_id or desc:
        raw = "\n".join([f"{k}: {v}" for k, v in row.items() if v is not None])
        return (
            "### System:\nTu es un assistant cybersécurité défensif spécialisé en vulnérabilités.\n\n"
            "### User:\nAnalyse cette vulnérabilité et donne un résumé défensif.\n\n"
            f"{raw}\n\n### Assistant:\n"
        )

    # 6. texte/label phishing
    text_keys = ["text", "Email Text", "email", "body", "message", "content", "url", "text_combined"]
    label_keys = ["label", "Email Type", "class", "category", "is_phishing", "phishing"]
    text, label = "", ""
    for k in text_keys:
        if k in row and safe_str(row.get(k)):
            text = safe_str(row.get(k))
            break
    for k in label_keys:
        if k in row and row.get(k) is not None:
            label = safe_str(row.get(k))
            break
    if text:
        return (
            "### System:\nTu es un assistant défensif spécialisé en cybersécurité.\n\n"
            f"### User:\nAnalyse ce contenu et donne un verdict.\n\n{text}\n\n"
            f"### Assistant:\nLabel : {label}\n"
        )

    # 7. fallback
    raw = "\n".join([f"{k}: {v}" for k, v in row.items() if v is not None])
    return (
        "### System:\nTu es un assistant cybersécurité défensif.\n\n"
        f"### User:\nAnalyse :\n\n{raw}\n\n### Assistant:\n"
    )


def load_one_sft_dataset(
    dataset_ref: str,
    name: str,
    split: str = "train",
    max_samples: int = 0,
) -> Optional[Dataset]:
    print(f"\n[+] Chargement SFT : {name}")
    candidate_splits = [split, "train", "test", "validation", "val"]
    seen = set()
    ds = None
    for sp in candidate_splits:
        if sp in seen:
            continue
        seen.add(sp)
        try:
            ds = load_local_or_hf_dataset(str(dataset_ref), split=sp)
            if sp != split:
                print(f"    (fallback split={sp})")
            break
        except Exception as e:
            last_err = e
            continue
    if ds is None:
        print(f"[ERREUR] Ignoré : {name}")
        return None

    try:
        ds = reduce_dataset(ds, max_samples=max_samples)
        print(f"    Lignes : {len(ds)} | Colonnes : {ds.column_names}")
    except Exception as e:
        print(f"[ERREUR] Lecture impossible : {name} ({e})")
        return None

    def mapper(row):
        return {"text": row_to_unified_sft_text(row)}

    try:
        return ds.map(mapper, remove_columns=ds.column_names)
    except Exception as e:
        print(f"[ERREUR] Conversion SFT : {name} ({e})")
        return None


def load_datasets_for_tasks(
    tasks: List[str],
    split: str = "train",
    global_max_samples: int = 0,
) -> Dataset:
    """Charge uniquement les datasets liés aux tâches demandées."""
    datasets_list = []
    for task in tasks:
        if task not in DATASETS_BY_TASK:
            print(f"[WARN] Tâche inconnue : {task}")
            continue
        for cfg in DATASETS_BY_TASK[task]:
            if cfg.get("type") != "sft":
                continue
            ds = load_one_sft_dataset(
                dataset_ref=cfg["dataset"],
                name=cfg["name"],
                split=split,
                max_samples=cfg.get("max_samples", 0),
            )
            if ds is not None and len(ds) > 0:
                datasets_list.append(ds)

    if not datasets_list:
        raise RuntimeError(f"Aucun dataset SFT chargé pour les tâches : {tasks}")

    merged = concatenate_datasets(datasets_list).shuffle(seed=42)
    if global_max_samples > 0 and len(merged) > global_max_samples:
        merged = merged.select(range(global_max_samples))

    print(f"\n[OK] SFT fusionné : {len(merged)} lignes")
    return merged


# ============================================================
# Construction du holdout (Phase 0)
# ============================================================

def build_holdout(
    holdout_dir: Path,
    samples_per_dataset: int = 200,
    seed: int = 42,
):
    """
    Extrait un holdout AVANT tout entraînement.
    Robuste aux datasets sans split 'train' (essaye 'test', 'validation')
    et aux datasets cassés côté HF (skip propre).
    """
    log("CONSTRUCTION DU HOLDOUT")
    holdout_dir.mkdir(parents=True, exist_ok=True)

    candidate_splits = ["train", "test", "validation", "val"]

    for task, datasets in DATASETS_BY_TASK.items():
        task_dir = holdout_dir / task
        task_dir.mkdir(parents=True, exist_ok=True)

        for cfg in datasets:
            name = cfg["name"]
            ds = None
            used_split = None
            last_err = None

            for split in candidate_splits:
                try:
                    ds = load_local_or_hf_dataset(cfg["dataset"], split=split)
                    used_split = split
                    break
                except Exception as e:
                    last_err = e
                    continue

            if ds is None:
                print(f"[SKIP] {name} : impossible de charger ({last_err})")
                continue

            try:
                ds = ds.shuffle(seed=seed)
                n = min(samples_per_dataset, len(ds))
                holdout = ds.select(range(n))
                out_path = task_dir / f"{name}.jsonl"
                holdout.to_json(str(out_path), force_ascii=False)
                print(f"[OK] {task}/{name} : {n} exemples (split={used_split}) -> {out_path}")
            except Exception as e:
                print(f"[SKIP] {name} : erreur extraction ({e})")

    print(f"\n[OK] Holdout sauvegardé : {holdout_dir}")


# ============================================================
# Détection colonnes et normalisation labels
# ============================================================

def detect_text_label_columns(ds: Dataset) -> Tuple[Optional[str], Optional[str]]:
    """
    Détecte les colonnes texte/label par match exact insensible à la casse.
    Pas de match partiel : trop de faux positifs (ex: 'type' matche 'datatype').
    """
    cols = ds.column_names
    lower_map = {c.lower().strip(): c for c in cols}

    text_candidates = [
        "text", "email text", "email", "body", "message",
        "content", "url", "text_combined", "sentence", "input",
    ]
    label_candidates = [
        "label", "email type", "class", "category",
        "is_phishing", "phishing", "status", "target", "labels",
    ]

    def find_exact(candidates):
        for cand in candidates:
            key = cand.lower().strip()
            if key in lower_map:
                return lower_map[key]
        return None

    text_col = find_exact(text_candidates)
    label_col = find_exact(label_candidates)

    # Fallback si rien trouvé : inspection des features
    if text_col is None or label_col is None:
        try:
            features = ds.features
            for col in cols:
                feat_str = str(features[col]).lower()
                if text_col is None and "string" in feat_str:
                    text_col = col
                elif label_col is None and ("int" in feat_str or "bool" in feat_str or "classlabel" in feat_str):
                    label_col = col
        except Exception:
            pass

    return text_col, label_col


def normalize_labels(
    ds: Dataset,
    label_col: str,
    label2id: Optional[Dict[str, int]] = None,
    verbose: bool = False,
) -> Tuple[Dataset, Dict[str, int], Dict[int, str]]:
    """
    Normalise les labels en entiers contigus 0..N-1.
    Filtre les lignes avec label None/vide.
    """
    def _has_valid_label(row):
        v = row.get(label_col)
        return v is not None and str(v).strip() != ""

    ds = ds.filter(_has_valid_label)
    if len(ds) == 0:
        raise ValueError(f"Aucun label valide dans la colonne '{label_col}'")

    labels_raw = [str(x).strip() for x in ds[label_col]]

    if label2id is None:
        unique = sorted(list(set(labels_raw)))
        label2id = {label: i for i, label in enumerate(unique)}
    id2label = {i: label for label, i in label2id.items()}

    def mapper(row):
        row["labels"] = label2id[str(row[label_col]).strip()]
        return row

    ds = ds.map(mapper)

    if verbose:
        dist = Counter(labels_raw)
        print(f"    Distribution labels : {dict(dist)}")

    return ds, label2id, id2label


def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="weighted", zero_division=0
    )
    return {
        "accuracy": accuracy_score(labels, preds),
        "precision": precision,
        "recall": recall,
        "f1": f1,
    }


# ============================================================
# LoRA targets : priorité aux attention projections
# ============================================================

def infer_lora_targets(model) -> List[str]:
    """
    Détecte les modules LoRA. Priorise les projections d'attention sur les FC denses,
    qui sont plus sûres pour la majorité des architectures (Llama, Mistral, BERT, etc).
    """
    attention_proj = {"q_proj", "k_proj", "v_proj", "o_proj"}
    mlp_proj = {"gate_proj", "up_proj", "down_proj"}
    bert_like = {"query", "key", "value"}

    found = set()
    for name, module in model.named_modules():
        last = name.split(".")[-1]
        if last in attention_proj or last in mlp_proj or last in bert_like:
            found.add(last)

    # Si on a des proj d'attention typiques Llama/Mistral, on prend tout (attention + MLP)
    if attention_proj & found:
        targets = sorted(found & (attention_proj | mlp_proj))
        print(f"[+] Modules LoRA (Llama/Mistral-like) : {targets}")
        return targets

    # BERT-like
    if bert_like & found:
        targets = sorted(found & bert_like)
        print(f"[+] Modules LoRA (BERT-like) : {targets}")
        return targets

    raise RuntimeError(
        "Impossible de détecter des target_modules LoRA standards. "
        "Spécifie-les manuellement via la config."
    )


def tokenize_sft(ds: Dataset, tokenizer, max_length: int) -> Dataset:
    def mapper(row):
        encoded = tokenizer(
            row["text"], truncation=True, max_length=max_length, padding=False,
        )
        encoded["labels"] = encoded["input_ids"].copy()
        return encoded
    return ds.map(mapper, remove_columns=ds.column_names)


# ============================================================
# Entraînement LLM LoRA ciblé par tâche
# ============================================================

def train_llm_lora_for_tasks(
    model_path: Path,
    tasks: List[str],
    output_dir: Path,
    split: str,
    global_max_samples: int,
    epochs: float,
    batch_size: int,
    grad_accum: int,
    lr: float,
    max_length: int,
    save_steps: int,
    logging_steps: int,
    lora_r: int,
    lora_alpha: int,
    lora_dropout: float,
    skip_existing: bool,
    use_early_stopping: bool = True,
    eval_ratio: float = 0.1,
    allow_cpu: bool = False,
    dataset_start: float = 0.0,
    dataset_fraction: float = 1.0,
    dataset_slice: int = 0,
):
    log(f"ENTRAÎNEMENT LLM LoRA CIBLÉ : {model_path.name} | tâches : {tasks}")

    # GARDE-FOU : pas d'entraînement LLM sur CPU sans flag explicite
    enforce_gpu(allow_cpu=allow_cpu)

    check_path(model_path, f"Modèle {model_path.name}")

    if skip_existing and (output_dir / "adapter_config.json").exists():
        print(f"[SKIP] Adapter déjà présent : {output_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    print("[+] Tokenizer...")
    try:
        tokenizer = AutoTokenizer.from_pretrained(
            str(model_path), local_files_only=True, trust_remote_code=True,
        )
    except Exception:
        print("[WARN] Échec de chargement local_files_only=True. Essai avec local_files_only=False...")
        tokenizer = AutoTokenizer.from_pretrained(
            str(model_path), local_files_only=False, trust_remote_code=True,
        )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("[+] Modèle...")
    dtype, use_fp16, use_bf16 = detect_dtype()
    on_gpu = torch.cuda.is_available()
    try:
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            local_files_only=True,
            trust_remote_code=True,
            torch_dtype=dtype,
            device_map="auto" if on_gpu else None,
        )
    except Exception:
        print("[WARN] Échec de chargement local_files_only=True. Essai avec local_files_only=False...")
        model = AutoModelForCausalLM.from_pretrained(
            str(model_path),
            local_files_only=False,
            trust_remote_code=True,
            torch_dtype=dtype,
            device_map="auto" if on_gpu else None,
        )
    if not on_gpu:
        # Cas --allow-cpu uniquement
        model.to("cpu")
    model.config.use_cache = False
    if hasattr(model, "gradient_checkpointing_enable"):
        model.gradient_checkpointing_enable()

    target_modules = infer_lora_targets(model)
    lora_config = LoraConfig(
        r=lora_r,
        lora_alpha=lora_alpha,
        lora_dropout=lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
        target_modules=target_modules,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print(f"[+] Chargement datasets pour tâches : {tasks}")
    full_ds = load_datasets_for_tasks(tasks, split=split, global_max_samples=global_max_samples)

    if (0.0 < dataset_fraction < 1.0) or (dataset_start > 0.0):
        start_idx = int(len(full_ds) * dataset_start)
        n_samples = int(len(full_ds) * dataset_fraction)
        n_samples = max(1, n_samples)
        end_idx = min(len(full_ds), start_idx + n_samples)
        
        full_ds = full_ds.shuffle(seed=42).select(range(start_idx, end_idx))
        print(f"[+] Sélection dataset : début à {dataset_start:.1%}, taille {dataset_fraction:.1%} -> Sélection de {len(full_ds)} exemples (de {start_idx} à {end_idx})")

    if use_early_stopping and eval_ratio > 0 and len(full_ds) > 100:
        split_ds = full_ds.train_test_split(test_size=eval_ratio, seed=42)
        train_raw = split_ds["train"]
        eval_raw = split_ds["test"]
    else:
        train_raw = full_ds
        eval_raw = None

    print("[+] Tokenisation...")
    train_ds = tokenize_sft(train_raw, tokenizer, max_length)
    eval_ds = tokenize_sft(eval_raw, tokenizer, max_length) if eval_raw is not None else None

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    ta_kwargs = dict(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        gradient_accumulation_steps=grad_accum,
        learning_rate=lr,
        fp16=use_fp16,
        bf16=use_bf16,
        logging_steps=logging_steps,
        save_steps=save_steps,
        save_total_limit=2,
        report_to="none",
        optim="adamw_torch",
        warmup_ratio=0.03,
        lr_scheduler_type="cosine",
        remove_unused_columns=False,
    )

    callbacks = []
    if eval_ds is not None:
        ta_kwargs["evaluation_strategy"] = "steps"
        ta_kwargs["eval_steps"] = save_steps
        ta_kwargs["save_strategy"] = "steps"
        ta_kwargs["load_best_model_at_end"] = True
        ta_kwargs["metric_for_best_model"] = "eval_loss"
        ta_kwargs["greater_is_better"] = False
        if use_early_stopping:
            callbacks.append(EarlyStoppingCallback(early_stopping_patience=3))

    training_args = make_training_args(**ta_kwargs)

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        data_collator=data_collator,
        callbacks=callbacks,
    )

    print("[+] Entraînement...")
    trainer.train()

    print(f"[+] Sauvegarde : {output_dir}")
    model.save_pretrained(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    save_json({
        "base_model": str(model_path),
        "tasks": tasks,
        "epochs": epochs,
        "lora_r": lora_r,
        "lora_alpha": lora_alpha,
        "target_modules": target_modules,
        "trained_at": datetime.now().isoformat(),
    }, output_dir / "training_meta.json")

    del trainer, model, tokenizer
    cleanup_memory()
    print(f"[OK] LoRA terminé : {output_dir}")


# ============================================================
# Entraînement BERT classifier
# ============================================================

def train_bert_classifier_adaptive(
    model_path: Path,
    task: str,
    output_dir: Path,
    split: str,
    max_samples: int,
    epochs: float,
    batch_size: int,
    lr: float,
    max_length: int,
    logging_steps: int,
    skip_existing: bool,
    use_early_stopping: bool = True,
    allow_cpu: bool = False,
    dataset_start: float = 0.0,
    dataset_fraction: float = 1.0,
    dataset_slice: int = 0,
):
    log(f"ENTRAÎNEMENT BERT : {model_path.name} | tâche : {task}")

    # GARDE-FOU : pas d'entraînement sur CPU sans flag explicite
    enforce_gpu(allow_cpu=allow_cpu)

    check_path(model_path, f"Modèle {model_path.name}")
    if skip_existing and (output_dir / "config.json").exists():
        print(f"[SKIP] Classifier déjà présent : {output_dir}")
        return

    output_dir.mkdir(parents=True, exist_ok=True)

    classif_datasets = [c for c in DATASETS_BY_TASK.get(task, [])
                        if c.get("type") == "classification"]
    if not classif_datasets:
        print(f"[ERREUR] Aucun dataset de classification pour la tâche : {task}")
        return

    cfg = classif_datasets[0]
    print(f"[+] Dataset : {cfg['name']}")

    # Fallback split robuste
    ds = None
    for sp in [split, "train", "test", "validation"]:
        try:
            ds = load_local_or_hf_dataset(cfg["dataset"], split=sp)
            if sp != split:
                print(f"    (fallback split={sp})")
            break
        except Exception:
            continue
    if ds is None:
        raise RuntimeError(f"Impossible de charger {cfg['dataset']}")

    ds = reduce_dataset(ds, max_samples=max_samples)
    if (0.0 < dataset_fraction < 1.0) or (dataset_start > 0.0):
        start_idx = int(len(ds) * dataset_start)
        n_samples = int(len(ds) * dataset_fraction)
        n_samples = max(1, n_samples)
        end_idx = min(len(ds), start_idx + n_samples)
        
        ds = ds.shuffle(seed=42).select(range(start_idx, end_idx))
        print(f"[+] Sélection dataset : début à {dataset_start:.1%}, taille {dataset_fraction:.1%} -> Sélection de {len(ds)} exemples (de {start_idx} à {end_idx})")
    print(f"[+] Exemples : {len(ds)} | Colonnes : {ds.column_names}")

    text_col, label_col = detect_text_label_columns(ds)
    if not text_col or not label_col:
        raise ValueError(f"Colonnes texte/label non détectées : {ds.column_names}")
    print(f"[+] text_col={text_col} | label_col={label_col}")

    # Filtre textes vides
    def _has_valid_text(row):
        v = row.get(text_col)
        return v is not None and str(v).strip() != ""
    ds = ds.filter(_has_valid_text)

    ds, label2id, id2label = normalize_labels(ds, label_col, verbose=True)

    split_ds = ds.train_test_split(test_size=0.15, seed=42)
    train_ds, eval_ds = split_ds["train"], split_ds["test"]
    print(f"[+] Train : {len(train_ds)} | Eval : {len(eval_ds)} | Labels : {label2id}")

    try:
        tokenizer = AutoTokenizer.from_pretrained(
            str(model_path), local_files_only=True, trust_remote_code=True,
        )
    except Exception:
        print("[WARN] Échec de chargement local_files_only=True. Essai avec local_files_only=False...")
        tokenizer = AutoTokenizer.from_pretrained(
            str(model_path), local_files_only=False, trust_remote_code=True,
        )

    def tok(batch):
        text_data = batch[text_col]
        if not isinstance(text_data, list):
            text_data = list(text_data)
        text_data = [str(t) if t is not None else "" for t in text_data]
        return tokenizer(text_data, truncation=True,
                         padding="max_length", max_length=max_length)

    train_ds = train_ds.map(tok, batched=True)
    eval_ds = eval_ds.map(tok, batched=True)
    keep = ["input_ids", "attention_mask", "labels"]
    train_ds = train_ds.remove_columns([c for c in train_ds.column_names if c not in keep])
    eval_ds = eval_ds.remove_columns([c for c in eval_ds.column_names if c not in keep])

    try:
        model = AutoModelForSequenceClassification.from_pretrained(
            str(model_path),
            local_files_only=True,
            trust_remote_code=True,
            num_labels=len(label2id),
            label2id=label2id,
            id2label=id2label,
            ignore_mismatched_sizes=True,
        )
    except Exception:
        print("[WARN] Échec de chargement local_files_only=True. Essai avec local_files_only=False...")
        model = AutoModelForSequenceClassification.from_pretrained(
            str(model_path),
            local_files_only=False,
            trust_remote_code=True,
            num_labels=len(label2id),
            label2id=label2id,
            id2label=id2label,
            ignore_mismatched_sizes=True,
        )

    _, use_fp16, _ = detect_dtype()

    training_args = make_training_args(
        output_dir=str(output_dir),
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        learning_rate=lr,
        fp16=use_fp16,
        logging_steps=logging_steps,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        save_total_limit=2,
        report_to="none",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
    )

    callbacks = []
    if use_early_stopping:
        callbacks.append(EarlyStoppingCallback(early_stopping_patience=2))

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        compute_metrics=compute_metrics,
        callbacks=callbacks,
    )

    print("[+] Entraînement...")
    trainer.train()
    metrics = trainer.evaluate()
    print(f"[METRICS] {metrics}")

    trainer.save_model(str(output_dir))
    tokenizer.save_pretrained(str(output_dir))

    save_json({
        "base_model": str(model_path),
        "task": task,
        "dataset": cfg["name"],
        "label2id": label2id,
        "id2label": id2label,
        "text_col": text_col,
        "label_col": label_col,
        "metrics": metrics,
        "trained_at": datetime.now().isoformat(),
    }, output_dir / "training_meta.json")

    del trainer, model, tokenizer
    cleanup_memory()
    print(f"[OK] BERT terminé : {output_dir}")


# ============================================================
# Évaluation BERT (baseline et post-training)
# ============================================================

def evaluate_bert_on_holdout(
    model_path: Path,
    holdout_jsonl: Path,
    max_length: int = 256,
    batch_size: int = 16,
    expect_classification_head: bool = True,
) -> Dict[str, Any]:
    """
    Évalue un BERT classifier sur un holdout.

    Si le checkpoint n'a PAS de tête de classification (cas de CySecBERT/SecBERT
    publiés en MaskedLM), la tête est initialisée aléatoirement et le score est
    du bruit. On le détecte et on retourne un warning.
    """
    if not holdout_jsonl.exists():
        return {"error": f"Holdout introuvable : {holdout_jsonl}"}

    try:
        ds = load_dataset("json", data_files=str(holdout_jsonl), split="train")
    except Exception as e:
        return {"error": f"Lecture holdout échouée : {e}"}

    text_col, label_col = detect_text_label_columns(ds)
    if not text_col or not label_col:
        return {"error": f"Colonnes texte/label non détectées. Colonnes : {ds.column_names}"}

    # Filtre textes vides
    def _has_valid_text(row):
        v = row.get(text_col)
        return v is not None and str(v).strip() != ""

    ds = ds.filter(_has_valid_text)
    if len(ds) == 0:
        return {"error": "Aucun texte valide dans le holdout"}

    try:
        ds, label2id, _ = normalize_labels(ds, label_col, verbose=True)
    except ValueError as e:
        return {"error": str(e)}

    # Détection tête classifier réelle
    has_real_classifier_head = False
    try:
        cfg = AutoConfig.from_pretrained(str(model_path), local_files_only=True, trust_remote_code=True)
        arch = (cfg.architectures or [""])[0].lower()
        if "sequenceclassification" in arch or "classification" in arch:
            has_real_classifier_head = True
    except Exception:
        pass

    # Tokenizer : essayer fast d'abord, puis slow en fallback,
    # puis renvoyer une erreur propre si vraiment impossible
    tokenizer = None
    tok_err = None
    for use_fast in (True, False):
        try:
            tokenizer = AutoTokenizer.from_pretrained(
                str(model_path),
                local_files_only=True,
                trust_remote_code=True,
                use_fast=use_fast,
            )
            break
        except Exception as e:
            tok_err = e
            continue
    if tokenizer is None:
        msg = str(tok_err)
        if "sentencepiece" in msg.lower() or "tiktoken" in msg.lower():
            msg += " — Installe : pip install sentencepiece protobuf"
        return {"error": f"Tokenizer non chargeable : {msg}"}

    try:
        model = AutoModelForSequenceClassification.from_pretrained(
            str(model_path),
            local_files_only=True,
            trust_remote_code=True,
            num_labels=len(label2id),
            ignore_mismatched_sizes=True,
        )
    except Exception as e:
        return {"error": f"Chargement modèle échoué : {e}"}

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device).eval()

    # Extraction explicite en list Python (évite les types PyArrow chunks)
    all_texts = [str(t) if t is not None else "" for t in ds[text_col]]
    all_labels = [int(l) for l in ds["labels"]]

    preds: List[int] = []
    n = len(all_texts)
    for i in range(0, n, batch_size):
        batch_texts = all_texts[i:i + batch_size]
        inputs = tokenizer(
            batch_texts,
            truncation=True,
            padding=True,
            max_length=max_length,
            return_tensors="pt",
        )
        inputs = {k: v.to(device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = model(**inputs).logits
        batch_preds = torch.argmax(logits, dim=-1).cpu().numpy().tolist()
        if not isinstance(batch_preds, list):
            batch_preds = [batch_preds]
        preds.extend(int(p) for p in batch_preds)

    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, preds, average="weighted", zero_division=0
    )

    del model, tokenizer
    cleanup_memory()

    result = {
        "accuracy": float(accuracy_score(all_labels, preds)),
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "n_samples": len(all_labels),
        "n_labels": len(label2id),
        "label2id": label2id,
    }

    if expect_classification_head and not has_real_classifier_head:
        result["warning"] = (
            "Tête de classification absente du checkpoint (modèle pré-entraîné en MaskedLM). "
            "Le score baseline est du bruit aléatoire et NE doit PAS servir de référence."
        )
        result["baseline_meaningful"] = False
    else:
        result["baseline_meaningful"] = True

    return result


def run_baseline_evaluation(
    holdout_dir: Path,
    reports_dir: Path,
    models: Dict[str, Path],
):
    """Phase 0 : évalue tous les modèles non fine-tunés."""
    log("PHASE 0 — ÉVALUATION BASELINE (modèles non fine-tunés)")
    reports_dir.mkdir(parents=True, exist_ok=True)

    report = {"timestamp": datetime.now().isoformat(), "scores": {}}

    phishing_holdouts = sorted((holdout_dir / "phishing").glob("*.jsonl"))
    if not phishing_holdouts:
        print(f"[WARN] Aucun holdout phishing trouvé dans {holdout_dir / 'phishing'}")
        print("       Lance d'abord : python train_adaptive_pipeline.py holdout")

    for model_name in ["cysecbert"]:
        if model_name not in models or not models[model_name].exists():
            print(f"[SKIP] {model_name} : modèle introuvable")
            continue
        report["scores"][model_name] = {}
        for h in phishing_holdouts:
            print(f"\n[+] Baseline {model_name} sur {h.name}...")
            metrics = evaluate_bert_on_holdout(models[model_name], h)
            report["scores"][model_name][h.stem] = metrics
            if "error" in metrics:
                print(f"    [ERREUR] {metrics['error']}")
            elif metrics.get("baseline_meaningful") is False:
                print(f"    [WARN] {metrics.get('warning', '')}")
                print(f"    Score (indicatif uniquement) : F1={metrics.get('f1', 0):.4f}")
            else:
                print(f"    → F1={metrics['f1']:.4f} | Acc={metrics['accuracy']:.4f} | n={metrics['n_samples']}")

    for model_name in ["phishsense"]:
        if model_name not in models or not models[model_name].exists():
            print(f"[SKIP] {model_name} : modèle introuvable")
            continue
        report["scores"][model_name] = {
            "note": "Évaluation générative non automatisée — voir 'test' pour inférence manuelle.",
            "available": True,
        }

    report_path = reports_dir / f"baseline_{datetime.now():%Y%m%d_%H%M%S}.json"
    save_json(report, report_path)
    print(f"\n[OK] Rapport baseline : {report_path}")
    return report


# ============================================================
# Merge LoRA → base model
# ============================================================

def merge_lora_into_base(
    base_model: Path,
    adapter_dir: Path,
    merged_output: Path,
):
    """Fusionne l'adapter LoRA dans le modèle de base → un seul fichier final."""
    log(f"MERGE LoRA -> BASE : {adapter_dir.name}")

    check_path(base_model, "Base model")
    check_path(adapter_dir, "Adapter")
    merged_output.mkdir(parents=True, exist_ok=True)

    print("[+] Chargement base...")
    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    base = AutoModelForCausalLM.from_pretrained(
        str(base_model),
        local_files_only=True,
        trust_remote_code=True,
        torch_dtype=dtype,
        device_map="auto" if torch.cuda.is_available() else None,
    )

    print("[+] Chargement adapter...")
    model = PeftModel.from_pretrained(base, str(adapter_dir))

    print("[+] Fusion (merge_and_unload)...")
    merged = model.merge_and_unload()

    print(f"[+] Sauvegarde fusionnée : {merged_output}")
    merged.save_pretrained(str(merged_output), safe_serialization=True)

    tokenizer = AutoTokenizer.from_pretrained(
        str(base_model), local_files_only=True, trust_remote_code=True,
    )
    tokenizer.save_pretrained(str(merged_output))

    del merged, model, base, tokenizer
    cleanup_memory()
    print(f"[OK] Modèle fusionné prêt à servir : {merged_output}")


# ============================================================
# Tests d'inférence
# ============================================================

def test_lora_adapter(base_model: Path, adapter_dir: Path, prompt: str, max_new_tokens: int = 250):
    log(f"TEST LoRA : {adapter_dir.name}")
    if not adapter_dir.exists():
        print(f"[SKIP] : {adapter_dir}")
        return

    tokenizer = AutoTokenizer.from_pretrained(str(base_model), local_files_only=True, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    base = AutoModelForCausalLM.from_pretrained(
        str(base_model), local_files_only=True, trust_remote_code=True,
        torch_dtype=dtype, device_map="auto" if torch.cuda.is_available() else None,
    )
    model = PeftModel.from_pretrained(base, str(adapter_dir)).eval()

    full = f"### System:\nTu es un assistant cybersécurité défensif.\n\n### User:\n{prompt}\n\n### Assistant:\n"
    inputs = tokenizer(full, return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        out = model.generate(
            **inputs, max_new_tokens=max_new_tokens,
            temperature=0.2, do_sample=True, pad_token_id=tokenizer.eos_token_id,
        )
    print(tokenizer.decode(out[0], skip_special_tokens=True))

    del model, base, tokenizer
    cleanup_memory()


def test_bert_classifier(model_dir: Path, text: str):
    log(f"TEST BERT : {model_dir.name}")
    if not model_dir.exists():
        print(f"[SKIP] : {model_dir}")
        return

    tokenizer = AutoTokenizer.from_pretrained(str(model_dir))
    model = AutoModelForSequenceClassification.from_pretrained(str(model_dir)).eval()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True, max_length=256)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    with torch.no_grad():
        probs = torch.softmax(model(**inputs).logits, dim=-1)[0].cpu().numpy()

    for idx, p in enumerate(probs):
        print(f"  {model.config.id2label[idx]}: {p:.4f}")

    del model, tokenizer
    cleanup_memory()


# ============================================================
# Inférence directe sur un modèle fusionné
# ============================================================

def predict_with_merged_llm(merged_model_path: Path, prompt: str, max_new_tokens: int = 300):
    log(f"PREDICT LLM (merged) : {merged_model_path.name}")
    check_path(merged_model_path, "Modèle fusionné")

    tokenizer = AutoTokenizer.from_pretrained(str(merged_model_path), local_files_only=True, trust_remote_code=True)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    dtype = torch.float16 if torch.cuda.is_available() else torch.float32
    model = AutoModelForCausalLM.from_pretrained(
        str(merged_model_path), local_files_only=True, trust_remote_code=True,
        torch_dtype=dtype, device_map="auto" if torch.cuda.is_available() else None,
    ).eval()

    full = f"### System:\nTu es un assistant cybersécurité défensif.\n\n### User:\n{prompt}\n\n### Assistant:\n"
    inputs = tokenizer(full, return_tensors="pt")
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        out = model.generate(
            **inputs, max_new_tokens=max_new_tokens,
            temperature=0.2, do_sample=True, pad_token_id=tokenizer.eos_token_id,
        )
    print(tokenizer.decode(out[0], skip_special_tokens=True))

    del model, tokenizer
    cleanup_memory()


# ============================================================
# Rapport de décision
# ============================================================

def generate_decision_report(
    reports_dir: Path,
    output_path: Path,
    min_delta: float = MIN_IMPROVEMENT_DELTA,
):
    """Compare baseline vs post-fine-tuning, recommande qui garder."""
    log("RAPPORT DE DÉCISION")

    baseline_files = sorted(reports_dir.glob("baseline_*.json"))
    finetuned_files = sorted(reports_dir.glob("finetuned_*.json"))

    if not baseline_files:
        print("[ERREUR] Aucun rapport baseline trouvé. Lance 'baseline' d'abord.")
        return

    baseline = load_json(baseline_files[-1])
    finetuned = load_json(finetuned_files[-1]) if finetuned_files else None

    recommendations = {}
    for model_name, scores in baseline["scores"].items():
        rec = {"baseline": scores, "decision": "unknown"}

        # Cas spécial : baseline non significatif (BERT sans tête)
        baseline_invalid = False
        if isinstance(scores, dict):
            for v in scores.values():
                if isinstance(v, dict) and v.get("baseline_meaningful") is False:
                    baseline_invalid = True
                    break

        if finetuned and model_name in finetuned.get("scores", {}):
            ft = finetuned["scores"][model_name]
            rec["finetuned"] = ft

            if baseline_invalid:
                # Pas de comparaison possible : on garde le finetuned par défaut
                # mais on alerte
                rec["decision"] = "KEEP_FINETUNED_BASELINE_INVALID"
                rec["note"] = "Baseline = bruit aléatoire (modèle pré-entraîné sans tête classif). Fine-tuning obligatoire."
            elif isinstance(scores, dict) and any(
                isinstance(v, dict) and "f1" in v for v in scores.values()
            ):
                baseline_f1 = np.mean([
                    v["f1"] for v in scores.values()
                    if isinstance(v, dict) and "f1" in v
                ])
                ft_f1 = np.mean([
                    v["f1"] for v in ft.values()
                    if isinstance(v, dict) and "f1" in v
                ])
                delta = ft_f1 - baseline_f1
                rec["baseline_f1_mean"] = float(baseline_f1)
                rec["finetuned_f1_mean"] = float(ft_f1)
                rec["delta_f1"] = float(delta)
                rec["decision"] = "KEEP_FINETUNED" if delta >= min_delta else "KEEP_BASELINE"
            else:
                rec["decision"] = "MANUAL_REVIEW"
        else:
            rec["decision"] = "NO_FINETUNED_AVAILABLE"

        recommendations[model_name] = rec

    save_json({
        "timestamp": datetime.now().isoformat(),
        "min_delta_required": min_delta,
        "baseline_report": str(baseline_files[-1]),
        "finetuned_report": str(finetuned_files[-1]) if finetuned_files else None,
        "recommendations": recommendations,
    }, output_path)

    print(f"\n[OK] Rapport décision : {output_path}\n")
    for name, rec in recommendations.items():
        line = f"  {name:15s} -> {rec['decision']}"
        if "delta_f1" in rec:
            line += f"  (Δ F1 = {rec['delta_f1']:+.4f})"
        print(line)


# ============================================================
# Commandes CLI
# ============================================================

def cmd_holdout(args):
    build_holdout(
        holdout_dir=Path(args.holdout_dir),
        samples_per_dataset=args.samples_per_dataset,
        seed=args.seed,
    )


def cmd_baseline(args):
    models = {
        "phishsense": Path(args.phish_model),
        "cysecbert": Path(args.cysecbert_model),
    }
    run_baseline_evaluation(
        holdout_dir=Path(args.holdout_dir),
        reports_dir=Path(args.reports_dir),
        models=models,
    )


def cmd_train(args):
    set_seed(args.seed)

    # Pré-vérification GPU AVANT toute opération coûteuse (chargement datasets, etc.)
    enforce_gpu(allow_cpu=args.allow_cpu)

    models = {
        "phishsense": Path(args.phish_model),
        "cysecbert": Path(args.cysecbert_model),
    }
    outputs = {
        "phishsense": Path(args.output_dir) / "phishsense-targeted-lora",
        "cysecbert": Path(args.output_dir) / "cysecbert-phishing",
    }

    selected = ["phishsense", "cysecbert"] if args.train == "all" else [args.train]
    print(f"[+] Sélection : {selected}")

    for name in selected:
        if name == "phishsense":
            tasks = MODEL_TASK_MAPPING[name]
            train_llm_lora_for_tasks(
                model_path=models[name],
                tasks=tasks,
                output_dir=outputs[name],
                split=args.split,
                global_max_samples=args.max_samples,
                epochs=args.llm_epochs,
                batch_size=args.llm_batch_size,
                grad_accum=args.grad_accum,
                lr=args.llm_lr,
                max_length=args.llm_max_length,
                save_steps=args.save_steps,
                logging_steps=args.logging_steps,
                lora_r=args.lora_r,
                lora_alpha=args.lora_alpha,
                lora_dropout=args.lora_dropout,
                skip_existing=args.skip_existing,
                use_early_stopping=args.early_stopping,
                allow_cpu=args.allow_cpu,
                dataset_start=args.dataset_start,
                dataset_fraction=args.dataset_fraction,
                dataset_slice=args.dataset_slice,
            )
        elif name == "cysecbert":
            train_bert_classifier_adaptive(
                model_path=models[name],
                task="phishing",
                output_dir=outputs[name],
                split=args.split,
                max_samples=args.bert_max_samples,
                epochs=args.bert_epochs,
                batch_size=args.bert_batch_size,
                lr=args.bert_lr,
                max_length=args.bert_max_length,
                logging_steps=args.logging_steps,
                skip_existing=args.skip_existing,
                use_early_stopping=args.early_stopping,
                allow_cpu=args.allow_cpu,
                dataset_start=args.dataset_start,
                dataset_fraction=args.dataset_fraction,
                dataset_slice=args.dataset_slice,
            )

    print("\n[OK] Entraînement terminé.")


def cmd_merge(args):
    models = {
        "phishsense": (Path(args.phish_model), Path(args.output_dir) / "phishsense-targeted-lora"),
    }
    selected = ["phishsense"] if args.target == "all" else [args.target]
    for name in selected:
        base, adapter = models[name]
        merged_out = Path(args.output_dir) / f"{name}-merged"
        if adapter.exists():
            merge_lora_into_base(base, adapter, merged_out)
        else:
            print(f"[SKIP] Adapter manquant : {adapter}")


def _is_trained_bert_classifier(path: Path) -> bool:
    """
    Vérifie qu'un dossier contient bien un classifier BERT entraîné et sauvegardé.
    Exige : config.json + un fichier de poids (pytorch_model.bin ou model.safetensors)
    + un tokenizer (vocab.txt / tokenizer.json / tokenizer_config.json).
    """
    if not path.exists() or not path.is_dir():
        return False
    if not (path / "config.json").exists():
        return False
    has_weights = any([
        (path / "pytorch_model.bin").exists(),
        (path / "model.safetensors").exists(),
    ])
    if not has_weights:
        # Peut être en sharded ; check pattern
        has_weights = any(path.glob("pytorch_model-*.bin")) or any(path.glob("model-*.safetensors"))
    if not has_weights:
        return False
    has_tokenizer = any([
        (path / "tokenizer.json").exists(),
        (path / "tokenizer_config.json").exists(),
        (path / "vocab.txt").exists(),
        (path / "spiece.model").exists(),
    ])
    return has_tokenizer


def cmd_eval(args):
    log("ÉVALUATION POST-ENTRAÎNEMENT")
    reports_dir = Path(args.reports_dir)
    reports_dir.mkdir(parents=True, exist_ok=True)

    outputs = {
        "cysecbert": Path(args.output_dir) / "cysecbert-phishing",
    }

    report = {"timestamp": datetime.now().isoformat(), "scores": {}}
    phishing_holdouts = sorted((Path(args.holdout_dir) / "phishing").glob("*.jsonl"))

    if not phishing_holdouts:
        print(f"[ERREUR] Aucun holdout phishing trouvé dans {Path(args.holdout_dir) / 'phishing'}")
        print("        Lance d'abord : python train_adaptive_pipeline.py holdout")
        return

    n_evaluated = 0
    for name, path in outputs.items():
        # Vérification stricte : modèle réellement entraîné et complet
        if not _is_trained_bert_classifier(path):
            print(f"[SKIP] {name} : pas de modèle entraîné valide à {path}")
            print(f"        (lance d'abord : python train_adaptive_pipeline.py train --train {name})")
            continue

        report["scores"][name] = {}
        n_evaluated += 1
        for h in phishing_holdouts:
            print(f"\n[+] Éval {name} sur {h.name}...")
            try:
                metrics = evaluate_bert_on_holdout(path, h, expect_classification_head=True)
            except Exception as e:
                metrics = {"error": f"Crash inattendu : {type(e).__name__}: {e}"}

            report["scores"][name][h.stem] = metrics
            if "error" in metrics:
                print(f"    [ERREUR] {metrics['error']}")
            else:
                print(f"    -> F1={metrics['f1']:.4f} | Acc={metrics['accuracy']:.4f} | n={metrics['n_samples']}")

    if n_evaluated == 0:
        print("\n[INFO] Aucun modèle entraîné disponible pour l'évaluation.")
        print("       Lance d'abord 'train' (sur GPU ou avec --allow-cpu).")
        return

    out = reports_dir / f"finetuned_{datetime.now():%Y%m%d_%H%M%S}.json"
    save_json(report, out)
    print(f"\n[OK] Rapport : {out}")


def cmd_decide(args):
    generate_decision_report(
        reports_dir=Path(args.reports_dir),
        output_path=Path(args.reports_dir) / f"decision_{datetime.now():%Y%m%d_%H%M%S}.json",
        min_delta=args.min_delta,
    )


def cmd_test(args):
    outputs = {
        "phishsense": Path(args.output_dir) / "phishsense-targeted-lora",
        "cysecbert": Path(args.output_dir) / "cysecbert-phishing",
    }
    test_lora_adapter(
        Path(args.phish_model), outputs["phishsense"],
        "Analyse cet email : Votre compte sera suspendu, cliquez ici.",
    )
    test_bert_classifier(outputs["cysecbert"],
                         "Your account will be suspended. Click here to verify.")


def cmd_predict(args):
    """Inférence sur un modèle fusionné ou un classifier BERT."""
    model_path = Path(args.model)
    if not model_path.exists():
        print(f"[ERREUR] Modèle introuvable : {model_path}")
        return

    # Heuristique : si c'est un BERT classifier, on lit le label_mapping
    config_path = model_path / "config.json"
    if config_path.exists():
        cfg = load_json(config_path)
        arch = (cfg.get("architectures") or [""])[0].lower()
        if "sequenceclassification" in arch:
            test_bert_classifier(model_path, args.prompt)
            return

    # Sinon, traité comme un LLM merged
    predict_with_merged_llm(model_path, args.prompt, max_new_tokens=args.max_new_tokens)


# ============================================================
# Main
# ============================================================

def build_parser():
    p = argparse.ArgumentParser(description="Pipeline adaptatif SecureRAG Hub")
    sub = p.add_subparsers(dest="cmd", required=True)

    def add_common(sp):
        sp.add_argument("--security-model", default=str(DEFAULT_MODELS["securityllm"]))
        sp.add_argument("--phish-model", default=str(DEFAULT_MODELS["phishsense"]))
        sp.add_argument("--cysecbert-model", default=str(DEFAULT_MODELS["cysecbert"]))
        sp.add_argument("--secbert-model", default=str(DEFAULT_MODELS["secbert"]))
        sp.add_argument("--output-dir", default=str(DEFAULT_OUTPUT_DIR))
        sp.add_argument("--holdout-dir", default=str(DEFAULT_HOLDOUT_DIR))
        sp.add_argument("--reports-dir", default=str(DEFAULT_REPORTS_DIR))
        sp.add_argument("--seed", type=int, default=42)

    # holdout
    ph = sub.add_parser("holdout", help="Phase 0 : construire le holdout")
    add_common(ph)
    ph.add_argument("--samples-per-dataset", type=int, default=200)
    ph.set_defaults(func=cmd_holdout)

    # baseline
    pb = sub.add_parser("baseline", help="Phase 0 : évaluer modèles non fine-tunés")
    add_common(pb)
    pb.set_defaults(func=cmd_baseline)

    # train
    pt = sub.add_parser("train", help="Phase 2 : entraînement ciblé (GPU forcé par défaut)")
    add_common(pt)
    pt.add_argument("--train", default="all",
                    choices=["all", "securityllm", "phishsense", "cysecbert", "secbert"])
    pt.add_argument("--skip-existing", action="store_true")
    pt.add_argument("--early-stopping", action="store_true", default=True)
    pt.add_argument("--no-early-stopping", dest="early_stopping", action="store_false")
    pt.add_argument("--allow-cpu", action="store_true",
                    help="Autorise l'entraînement sur CPU (très lent, déconseillé pour les LLM).")
    pt.add_argument("--split", default="train")
    pt.add_argument("--max-samples", type=int, default=0)
    pt.add_argument("--bert-max-samples", type=int, default=0)
    pt.add_argument("--llm-epochs", type=float, default=3.0)
    pt.add_argument("--llm-batch-size", type=int, default=1)
    pt.add_argument("--grad-accum", type=int, default=8)
    pt.add_argument("--llm-lr", type=float, default=2e-4)
    pt.add_argument("--llm-max-length", type=int, default=1024)
    pt.add_argument("--lora-r", type=int, default=16)
    pt.add_argument("--lora-alpha", type=int, default=32)
    pt.add_argument("--lora-dropout", type=float, default=0.05)
    pt.add_argument("--bert-epochs", type=float, default=3.0)
    pt.add_argument("--bert-batch-size", type=int, default=8)
    pt.add_argument("--bert-lr", type=float, default=2e-5)
    pt.add_argument("--bert-max-length", type=int, default=256)
    pt.add_argument("--logging-steps", type=int, default=10)
    pt.add_argument("--save-steps", type=int, default=200)
    pt.add_argument("--dataset-start", type=float, default=0.0,
                    help="Offset de début pour la sélection du dataset (ex: 0.20 pour commencer à 20%%)")
    pt.add_argument("--dataset-fraction", type=float, default=1.0,
                    help="Fraction du dataset à utiliser pour l'entraînement (ex: 0.20 pour 20%%)")
    pt.add_argument("--dataset-slice", type=int, default=0,
                    help="Index de la tranche de dataset à utiliser (ex: 1 pour la tranche suivante)")
    pt.set_defaults(func=cmd_train)

    # eval
    pe = sub.add_parser("eval", help="Évaluer les modèles entraînés sur holdout")
    add_common(pe)
    pe.set_defaults(func=cmd_eval)

    # decide
    pd = sub.add_parser("decide", help="Phase 4 : rapport de décision")
    add_common(pd)
    pd.add_argument("--min-delta", type=float, default=MIN_IMPROVEMENT_DELTA)
    pd.set_defaults(func=cmd_decide)

    # merge
    pm = sub.add_parser("merge", help="Phase 3 : fusionner LoRA → modèle final")
    add_common(pm)
    pm.add_argument("--target", default="all", choices=["all", "securityllm", "phishsense"])
    pm.set_defaults(func=cmd_merge)

    # test
    pts = sub.add_parser("test", help="Tests d'inférence sur adapters LoRA et classifiers")
    add_common(pts)
    pts.set_defaults(func=cmd_test)

    # predict
    pp = sub.add_parser("predict", help="Inférence rapide sur un modèle (auto: LLM merged ou BERT classifier)")
    add_common(pp)
    pp.add_argument("--model", required=True, help="Chemin vers le modèle (merged LLM ou BERT classifier)")
    pp.add_argument("--prompt", required=True, help="Texte d'entrée")
    pp.add_argument("--max-new-tokens", type=int, default=300)
    pp.set_defaults(func=cmd_predict)

    return p


def main():
    parser = build_parser()
    args = parser.parse_args()
    Path(args.output_dir).mkdir(parents=True, exist_ok=True)
    Path(args.reports_dir).mkdir(parents=True, exist_ok=True)
    args.func(args)


if __name__ == "__main__":
    main()