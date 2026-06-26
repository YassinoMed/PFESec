#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
web_server.py — Serveur HTTP minimal pour l'interface de test des modèles de sécurité.
Fournit une API REST pour lister les modèles, exécuter des inférences et lancer des scripts de test.
Aucune dépendance externe requise (standard library uniquement).
"""

import os
import json
import subprocess
import urllib.parse
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re

# Activer le mode offline de HuggingFace
os.environ["HF_HUB_OFFLINE"] = "1"
os.environ["TRANSFORMERS_OFFLINE"] = "1"

BASE_DIR = Path(__file__).resolve().parent
PORT = 8000
VENV_PYTHON = BASE_DIR.parent / "myenv" / "Scripts" / "python.exe"
PYTHON_EXE = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable

class SecurityTestHandler(BaseHTTPRequestHandler):
    def end_headers(self):
        # Autoriser CORS pour le dev local
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def do_GET(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # Rediriger la racine vers index.html
        if path == "/" or path == "":
            self.serve_file(BASE_DIR / "web" / "index.html", "text/html")
            return

        # Serveur de fichiers statiques pour le dossier "web"
        if path.startswith("/web/"):
            file_path = BASE_DIR / path.lstrip("/")
            if file_path.exists() and file_path.is_file():
                content_type = self.get_content_type(file_path)
                self.serve_file(file_path, content_type)
            else:
                self.send_error_response(404, "Fichier statique introuvable")
            return

        # --- ENDPOINT API: Liste des modèles ---
        if path == "/api/models":
            self.handle_list_models()
            return

        # --- ENDPOINT API: Liste des scripts de test ---
        if path == "/api/test-scripts":
            self.handle_list_test_scripts()
            return

        # --- ENDPOINT API: Lire un script de test ---
        if path == "/api/test-scripts/view":
            query = urllib.parse.parse_qs(parsed_url.query)
            script_name = query.get("name", [None])[0]
            if script_name:
                self.handle_view_test_script(script_name)
            else:
                self.send_error_response(400, "Paramètre 'name' requis")
            return

        # Fallback aux autres fichiers ou 404
        # Si index.html n'est pas préfixé par /web/ mais directement accessible
        fallback_file = BASE_DIR / "web" / path.lstrip("/")
        if fallback_file.exists() and fallback_file.is_file() and not path.startswith("/api/"):
            content_type = self.get_content_type(fallback_file)
            self.serve_file(fallback_file, content_type)
            return

        self.send_error_response(404, "API non trouvée")

    def do_POST(self):
        parsed_url = urllib.parse.urlparse(self.path)
        path = parsed_url.path

        # Lire le corps de la requête
        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length)
        
        try:
            body = json.loads(post_data.decode('utf-8')) if post_data else {}
        except Exception:
            self.send_error_response(400, "JSON invalide")
            return

        # --- ENDPOINT API: Prédire (Inférence mono-exemple) ---
        if path == "/api/predict":
            self.handle_predict(body)
            return

        # --- ENDPOINT API: Lancer un test unitaire ou global ---
        if path == "/api/run-tests":
            self.handle_run_tests(body)
            return

        self.send_error_response(404, "Action non trouvée")

    # ============================================================
    # Handlers d'API
    # ============================================================

    def handle_list_models(self):
        """Récupère les modèles locaux disponibles et leur statut."""
        outputs_dir = BASE_DIR / "outputs"
        models_dir = BASE_DIR / "models"

        models = [
            {
                "id": "cysecbert",
                "name": "CySecBERT Classifier",
                "type": "BERT (Classification)",
                "path": str(outputs_dir / "cysecbert-phishing"),
                "base_path": str(models_dir / "CySecBERT"),
                "status": "READY" if (outputs_dir / "cysecbert-phishing" / "config.json").exists() else "NOT_TRAINED",
                "description": "Modèle BERT fine-tuné sur la détection d'emails de phishing et malveillants."
            },
            {
                "id": "secbert",
                "name": "SecBERT Classifier",
                "type": "BERT (Classification)",
                "path": str(outputs_dir / "secbert-phishing"),
                "base_path": str(models_dir / "SecBERT"),
                "status": "READY" if (outputs_dir / "secbert-phishing" / "config.json").exists() else "NOT_TRAINED",
                "description": "Modèle SecBERT adapté à la cybersécurité, orienté classification de phishing."
            },
            {
                "id": "phishsense-merged",
                "name": "Llama Phishsense (Merged)",
                "type": "LLM (Inférence)",
                "path": str(outputs_dir / "phishsense-merged"),
                "base_path": str(models_dir / "Llama-Phishsense-1B"),
                "status": "READY" if (outputs_dir / "phishsense-merged" / "config.json").exists() else "NOT_MERGED",
                "description": "Llama 1B avec LoRA fusionné, spécialisé dans l'analyse sémantique du phishing."
            },
            {
                "id": "securityllm-merged",
                "name": "SecurityLLM (Merged)",
                "type": "LLM (Inférence)",
                "path": str(outputs_dir / "securityllm-merged"),
                "base_path": str(models_dir / "SecurityLLM"),
                "status": "READY" if (outputs_dir / "securityllm-merged" / "config.json").exists() else "NOT_MERGED",
                "description": "Modèle SecurityLLM 7B fusionné, assistant d'analyse SOC et règles de détection."
            },
            {
                "id": "phishsense",
                "name": "Llama Phishsense (LoRA Adapter)",
                "type": "LLM + LoRA",
                "path": str(outputs_dir / "phishsense-targeted-lora"),
                "base_path": str(models_dir / "Llama-Phishsense-1B"),
                "status": "READY" if (outputs_dir / "phishsense-targeted-lora" / "adapter_config.json").exists() else "NOT_TRAINED",
                "description": "Adapter LoRA léger pour la détection de phishing sur base Llama-Phishsense-1B."
            },
            {
                "id": "securityllm",
                "name": "SecurityLLM (LoRA Adapter)",
                "type": "LLM + LoRA",
                "path": str(outputs_dir / "securityllm-targeted-lora"),
                "base_path": str(models_dir / "SecurityLLM"),
                "status": "READY" if (outputs_dir / "securityllm-targeted-lora" / "adapter_config.json").exists() else "NOT_TRAINED",
                "description": "Adapter LoRA d'analyse SOC entraîné sur base SecurityLLM."
            }
        ]

        self.send_json_response(200, {"models": models})

    def handle_list_test_scripts(self):
        """Liste les fichiers de scripts de test (.txt) disponibles."""
        tests_dir = BASE_DIR / "tests"
        scripts = []

        if tests_dir.exists():
            for file in tests_dir.glob("*.txt"):
                # Déterminer la catégorie en fonction du nom
                category = "Autre"
                if "phishing" in file.name.lower():
                    category = "Détection Phishing (BERT & LLM)"
                elif "cyber_defense" in file.name.lower():
                    category = "Analyse SOC & Règles (SecurityLLM)"
                elif "robustness" in file.name.lower():
                    category = "Robustesse & Adversarial (BERT)"

                scripts.append({
                    "name": file.name,
                    "path": str(file),
                    "category": category,
                    "size_bytes": file.stat().st_size
                })

        self.send_json_response(200, {"scripts": scripts})

    def handle_view_test_script(self, script_name: str):
        """Lit et retourne le contenu structuré d'un script de test."""
        # Nettoyage minimal pour éviter le Directory Traversal
        script_name = Path(script_name).name
        script_file = BASE_DIR / "tests" / script_name

        if not script_file.exists() or not script_file.is_file():
            self.send_error_response(404, "Script de test introuvable")
            return

        try:
            # On utilise le test_runner pour parser le fichier proprement
            sys.path.append(str(BASE_DIR))
            from test_runner import parse_test_file
            tests = parse_test_file(script_file)
            self.send_json_response(200, {
                "script_name": script_name,
                "total_tests": len(tests),
                "tests": tests
            })
        except Exception as e:
            self.send_error_response(500, f"Erreur lors du parsing du fichier : {str(e)}")

    def handle_predict(self, body: Dict[str, Any]):
        """Exécute une prédiction unitaire via subprocess pour préserver la VRAM."""
        model_id = body.get("model")
        prompt = body.get("prompt", "")

        if not model_id or not prompt:
            self.send_error_response(400, "Modèle et prompt requis")
            return

        # Heuristique : utiliser le script train_adaptive_pipeline.py predict
        # qui évite de charger les modèles en mémoire résidente dans le serveur web.
        cmd = [
            PYTHON_EXE,
            str(BASE_DIR / "train_adaptive_pipeline.py"),
            "predict",
            "--model",
            str(self.get_model_path_by_id(model_id)),
            "--prompt",
            prompt
        ]

        print(f"[+] Lancement de l'inférence : {' '.join(cmd)}")
        try:
            # Lancement avec timeout pour éviter les blocages
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=120,
                check=False
            )

            stdout = result.stdout.decode("utf-8", errors="replace")
            stderr = result.stderr.decode("utf-8", errors="replace")

            # Parser le stdout pour extraire la sortie formatée
            output_data = self.parse_predict_output(stdout, model_id)
            output_data["raw_output"] = stdout
            if stderr:
                output_data["stderr"] = stderr

            self.send_json_response(200, output_data)

        except subprocess.TimeoutExpired:
            self.send_error_response(504, "L'inférence a dépassé le délai maximum de 2 minutes (Timeout)")
        except Exception as e:
            self.send_error_response(500, f"Erreur lors de l'inférence : {str(e)}")

    def handle_run_tests(self, body: Dict[str, Any]):
        """Lance le script test_runner.py pour évaluer un fichier complet."""
        model_id = body.get("model")
        script_name = body.get("script")
        filter_id = body.get("filter_id", "")

        if not model_id or not script_name:
            self.send_error_response(400, "Modèle et script de test requis")
            return

        script_name = Path(script_name).name
        script_path = BASE_DIR / "tests" / script_name

        if not script_path.exists():
            self.send_error_response(404, "Script de test introuvable")
            return

        # Construction de la commande de test
        cmd = [
            PYTHON_EXE,
            str(BASE_DIR / "test_runner.py"),
            "--test-file",
            str(script_path),
            "--model",
            model_id,
            "--report"
        ]

        if filter_id:
            cmd.extend(["--filter-id", filter_id])

        print(f"[+] Lancement du test batch : {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=300, # 5 minutes max pour du batch
                check=False
            )

            stdout = result.stdout.decode("utf-8", errors="replace")
            stderr = result.stderr.decode("utf-8", errors="replace")

            # Chercher le fichier de rapport JSON généré récemment
            reports_dir = BASE_DIR / "reports"
            latest_report = None
            if reports_dir.exists():
                reports = list(reports_dir.glob(f"test_report_{model_id}_*.json"))
                if reports:
                    latest_report = max(reports, key=os.path.getmtime)

            report_data = {}
            if latest_report and latest_report.exists():
                with open(latest_report, "r", encoding="utf-8") as f:
                    report_data = json.load(f)

            self.send_json_response(200, {
                "success": result.returncode == 0,
                "stdout": stdout,
                "stderr": stderr,
                "report": report_data
            })

        except subprocess.TimeoutExpired:
            self.send_error_response(504, "L'exécution des tests a dépassé le délai maximum de 5 minutes")
        except Exception as e:
            self.send_error_response(500, f"Erreur lors de l'exécution : {str(e)}")

    # ============================================================
    # Helpers
    # ============================================================

    def get_model_path_by_id(self, model_id: str) -> Path:
        """Résout le chemin du modèle par son ID."""
        outputs_dir = BASE_DIR / "outputs"
        if model_id == "cysecbert":
            return outputs_dir / "cysecbert-phishing"
        elif model_id == "secbert":
            return outputs_dir / "secbert-phishing"
        elif model_id == "phishsense-merged":
            return outputs_dir / "phishsense-merged"
        elif model_id == "securityllm-merged":
            return outputs_dir / "securityllm-merged"
        elif model_id == "phishsense":
            return outputs_dir / "phishsense-targeted-lora"
        elif model_id == "securityllm":
            return outputs_dir / "securityllm-targeted-lora"
        return outputs_dir / model_id

    def parse_predict_output(self, stdout: str, model_id: str) -> Dict[str, Any]:
        """Parse le stdout de la commande predict pour renvoyer des données JSON structurées."""
        data = {"predicted": False, "prediction": ""}
        
        # Cas BERT
        if model_id in ["cysecbert", "secbert"]:
            # Format attendu (imprimé par test_bert_classifier) :
            # Prédit : [LABEL] (confiance : XX.XX%)
            # Ou "Probabilités :" suivi des labels
            label_match = re.search(r'Prédit\s*:\s*(.+?)\s*\(confiance\s*:\s*([\d\.]+)%\)', stdout)
            if label_match:
                data["predicted"] = True
                data["prediction"] = label_match.group(1).strip()
                data["confidence"] = float(label_match.group(2)) / 100.0
            
            # Rechercher la distribution de probabilité
            probs = {}
            for line in stdout.splitlines():
                prob_match = re.search(r'-\s*(.+?)\s*:\s*([\d\.]+)%', line)
                if prob_match:
                    probs[prob_match.group(1).strip()] = float(prob_match.group(2)) / 100.0
            if probs:
                data["probabilities"] = probs

        # Cas LLM
        else:
            # Les LLM retournent la réponse générée sous "===== SORTIE MODÈLE ====="
            # ou "Réponse :" ou juste le texte final
            # Dans train_adaptive_pipeline.py :
            # print("===== SORTIE MODÈLE =====")
            # print(text)
            # print("=========================")
            pattern = r'={5,}\s*SORTIE MODÈLE\s*={5,}\n(.*?)={5,}'
            match = re.search(pattern, stdout, re.DOTALL)
            if match:
                data["predicted"] = True
                data["prediction"] = match.group(1).strip()
            else:
                # Fallback : chercher tout texte après "Réponse :" ou extraire les dernières lignes
                lines = stdout.splitlines()
                idx = -1
                for i, line in enumerate(lines):
                    if "Réponse :" in line or "Response :" in line:
                        idx = i
                        break
                if idx != -1:
                    data["predicted"] = True
                    data["prediction"] = "\n".join(lines[idx+1:]).strip()
                else:
                    # Renvoyer les 15 dernières lignes nettoyées des logs de chargement
                    filtered_lines = [l for l in lines if not l.startswith("loading") and not l.startswith("Loading") and "[+" not in l and "[OK]" not in l]
                    data["prediction"] = "\n".join(filtered_lines[-10:]).strip()
                    data["predicted"] = True

        return data

    def serve_file(self, filepath: Path, content_type: str):
        try:
            content = filepath.read_bytes()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", len(content))
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_error_response(500, f"Erreur de lecture de fichier : {str(e)}")

    def send_json_response(self, status: int, data: Any):
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def send_error_response(self, status: int, message: str):
        self.send_json_response(status, {"error": message})

    def get_content_type(self, filepath: Path) -> str:
        suffix = filepath.suffix.lower()
        if suffix == ".html" or suffix == ".htm":
            return "text/html; charset=utf-8"
        elif suffix == ".css":
            return "text/css; charset=utf-8"
        elif suffix == ".js":
            return "application/javascript; charset=utf-8"
        elif suffix == ".json":
            return "application/json; charset=utf-8"
        elif suffix == ".png":
            return "image/png"
        elif suffix == ".jpg" or suffix == ".jpeg":
            return "image/jpeg"
        elif suffix == ".gif":
            return "image/gif"
        elif suffix == ".svg":
            return "image/svg+xml"
        elif suffix == ".txt":
            return "text/plain; charset=utf-8"
        return "application/octet-stream"


def run_server():
    server_address = ('', PORT)
    httpd = HTTPServer(server_address, SecurityTestHandler)
    print(f"\n{'='*80}")
    print(f"  SERVEUR DE TEST DE SÉCURITÉ LANCÉ")
    print(f"  URL d'accès : http://localhost:{PORT}/")
    print(f"  Dossier racine : {BASE_DIR}")
    print(f"{'='*80}\n")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[-] Serveur arrêté.")
        sys.exit(0)


if __name__ == "__main__":
    run_server()
