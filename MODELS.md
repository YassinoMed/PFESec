# Registre des Modèles d'Intelligence Artificielle — SecureRAG Hub

Ce document répertorie tous les modèles d'intelligence artificielle enregistrés et disponibles au sein de la plateforme SecureRAG Hub, classés par domaine de sécurité et cas d'usage.

---

## Vue d'Ensemble des Modèles

| ID du Modèle | Nom du Modèle | Catégorie | Framework | Hugging Face ID / Source | Taille | Params | Mémoire requis (MB) | GPU requis |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **cysecbert** | CySecBERT | Sécurité Email | PyTorch | `TUKE-Phishing-Detection/CySecBERT` | 110M | 110M | 520 | Non |
| **phishsense** | PhishSense 1B | Sécurité Email | PyTorch | `microsoft/PhishSense-1B` | 1B | 1.0B | 2 100 | Oui |
| **codebert** | CodeBERT | Sécurité Web | PyTorch | `microsoft/codebert-base` | 125M | 125M | 530 | Non |
| **graphcodebert** | GraphCodeBERT | Sécurité Web | PyTorch | `microsoft/graphcodebert-base` | 125M | 125M | 540 | Non |
| **netbert** | NetBERT | Sécurité Réseau | PyTorch | `icsi/netbert` | 110M | 110M | 520 | Non |
| **flowtransformer** | FlowTransformer | Sécurité Réseau | PyTorch | `icsi/flow-transformer` | 85M | 85M | 450 | Non |
| **malbert** | MalBERT | Analyse Malware | PyTorch | `malbert/malbert-base` | 110M | 110M | 530 | Non |
| **malconv** | MalConv | Analyse Malware | PyTorch | `malconv/malconv2` | 12M | 12M | 350 | Non |
| **attackbert** | AttackBERT | Threat Intelligence | PyTorch | `da09/AttackBERT` | 110M | 110M | 530 | Non |
| **iocbert** | IOCBERT | Threat Intelligence | PyTorch | `da09/IOC-BERT` | 110M | 110M | 530 | Non |
| **urlbert** | URLBERT | Analyse d'URLs | PyTorch | `da09/URLBERT` | 110M | 110M | 530 | Non |
| **urlnet** | URLNet | Analyse d'URLs | PyTorch | `da09/URLNet` | 5M | 5M | 120 | Non |
| **logbert** | LogBERT | Analyse de Logs | PyTorch | `logbert/logbert` | 110M | 110M | 530 | Non |
| **deeplog** | DeepLog | Analyse de Logs | PyTorch | `deeplog/deeplog` | 8M | 8M | 200 | Non |
| **paddleocr** | PaddleOCR | Reconnaissance OCR | PaddlePaddle | `PaddleOCR-json/PaddleOCR` | 14M | 14M | 800 | Non |
| **trocr_small** | TrOCR-small | Reconnaissance OCR | PyTorch | `microsoft/trocr-small-handwritten` | 60M | 60M | 400 | Non |
| **qwen2_5_1_5b** | Qwen2.5-1.5B-Instruct | Security LLM | PyTorch | `Qwen/Qwen2.5-1.5B-Instruct` | 1.5B | 1.5B | 3 500 | Oui |
| **smollm2_1_7b** | SmolLM2-1.7B-Instruct | Security LLM | PyTorch | `HuggingFaceTB/SmolLM2-1.7B-Instruct` | 1.7B | 1.7B | 3 800 | Oui |

---

## Détails par Cas d'Usage

### 📧 1. Sécurité Email & Phishing
* **CySecBERT** (`cysecbert`) : Modèle BERT fine-tuné spécifiquement pour la classification d'emails malveillants et de tentatives de phishing.
* **PhishSense 1B** (`phishsense`) : Modèle de type LLM de 1 milliard de paramètres spécialisé dans la détection de campagnes de phishing complexes et d'usurpations d'identité.

### 🕸️ 2. Sécurité Web & Analyse de Code
* **CodeBERT** (`codebert`) : BERT entraîné conjointement sur du texte naturel et du code source. Utilisé pour repérer les injections ou les faiblesses dans le code source d'applications.
* **GraphCodeBERT** (`graphcodebert`) : Intègre les flux de données du code pour une analyse structurelle plus poussée.

### 📡 3. Sécurité Réseau & Trafic
* **NetBERT** (`netbert`) : Modèle BERT entraîné sur des traces de trafic réseau brutes pour la classification de paquets et de protocoles.
* **FlowTransformer** (`flowtransformer`) : Détecte les anomalies de trafic en analysant la séquence temporelle des flux réseau.

### 🦠 4. Détection et Analyse de Malware
* **MalBERT** (`malbert`) : Classification comportementale de malwares à partir des appels système et du code d'assemblage.
* **MalConv** (`malconv`) : Réseau de neurones convolutif 1D capable de classifier un fichier exécutable comme malveillant en lisant directement les octets bruts (format PE).

### 📑 5. Analyse de Logs et Journaux
* **LogBERT** (`logbert`) : Applique l'architecture BERT pour modéliser le flux normal des logs système (Syslog, Event Log Windows) et lever des alertes sur les séquences anormales.
* **DeepLog** (`deeplog`) : Modèle basé sur un réseau LSTM pour l'apprentissage séquentiel et la prédiction de patterns de logs anormaux.

### 🛡️ 6. Threat Intelligence (CTI)
* **AttackBERT** (`attackbert`) : Modélise les descriptions textuelles de menaces pour les mapper automatiquement vers les tactiques et techniques du framework **MITRE ATT&CK**.
* **IOCBERT** (`iocbert`) : Extraction automatique d'Indicateurs de Compromission (adresses IP, hashes, domaines, clés de registre) depuis des rapports de sécurité non structurés.

### 🌐 7. Analyse d'URLs et Réputation
* **URLBERT** (`urlbert`) : Modèle BERT pré-entraîné pour la classification statique d'adresses URL suspectes sans requête réseau.
* **URLNet** (`urlnet`) : Réseau convolutif de caractères pour la détection de typosquatting et de domaines éphémères.

### 🧠 8. Grands Modèles de Langage (LLMs)
* **Qwen2.5-1.5B-Instruct** (`qwen2_5_1_5b`) : LLM compact et performant d'Alibaba, optimisé pour les tâches de raisonnement locales à faible latence.
* **SmolLM2-1.7B-Instruct** (`smollm2_1_7b`) : Petit modèle de langage très rapide de Hugging Face servant à la synthèse d'alertes et la structuration des playbooks de réponse SOC.
