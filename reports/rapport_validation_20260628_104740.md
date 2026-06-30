# Rapport de Validation - SecureRAG Hub / AI Security Council

**Date :** 28/06/2026 10:47
**Mode :** Direct

## Resume

| Metrique | Valeur |
|---|---|
| Total | 3 |
| ? PASS | **2** (66.7%) |
| ? FAIL | 1 (33.3%) |
| ?? ERROR | 0 (0%) |
| ?? SKIP | 0 |

---
## Resultats par categorie

| Categorie | Total | PASS | FAIL | ERROR | Taux succes |
|---|---|---|---|---|---|
| Classification | 3 | 2 | 1 | 0 | 66.7% |

---
## Detail des tests

| ID | Priorite | Categorie | Titre | Resultat | Entree | Attendu | Obtenu | Experts | Consensus | Confiance | Latence | DJ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T01 | PRIORITE 1 - | Classification | Email phishing evident | ? PASS | URGENT: Votre compte a ete suspendu. Cli | PHISHING CONFIRME | PHISHING CONFIRMÉ | phishing_expert, email_header_ | 100.0% | High | 0.0s | ? |
| T02 | PRIORITE 1 - | Classification | Email legitime | ? FAIL | Bonjour, suite a notre reunion de vendre | LEGITIME | EMAIL LÉGITIME | phishing_expert, email_header_ | 40.5% | Low | 0.0s | ? |
| T03 | PRIORITE 1 - | Classification | Email ambigu | ? PASS | Cher client, nous avons remarque une act | INCERTAIN + escalade | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 32.0% | Low | 0.0s | ? |

---
## Tests necessitant verification manuelle

Les tests suivants marques comme PASS necessitent une verification humaine :

| ID | Test | Raison |
|---|---|---|

---
*Rapport genere automatiquement par test_validation_suite.py le 2026-06-28 10:47*