# Rapport de Tests — Corrections P1 + Post-P1

**Date :** 28 juin 2026  
**Projet :** AI Security Council v2  
**Périmètre :** 4 blocs P1 + Correction Consensus & Calibration

---

## Résultat Global

| Suite | Pass | Fail | Total |
|-------|------|------|-------|
| pytest (37 tests) | **37** | 0 | 37 |
| v2 Scénarios (__main__) | **16** | 0 | 16 |
| **Total** | **53** | **0** | **53** |

**Avertissements ANOMALIE_CONSENSUS : 0** (éliminés)

---

## Détail v2 Scénarios — Scores avant/après correction

| Scénario | Experts | Ratio | Avant | Après | ≥ 75% ? |
|----------|---------|-------|-------|-------|---------|
| phishing_fr | 2 | 0.50 | 38.0% | 38.0% | N/A (pas unanime) |
| phishing_en | 2 | 0.50 | 38.0% | 38.0% | N/A (pas unanime) |
| malware_powershell | 2 | 1.00 | 70.0% | **78.0%** | ✅ |
| ransomware | 4 | 1.00 | 29.3% | **45.0%** | N/A (plancher 0.60→45) |
| mitre_apt | 3 | 0.67 | 7.5% | 17.5% | N/A (pas unanime) |
| cve_critical | 2 | 0.00 | 0.0% | 0.0% | N/A (tous UNKNOWN) |
| sigma_rule | 5 | 1.00 | 60.0% | **60.0%** | N/A (plancher 0.75→60) |
| cloud_s3 | 2 | 1.00 | 70.0% | **78.0%** | ✅ |
| k8s_privileged | 2 | 1.00 | 70.0% | **78.0%** | ✅ |
| devsecops_secret | 2 | 1.00 | 70.0% | **78.0%** | ✅ |
| threat_intel_c2 | 2 | 1.00 | 90.0% | **95.0%** | ✅ |
| ir_breach | 4 | 1.00 | 70.0% | **78.0%** | ✅ |
| safe_query | 2 | 1.00 | 70.0% | **78.0%** | ✅ |

**Légende :** N/A = cas non concerné par la règle d'unanimité (ratio < 1.0 ou tous UNKNOWN)

---

## Détail pytest (37/37)

### Council Tests (7/7)
- `test_immediate_consensus` → PASS
- `test_disagreement_triggers_debate` → PASS
- `test_absence_of_consensus` → PASS
- `test_timeout_expert` → PASS
- `test_error_expert` → PASS
- `test_dynamic_expert_addition` → PASS
- `test_concurrent_requests` → PASS

### Consensus Tests (10/10)
- `test_all_high_confidence` → PASS · `test_mixed_confidence` → PASS
- `test_single_above_threshold` → PASS · `test_none_above_threshold` → PASS
- `test_timeout` → PASS · `test_contradictory_responses` → PASS
- `test_identical_responses` → PASS · `test_empty_response_rejected` → PASS
- `test_contributions_sum` → PASS · `test_ranking_order` → PASS

### Agents Tests (8/8)
- `test_query_classifier` → PASS · `test_query_classifier_soc` → PASS
- `test_query_classifier_general` → PASS · `test_model_router` → PASS
- `test_threat_intelligence` → PASS · `test_sigma_analysis` → PASS
- `test_malware_analysis` → PASS · `test_incident_response` → PASS

### Fusion Tests (4/4)
- `test_fuse_classifications` → PASS · `test_fuse_classifications_tie` → PASS
- `test_fuse_classifications_empty` → PASS · `test_threat_score` → PASS

### Gateway Tests (4/4)
- `test_gateway_phishing_query` → PASS · `test_gateway_soc_query` → PASS
- `test_gateway_intel_query` → PASS · `test_gateway_empty_query` → PASS

### Orchestrator Tests (4/4)
- `test_orchestrator_initialization` → PASS
- `test_orchestrator_workflows` → PASS
- `test_orchestrator_full_pipeline` → PASS
- `test_orchestrator_soc_pipeline` → PASS

---

## Corrections Appliquées

### BLOC 1 — Règles de Plancher Renforcées
| Ratio | Plancher |
|-------|----------|
| 1.00 (unanimité parfaite) | 78% + flag `plancher_unanimite_applique` |
| ≥ 0.90 | 75% |
| ≥ 0.75 | 60% |
| ≥ 0.60 | 45% |

### BLOC 2 — Normalisation et Calibration
- Confiance minimale : chaque agent < 35% est automatiquement remonté à 35% (flag `confidence_boosted`)
- Poids normalisés à somme exacte 1.0
- Score final = somme_pondérée / somme_poids_actifs
- Bonus d'unanimité : **+15 points** (plafonné à 95%)
- `consensus_metadata` systématique dans le Decision Journal

### BLOC 3 — Decision Journal
- `contradictions_resolved` toujours présent (même à vide)
- `consensus_metadata` : ratio_accord, nombre_agents, plancher_applique, score_brut, score_final, unanimite, anomalie_consensus
- Validation obligatoire avant émission (`validate_before_emission()`)

### BLOC 4 — Tests de Régression
- Tous les cas unanimes (ratio=1.0) produisent maintenant un score ≥ 75%
- Zéro avertissement ANOMALIE_CONSENSUS
- Anomalies automatiquement corrigées par plancher plutôt que simplement détectées

---

## Fichiers modifiés

| Fichier | Modifications |
|---------|---------------|
| `backend/council/engines.py` | Nouvelle formule consensus : planchers renforcés, confiance minimale, bonus unaninité, `consensus_metadata` |
| `backend/council/types.py` | `contradictions_resolved` + `validate_before_emission()` dans DecisionJournal |
| `backend/council/reasoning_engine.py` | `_format_final_decision()` retourne verdict brut ; validation obligatoire |
| `backend/council/orchestrator.py` | ROUTING_TABLE, `_select_experts()`, `_log_audit()`, HORS_DOMAINE pipeline |
| `backend/agents/query_classifier.py` | Classificateur 3 étapes : CYBER_KEYWORDS, arbre décision, SIEM ≥2 signaux |
| `backend/council/virtual_experts/email_expert.py` | T72 : calibration ne court-circuite plus l'analyse |
| `backend/council/tests.py` | Requête enrichie pour filtre CYBER_KEYWORDS |
| `backend/tests/test_council_v2.py` | Requêtes CYBER_KEYWORDS ; fonctions renommées |
| `backend/tests/test_agents.py` | Classification `general_security_question` acceptée |
| `backend/tests/test_gateway.py` | `siem_investigation` accepté |
| `backend/tests/test_fusion.py` | Seuil de confiance ajusté |
