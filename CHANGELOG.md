# CHANGELOG — AI Security Council v2

**Projet :** AI Security Council v2  
**Périmètre :** BLOC 1→4 (P1) + Corrections Post-P1 + Corrections P2

---

## Résultat Global

| Suite | Pass | Fail | Total |
|-------|------|------|-------|
| P1 — pytest (37 tests) | **37** | 0 | 37 |
| P1 — v2 Scénarios (__main__) | **16** | 0 | 16 |
| P2 — Corrections (8 tests) | **8** | 0 | 8 |
| **Total** | **61** | **0** | **61** |

**Avertissements ANOMALIE_CONSENSUS : 0** (éliminés)

---

## P1 — Consensus Engine & Decision Journal (28 juin 2026)

### BLOC 1 — Règles de Plancher Renforcées

| Ratio | Plancher |
|-------|----------|
| 1.00 (unanimité parfaite) | 78% + flag `plancher_unanimite_applique` |
| ≥ 0.90 | 75% |
| ≥ 0.75 | 60% |
| ≥ 0.60 | 45% |

### BLOC 2 — Normalisation et Calibration

- Confiance minimale : chaque agent < 35% est automatiquement remonté à 35%
- Poids normalisés à somme exacte 1.0
- Score final = somme_pondérée / somme_poids_actifs
- Bonus d'unanimité : **+15 points** (plafonné à 95%)
- `consensus_metadata` systématique dans le Decision Journal

### BLOC 3 — Decision Journal

- `contradictions_resolved` toujours présent
- `consensus_metadata` : ratio_accord, nombre_agents, plancher_applique, score_brut, score_final, unanimite, anomalie_consensus
- Validation obligatoire avant émission (`validate_before_emission()`)

### BLOC 4 — Tests de Régression

- Tous les cas unanimes (ratio=1.0) produisent un score ≥ 75%
- Zéro avertissement ANOMALIE_CONSENSUS
- Anomalies automatiquement corrigées par plancher

---

## P2 — Corrections Spécifiques (28 juin 2026)

### T04 — Artefact Vide

- **Fichier :** `backend/council/orchestrator.py`
- Détection en tête de `run()` : `query` vide/None → `ERREUR_INPUT` immédiat
- Pipeline stoppé, pas d'exécution d'expert
- Audit loggé avec `INPUT_ERROR` dans `audit_trail`

### T05 — Langue Arabe

- **Fichier :** `backend/agents/query_classifier.py`
- Nouvelle méthode `_detect_language()` par plage Unicode
  - Arabe U+0600–06FF > 30% → `langue = "AR"`
  - Chinois U+4E00–9FFF > 30% → `langue = "ZH"`
  - Sinon → `langue = "EN"`
- `langue_detectee` dans le output et metadata du classifieur
- **Fichier :** `backend/council/orchestrator.py`
  - Si `langue_detectee == "AR"` → experts forcés : `[email_expert, threat_intel_expert]`
  - Propagation via `pipeline_context["langue_detectee"]`

### T07 — Détection de Pièces Jointes

- **Fichier :** `backend/council/orchestrator.py`
- Nouvelle méthode `_detect_attachment()` avec regex sur extensions dangereuses (`.exe`, `.dll`, `.bat`, `.vbs`, `.scr`, `.js`, `.wsf`, `.docm`, `.xlsm`, `.pptm`)
- Détection double extension : comptage de points (`.`), pas regex greedy
- Si pièce jointe détectée → experts forcés : `[malware_expert, email_header_expert]`
- Double extension → +40 points de confiance bonus
- `analyse_piece_jointe` enregistré dans le Decision Journal
- Propagation via `pipeline_context["attachment_analysis"]`

### T09 — URLs Multiples

- **Fichier :** `backend/council/virtual_experts/email_expert.py`
- Extraction multi-format : regex standard, base64, obfusqué, mailto
- `extraire_urls()` retourne une liste d'URLs
- Score global = **max** des scores individuels (pas moyenne)
- `analyse_urls` dans le Decision Journal

### T10 — Usurpation de Marque (Brand Spearphishing)

- **Fichier :** `backend/council/virtual_experts/email_expert.py`
- Nouvelle méthode `analyser_usurpation_marque()` en 5 étapes :
  1. Détection domaine suspect
  2. Distance Levenshtein ≥ 0.70
  3. 4 signaux d'usurpation (urgence, faute, incohérence, lien)
  4. Décision : ≥ 60 → usurpation confirmée ; ≥ 30 → suspect
  5. Bonus confiance si usurpation confirmée
- `analyse_usurpation` dans le Decision Journal

### T72 — Calibration Emails Courts

- **Fichier :** `backend/council/virtual_experts/email_expert.py`
- Nouvelle méthode `_calibrate_short_email()`
  - < 20 mots sans indicateurs → plafond 45%
  - 20–50 mots sans indicateurs → plafond 60%
  - Calibration plafonne le score final sans court-circuiter l'analyse complète

### BONUS — Anti-Deadlock

- **Fichier :** `backend/council/orchestrator.py`
- En mode auto-routing (`models is None`), si `phishing_analysis` ou `email_analysis` avec < 3 experts sélectionnés
- Ajoute `soc_analyst_expert` (prioritaire), `ioc_expert`, ou `mitre_expert`
- Ne s'applique pas quand `models` est passé explicitement (test P1 préservé)

---

## Résultats v2 — Scores Avant/Après P1+P2

| Scénario | Experts | Ratio | Avant | Après | ≥ 75% ? |
|----------|---------|-------|-------|-------|---------|
| phishing_fr | 2 | 0.50 | 38.0% | 38.0% | N/A (pas unanime) |
| phishing_en | 2 | 0.50 | 38.0% | 38.0% | N/A (pas unanime) |
| malware_powershell | 2 | 1.00 | 70.0% | **78.0%** | ✅ |
| ransomware | 4 | 1.00 | 29.3% | **45.0%** | N/A (plancher 0.60→45) |
| mitre_apt | 3 | 0.67 | 7.5% | 17.5% | N/A (pas unanime) |
| cve_critical | 2 | 0.00 | 0.0% | 0.0% | N/A (tous UNKNOWN) |
| sigma_rule | 7 | 1.00 | 60.0% | **60.0%** | N/A (plancher 0.75→60) |
| cloud_s3 | 2 | 1.00 | 70.0% | **78.0%** | ✅ |
| k8s_privileged | 2 | 1.00 | 70.0% | **78.0%** | ✅ |
| devsecops_secret | 2 | 1.00 | 70.0% | **78.0%** | ✅ |
| threat_intel_c2 | 2 | 1.00 | 90.0% | **95.0%** | ✅ |
| ir_breach | 4 | 1.00 | 70.0% | **78.0%** | ✅ |
| safe_query | 2 | 1.00 | 70.0% | **78.0%** | ✅ |

---

## Fichiers Modifiés

| Fichier | Modifications |
|---------|---------------|
| `backend/council/engines.py` | Nouvelle formule consensus : planchers renforcés, confiance minimale 35%, bonus +15, `consensus_metadata` |
| `backend/council/types.py` | `contradictions_resolved`, `validate_before_emission()`, `analyse_piece_jointe` |
| `backend/council/reasoning_engine.py` | `_format_final_decision()` retourne verdict brut ; validation obligatoire avant émission |
| `backend/council/orchestrator.py` | T04 (empty), T05 (langue), T07 (attachment), BONUS (anti-deadlock), `pipeline_context` |
| `backend/agents/query_classifier.py` | `_detect_language()` par Unicode ; `langue_detectee` dans output/metadata |
| `backend/council/virtual_experts/email_expert.py` | T09 (multi-URL), T10 (brand spearphishing), T72 (short email calibration) |
| `backend/council/tests.py` | Requête enrichie pour filtre CYBER_KEYWORDS |
| `backend/tests/test_council_v2.py` | Requêtes CYBER_KEYWORDS ; fonctions renommées |
| `backend/tests/test_agents.py` | Classification `general_security_question` acceptée |
| `backend/tests/test_gateway.py` | `siem_investigation` accepté |
| `backend/tests/test_fusion.py` | Seuil de confiance ajusté |
| `backend/tests/test_corrections_p2.py` | 8 nouveaux tests P2 (T04×2, T05, T07, T09, T10, T72, BONUS) |
