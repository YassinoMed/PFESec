# AI Security Engine Architecture Specification — SecureRAG Hub Enterprise
**Version:** 3.0-Enterprise-Spec  
**Author:** Senior AI & Cybersecurity Architect  
**Classification:** Internal Enterprise Confidential  

---

## Table des Matières
1. [AI Security Engine (Moteur Central)](#1-ai-security-engine-moteur-central)
2. [AI Orchestrator](#2-ai-orchestrator)
3. [AI Model Registry & Spécifications des Modèles](#3-ai-model-registry--spécifications-des-modèles)
4. [AI Inference Layer (Couche d'Inférence)](#4-ai-inference-layer-couche-dinférence)
5. [AI Consensus Engine (Moteur de Consensus)](#5-ai-consensus-engine-moteur-de-consensus)
6. [AI Correlation Engine (Moteur de Corrélation)](#6-ai-correlation-engine-moteur-de-corrélation)
7. [AI Risk Engine (Moteur d'Évaluation des Risques)](#7-ai-risk-engine-moteur-dévaluation-des-risques)
8. [Explainable AI (XAI - Explicabilité)](#8-explainable-ai-xai---explicabilité)
9. [AI Decision Engine](#9-ai-decision-engine)
10. [AI Recommendation Engine](#10-ai-recommendation-engine)
11. [Architecture Logique & Diagrammes ASCII](#11-architecture-logique--diagrammes-ascii)
12. [Cycle de Pipeline Complet End-to-End](#12-cycle-de-pipeline-complet-end-to-end)

---

## 1. AI Security Engine (Moteur Central)

### Rôle
L'**AI Security Engine** constitue le noyau d'intelligence cyber-défensive de la plateforme **SecureRAG Hub**. Conçu pour fonctionner au cœur d'un Centre d'Opérations de Sécurité (SOC) moderne, il traite des flux massifs d'événements de sécurité hétérogènes (télémétrie réseau, logs, emails, exécutables suspectés, documents numérisés) pour identifier de manière autonome les menaces avancées et automatiser les décisions de remédiation en temps réel.

### Responsabilités
* **Ingestion & Normalisation :** Réceptionner les données brutes provenant de sources multiples (SIEM, EDR, passerelles de messagerie, flux de Threat Intel) et les traduire dans un schéma d'événements normalisé de sécurité.
* **Orchestration Multi-Agent :** Déclencher les agents experts virtuels appropriés pour collecter et fusionner les preuves.
* **Raisonnement de Sécurité Structuré (Pipeline en 9 étapes) :** Structurer les étapes logiques internes du moteur pour éviter l'exposition de "Chain-of-Thought" (CoT) non structurés.
* **Garantie d'Intégrité & d'Auditabilité :** Fournir un journal des décisions complet, décrivant précisément les calculs de risques et la traçabilité des votes pour chaque incident.

### Fonctionnement & Flux Internes
Le moteur applique un cycle de traitement synchrone-asynchrone hybride :
1. **Ingestion :** La requête ou l'alerte brute arrive par l'API Gateway.
2. **Classification & Routage :** La requête est envoyée au module de classification automatique pour identifier le domaine (ex: phishing, malware, intrusion réseau).
3. **Appel des Modèles :** Les modèles appropriés du domaine sont activés via le registre de modèles.
4. **Calcul du Consensus :** Les résultats d'inférence des modèles sont comparés par l'Engine de Consensus.
5. **Corrélation Multi-Vectorielle :** Les alertes sont croisées avec les IOCs locaux et le framework MITRE ATT&CK.
6. **Évaluation du Risque :** Un score composite et un vecteur CVSS simulé sont générés.
7. **Explication & Justification (XAI) :** Une analyse en langage naturel et l'identification des tokens critiques sont réalisées par le LLM de Sécurité.
8. **Décision & Recommandations :** Génération du playbook de réponse SOC (confinement, éradication, etc.) et envoi vers le SIEM/SOAR.

### Interactions avec les autres composants
```
                       +-----------------------+
                       |   API Gateway / SOC   |
                       +-----------+-----------+
                                   | (Ingestion)
                                   v
                      +------------+------------+
                      |   AI Security Engine    |
                      +------------+------------+
                                   |
         +-------------------------+-------------------------+
         |                         |                         |
         v                         v                         v
+--------+--------+       +--------+--------+       +--------+--------+
| AI Orchestrator | <---> | Model Registry  | <---> | Inference Layer |
+--------+--------+       +-----------------+       +-----------------+
         |
         +-------------------------+-------------------------+
         |                         |                         |
         v                         v                         v
+--------+--------+       +--------+--------+       +--------+--------+
|Consensus Engine | <---> |Correlation Eng. | <---> |   Risk Engine   |
+--------+--------+       +-----------------+       +-----------------+
         |
         +-------------------------+
         |                         |
         v                         v
+--------+--------+       +--------+--------+
| Explainable AI  | <---> | Decision Engine |
+-----------------+       +-----------------+
```

---

## 2. AI Orchestrator

L'**AI Orchestrator** pilote le cycle de vie du traitement des alertes. Il coordonne l'exécution distribuée et asynchrone des modèles et des agents de sécurité.

### Routing Intelligent
Dès la réception d'une alerte, l'Orchestrateur utilise le `QueryClassifierAgent` pour évaluer les caractéristiques sémantiques de la charge utile. Il détermine immédiatement les domaines de sécurité applicables et sélectionne le workflow de traitement adapté (ex: `phishing_workflow`, `malware_workflow`, `intrusion_workflow`).

### Sélection Automatique des Modèles
Le routeur sémantique interroge l'**AI Model Registry** pour identifier les deux modèles de Deep Learning spécifiques affectés au domaine qualifié, ainsi que le LLM de sécurité destiné à la synthèse. Si une analyse multi-domaine est nécessaire, l'Orchestrateur sélectionne les paires de modèles pour chaque vecteur (ex: Malware PE + Log Système).

### Exécution Parallèle & Asynchrone
Pour minimiser la latence (SLA SOC strict), les modèles sont exécutés en parallèle en utilisant le framework asynchrone de Python (`asyncio.gather`). L'Orchestrateur envoie les requêtes de prédiction de manière concurrente à l'Inference Layer.

### Gestion CPU/GPU & Allocation
* **Modèles légers (BERT, CNNs) :** Les modèles de classification sémantique d'une taille inférieure à 500M de paramètres sont alloués en priorité sur le processeur (CPU) en utilisant des runtimes optimisés (ONNX Runtime, OpenVINO) pour préserver la VRAM.
* **Grands Modèles (LLMs, TrOCR, PhishSense 1B) :** Ces modèles sont alloués sur le GPU. L'Orchestrateur gère la répartition de la VRAM en allouant des contextes CUDA distincts ou en s'appuyant sur un serveur Triton Inference Server gérant des instances dynamiques.

### Priorisation & Scheduling
Les requêtes entrantes sont classées dans des files d'attente prioritaires gérées par un ordonnanceur de type **Priority Queue** :
* **Priorité 1 (P1 - Critique) :** Suspicion de Ransomware, exfiltration de données active, détection de Rootkit. Traitement instantané avec préemption des ressources CPU/GPU.
* **Priorité 2 (P2 - Haute) :** Phishing suspecté sur boîte VIP, trafic réseau anormal vers une IP hostile.
* **Priorité 3 (P3 - Moyenne) :** Anomalie de log, analyse de documents RH suspectés.
* **Priorité 4 (P4 - Basse/Info) :** Logs d'audit standards, balayage réseau externe.

### Monitoring des Ressources
Un agent de monitoring interne supervise en permanence :
* La mémoire système (RAM) et la mémoire vidéo (VRAM) consommée.
* La température, le taux d'utilisation des cores GPU/CPU.
* Le temps d'inférence de chaque modèle pour détecter des dérives de performances.

### Gestion Mémoire & Cache
L'Orchestrateur intègre un cache Redis L2 partagé à faible latence (indexé par le hash SHA-256 de la donnée d'entrée : contenu de l'email, binaire PE, URL, log brut). Si une entrée identique a déjà été analysée dans la fenêtre de rétention active (ex: 24h), le score d'inférence historique est immédiatement renvoyé sans ré-exécuter le pipeline Deep Learning.

### Stratégies de Fallback (Dégradation Gracieuse)
Si un modèle GPU ne répond pas dans le délai imparti (timeout configuré à 30 secondes) ou s'il rencontre une erreur d'allocation VRAM (OOM - Out of Memory) :
1. **Fallback Niveau 1 :** Commutation automatique vers le modèle secondaire du même domaine sur un endpoint d'inférence CPU d'urgence (modèle quantifié).
2. **Fallback Niveau 2 :** Activation des agents experts virtuels basés sur des règles d'heuristiques, expressions régulières d'indicateurs de compromission et interrogeant la base de connaissances locale (RAG) sans ressource GPU.
3. **Fallback Niveau 3 :** Lever une alerte système dans le journal de décision en affectant un tag `WARNING_DEGRADED_MODE` avec un score de confiance pondéré par défaut.

### Orchestration Multi-Modèles
L'orchestration prend en charge le chaînage complexe de modèles (Pipeline Multi-Modèles) :
* **Scénario d'analyse de document malveillant :**
  ```
  Entrée (PDF Suspect) 
     --> Inférence 1: PaddleOCR (Extraction de texte depuis l'image du document)
     --> Inférence 2: CySecBERT (Classification de la dangerosité sémantique du texte extrait)
     --> Inférence 3: URLNet (Analyse des liens extraits par l'OCR)
     --> Inférence 4: SmolLM2 (Synthèse de l'attaque globale et rédaction du rapport SOC)
  ```

---

## 3. AI Model Registry & Spécifications des Modèles

L'**AI Model Registry** est le registre unique répertoriant tous les modèles de Deep Learning qualifiés pour SecureRAG Hub.

### Métadonnées du Registre
Chaque modèle doit obligatoirement être enregistré avec le schéma de propriétés suivant :
* `model_id` (Identifiant unique, string)
* `model_name` (Nom commercial/académique, string)
* `category` (Domaine de sécurité, enum)
* `framework` (PyTorch, TensorFlow, ONNX, PaddlePaddle, LightGBM)
* `parameters_count` (Nombre de paramètres, string)
* `gpu_memory_used_mb` (Mémoire GPU requise au chargement, entier)
* `version` (Version sémantique du modèle, string)
* `license` (Licence open-source ou propriétaire, string)
* `intrinsic_trust_score` (Poids de confiance intrinsèque par défaut de 0.0 à 100.0, float)
* `status` (État actuel du modèle dans l'instance : LOADED, UNLOADED, DOWNLOADING, ERROR)
* `metrics` (F1-Score, Précision, Rappel lors de la validation, dict)
* `domain` (Champ d'application réseau/système/applicatif, string)
* `endpoint` (URL locale d'inférence ou chemin local du modèle, string)
* `compatibility` (Architectures cibles supportées : CUDA, CPU-AVX2, ROCm, CoreML, etc.)

---

### Tableau Global du Registre des Modèles

| ID du Modèle | Nom du Modèle | Catégorie | Framework | Version | Params | VRAM Req. (MB) | Licence | Score Confiance | État | Métriques F1 | Endpoint / Source |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **cysecbert** | CySecBERT | Email Security | PyTorch | v1.2 | 110M | 520 | Apache-2.0 | 85.0 | LOADED | F1: 0.942 | `TUKE-Phishing-Detection/CySecBERT` |
| **phishsense** | PhishSense 1B | Email Security | PyTorch | v2.0 | 1.0B | 2 100 | MIT | 92.0 | LOADED | F1: 0.965 | `microsoft/PhishSense-1B` |
| **codebert** | CodeBERT | Web Security | PyTorch | v1.0 | 125M | 530 | MIT | 87.0 | LOADED | F1: 0.918 | `microsoft/codebert-base` |
| **graphcodebert** | GraphCodeBERT | Web Security | PyTorch | v1.0 | 125M | 540 | MIT | 89.0 | LOADED | F1: 0.931 | `microsoft/graphcodebert-base` |
| **netbert** | NetBERT | Network Security | PyTorch | v1.1 | 110M | 520 | BSD-3 | 84.0 | LOADED | F1: 0.905 | `icsi/netbert` |
| **flowtransformer**| FlowTransformer| Network Security | PyTorch | v2.1 | 85M | 450 | MIT | 88.0 | LOADED | F1: 0.924 | `icsi/flow-transformer` |
| **malbert** | MalBERT | Malware Analysis | PyTorch | v1.0 | 110M | 530 | Apache-2.0 | 89.0 | LOADED | F1: 0.938 | `malbert/malbert-base` |
| **malconv** | MalConv | Malware Analysis | PyTorch | v2.0 | 12M | 350 | Apache-2.0 | 82.0 | LOADED | F1: 0.884 | `malconv/malconv2` |
| **attackbert** | AttackBERT | Threat Intelligence | PyTorch | v1.4 | 110M | 530 | MIT | 86.0 | LOADED | F1: 0.912 | `da09/AttackBERT` |
| **iocbert** | IOCBERT | Threat Intelligence | PyTorch | v1.2 | 110M | 530 | MIT | 88.0 | LOADED | F1: 0.929 | `da09/IOC-BERT` |
| **urlbert** | URLBERT | URL Analysis | PyTorch | v1.0 | 110M | 530 | MIT | 86.0 | LOADED | F1: 0.920 | `da09/URLBERT` |
| **urlnet** | URLNet | URL Analysis | PyTorch | v2.0 | 5M | 120 | Apache-2.0 | 83.0 | LOADED | F1: 0.895 | `da09/URLNet` |
| **logbert** | LogBERT | Log Analysis | PyTorch | v1.3 | 110M | 530 | Apache-2.0 | 85.0 | LOADED | F1: 0.915 | `logbert/logbert` |
| **deeplog** | DeepLog | Log Analysis | PyTorch | v2.0 | 8M | 200 | MIT | 84.0 | LOADED | F1: 0.898 | `deeplog/deeplog` |
| **paddleocr** | PaddleOCR | OCR & Documents | PaddlePaddle | v4.0 | 14M | 800 | Apache-2.0 | 90.0 | LOADED | F1: 0.950 | `PaddleOCR-json/PaddleOCR` |
| **trocr** | TrOCR-small | OCR & Documents | PyTorch | v1.0 | 60M | 400 | MIT | 92.0 | LOADED | F1: 0.958 | `microsoft/trocr-small-handwritten`|
| **qwen2.5_1.5b** | Qwen2.5-1.5B-Instruct | Security LLM | PyTorch | v2.5 | 1.5B | 3 500 | Apache-2.0 | 91.0 | LOADED | F1: 0.940 | `Qwen/Qwen2.5-1.5B-Instruct` |
| **smollm2_1.7b** | SmolLM2-1.7B-Instruct | Security LLM | PyTorch | v2.0 | 1.7B | 3 800 | Apache-2.0 | 90.0 | LOADED | F1: 0.932 | `HuggingFaceTB/SmolLM2-1.7B-Instruct` |

---

### Fiches Techniques Détaillées par Domaine

#### Domaine 1 : Email Security

##### 1. CySecBERT
* **Rôle :** Classification sémantique fine-tunée des corps de texte d'emails pour repérer l'ingénierie sociale, le harponnage (spearphishing) et le spam malveillant.
* **Fonctionnement :** Basé sur une architecture de type BERT (Encoder-only) pré-entraînée sur un corpus spécialisé cyber. Il calcule des représentations denses du texte pour classifier l'email via une tête de classification linéaire.
* **Pipeline de Traitement :**
  ```
  Texte Brut de l'Email -> Tokenizer (WordPiece, max_length=512) -> CySecBERT Backbone -> Extraction du token [CLS] -> Logits de classification -> Sigmoïde -> Classement [Normal vs Phishing/Malicieux]
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* String (Corps de l'email extrait).
  * *Sortie :* Tenseur Float (Dimension 1x2, logits ou probabilité Softmax).
* **Prétraitement :** Nettoyage des caractères de contrôle, tokenisation WordPiece avec troncature à 512 tokens.
* **Post-traitement :** Seuil de décision probabiliste fixé à `P >= 0.75` pour marquer comme suspect.
* **Niveau de confiance :** 85% par défaut.
* **Avantages :** Très rapide (inférence en moins de 10ms sur CPU) et forte compréhension du jargon de l'ingénierie sociale.
* **Limites :** Insensible aux pièces jointes binaires et aux liens URL obfusqués dans le code HTML.
* **Temps d'inférence & Consommation :** Latence ~8ms sur CPU, RAM ~520MB.

##### 2. PhishSense
* **Rôle :** Détection de campagnes complexes de phishing et d'usurpations d'identité (Business Email Compromise - BEC) par raisonnement contextuel.
* **Fonctionnement :** Modèle de type Transformer génératif / décodeur de 1 milliard de paramètres entraîné pour identifier la cohérence logique, le ton d'urgence et la non-concordance de l'identité de l'expéditeur.
* **Pipeline de Traitement :**
  ```
  Email + Metadata (En-têtes, SPF, DKIM) -> Tokenizer (BPE) -> Inférence GPU -> Extraction de features de danger -> Softmax -> Vecteur de menace
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* Dictionnaire JSON (Email structuré avec en-têtes SPF/DKIM/DMARC et corps).
  * *Sortie :* Dictionnaire (Score de phishing de 0 à 100, liste de menaces identifiées).
* **Prétraitement :** Normalisation des en-têtes DKIM/SPF et alignement syntaxique.
* **Post-traitement :** Combinaison du score généré avec le score SPF/DKIM.
* **Niveau de confiance :** 92% par défaut.
* **Avantages :** Analyse conjointe des données de protocole (headers) et du texte.
* **Limites :** Nécessite une ressource GPU pour garantir des temps de réponse acceptables.
* **Temps d'inférence & Consommation :** Latence ~45ms sur GPU (CUDA), VRAM ~2.1GB.

---

#### Domaine 2 : Web Security (Analyse de Code)

##### 1. CodeBERT
* **Rôle :** Analyse statique du code source d'applications pour la détection de vulnérabilités applicatives (SQL Injection, XSS, Path Traversal, secrets exposés).
* **Fonctionnement :** Architecture BERT pré-entraînée sur des langages de programmation multiples (Python, Go, Java, JS, C++). Modélise la sémantique lexicale pour localiser les failles logicielles.
* **Pipeline de Traitement :**
  ```
  Code Source -> Lexer/Tokenizer (RoBERTa Byte-Level BPE) -> Inférence CodeBERT -> Classification des tokens sensibles -> Logits par type de faille
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* Fichier source ou snippet textuel (String).
  * *Sortie :* Liste de dictionnaires contenant le type de vulnérabilité détectée et les lignes associées.
* **Prétraitement :** Extraction des commentaires, tokenisation Byte-Level BPE.
* **Post-traitement :** Filtrage par seuil de confiance et déduplication des alertes sur la même ligne de code.
* **Niveau de confiance :** 87% par défaut.
* **Avantages :** Comprend la sémantique multi-langage sans compilation préalable.
* **Limites :** Sensible aux attaques par obfuscation de variables complexes.
* **Temps d'inférence & Consommation :** Latence ~15ms sur CPU, RAM ~530MB.

##### 2. GraphCodeBERT
* **Rôle :** Détection de vulnérabilités structurelles profondes basées sur le graphe de flux de données (Data Flow Graph - DFG).
* **Fonctionnement :** Modèle de graphe neuronal hybride qui intègre l'analyse syntaxique du code et la structure de transfert des variables (qui contrôle quoi et où).
* **Pipeline de Traitement :**
  ```
  Code Source -> AST Generation -> Data Flow Graph Construction -> GraphCodeBERT Transformer -> Agrégation de graphe -> Classification de vulnérabilité
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* Représentation JSON de l'arbre de syntaxe abstraite (AST) et du graphe de flux de données.
  * *Sortie :* Probabilité de faille critique (float [0, 1]) et chemin d'exécution vulnérable.
* **Prétraitement :** Analyse statique du code source pour extraire le DFG en Python.
* **Post-traitement :** Normalisation des chemins critiques de données identifiés.
* **Niveau de confiance :** 89% par défaut.
* **Avantages :** Capacité supérieure pour identifier les vulnérabilités complexes de manipulation de variables d'entrée.
* **Limites :** Temps de prétraitement (génération du graphe) supérieur aux autres modèles.
* **Temps d'inférence & Consommation :** Latence ~35ms sur CPU/GPU, VRAM/RAM ~540MB.

---

#### Domaine 3 : Network Security

##### 1. NetBERT
* **Rôle :** Classification sémantique de paquets réseau bruts et détection d'anomalies de protocole (ex: exfiltration DNS, tunneling HTTP, scan de ports furtif).
* **Fonctionnement :** Modèle pré-entraîné sur des représentations hexadécimales de charges utiles IP/TCP/UDP. Il "lit" le trafic réseau comme du texte.
* **Pipeline de Traitement :**
  ```
  Trame Réseau PCAP -> Extraction Payload (Hex String) -> Tokenizer (Custom Hex) -> NetBERT -> Classification de comportement malicieux
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* String d'octets hexadécimaux représentant le paquet IP (ex : `4500003c1a2b...`).
  * *Sortie :* Classe de protocole/attaque détectée (ex: `DNS_Tunneling`).
* **Prétraitement :** Extraction des couches applicatives et conversion en représentations hexadécimales standardisées.
* **Post-traitement :** Seuil de probabilité pour lever une alerte fixé à 0.80.
* **Niveau de confiance :** 84% par défaut.
* **Avantages :** Analyse le contenu applicatif brut du paquet sans dépendre uniquement de l'en-tête de protocole.
* **Limites :** Inefficace si le trafic est chiffré de bout en bout (sans interception TLS).
* **Temps d'inférence & Consommation :** Latence ~12ms sur CPU, RAM ~520MB.

##### 2. FlowTransformer
* **Rôle :** Analyse séquentielle et temporelle des flux réseau (NetFlow) pour repérer des comportements d'intrusion complexes (mouvements latéraux, C2 Beaconing).
* **Fonctionnement :** Modèle basé sur un Transformer temporel 1D calculant l'attention entre les paquets successifs d'une connexion réseau pour identifier des anomalies de périodicité ou de volume.
* **Pipeline de Traitement :**
  ```
  NetFlow Vector (Time, Size, Dir) -> Sequence Builder (window size = 50 packets) -> FlowTransformer -> Output Vector -> Anomaly Detection
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* Tenseur Float de dimension `[Batch, SequenceLength, Features]` contenant les métriques des paquets.
  * *Sortie :* Score d'anomalie réseau globale (float de 0.0 à 1.0).
* **Prétraitement :** Normalisation MinMax des tailles de paquets et calcul du delta temporel inter-paquets.
* **Post-traitement :** Analyse de persistance des anomalies sur plusieurs fenêtres de flux.
* **Niveau de confiance :** 88% par défaut.
* **Avantages :** Détecte les balises de commande & contrôle (C2) même si la trame est totalement chiffrée.
* **Limites :** Nécessite le maintien en mémoire des historiques d'états de flux récents.
* **Temps d'inférence & Consommation :** Latence ~18ms sur CPU, RAM ~450MB.

---

#### Domaine 4 : Malware Analysis

##### 1. MalBERT
* **Rôle :** Classification de comportements de fichiers et d'API système pour détecter des logiciels malveillants (Ransomwares, Chevaux de Troie, Spywares).
* **Fonctionnement :** Modèle BERT spécialisé dans la séquence temporelle des appels d'API système (Windows API Calls, Linux Syscalls) générés dans un bac à sable ou extraits statiquement.
* **Pipeline de Traitement :**
  ```
  Sequence d'Appels API -> Tokenizer (Custom API Vocab) -> MalBERT Backbone -> CLS Representation -> Dense Layer -> Softmax
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* String d'appels système ordonnés séparés par des espaces (ex: `NtCreateFile LdrLoadDll RegOpenKeyEx`).
  * *Sortie :* Catégorie de Malware (Ransomware, Trojan, Dropper, Benign).
* **Prétraitement :** Mapping des appels d'API complexes vers des tokens normalisés.
* **Post-traitement :** Association des appels critiques identifiés à des techniques du framework MITRE ATT&CK.
* **Niveau de confiance :** 89% par défaut.
* **Avantages :** Analyse comportementale de l'exécution, résistante aux techniques d'obfuscation de code binaire statique.
* **Limites :** Dépend de la qualité de l'exécution dans le bac à sable ou du désassemblage.
* **Temps d'inférence & Consommation :** Latence ~14ms sur CPU, RAM ~530MB.

##### 2. MalConv
* **Rôle :** Classification ultra-rapide de fichiers exécutables Windows PE en lisant directement les octets bruts du fichier.
* **Fonctionnement :** Réseau de neurones convolutif 1D (CNN) entraîné à projeter les premiers mégaoctets d'un exécutable dans un espace vectoriel pour y détecter des motifs suspects de compilation, d'importations frauduleuses ou de payloads.
* **Pipeline de Traitement :**
  ```
  Fichier Exécutable PE -> Byte Ingestion (Max 2MB) -> Embedding Layer -> Conv1D Layer -> Global Max Pooling -> FC Layer -> Softmax
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* Tableau d'octets binaires (Uint8 Array).
  * *Sortie :* Probabilité de malveillance (float de 0.0 à 1.0).
* **Prétraitement :** Lecture des 2 premiers Mo du fichier brut, conversion en entiers de 0 à 255.
* **Post-traitement :** Alerte directe si le score franchit `P >= 0.85`.
* **Niveau de confiance :** 82% par défaut.
* **Avantages :** Pas besoin de désassembler ou d'exécuter le fichier ; traitement en moins de 5ms.
* **Limites :** Peut être induit en erreur par l'ajout massif de données neutres en fin de fichier (Padding).
* **Temps d'inférence & Consommation :** Latence ~5ms sur CPU, RAM ~350MB.

---

#### Domaine 5 : Threat Intelligence (CTI)

##### 1. AttackBERT
* **Rôle :** Mapping sémantique automatique de rapports d'incident textuels non structurés vers les techniques et tactiques du framework **MITRE ATT&CK**.
* **Fonctionnement :** Modèle BERT fine-tuné sur les bases de données d'attaques d'APT, rapports de sécurité et de CTI pour associer des phrases descriptives à des identifiants techniques (ex: T1566, T1059).
* **Pipeline de Traitement :**
  ```
  Texte de Rapport CTI -> Tokenizer (WordPiece) -> AttackBERT -> Classification Multi-Label (150+ techniques) -> Sigmoid Vector
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* String (Rapport de Threat Intelligence, article de blog cyber).
  * *Sortie :* Vecteur de techniques MITRE ATT&CK détectées avec leur score de confiance associé.
* **Prétraitement :** Segmentation du texte par phrase, élimination des bruits textuels.
* **Post-traitement :** Filtrage des techniques ayant un score de confiance inférieur à 70%.
* **Niveau de confiance :** 86% par défaut.
* **Avantages :** Automatise la catégorisation MITRE des rapports en quelques fractions de seconde.
* **Limites :** Dépend de la mise à jour régulière des tactiques MITRE dans son vocabulaire.
* **Temps d'inférence & Consommation :** Latence ~11ms sur CPU, RAM ~530MB.

##### 2. IOCBERT
* **Rôle :** Extraction d'entités nommées (NER) spécialisées dans la cybersécurité pour isoler les indicateurs de compromission (IP, Hashes, Noms de domaine, CVE, URLs, Fichiers).
* **Fonctionnement :** Modèle d'extraction d'entités BERT token-by-token (BIO Tagging scheme) entraîné à l'aide de données d'entraînement cyber pour localiser précisément la syntaxe et le contexte des IOCs au sein de longs textes non structurés.
* **Pipeline de Traitement :**
  ```
  Texte Brut -> Tokenizer (WordPiece) -> IOCBERT Backbone -> Classification par Token (B-IOC, I-IOC, O) -> Agrégation des IOCs extraits
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* String de texte.
  * *Sortie :* Dictionnaire d'IOCs classés par types (`{"ips": [...], "hashes": [...], "cves": [...]}`).
* **Prétraitement :** Normalisation Unicode du texte.
* **Post-traitement :** Validation syntaxique des IOCs extraits via expressions régulières (ex: Regex IP/Hash).
* **Niveau de confiance :** 88% par défaut.
* **Avantages :** Extrait des IOCs mal formulés ou obfusqués sémantiquement que les regex standards ignorent.
* **Limites :** Peut générer des faux positifs sur des adresses IP d'exemples ou de documentations internes.
* **Temps d'inférence & Consommation :** Latence ~10ms sur CPU, RAM ~530MB.

---

#### Domaine 6 : URL Analysis

##### 1. URLBERT
* **Rôle :** Détection de sites de phishing et d'hébergement de malwares par analyse statique de la structure textuelle de l'URL.
* **Fonctionnement :** Modèle BERT entraîné sur des millions d'URLs pour capturer la structure sémantique (mots-clés usurpés, domaines étranges, sous-domaines profonds).
* **Pipeline de Traitement :**
  ```
  Chaîne URL -> Tokenizer (BPE spécial URL) -> URLBERT Backbone -> CLS Representation -> Sigmoid Classification
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* String de l'URL (ex: `http://connexion-banque-securisee.xyz/login`).
  * *Sortie :* Probabilité de danger (float [0.0, 1.0]).
* **Prétraitement :** Découpage de l'URL par délimiteurs standard (`/`, `.`, `-`, `?`, `=`).
* **Post-traitement :** Analyse complémentaire d'appartenance à une liste blanche globale.
* **Niveau de confiance :** 86% par défaut.
* **Avantages :** Pas besoin d'effectuer de requête réseau HTTP vers le serveur pour classifier l'URL.
* **Limites :** Ne détecte pas les redirections dynamiques effectuées après le chargement initial de la page.
* **Temps d'inférence & Consommation :** Latence ~7ms sur CPU, RAM ~530MB.

##### 2. URLNet
* **Rôle :** Détection d'URLs malveillantes par traitement convolutif hybride au niveau des caractères et des mots (Character & Word Level CNN).
* **Fonctionnement :** Architecture CNN combinant des filtres de caractères et de mots pour identifier des variations légères de typosquatting et des algorithmes de génération de domaines (DGA).
* **Pipeline de Traitement :**
  ```
  URL -> Conv1D sur Caractères + Conv1D sur Mots -> Fusion des Features (Concatenate) -> Fully Connected -> Softmax
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* String de l'URL.
  * *Sortie :* Label de danger (Malicious, Benign).
* **Prétraitement :** Encodage One-Hot des caractères et tokenisation par espace.
* **Post-traitement :** Seuillage de sensibilité de détection.
* **Niveau de confiance :** 83% par défaut.
* **Avantages :** Extrêmement robuste contre l'offuscation par insertion de caractères Unicode spéciaux.
* **Limites :** Vocabulaire figé pour les mots, nécessite des ré-entraînements fréquents.
* **Temps d'inférence & Consommation :** Latence ~4ms sur CPU, RAM ~120MB.

---

#### Domaine 7 : Log Analysis

##### 1. LogBERT
* **Rôle :** Détection d'anomalies comportementales dans les journaux d'événements système (Syslog, EventLogs Windows, audits Cloud).
* **Fonctionnement :** Modèle de langage BERT masqué (MLM) entraîné à prédire le "prochain log normal" dans une séquence temporelle. Toute rupture de pattern est signalée comme une anomalie.
* **Pipeline de Traitement :**
  ```
  Séquence de Clés de Logs -> Tokenizer (Log Keys) -> LogBERT -> Prédiction de Probabilité de Séquence -> Calcul de Perplexité -> Seuil d'anomalie
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* Liste de chaînes de caractères (templates de logs successifs).
  * *Sortie :* Score d'anomalie de séquence (float).
* **Prétraitement :** Parsing des logs bruts (Drain parser) pour remplacer les variables (IP, dates) par des clés de template (ex: `User <*> logged in from <*>`).
* **Post-traitement :** Filtrage des alertes mineures basées sur les heures de maintenance connues.
* **Niveau de confiance :** 85% par défaut.
* **Avantages :** Capable d'analyser des enchaînements d'actions qui sont individuellement normaux, mais anormaux dans leur séquence globale.
* **Limites :** Sensible aux changements de format de logs suite à des mises à jour système.
* **Temps d'inférence & Consommation :** Latence ~15ms sur CPU, RAM ~530MB.

##### 2. DeepLog
* **Rôle :** Modélisation d'anomalies de flux système et de temps d'exécution à partir des logs de bas niveau.
* **Fonctionnement :** Réseau de neurones récurrent de type LSTM (Long Short-Term Memory) empilé qui modélise les chemins d'exécution de code système à partir de patterns de logs séquentiels.
* **Pipeline de Traitement :**
  ```
  Sequence de Templates -> LSTM Hidden States -> Dense -> Softmax -> Comparaison avec les logs réels -> Calcul d'écart de pattern
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* Tenseur 2D de templates de logs numérisés.
  * *Sortie :* Probabilité de déviation anormale.
* **Prétraitement :** Numérisation des logs par template ID.
* **Post-traitement :** Corrélation temporelle des anomalies détectées.
* **Niveau de confiance :** 84% par défaut.
* **Avantages :** Modèle très léger (seulement quelques Mo de paramètres) et très rapide.
* **Limites :** Ne capture pas le contenu sémantique en langage naturel des messages de logs.
* **Temps d'inférence & Consommation :** Latence ~6ms sur CPU, RAM ~200MB.

---

#### Domaine 8 : OCR & Documents

##### 1. PaddleOCR
* **Rôle :** Extraction de texte depuis les captures d'écran, factures, scans de documents, et images pour l'analyse anti-fraude et DLP.
* **Fonctionnement :** Réseau neuronal hybride composé d'un détecteur de texte (DBNet) et d'un classifieur de reconnaissance de texte (CRNN) optimisé pour l'exécution rapide.
* **Pipeline de Traitement :**
  ```
  Image/Scan -> Détecteur DBNet (Contours de texte) -> Crop Images -> CRNN (Reconnaissance de caractères) -> Extraction de chaînes textuelles
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* Matrice d'image (JPEG, PNG, PDF rasterisé).
  * *Sortie :* Dictionnaire contenant le texte extrait et les coordonnées spatiales (bounding boxes).
* **Prétraitement :** Redimensionnement, conversion en niveaux de gris et normalisation du contraste.
* **Post-traitement :** Reconstruction des phrases par proximité géométrique des blocs de texte.
* **Niveau de confiance :** 90% par défaut.
* **Avantages :** Vitesse de traitement exceptionnelle et support parfait de langages multiples.
* **Limites :** Sensible aux filigranes ou aux fonds complexes sur les documents de mauvaise qualité.
* **Temps d'inférence & Consommation :** Latence ~150ms sur CPU, RAM ~800MB.

##### 2. TrOCR
* **Rôle :** Reconnaissance optique de caractères de haute précision, notamment pour les textes manuscrits ou dégradés dans les rapports de sécurité numérisés.
* **Fonctionnement :** Modèle d'attention de bout en bout basé sur l'architecture Transformer (Vision Transformer - ViT pour l'encodage de l'image et BERT pour le décodage de texte).
* **Pipeline de Traitement :**
  ```
  Image segmentée -> Patch Extraction (ViT Encoder) -> Hidden States -> Transformer Decoder (Autoregressive Token Generation) -> Output Text
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* Image recadrée contenant une ligne de texte.
  * *Sortie :* String (Texte transcrit).
* **Prétraitement :** Redimensionnement en `384x384` pixels, normalisation de couleur RVB.
* **Post-traitement :** Correction grammaticale et sémantique via dictionnaire.
* **Niveau de confiance :** 92% par défaut.
* **Avantages :** Précision supérieure sur les écritures manuscrites complexes et les documents numérisés dégradés.
* **Limites :** Gourmand en ressources de calcul (inférence séquentielle).
* **Temps d'inférence & Consommation :** Latence ~80ms sur GPU, VRAM ~400MB.

---

#### Domaine 9 : Security LLM (Modèles de Raisonnement)

##### 1. Qwen2.5-1.5B-Instruct
* **Rôle :** Raisonnement de sécurité local, extraction sémantique d'IOCs, classification finale, et explication textuelle d'incidents.
* **Fonctionnement :** Modèle de langage autoregressif de 1.5 milliard de paramètres optimisé par fine-tuning d'instructions. Fournit des chaînes de raisonnement structurées à faible latence.
* **Pipeline de Traitement :**
  ```
  Security System Prompt + Incident Data -> Tokenizer (Qwen Tokenizer) -> K-V Caching -> Inférence Auto-regressive -> Output JSON/Text
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* Chaîne de prompt formatée (Système, Historique, Utilisateur).
  * *Sortie :* Dictionnaire JSON structuré (décisions, explications, techniques).
* **Prétraitement :** Concaténation des invites système et injection des données de contexte (Preuves RAG).
* **Post-traitement :** Validation syntaxique du format JSON généré (Regex/JSON Load validation).
* **Niveau de confiance :** 91% par défaut.
* **Avantages :** Excellente capacité de raisonnement logique malgré sa petite taille ; supporte le formatage structuré JSON natif.
* **Limites :** Fenêtre de contexte limitée à 32k tokens pour conserver de bonnes performances locales.
* **Temps d'inférence & Consommation :** Latence ~25 tokens/s sur GPU, VRAM ~3.5GB (en quantification FP16/INT8).

##### 2. SmolLM2-1.7B-Instruct
* **Rôle :** Synthèse d'alertes SOC en temps réel, génération rapide de playbooks de remédiation, et structuration des rapports.
* **Fonctionnement :** LLM compact de 1.7 milliard de paramètres optimisé pour les architectures locales à faibles ressources, entraîné sur un corpus d'instructions de haute qualité.
* **Pipeline de Traitement :**
  ```
  Rapport Cyber Brut -> Prompt de Synthèse -> SmolLM2 -> Génération de Playbook de Remédiation -> Output Markdown/JSON
  ```
* **Format des données & Entrées/Sorties :**
  * *Entrée :* Prompt textuel contenant les données d'incidents fusionnées.
  * *Sortie :* Playbook d'incident de sécurité structuré (Markdown).
* **Prétraitement :** Normalisation des données d'incident.
* **Post-traitement :** Extraction des blocs de code Markdown (playbooks de remédiation) et validation des commandes.
* **Niveau de confiance :** 90% par défaut.
* **Avantages :** Très faible empreinte mémoire, vitesse de génération élevée (~35 tokens/s sur GPU).
* **Limites :** Capacité de raisonnement logique complexe légèrement en retrait sur les longues chaînes d'arguments.
* **Temps d'inférence & Consommation :** Latence ~30 tokens/s sur GPU, VRAM ~3.8GB.

---

## 4. AI Inference Layer (Couche d'Inférence)

L'**AI Inference Layer** encapsule les runtimes d'exécution des modèles Deep Learning et gère leur cycle de vie opérationnel.

### Chargement Dynamique des Modèles
Le moteur utilise un chargeur de modèles basé sur une fabrique logicielle (Model Factory). Les modèles sont instanciés à la demande ou pré-chargés en fonction de la charge du SOC. Si un modèle de Malware n'est pas sollicité pendant 10 minutes, l'Inference Layer peut libérer sa mémoire VRAM (`torch.cuda.empty_cache()`) au profit d'un modèle de classification LLM plus actif.

### Versioning des Modèles
Chaque modèle possède un identifiant de version sémantique au sein du registre (ex: `cysecbert-v1.2.0`). La couche d'inférence supporte l'exécution en parallèle de deux versions distinctes du même modèle pour réaliser des tests de performance de type **A/B Testing** ou des bascules sans interruption de service.

### Runtimes CPU & GPU Supportés
* **ONNX Runtime (CPU/GPU) :** Utilisé pour l'exécution optimisée de tous les modèles BERT et CNN. Il exploite les instructions vectorielles CPU (AVX-512, AMX).
* **PyTorch (CUDA 12+) :** Utilisé pour l'inférence des modèles Transformer complexes et LLMs.
* **Triton Inference Server :** En production, l'Inference Layer fait office de client pour Triton, gérant la concurrence d'accès GPU.

### Dynamic Batching (Regroupement Dynamique)
Pour maximiser l'efficacité du GPU, l'Inference Layer regroupe les requêtes d'inférence arrivant dans une fenêtre temporelle très courte (ex: 5ms) en un seul lot (Batch) avant d'appeler le modèle. Cela permet de diviser la latence globale par un facteur de 3 lors des pics d'alertes.

### Streaming d'Inférence (SSE)
Pour les modèles génératifs (Qwen2.5 et SmolLM2), l'Inference Layer propose un endpoint de streaming basé sur les **Server-Sent Events (SSE)**. Cela permet d'afficher les justifications de l'incident et le rapport SOC au fil de l'eau sur l'interface de l'analyste SOC.

### Quantification des Modèles
Pour réduire la consommation de VRAM, les modèles subissent une quantification post-entraînement :
* Les LLMs sont convertis au format **AWQ / GPTQ INT4** ou **GGUF (INT8)**, réduisant l'empreinte mémoire de 70% pour un impact sur la précision de moins de 1%.
* Les modèles BERT sont quantifiés en **FP16** ou **INT8** (via ONNX quantization).

### Monitoring d'Inférence
La couche expose des métriques au format Prometheus :
* `inference_latency_seconds_bucket` (Temps passé à traiter l'inférence brute).
* `gpu_memory_used_bytes` (Allocation VRAM).
* `batch_size_distribution` (Taille des batches dynamiques formés).

---

## 5. AI Consensus Engine (Moteur de Consensus)

Le **Consensus Engine** arbitre les divergences d'opinion entre les différents modèles du même domaine de sécurité afin de consolider une décision d'incident unique et fiable.

```
                  +--------------------------------+
                  |   Predictions des Modèles (M)  |
                  +---------------+----------------+
                                  |
                                  v
                  +---------------+----------------+
                  |   Filtrage de Confiance (>=Tc) |
                  +---------------+----------------+
                                  |
                                  v
                  +---------------+----------------+
                  |  Pondération des Votes (W_m)   |
                  +---------------+----------------+
                                  |
                                  v
                  +---------------+----------------+
                  |  Calcul du Score Global (S_g)  |
                  +---------------+----------------+
                                  |
        +-------------------------+-------------------------+
        |                                                   |
        v                                                   v
[Similitude des Reponses >= R]                 [Similitude des Reponses < R]
        |                                                   |
        v                                                   v
Consensus Atteint                              Contradiction Détectée
(Synthese du Score / Reponse)                  (Evaluation de Robustesse)
```

### Algorithme de Vote et de Consensus
L'algorithme de consensus fonctionne selon le principe du **Weighted Confidence Average** (Moyenne de Confiance Pondérée) couplé à une analyse de cohérence lexicale :

1. **Extraction des Votes :** Chaque modèle $m$ fournit une conclusion $C_m \in \{\text{BLOCK}, \text{ACCEPT}\}$ et un score de confiance individuel $P_m \in [0, 100]$.
2. **Filtrage des Votes :** Les votes dont la confiance $P_m$ est inférieure au seuil de confiance minimal configuré ($T_c = 80.0\%$) sont rejetés et déplacés vers la liste d'audit des rejets.
3. **Calcul du Poids Dynamique :** Chaque vote retenu se voit attribuer un poids $W_m$ en fonction du score de confiance et du poids intrinsèque du modèle :
   $$W_m = \begin{cases} 
   4, & \text{si } P_m \ge 90\% \\
   2, & \text{si } 80\% \le P_m < 90\% \\
   1, & \text{si } P_m < 80\%
   \end{cases}$$
4. **Calcul du Score Global ($S_g$) :**
   $$S_g = \frac{\sum_{m \in \text{Retained}} P_m \times W_m}{\sum_{m \in \text{Retained}} W_m}$$
5. **Vérification de Similitude :** L'algorithme calcule la similarité textuelle (Jaccard) entre les conclusions textuelles détaillées des modèles retenus. Si la similarité est supérieure au ratio d'overlap $R = 0.60$ et que les labels catégoriels ($C_m$) concordent, le consensus est marqué comme **Atteint** (`consensus_reached = True`).

### Détection des Contradictions
Si deux modèles de haute confiance ($P_m \ge 90\%$) produisent des conclusions opposées (ex : `CySecBERT = BLOCK` et `PhishSense = ACCEPT`), le consensus est rompu :
* L'alerte est marquée du tag `CONTRADICTION_DETECTED`.
* Le système applique une règle de robustesse : **Priorité à la Sécurité (Fail-Safe)**. Si au moins un modèle qualifié demande le blocage avec une haute confiance, la décision conservatrice temporaire appliquée est **BLOCK**, mais le niveau de confiance final est rétrogradé à **Medium** et l'alerte est immédiatement transférée au Tier 2 du SOC pour validation.

### Synthèse de la Décision
Le rapport de décision fusionne les arguments textuels des modèles via le LLM de Sécurité qui réalise une synthèse textuelle argumentée en français en précisant la contribution de chaque modèle (ex: *« Décision de blocage prise à 95% de confiance suite à la concordance de CySecBERT (94%) et PhishSense (96%) sur les en-têtes. »*).

---

## 6. AI Correlation Engine (Moteur de Corrélation)

Le **Correlation Engine** assure la fusion sémantique et la chronologie temporelle de l'attaque en assemblant les indices hétérogènes de sécurité.

### Fusion Multi-Vectorielle
Le moteur construit un **Graphe d'Attaque Dirigé (DAG)** en reliant les indices extraits des différents canaux :
* **Vecteur 1 (Messagerie) :** Email suspect détecté par `PhishSense`.
* **Vecteur 2 (Fichier joint) :** Binaire extrait détecté comme Ransomware par `MalBERT` et `MalConv`.
* **Vecteur 3 (Réseau) :** Connexion TCP suspecte détectée par `FlowTransformer` vers une IP présente dans les logs DNS analysés par `NetBERT`.
* **Vecteur 4 (Document OCR) :** Lettre de demande de rançon analysée par `PaddleOCR`.
* **Vecteur 5 (Système) :** Logs d'écriture de fichiers anormaux repérés par `LogBERT`.

### Algorithme de Corrélation
1. **Extraction des Clés Pivot (Entities Extraction) :** Le moteur identifie les indicateurs pivots : adresses IP source/destination, adresses emails, empreintes de fichiers (hashes SHA-256), noms d'utilisateurs, identifiants de processus (PIDs), et clés de registre Windows.
2. **Corrélation Temporelle (sliding window) :** Les événements se produisant sur une même machine ou impliquant une même clé pivot dans une fenêtre de temps glissante de 2 heures sont connectés.
3. **Mapping MITRE ATT&CK :** Les techniques extraites par `AttackBERT` pour chaque événement sont mappées sur la matrice des tactiques (de l'Accès Initial à l'Impact).
4. **Vérification de CVE :** Les vulnérabilités identifiées dans les logs ou les codes sources sont croisées avec les bases CVE locales pour valider l'exploitabilité de l'intrusion.

---

## 7. AI Risk Engine (Moteur d'Évaluation des Risques)

Le **Risk Engine** calcule des indicateurs numériques précis pour prioriser le traitement des alertes au sein du SOC.

### Formule du Score de Risque Composite ($RS$)
Le score de risque global est évalué sur une échelle de 0 à 100 :
$$RS = \min\left(\left(\frac{\text{Likelihood}}{100}\right) \times \text{ImpactScore} \times 10 \times \left(\frac{\text{ConsensusScore}}{100}\right) \times \gamma, 100.0\right)$$
Où :
* **Likelihood :** Probabilité de réussite de l'attaque (0 à 100).
* **ImpactScore :** Sévérité de l'impact potentiel sur l'actif (1.0 à 10.0).
* **ConsensusScore :** Score global de confiance du consensus IA (0 à 100).
* **$\gamma$ :** Facteur multiplicateur de criticité de l'actif concerné ($\gamma = 1.2$ pour les serveurs critiques de base de données ou Active Directory, $\gamma = 1.0$ par défaut).

---

### Formule de Probabilité d'Exploitation ($\text{Likelihood}$)
$$\text{Likelihood} = \text{clamp}\left(\frac{\text{AvgConfidence} + \text{ConsensusScore}}{2.0} \times \alpha, 0.0, 100.0\right)$$
Où :
* **AvgConfidence :** Moyenne arithmétique de la confiance rapportée par tous les modèles actifs du domaine.
* **$\alpha$ :** Coefficient multiplicateur de preuve technique ($\alpha = 1.15$ si un IOC confirmé ou une signature de vulnérabilité CVE active est détecté dans le corpus de corrélation, $\alpha = 1.0$ sinon).

---

### Formule d'Impact Métier ($\text{ImpactScore}$)
L'impact est déterminé par l'analyse des mots-clés d'impact identifiés dans les rapports et la nature des actifs ciblés :
$$\text{ImpactScore} = \text{clamp}\left(\text{BaseImpact} + \sum \text{AssetWeight}, 1.0, 10.0\right)$$
* *BaseImpact* dépend du type d'action suspecté :
  * Ransomware / Chiffrement : $8.0$
  * Exfiltration de Données : $7.0$
  * Accès non autorisé (Privilège admin) : $6.0$
  * Phishing simple / Scan réseau : $3.0$
* *AssetWeight* est le poids de l'actif compromis :
  * Active Directory : $+2.0$
  * Serveur de base de données de production : $+1.5$
  * Postes de travail utilisateur simple : $+0.5$

---

### Formule de Sévérité Composée ($\text{SeverityScore}$)
$$\text{SeverityScore} = \text{clamp}(0.4 \times \text{ConsensusScore} + 0.3 \times \text{Likelihood} + 0.3 \times (\text{ImpactScore} \times 10), 0.0, 100.0)$$

La sévérité s'interprète selon les paliers opérationnels suivants :
* **CRITICAL :** Score $\ge 90.0$
* **HIGH :** $75.0 \le \text{Score} < 90.0$
* **MEDIUM :** $50.0 \le \text{Score} < 75.0$
* **LOW :** $25.0 \le \text{Score} < 50.0$
* **INFORMATIONAL :** $\text{Score} < 25.0$

---

### Priorité SOC & Niveaux de Criticité
La criticité de l'incident dicte le niveau d'intervention (SLA) :
* **Priorité 1 (P1 - SLA < 15min) :** Sévérité = CRITICAL. Isolement automatique déclenché.
* **Priorité 2 (P2 - SLA < 1h) :** Sévérité = HIGH. Notification des équipes d'astreinte.
* **Priorité 3 (P3 - SLA < 4h) :** Sévérité = MEDIUM. Analyse manuelle par le Tier 1/2 du SOC.
* **Priorité 4 (P4 - SLA < 24h) :** Sévérité = LOW/INFO. Consignation dans les registres de monitoring.

---

### Vecteur CVSS v3.1 Simulée
Le Risk Engine génère une chaîne de vecteur CVSS standardisée facilitant l'intégration avec les outils de remédiation tiers.
Exemple : `CVSS:3.1/AV:N/AC:L/PR:N/UI:R/S:C/C:H/I:H/A:H` (représentant une attaque réseau, faible complexité, aucun privilège requis, nécessitant une action utilisateur, avec impact élevé sur la confidentialité, l'intégrité et la disponibilité).

---

## 8. Explainable AI (XAI - Explicabilité)

Chaque décision prise par le moteur de sécurité doit être entièrement transparente et auditable par les analystes SOC. L'explicabilité est découpée en quatre niveau complémentaires :

### Attribution de Caractéristiques (Feature Attribution)
Pour les modèles de classification textuelle (ex: `CySecBERT`, `CodeBERT`), le moteur calcule des attributions de caractéristiques en s'appuyant sur des méthodes d'explicabilité post-hoc (Integrated Gradients ou approximations SHAP). Les tokens ou mots ayant le plus fort impact sur la prédiction positive (ex : mots-clés d'urgence comme "immédiatement", "suspendu" ou commandes suspectes comme `invoke-expression`) sont extraits et présentés à l'utilisateur.

### Cartographie des Poids d'Attention (Attention Weights Visualizer)
Le moteur XAI capture les cartes d'attention multi-têtes des couches Transformer supérieures des modèles BERT du domaine réseau ou email. Cela permet de justifier graphiquement quels groupes d'octets ou d'entités sont corrélés dans la détection d'anomalies (ex: relation entre un port source inhabituel et un volume de données suspect).

### Justification Sémantique en Langage Naturel
Le LLM de Sécurité exploite le contexte structuré des preuves extraites pour formuler une explication claire et concise de l'incident en évitant le jargon technique interne du modèle.

```json
"explicabilite": {
  "modele_principal": "phishsense",
  "score_confiance": 96.5,
  "justification": "Détection d'un email de phishing imitant un service de support cloud. L'adresse de l'expéditeur ne correspond pas au domaine SPF de l'organisation et le texte présente un caractère d'urgence marqué pour réinitialiser un mot de passe.",
  "tokens_critiques": ["mot de passe", "suspendu", "immédiatement", "http://connexion-banque-securisee.xyz"],
  "indicateurs_identifies": ["SPF_FAIL", "URGENCY_TONE", "SUSPICIOUS_DOMAIN_REPUTATION"],
  "regles_appliquees": ["R102_AUTH_BYPASS_ATTEMPT", "R204_URGENT_CALL_TO_ACTION"]
}
```

---

## 9. AI Decision Engine

### Rôle
Le **AI Decision Engine** est le composant de décision finale de la plateforme. Il transforme les sorties du Risk Engine, du Consensus Engine et de la corrélation en une **fiche d'incident normalisée**, exploitable par les analystes SOC et les systèmes SOAR.

### Responsabilités
* **Classification de l'Incident :** Qualification automatique du type d'attaque (Phishing, Ransomware, Exfiltration, Intrusion Réseau, etc.) à partir des labels de consensus.
* **Mapping MITRE ATT&CK Final :** Consolidation des techniques MITRE détectées par `AttackBERT` et les moteurs de corrélation en une chronologie d'attaque unique.
* **Extraction et Déduplication des IOCs :** Fusion de tous les IOCs détectés (IPs, hashes, domaines, emails, URIs) avec suppressions des doublons et validation croisée par `IOCBERT`.
* **Attribution de Niveau de Criticité :** Détermination du niveau P1-P4 selon le score de sévérité calculé par le Risk Engine.
* **Déclenchement d'Alertes :** Envoi de notifications structurées vers le SIEM, le système de ticketing et le SOAR.

### Fonctionnement & Algorithme de Décision
Le Decision Engine utilise une **matrice de décision multi-critères** pondérée :

```
Decision = f(IncidentType, SeverityScore, ConsensusScore, AffectedAssets)
```

1. **Aggrégation des Entrées :** Collecte des preuves consolidées, des scores de risque, du mapping MITRE et des IOCs.
2. **Classification Finale :** Application d'un classifieur à base de règles (Decision Tree Rules Engine) qui croise le type de menace majoritaire avec les assets affectés.
3. **Attribution de Priorité SOC :** Détermination de P1-P4 à partir du SeverityScore :
   * `CRITICAL (>=90)` → **P1** - Escalade immédiate, activation du runbook d'urgence.
   * `HIGH (75-89)` → **P2** - Notification équipe d'astreinte, blocage préventif.
   * `MEDIUM (50-74)` → **P3** - Analyse Tier 2 programmée.
   * `LOW (<50)` → **P4** - Enregistrement passif pour audit.
4. **Validation de Cohérence :** Vérification que la décision est cohérente avec les règles SOC prédéfinies (ex: pas de P4 pour un ransomware confirmé).
5. **Génération du Décision Journal :** Production d'un rapport JSON structuré contenant tous les éléments de décision.

### Entrées / Sorties
| Type | Description | Format |
|:---|:---|:---|
| **Entrées** | Preuves corrélées, RiskScore, ConsensusScore, MITRE mappings, IOCs | `Dict[str, Any]` |
| **Sorties** | Fiche d'incident structurée, Décision (BLOCK/ACCEPT/INVESTIGATE), Priorité SOC, IOCs finaux | `IncidentReport` (JSON) |

### Technologies Recommandées
* **Rules Engine :** `Durable Rules` ou `Python ` `decision` (library de Decision Trees)
* **État :** State machine avec `transitions` (Python library)
* **Format de Sortie :** JSON Schema validé (`pydantic` models)

---

## 10. AI Recommendation Engine

### Rôle
L'**AI Recommendation Engine** produit des playbooks de réponse aux incidents (IR Playbooks) entièrement contextualisés, exploitant la base de connaissances RAG locale et les modèles LLM de sécurité pour générer des recommandations actionnables par les équipes SOC.

### Responsabilités
* **Génération de Playbooks de Réponse :** Production d'un plan structuré en 4 phases opérationnelles.
* **Contextualisation par la Base RAG :** Enrichissement des recommandations par les données historiques, les procédures internes et les cas précédents stockés dans la base vectorielle (RAG).
* **Personnalisation par Actif :** Adaptation des recommandations en fonction du type d'actif compromis (serveur AD, base de données, poste utilisateur, équipement réseau).
* **Priorisation des Actions :** Classement des actions recommandées par urgence et par impact potentiel.
* **Génération de Rapports SOC :** Production d'un résumé textuel formaté pour le rapport d'incident destiné au responsable SOC.

### Fonctionnement & Pipeline
```
+------------------+      +------------------+      +------------------+
| Décision Engine  | ---> | Contexte Incident | ---> |  RAG Knowledge   |
| (Incident + IOC) |      |  + Assets Métier  |      |  Base Vectorielle|
+------------------+      +------------------+      +--------+---------+
                                                                |
                                                                v
+------------------+      +------------------+      +------------------+
| SmolLM2-1.7B     | <--- | Prompt Template  | <--- | Context Retrieval|
| Synthèse Rapide  |      | Construction     |      | (Top-K Documents)|
+------------------+      +------------------+      +------------------+
         |
         v
+------------------+      +------------------+
| Qwen2.5-1.5B     | ---> | Validation &     |
| Structuration    |      | Enrichissement   |
+------------------+      +------------------+
         |
         v
+------------------------------------------------------------------+
|           Playbook IR Structuré (4 Phases + Prévention)          |
+------------------------------------------------------------------+
```

### Les 4 Phases du Playbook de Réponse

| Phase | Objectif | Actions Générées | SLA |
|:---|:---|:---|:---|
| **1. Confinement** | Stopper la propagation immédiate | Isolation EDR, blocage IP/DNS Firewall, quarantaine email | < 15 min |
| **2. Éradication** | Supprimer la menace | Suppression persistances (regedit, cron), purge boîtes mail, rollback de config | < 4 h |
| **3. Récupération** | Restaurer l'état nominal | Réinitialisation credentials, restauration backups, validation intégrité | < 24 h |
| **4. Prévention** | Éviter la récidive | Règle Yara/Sigma, politique de blocage, formation sensibilisation, mise à jour correctifs | < 7 j |

### Algorithme de Génération de Recommandations
1. **Analyse du Contexte Incident :** Extraction des attributs critiques (type, score, IOCs, assets, MITRE TTPs).
2. **Requête RAG :** Interrogation de la base vectorielle avec les embeddings du contexte (`all-MiniLM-L6-v2`) pour récupérer les playbooks similaires et les procédures standards.
3. **Construction du Prompt :** Template structuré injectant les preuves, le contexte RAG, et les contraintes SOC (niveau de l'analyste cible, temps de réponse max).
4. **Inférence LLM Rapide (SmolLM2) :** Génération initiale du playbook en langage naturel (~500 tokens) avec priorisation des actions.
5. **Validation & Structuration (Qwen2.5) :** Reformatage en JSON structuré avec vérification de la cohérence des actions recommandées.
6. **Post-Traitement :** Vérification que les commandes et actions générées sont syntaxiquement valides et que les IOCs sont correctement référencés.

### Entrées / Sorties
| Type | Description | Format |
|:---|:---|:---|
| **Entrées** | Incident consolidé (type, score, IOCs, MITRE, assets), Contexte RAG | `IncidentReport` + `List[Document]` |
| **Sorties** | Playbook IR structuré (4 phases + prévention), Rapport SOC textuel | `PlaybookIR` (JSON+Markdown) |

### Technologies Recommandées
* **RAG Vector DB :** `ChromaDB` (embarqué) ou `Qdrant` (production) pour le stockage des playbooks historiques
* **Embeddings :** `sentence-transformers/all-MiniLM-L6-v2`
* **LLM Orchestration :** `LangChain` ou `Haystack` pour le chaînage SmolLM2 → Qwen2.5
* **Template Engine :** `Jinja2` pour la construction des prompts SOC
* **Format de Sortie :** Markdown structuré + JSON (double format pour affichage et interopérabilité SOAR)

---

## 11. Architecture Logique & Diagrammes ASCII

### A. Architecture Globale
```
+---------------------------------------------------------------------------------------------------+
|                                        SECURE RAG HUB API GATEWAY                                 |
+---------------------------------------------------------------------------------------------------+
                                                  | (Event Ingestion)
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                         AI SECURITY ENGINE                                        |
|                                                                                                   |
|  +--------------------+      +--------------------+      +--------------------+      +---------+  |
|  |   AI Orchestrator  | <--> | AI Model Registry  | <---> |  Inference Layer   | <--> |   RAG   |  |
|  +---------+----------+      +--------------------+      +--------------------+      +---------+  |
|            |                                                                                      |
|            v                                                                                      |
|  +--------------------+      +--------------------+      +--------------------+                   |
|  |  Consensus Engine  | <--> |  Correlation Eng.  | <---> |    Risk Engine     |                   |
|  +---------+----------+      +--------------------+      +---------+----------+                   |
|            |                                                       |                              |
|            +--------------------------+----------------------------+                              |
|                                       v                                                           |
|  +--------------------+      +--------------------+      +--------------------+                   |
|  | Explainable AI XAI | <--> |   Decision Engine  | <---> | Recommendation Eng |                   |
|  +--------------------+      +--------------------+      +--------------------+                   |
+---------------------------------------------------------------------------------------------------+
                                                  | (Structured Decison output)
                                                  v
+---------------------------------------------------------------------------------------------------+
|                                  SOC DASHBOARD & SOAR PLAYBOOKS                                   |
+---------------------------------------------------------------------------------------------------+
```

---

### B. Flux de Données & Traitement (Data Flow)
```
[Evenement Brut] 
       |
       v
(1) Normalisation  --> (JSON standardisé)
       |
       v
(2) Query Classifier -> (Classification de Domaine, ex: Phishing)
       |
       v
(3) Model Routing ----> (Activation de CySecBERT & PhishSense + Qwen2.5)
       |
       v
(4) Inférence --------> (Predictions Parallèles GPU/CPU)
       |
       v
(5) Consensus Engine -> (Moyenne de confiance pondérée + similarité de vote)
       |
       v
(6) Correlation Engine  (Mapping MITRE, enrichment d'IOCs sémantiques)
       |
       v
(7) Risk Engine ------> (Formules Mathématiques RS / Likelihood / Impact)
       |
       v
(8) Explainable AI ---> (Integrated Gradients + Justification en langage naturel)
       |
       v
(9) Decision Engine --> (Fiche d'incident structurée + Playbook de Remédiation)
```

---

### C. Pipeline d'Inférence (Inference Pipeline)
```
              +----------------------------+
              | Requête d'Inférence Brut   |
              +--------------+-------------+
                             |
                             v
              +--------------+-------------+
              |      Dynamic Batcher       |
              +--------------+-------------+
                             | (Batch 5ms)
                             v
              +--------------+-------------+
              |   Inference Layer Router   |
              +--------+-------------+-----+
                       |             |
            (GPU/CUDA) v             v (CPU-ONNX)
              +--------+----+   +----+--------+
              | Transformer |   |  BERT / CNN  |
              +--------+----+   +----+--------+
                       |             |
                       +------+------+
                              |
                              v
              +--------------+-------------+
              |   Post-Processing / Cast   |
              +--------------+-------------+
                             |
                             v
              +--------------+-------------+
              |    Output Logits/Tokens    |
              +----------------------------+
```

---

### D. Pipeline de Consensus (Consensus Pipeline)
```
          +-------------------+         +-------------------+
          | Inférence Modèle A|         | Inférence Modèle B|
          +---------+---------+         +---------+---------+
                    |                               |
                    v                               v
          +---------+-------------------------------+---------+
          |         Filtrage par Seuil de Confiance (>=Tc)    |
          +-------------------------+-------------------------+
                                    |
                                    v
          +-------------------------+-------------------------+
          |         Calcul des Poids Dynamiques (Wm)          |
          +-------------------------+-------------------------+
                                    |
                                    v
          +-------------------------+-------------------------+
          |     Calcul du Score Global de Consensus (Sg)      |
          +-------------------------+-------------------------+
                                    |
                                    v
          +-------------------------+-------------------------+
          |       Analyse de Similitude Textuelle (Jaccard)   |
          +-------------------------+-------------------------+
                                    |
                +-------------------+-------------------+
                |                                       |
    (Similitude >= 0.60)                    (Similitude < 0.60)
                v                                       v
    [Consensus Établi]                    [Contradiction Détectée]
     Score Fusionné                        Règle Fail-Safe Activée
     Justification LLM                     Rétrogradation Confiance
```

---

### E. Pipeline de Corrélation (Correlation Pipeline)
```
+------------------+   +------------------+   +------------------+
|    Logs Bruts    |   |  Fichiers PE     |   |   Trafic PCAP    |
+--------+---------+   +--------+---------+   +--------+---------+
         |                      |                      |
         +----------------------+----------------------+
                                |
                                v
               +----------------+----------------+
               |     Extraction d'Indicateurs    |
               |      (IP, Hashes, Domaines)     |
               +----------------+----------------+
                                |
                                v
               +----------------+----------------+
               |  Graphe d'Attaque Dirigé (DAG)  |
               +----------------+----------------+
                                | (Lien Temporel & Sémantique)
                                v
               +----------------+----------------+
               |    Enrichissement de CVE &      |
               |       Tactiques MITRE           |
               +----------------+----------------+
                                |
                                v
               +----------------+----------------+
               |     Preuves Multi-Vectorielles  |
               +---------------------------------+
```

---

### F. Pipeline de Décision (Decision Pipeline)
```
              +----------------------------+
              |     Preuves Corrélées      |
              +--------------+-------------+
                             |
                             v
              +--------------+-------------+
              |        Risk Assessment     |
              |       (Calcul de Score)    |
              +--------------+-------------+
                             |
                             v
              +--------------+-------------+
              |     Decision Engine Matrix |
              +--------------+-------------+
                             |
                +------------+------------+
                |                         |
          (Score >= 50)             (Score < 50)
                v                         v
        [Lever Incident]           [Alerte Passive]
        - Niveau Criticité P1-P3    - Enregistrement Audit
        - Extraction IOCs           - Niveau P4 (Info)
        - Playbook IR Activé
```

---

### G. Pipeline Complet (Full End-to-End Pipeline)
```
+------------------------------------------------------------------+
|         ENTRÉE : Événement Brut (Email, Log, PE, URL, Image)     |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    1. PRÉTRAITEMENT                                               |
|    - Normalisation & Parsing                                     |
|    - Extraction des pièces jointes & URLs                        |
|    - Hashing (SHA-256) pour déduplication cache                  |
|    - Classification de domaine (QueryClassifierAgent)            |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    2. SÉLECTION DU DOMAINE                                       |
|    - Identification des domaines applicables                     |
|    - Détermination du workflow (phishing, malware, réseau, etc.) |
|    - Sélection du type d'inférence (single ou multi-domaine)     |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    3. SÉLECTION AUTOMATIQUE DES MODÈLES                          |
|    - Interrogation du Model Registry                             |
|    - Sélection des 2 modèles par domaine détecté                 |
|    - Allocation CPU/GPU par modèle                               |
|    - Activation du modèle LLM de synthèse (Qwen2.5 / SmolLM2)   |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    4. INFÉRENCE PARALLÈLE                                        |
|    - Exécution concurrente asyncio.gather()                      |
|    - Dynamic Batching (fenêtre 5ms)                              |
|    - GPU: PhishSense, Qwen2.5, SmolLM2, TrOCR                   |
|    - CPU: CySecBERT, MalBERT, MalConv, URLBERT, etc.            |
|    - Monitoring des temps d'inférence & métriques Prometheus     |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    5. CONSENSUS PAR DOMAINE                                      |
|    - Filtrage par seuil de confiance (Tc >= 80)                  |
|    - Calcul du Score Global Pondéré (Sg)                         |
|    - Analyse de similarité textuelle (Jaccard)                   |
|    - Détection de contradictions                                 |
|    - Synthèse LLM des résultats (accord/désaccord)               |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    6. CORRÉLATION MULTI-VECTORIELLE                              |
|    - Extraction des entités pivots (IP, hash, domaines, users)   |
|    - Construction du DAG d'attaque                               |
|    - Fenêtre temporelle glissante (2h)                           |
|    - Croisement IOC ↔ CVE ↔ MITRE ATT&CK                        |
|    - Fusion des preuves multi-domaines                           |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    7. CALCUL DU RISQUE                                           |
|    - Likelihood = f(Confiance, Preuve technique)                 |
|    - ImpactScore = f(TypeAttaque, Actif)                         |
|    - RiskScore = RS = min(Likelihood×Impact×Consensus×γ/100,100) |
|    - SeverityScore = 0.4×Consensus + 0.3×Likelihood + 0.3×Impact|
|    - Génération vecteur CVSS v3.1 simulé                         |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    8. MITRE MAPPING                                              |
|    - AttackBERT: classification multi-label (150+ techniques)    |
|    - Construction de la chaîne d'attaque complète                |
|    - Mapping Tactique → Technique → Procédure (TTP)             |
|    - Vérification de cohérence de la kill chain                  |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    9. EXPLAINABLE AI (XAI)                                       |
|    - Feature attribution (Integrated Gradients / SHAP)           |
|    - Extraction des tokens critiques                             |
|    - Cartes d'attention multi-têtes                              |
|    - Justification en langage naturel (LLM synthèse)             |
|    - Règles SOC appliquées listées                               |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    10. DÉCISION FINALE                                           |
|     - Classification finale (Phishing, Ransomware, etc.)         |
|     - Matrice de décision multi-critères                         |
|     - Attribution P1-P4                                          |
|     - Décision : BLOCK / ACCEPT / INVESTIGATE                    |
|     - Génération du Décision Journal                             |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    11. RECOMMANDATIONS & PLAYBOOK IR                             |
|     - Requête RAG (base vectorielle de playbooks)                |
|     - Génération SmolLM2 rapide                                  |
|     - Structuration Qwen2.5                                      |
|     - 4 phases : Confinement → Éradication → Récupération → Prév.|
|     - Rapport SOC formaté (JSON + Markdown)                      |
+------------------------------------------------------------------+
                              |
                              v
+------------------------------------------------------------------+
|    12. PUBLICATION & RÉPONSE SOC                                 |
|     - Envoi vers SIEM / SOAR                                     |
|     - Ticketing (P1-P4 selon priorité)                           |
|     - Notification des équipes d'astreinte                       |
|     - Archivage dans le journal d'audit                          |
+------------------------------------------------------------------+
```

---

### H. Pipeline IA Multi-Domaine (Multi-Domain AI Pipeline)
```
                         +---------------------------+
                         |  Requête Multi-Domaine   |
                         |  (Email + URL + PE)      |
                         +------------+-------------+
                                      |
                    +-----------------+------------------+
                    |                                    |
                    v                                    v
       +------------+-------------+         +------------+-------------+
       |    Domaine Email         |         |    Domaine Malware       |
       |  CySecBERT + PhishSense  |         |    MalBERT + MalConv     |
       +------------+-------------+         +------------+-------------+
                    |                                    |
                    v                                    v
       +------------+-------------+         +------------+-------------+
       | Consensus Email          |         | Consensus Malware        |
       | (Score, Confiance)       |         | (Score, Confiance)       |
       +------------+-------------+         +------------+-------------+
                    |                                    |
                    +-----------------+------------------+
                                      |
        +-----------------------------+-----------------------------+
        |                                                           |
        v                                                           v
+-------+-----------------------------+     +--------------------+--+---+
|   Domaine URL Analysis              |     |   Domaine Log       |      |
|   URLBERT + URLNet                  |     |   LogBERT + DeepLog |      |
+-------+-----------------------------+     +--------------------+-------+
        |                                                           |
        v                                                           v
+-------+-----------------------------+     +--------------------+-------+
| Consensus URL                       |     | Consensus Log              |
| (Score, Confiance)                  |     | (Score, Confiance)         |
+-------------------------------------+     +----------------------------+
        |                                                           |
        +-----------------------------+-----------------------------+
                                      |
                                      v
                    +-----------------+------------------+
                    |    Corrélation Globale             |
                    |    (DAG Multi-Vectoriel)           |
                    +-----------------+------------------+
                                      |
                                      v
                    +-----------------+------------------+
                    |    Risk Engine Composite           |
                    |    + XAI + Decision                |
                    +-----------------+------------------+
                                      |
                                      v
                    +-----------------+------------------+
                    |    Recommandations IR              |
                    |    (Playbook Multi-Vecteur)        |
                    +------------------------------------+
```

---

### I. Cycle de Vie des Modèles (Model Lifecycle Pipeline)
```
+---------------------------+       +---------------------------+
|   TÉLÉCHARGEMENT         | ----> |   VALIDATION              |
|   Hugging Face Hub       |       |   Tests de performance    |
|   Version sémantique     |       |   Évaluation F1           |
+---------------------------+       +---------------------------+
                                              |
                                              v
+---------------------------+       +---------------------------+
|   QUANTIFICATION          | <---- |   ENREGISTREMENT          |
|   FP16 / INT8 / AWQ       |       |   Model Registry          |
|   ONNX Conversion         |       |   Metadata + Metrics      |
+---------------------------+       +---------------------------+
                                              |
                                              v
+---------------------------+       +---------------------------+
|   CHARGEMENT              |       |   INFÉRENCE              |
|   Dynamic Loading         |       |   Active Predictions      |
|   GPU/CPU Allocation      |       |   Monitoring temps réel   |
+---------------------------+       +---------------------------+
                                              |
                                              v
+---------------------------+       +---------------------------+
|   DÉCHARGEMENT            |       |   MISE À JOUR            |
|   Libération VRAM/RAM     |       |   Nouvelle version        |
|   Cache vidé (TTL expiré) |       |   A/B Testing             |
+---------------------------+       +---------------------------+
```

---

## 12. Cycle de Pipeline Complet End-to-End

Le traitement complet d'un événement au sein de l'**AI Security Engine** s'effectue selon le cycle séquentiel et parfaitement auditable suivant 12 étapes :

```
Entrée
  ↓
1. Prétraitement
  ↓
2. Sélection du Domaine
  ↓
3. Sélection Automatique des Modèles
  ↓
4. Inférence Parallèle
  ↓
5. Consensus
  ↓
6. Corrélation
  ↓
7. Calcul du Risque
  ↓
8. MITRE Mapping
  ↓
9. Explainable AI (XAI)
  ↓
10. Décision
  ↓
11. Recommandations
  ↓
12. Réponse SOC
```

### Étape 1 : Prétraitement
* **Action :** Nettoyage du HTML, détection d'encodages anormaux (Base64 masqué), extraction des pièces jointes (fichiers PE, PDF, images) et des URLs, calcul du hash SHA-256 pour déduplication via le cache Redis.
* **Technologies :** `BeautifulSoup` (HTML), `PyMuPDF` (PDF), `Pillow` (images), `hashlib` (SHA-256).
* **Sortie :** `NormalizedEvent` (JSON structuré, schéma validé Pydantic).

### Étape 2 : Sélection du Domaine
* **Action :** Le `QueryClassifierAgent` (classifieur TF-IDF + Regression Logistique ou petit BERT) évalue l'alerte et détecte les probabilités par domaine (ex: `email: 0.95`, `malware: 0.88`, `url: 0.92`).
* **Règle :** Si `P(domaine) >= 0.60`, le domaine est activé.
* **Sortie :** `List[Domain]` des domaines sélectionnés avec leurs scores.

### Étape 3 : Sélection Automatique des Modèles
* **Action :** L'Orchestrateur interroge le **AI Model Registry** et sélectionne **2 modèles par domaine** :
  * Email → `CySecBERT` (CPU) + `PhishSense` (GPU)
  * Web → `CodeBERT` (CPU) + `GraphCodeBERT` (CPU)
  * Network → `NetBERT` (CPU) + `FlowTransformer` (CPU)
  * Malware → `MalBERT` (CPU) + `MalConv` (CPU)
  * Threat Intel → `AttackBERT` (CPU) + `IOCBERT` (CPU)
  * URL → `URLBERT` (CPU) + `URLNet` (CPU)
  * Logs → `LogBERT` (CPU) + `DeepLog` (CPU)
  * OCR → `PaddleOCR` (CPU) + `TrOCR` (GPU)
  * LLM → `Qwen2.5-1.5B` (GPU) + `SmolLM2-1.7B` (GPU)
* **Allocation :** CPU pour modèles < 500M params, GPU pour LLMs.
* **Sortie :** `ModelExecutionPlan`.

### Étape 4 : Inférence Parallèle
* **Action :** Lancement concurrent (`asyncio.gather`) via l'Inference Layer. Dynamic batching (fenêtre 5ms) pour GPU. Monitoring Prometheus de chaque inférence.
* **Fallback :** Timeout >30s ou OOM → bascule CPU quantifié.
* **Sortie :** `Dict[ModelID, InferenceResult]`.

### Étape 5 : Consensus
* **Action :** Algorithme **Weighted Confidence Average** par domaine :
  1. Filtrage : `P_m < Tc=80` → rejet.
  2. Poids dynamiques `W_m` par palier.
  3. Score global `S_g = sum(P_m * W_m) / sum(W_m)`.
  4. Similarité Jaccard >= 0.60 → **Consensus Atteint**.
  5. Sinon → **Contradiction** → Règle Fail-Safe.
* **Sortie :** `Dict[Domain, ConsensusResult]`.

### Étape 6 : Corrélation
* **Action :** Construction du **Graphe d'Attaque Dirigé (DAG)** : extraction des entités pivots (IPs, hashes, domaines), fenêtre temporelle 2h, croisement IOC ↔ CVE ↔ MITRE ATT&CK, fusion multi-vectorielle.
* **Sortie :** `AttackTimeline` (DAG, techniques MITRE, IOCs enrichis, CVEs).

### Étape 7 : Calcul du Risque
* **Formules :**
  * `Likelihood = clamp((AvgConf + ConsensusScore)/2 * alpha, 0, 100)` avec `alpha=1.15` si IOC/CVE, sinon `1.0`.
  * `ImpactScore = clamp(BaseImpact + sum(AssetWeight), 1.0, 10.0)`.
  * `RS = min((Likelihood/100) * ImpactScore * 10 * (ConsensusScore/100) * gamma, 100)`.
  * `SeverityScore = clamp(0.4*Consensus + 0.3*Likelihood + 0.3*(Impact*10), 0, 100)`.
  * Priorité: P1 (>=90), P2 (75-89), P3 (50-74), P4 (<50).
* **Sortie :** `RiskAssessment`.

### Étape 8 : MITRE Mapping
* **Action :** `AttackBERT` classification multi-label (150+ techniques). Construction de la kill chain complète (TA0001 → TA0040). Vérification de cohérence.
* **Sortie :** `MITREChain` (TTPs ordonnées avec scores de confiance).

### Étape 9 : Explainable AI (XAI)
* **Action :** Integrated Gradients / SHAP pour l'attribution de features. Cartes d'attention multi-têtes. Qwen2.5 génère une justification en langage naturel structurée (JSON) avec tokens critiques et règles appliquées.
* **Sortie :** `XAIExplanation`.

### Étape 10 : Décision
* **Action :** Matrice de décision multi-critères. Classification finale. Attribution P1-P4. Décision: `BLOCK` / `ACCEPT` / `INVESTIGATE`. Génération du **Décision Journal** horodaté.
* **Sortie :** `DecisionJournal`.

### Étape 11 : Recommandations
* **Action :** Requête RAG (ChromaDB/Qdrant) sur la base vectorielle de playbooks. SmolLM2 génération rapide (~500 tokens). Qwen2.5 structuration JSON. 4 phases : Confinement → Éradication → Récupération → Prévention.
* **Sortie :** `PlaybookIR` (JSON + Markdown).

### Étape 12 : Réponse SOC
* **Action :** Publication vers SIEM (format CEF/LEEF), SOAR (déclenchement automatique si P1/P2), ticketing, notifications (email/Slack/Teams), archivage dans le Decision Journal.
* **Sortie :** Confirmation de publication, ID d'incident, timestamp.
