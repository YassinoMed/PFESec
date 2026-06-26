import os
import argparse
from pathlib import Path

import torch
from huggingface_hub import snapshot_download
from transformers import AutoTokenizer, AutoModel, AutoModelForCausalLM
from datasets import load_dataset


BASE_DIR = Path(__file__).resolve().parent
MODELS_DIR = BASE_DIR / "models"
DATASETS_DIR = BASE_DIR / "datasets"


REPOS = {
    "SecurityLLM": {
        "repo_id": "ZySec-AI/SecurityLLM",
        "repo_type": "model",
        "local_dir": MODELS_DIR / "SecurityLLM",
        "kind": "causal_lm",
    },
    "Llama-Phishsense-1B": {
        "repo_id": "AcuteShrewdSecurity/Llama-Phishsense-1B",
        "repo_type": "model",
        "local_dir": MODELS_DIR / "Llama-Phishsense-1B",
        "kind": "causal_lm",
    },
    "CySecBERT": {
        "repo_id": "markusbayer/CySecBERT",
        "repo_type": "model",
        "local_dir": MODELS_DIR / "CySecBERT",
        "kind": "bert",
    },
    "SecBERT": {
        "repo_id": "jackaduma/SecBERT",
        "repo_type": "model",
        "local_dir": MODELS_DIR / "SecBERT",
        "kind": "bert",
    },
    "cybersecurity-rules": {
        "repo_id": "jcordon5/cybersecurity-rules",
        "repo_type": "dataset",
        "local_dir": DATASETS_DIR / "cybersecurity-rules",
        "kind": "dataset",
    },
}


def download_all():
    MODELS_DIR.mkdir(exist_ok=True)
    DATASETS_DIR.mkdir(exist_ok=True)

    for name, item in REPOS.items():
        print(f"\n[+] Téléchargement : {name}")
        print(f"    Repo   : {item['repo_id']}")
        print(f"    Dossier: {item['local_dir']}")

        snapshot_download(
            repo_id=item["repo_id"],
            repo_type=item["repo_type"],
            local_dir=str(item["local_dir"]),
            resume_download=True,
        )

        print(f"[OK] {name} téléchargé.")


def check_files():
    print("\n[+] Vérification des fichiers locaux")

    for name, item in REPOS.items():
        path = item["local_dir"]

        print(f"\n--- {name} ---")
        print(f"Dossier : {path}")

        if not path.exists():
            print("[ERREUR] Dossier introuvable.")
            continue

        files = list(path.glob("*"))

        if not files:
            print("[ERREUR] Dossier vide.")
            continue

        for file in files[:20]:
            print(" ", file.name)

        if item["kind"] in ["causal_lm", "bert"]:
            config = path / "config.json"
            if config.exists():
                print("[OK] config.json trouvé.")
            else:
                print("[ATTENTION] config.json absent.")

        print("[OK] Vérification terminée.")


def set_offline_mode():
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"
    os.environ["HF_DATASETS_OFFLINE"] = "1"


def test_causal_lm(name, path, prompt):
    print(f"\n[+] Test modèle génératif : {name}")

    tokenizer = AutoTokenizer.from_pretrained(
        str(path),
        local_files_only=True,
        trust_remote_code=True,
    )

    dtype = torch.float16 if torch.cuda.is_available() else torch.float32

    model = AutoModelForCausalLM.from_pretrained(
        str(path),
        local_files_only=True,
        trust_remote_code=True,
        torch_dtype=dtype,
        device_map="auto" if torch.cuda.is_available() else None,
    )

    if not torch.cuda.is_available():
        model.to("cpu")

    inputs = tokenizer(prompt, return_tensors="pt", truncation=True)

    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        output = model.generate(
            **inputs,
            max_new_tokens=120,
            temperature=0.2,
            do_sample=True,
            pad_token_id=tokenizer.eos_token_id,
        )

    text = tokenizer.decode(output[0], skip_special_tokens=True)

    print("\n===== SORTIE MODÈLE =====")
    print(text)
    print("=========================")


def test_bert(name, path):
    print(f"\n[+] Test BERT : {name}")

    tokenizer = AutoTokenizer.from_pretrained(
        str(path),
        local_files_only=True,
        trust_remote_code=True,
    )

    model = AutoModel.from_pretrained(
        str(path),
        local_files_only=True,
        trust_remote_code=True,
    )

    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)
    model.eval()

    text = "Suspicious PowerShell encoded command execution detected."

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512,
    )

    inputs = {k: v.to(device) for k, v in inputs.items()}

    with torch.no_grad():
        outputs = model(**inputs)

    embedding = outputs.last_hidden_state[:, 0, :]

    print("[OK] Modèle chargé.")
    print("Texte :", text)
    print("Shape embedding :", tuple(embedding.shape))


def find_dataset_files(path):
    parquet_files = list(path.rglob("*.parquet"))
    json_files = list(path.rglob("*.json")) + list(path.rglob("*.jsonl"))
    csv_files = list(path.rglob("*.csv"))

    if parquet_files:
        return "parquet", [str(f) for f in parquet_files]
    if json_files:
        return "json", [str(f) for f in json_files]
    if csv_files:
        return "csv", [str(f) for f in csv_files]

    return None, []


def test_dataset(path):
    print("\n[+] Test dataset cybersecurity-rules")

    dataset_type, files = find_dataset_files(path)

    if dataset_type is None:
        print("[ERREUR] Aucun fichier parquet/json/jsonl/csv trouvé.")
        print("Fichiers présents :")
        for f in list(path.rglob("*"))[:30]:
            print(" ", f)
        return

    print(f"[OK] Type détecté : {dataset_type}")
    print(f"[OK] Nombre de fichiers : {len(files)}")

    ds = load_dataset(dataset_type, data_files=files, split="train")

    print("[OK] Dataset chargé.")
    print("Nombre de lignes :", len(ds))

    print("\n===== PREMIÈRE LIGNE =====")
    print(ds[0])
    print("==========================")


def test_all():
    set_offline_mode()

    check_files()

    # Test SecurityLLM
    test_causal_lm(
        "SecurityLLM",
        REPOS["SecurityLLM"]["local_dir"],
        "Tu es un analyste SOC. Donne une procédure défensive pour analyser une alerte SSH brute force.",
    )

    # Test Llama-Phishsense-1B
    test_causal_lm(
        "Llama-Phishsense-1B",
        REPOS["Llama-Phishsense-1B"]["local_dir"],
        "Analyse ce message pour phishing : Votre compte sera suspendu. Cliquez ici pour confirmer votre mot de passe.",
    )

    # Test CySecBERT
    test_bert(
        "CySecBERT",
        REPOS["CySecBERT"]["local_dir"],
    )

    # Test SecBERT
    test_bert(
        "SecBERT",
        REPOS["SecBERT"]["local_dir"],
    )

    # Test dataset
    test_dataset(
        REPOS["cybersecurity-rules"]["local_dir"],
    )


def test_one(name):
    set_offline_mode()

    if name not in REPOS:
        print("[ERREUR] Nom inconnu.")
        print("Noms possibles :", ", ".join(REPOS.keys()))
        return

    item = REPOS[name]

    if item["kind"] == "causal_lm":
        test_causal_lm(
            name,
            item["local_dir"],
            "Donne une analyse cybersécurité défensive courte.",
        )

    elif item["kind"] == "bert":
        test_bert(name, item["local_dir"])

    elif item["kind"] == "dataset":
        test_dataset(item["local_dir"])


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--download",
        action="store_true",
        help="Télécharger tous les modèles et datasets en local.",
    )

    parser.add_argument(
        "--check",
        action="store_true",
        help="Vérifier les fichiers téléchargés.",
    )

    parser.add_argument(
        "--test-all",
        action="store_true",
        help="Tester tous les modèles localement.",
    )

    parser.add_argument(
        "--test-one",
        type=str,
        help="Tester un seul modèle : SecurityLLM, Llama-Phishsense-1B, CySecBERT, SecBERT, cybersecurity-rules",
    )

    args = parser.parse_args()

    if args.download:
        download_all()

    if args.check:
        check_files()

    if args.test_all:
        test_all()

    if args.test_one:
        test_one(args.test_one)

    if not any([args.download, args.check, args.test_all, args.test_one]):
        parser.print_help()


if __name__ == "__main__":
    main()