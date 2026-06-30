# Architecture de Sélection Dynamique de Modèles

> Le cœur du projet n'est pas le nombre de modèles, mais l'architecture qui sélectionne dynamiquement 3-4 experts pertinents selon le contexte. Vingt modèles dans un registre ne valent rien si le routage est figé.

---

## Architecture

```
Requête → QueryClassifier → ModelRouter ─┬─ cysecbert (phishing)
                                           ├─ phishsense (phishing)
                                           ├─ qwen2_5_1_5b (SOC, raisonnement)
                                           ├─ smollm2_1_7b (synthèse, général)
                                           └─ 16 experts virtuels (heuristiques)
                   ↓
           EvidenceFusionEngine
                   ↓
           CouncilConsensusEngine
                   ↓
           Décision + Justification
```

### Les 3 pièces maîtresses

| Composant | Rôle | Fichier |
|-----------|------|---------|
| **Master AI (AIOrchestrator)** | Reçoit la requête, orchestre le pipeline complet : classification → routage → exécution experts → fusion → consensus → décision | `backend/council/orchestrator.py` |
| **Model Router** | Aiguille chaque requête vers 1-3 modèles seulement selon la classification (cyber, phishing, SOC, etc.) | `backend/routing/routing_engine.py` |
| **Evidence Fusion Engine** | Fusionne les preuves de sources multiples en un verdict unifié avec score de confiance | `backend/fusion/evidence_fusion.py` |
| **Virtual Expert Council** | 16 experts spécialisés (heuristiques) qui analysent sous tous les angles : email, malware, IOC, MITRE, SOC, cloud, k8s... | `backend/council/virtual_experts/` |

### Valeur ajoutée

- **Sélection contextuelle** : pas d'exécution systématique de tous les modèles → 3-4 experts par requête max
- **Délibération** : les experts votent, le Conseil débat si désaccord → `ConsensusEngine` avec planchers renforcés
- **Évolutivité** : le registre peut contenir N modèles, seuls les pertinents sont appelés
- **Résilience** : Evidence Fusion + Consensus = décision robuste même si un expert est défaillant

---

## Modèles Actifs dans le Pipeline d'Inférence

**4 modèles chargés en mémoire** (GPU/CPU) → les seuls réellement utilisés en production :

| ID | Modèle | Source HF | Présent sur HF ? | Chargé dans |
|---|---|---|---|---|
| `cysecbert` | CySecBERT | `markusbayer/CySecBERT` | ✅ Existe | `inference_server.py` (BERT classifier) |
| `phishsense` | Llama-Phishsense-1B | `AcuteShrewdSecurity/Llama-Phishsense-1B` | ✅ Existe | `inference_server.py` (LLM + LoRA) |
| `qwen2_5_1_5b` | Qwen2.5-1.5B-Instruct | `Qwen/Qwen2.5-1.5B-Instruct` | ✅ Existe | `inference_server.py` (LLM causal) |
| `smollm2_1_7b` | SmolLM2-1.7B-Instruct | `HuggingFaceTB/SmolLM2-1.7B-Instruct` | ✅ Existe | `inference_server.py` (LLM causal) |

---

## Modèles dans le Registre (Config Only — Mock Wrapper)

Ces 14 modèles ont une entrée dans le registre mais **ne sont pas chargés dans le pipeline d'inférence**. Le wrapper `GenericModelWrapper` retourne des données simulées (aléatoires).

### Problèmes d'existence sur Hugging Face

| ID | Source HF déclarée | Existe réellement ? | Statut |
|---|---|---|---|
| `secbert` | `jackaduma/SecBERT` | ✅ Existe | Chargé seulement dans `sec.py` (script standalone) |
| `codebert` | `microsoft/codebert-base` | ✅ Existe | Jamais chargé dans le pipeline |
| `graphcodebert` | `microsoft/graphcodebert-base` | ✅ Existe | Jamais chargé dans le pipeline |
| `netbert` | `icsi/netbert` | ❌ 401 — renommé | Existe sous `antoinelouis/netbert` |
| `securityllm` | `ZySec-AI/SecurityLLM` | ✅ Existe | Chargé seulement dans `sec.py` (script standalone) — l'agent `securityllm_synthesis` est un formateur de texte, pas un LLM |
| `malbert` | `malbert/malbert-base` | ❌ Introuvable | N'existe pas sur HF |
| `attackbert` | `da09/AttackBERT` | ❌ Introuvable | Proche : `basel/ATTACK-BERT` |
| `iocbert` | `da09/IOC-BERT` | ❌ Introuvable | N'existe pas sur HF |
| `urlbert` | `da09/URLBERT` | ❌ Introuvable | N'existe pas sur HF |
| `logbert` | `logbert/logbert` | ❌ Introuvable | Papier seulement (2103.04475) |
| `malconv` | — | ⚠️ Pas sur HF | Aucun code de chargement |
| `urlnet` | — | ⚠️ Pas sur HF | Aucun code de chargement |
| `deeplog` | — | ⚠️ Pas sur HF | Aucun code de chargement |
| `flowtransformer` | — | ⚠️ Pas sur HF | Aucun code de chargement |

### Modèles sans aucune implémentation

| ID | Problème | Détail |
|---|---|---|
| `paddleocr` | Aucun code PaddlePaddle | `import paddle` inexistant dans la base |
| `trocr_small` | Aucun code TrOCR | Aucun `from_pretrained` TrOCR |
| `all-MiniLM-L6-v2` | Juste une chaîne dans `config.py` | Aucun `SentenceTransformer()` instancié |

---

## Experts Virtuels (16 — Heuristiques, 0 GPU)

> Les experts virtuels sont le véritable moteur d'analyse. Ils n'ont pas besoin de GPU car ils appliquent des règles, regex, et algorithmes symboliques. Le Master AI les sélectionne dynamiquement (3-4 par requête).

| ID | Rôle | Catégorie | Code |
|---|---|---|---|
| `phishing_expert` | Phishing Analyst | phishing | `email_expert.py` |
| `email_header_expert` | Email Protocol Analyst | email_security | `email_expert.py` |
| `malware_expert` | Malware Analyst | malware_analysis | `malware_expert.py` |
| `threat_intel_expert` | Threat Intelligence Analyst | threat_intelligence | `threat_intel_expert.py` |
| `ioc_expert` | IOC Specialist | ioc_analysis | `ioc_expert.py` |
| `mitre_expert` | MITRE ATT&CK Analyst | mitre | `mitre_expert.py` |
| `sigma_expert` | Sigma Rules Analyst | sigma | `sigma_expert.py` |
| `incident_response_expert` | IR & DFIR Specialist | incident_response | `incident_response_expert.py` |
| `soc_analyst_expert` | SOC Triage Analyst | soc_operations | `soc_analyst_expert.py` |
| `rag_knowledge_expert` | Knowledge Base Analyst | rag | `rag_expert.py` |
| `vulnerability_expert` | Vulnerability Analyst | vulnerability | `vulnerability_expert.py` |
| `cloud_security_expert` | Cloud Security Analyst | cloud_security | `cloud_security_expert.py` |
| `kubernetes_security_expert` | K8s Security Analyst | kubernetes_security | `k8s_expert.py` |
| `devsecops_expert` | DevSecOps Analyst | devsecops | `devsecops_expert.py` |
| `risk_assessment_virtual_expert` | Risk Assessment Expert | risk_assessment | `email_expert.py` |
| `url_reputation_expert` | URL Reputation Expert | url_analysis | `email_expert.py` |

---

## Datasets de Fine-Tuning

| Dataset | Source HF | Tâche |
|---|---|---|
| phishing_email_dataset | `zefang-liu/phishing-email-dataset` | Phishing |
| cybersecurity_rules | `jcordon5/cybersecurity-rules` | Cyber général |
| trendyol_cybersecurity_instruction | `Trendyol/Trendyol-Cybersecurity-Instruction-Tuning-Dataset` | Cyber général |
| cybersecurity_32k_instruction | `Vanessasml/cybersecurity_32k_instruction_input_output` | Cyber général |
| cybersecurity_sharegpt | `ChaoticNeutrals/Cybersecurity-ShareGPT` | Cyber général |
| cybersecurity_llm_cve | `Bouquets/Cybersecurity-LLM-CVE` | CVE |
| cve_llm_training | `morpheuslord/cve-llm-training` | CVE |
| cybersecurity_eval | `CyberNative/CyberSecurityEval` | Évaluation seulement |

---

## Synthèse Honnête

| Catégorie | Quantité | Réellement actif ? |
|---|---|---|
| Modèles ML chargés dans le pipeline | **4** | ✅ Oui |
| Modèles dans le registre (mock) | **14** | ❌ Non — mock data seulement |
| Modèles avec HF ID inexistant | **5** | ❌ `da09/*` × 3, `malbert`, `logbert` |
| Modèles sans aucune implémentation | **3** | ❌ `paddleocr`, `trocr_small`, `all-MiniLM-L6-v2` |
| Experts virtuels (heuristiques) | **16** | ✅ Oui — sélection dynamique |
| **Total modèles réellement utiles** | **20** (4 ML + 16 virtuels) | |

> **Le registre de 20 modèles est une capacité d'extension, pas un inventaire d'exécution.** La valeur est dans le **Master AI** qui sélectionne 3-4 experts selon le contexte, la **Fusion** qui combine les preuves, et le **Consensus** qui tranche les désaccords.
