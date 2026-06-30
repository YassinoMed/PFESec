# Rapport de Validation - SecureRAG Hub / AI Security Council

**Date :** 28/06/2026 13:50
**Mode :** Direct

## Resume

| Metrique | Valeur |
|---|---|
| Total | 3 |
| ? PASS | **0** (0.0%) |
| ? FAIL | 3 (100.0%) |
| ?? ERROR | 0 (0%) |
| ?? SKIP | 0 |

---
## Resultats par categorie

| Categorie | Total | PASS | FAIL | ERROR | Taux succes |
|---|---|---|---|---|---|
| Classification | 2 | 0 | 2 | 0 | 0.0% |
| Entrees limites | 1 | 0 | 1 | 0 | 0.0% |

---
## Detail des tests

| ID | Priorite | Categorie | Titre | Resultat | Entree | Attendu | Obtenu | Experts | Consensus | Confiance | Latence | DJ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T09 | PRIORITE 3 - | Classification | Email avec plusieurs URLs | ? FAIL | Consultez http://url1.com et http://url2 | PHISHING + liste URLs | LIEN MALVEILLANT CONFIRMÉ | url_expert, phishing_expert, i | 100.0% | High | 0.0s | ? |
| T10 | PRIORITE 3 - | Classification | Email imitant Microsoft | ? FAIL | From: security@microsoft-support.com
Sub | PHISHING SPEARPHISHING | LIEN MALVEILLANT CONFIRMÉ | url_expert, phishing_expert, i | 100.0% | High | 0.0s | ? |
| T72 | PRIORITE 3 - | Entrees limites | Email tres court (5 mots) | ? FAIL | Votre compte est suspendu | Traite avec incertitude | Score: 82.0% (incertitude normale pour e |  | 82.0% | High | 0.0s | ? |

---
## Tests necessitant verification manuelle

Les tests suivants marques comme PASS necessitent une verification humaine :

| ID | Test | Raison |
|---|---|---|

---
*Rapport genere automatiquement par test_validation_suite.py le 2026-06-28 13:50*