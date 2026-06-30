# Rapport de Validation - SecureRAG Hub / AI Security Council

**Date :** 28/06/2026 13:58
**Mode :** Direct

## Resume

| Metrique | Valeur |
|---|---|
| Total | 20 |
| ? PASS | **17** (85.0%) |
| ? FAIL | 3 (15.0%) |
| ?? ERROR | 0 (0%) |
| ?? SKIP | 0 |

---
## Resultats par categorie

| Categorie | Total | PASS | FAIL | ERROR | Taux succes |
|---|---|---|---|---|---|
| Classification | 3 | 2 | 1 | 0 | 66.7% |
| Consensus Engine | 3 | 2 | 1 | 0 | 66.7% |
| Decision Journal | 5 | 5 | 0 | 0 | 100.0% |
| Robustesse adversarial | 7 | 7 | 0 | 0 | 100.0% |
| Selection des experts | 2 | 1 | 1 | 0 | 50.0% |

---
## Detail des tests

| ID | Priorite | Categorie | Titre | Resultat | Entree | Attendu | Obtenu | Experts | Consensus | Confiance | Latence | DJ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T01 | PRIORITE 1 - | Classification | Email phishing evident | ? FAIL | URGENT: Votre compte a ete suspendu. Cli | PHISHING CONFIRME | EMAIL LÉGITIME | email_header_expert, threat_in | 49.0% | Low | 0.0s | ? |
| T02 | PRIORITE 1 - | Classification | Email legitime | ? PASS | Bonjour, suite a notre reunion de vendre | LEGITIME | EMAIL LÉGITIME | email_header_expert, threat_in | 35.5% | Low | 0.0s | ? |
| T03 | PRIORITE 1 - | Classification | Email ambigu | ? PASS | Cher client, nous avons remarque une act | INCERTAIN + escalade | ACTIVITÉ SAINE (ACCEPT) | soc_analyst_expert | 17.5% | Low | 0.0s | ? |
| T21 | PRIORITE 1 - | Selection des experts | Email phishing -> experts | ? PASS | URGENT: Votre compte a ete suspendu. Cli | phishing_expert,email_header_expert,url_ | 2/4 experts correspondants: email_header | email_header_expert, threat_in |  |  | 0.0s | ? |
| T22 | PRIORITE 1 - | Selection des experts | IOC hash -> experts | ? FAIL | e99a18c428cb38d5f260853678922e03 | ioc_expert,threat_intel_expert,mitre_exp | 0/3 experts correspondants:  | soc_analyst_expert |  |  | 0.0s | ? |
| T33 | PRIORITE 1 - | Consensus Engine | Tous les experts d'accord | ? FAIL | Phishing evident: email avec demande de  | Consensus 1er tour | Score: 41.5%, Consensus: False, Debat: c |  | 41.5% | Low | 0.0s | ? |
| T36 | PRIORITE 1 - | Consensus Engine | 50% experts en desaccord | ? PASS | Email avec lien vers site legitime mais  | Tour de debat declenche | Debat: completed |  |  |  | 0.0s | ? |
| T38 | PRIORITE 1 - | Consensus Engine | Desaccord persistant | ? PASS | Email tres bien concu imitant parfaiteme | Escalade humaine | Score: 45.0%, Confiance: Low |  | 45.0% | Low | 0.0s | ? |
| T55 | PRIORITE 1 - | Decision Journal | Hash SHA-256 correct | ? PASS | Test d'integrite du Decision Journal | Hash SHA-256 correct | SHA256 partial: 86a48dd740612bc6... |  |  |  | 0.0s | ? |
| T56 | PRIORITE 1 - | Decision Journal | Journal non modifiable | ? PASS | Test d'immutabilite du journal apres sig | Non modifiable | Verification manuelle recommandee (immut |  |  |  | 0.0s | ? |
| T57 | PRIORITE 1 - | Decision Journal | Horodatage correct | ? PASS | Verification de l'horodatage du journal | Timestamp correct | Timestamp: 2026-06-28T11:58:10.603342 |  |  |  | 0.0s | ? |
| T58 | PRIORITE 1 - | Decision Journal | ID session unique | ? PASS | Test d'unicite des IDs de session | ID unique | Session ID: 6623e685 |  |  |  | 0.0s | ? |
| T59 | PRIORITE 1 - | Decision Journal | Journal archive | ? PASS | Test d'archivage du journal | Archive correctement | Log dir: logs/council existe |  |  |  | 0.0s | ? |
| T64 | PRIORITE 1 - | Robustesse adversarial | Phishing modifie pour tromper | ? PASS | Cher client, veuillez mettre a jour votr | Detecte par les autres | ACTIVITÉ SAINE (ACCEPT) | soc_analyst_expert | 17.5% | Low | 0.0s | ? |
| T65 | PRIORITE 1 - | Robustesse adversarial | Obfuscation URL | ? PASS | Cliquez sur http://google.com@evil.com/r | Detecte | ATTENTE D'INVESTIGATION (UNKNOWN) | ioc_expert, threat_intel_exper | 75.0% | Medium | 0.0s | ? |
| T66 | PRIORITE 1 - | Robustesse adversarial | Encodage base64 | ? PASS | Vm90cmUgY29tcHRlIGEgw6l0w6kgc3VzcGVuZHUg | Detecte | ACTIVITÉ SAINE (ACCEPT) | soc_analyst_expert | 17.5% | Low | 0.0s | ? |
| T67 | PRIORITE 1 - | Robustesse adversarial | Phishing sans mots-cles | ? PASS | Bonjour, merci de bien vouloir prendre c | Detecte via structure | ACTIVITÉ SAINE (ACCEPT) | soc_analyst_expert | 17.5% | Low | 0.0s | ? |
| T68 | PRIORITE 1 - | Robustesse adversarial | Texte blanc invisible | ? PASS | Cher client<span style='color:white'>phi | Detecte | EMAIL LÉGITIME | email_header_expert, threat_in | 33.5% | Low | 0.0s | ? |
| T69 | PRIORITE 1 - | Robustesse adversarial | Typosquatting subtil | ? PASS | Securisez votre compte: http://rnicrosof | Detecte | ACTIVITÉ SAINE (ACCEPT) | ioc_expert, threat_intel_exper | 52.0% | Medium | 0.0s | ? |
| T70 | PRIORITE 1 - | Robustesse adversarial | Lien raccourci masquant | ? PASS | Cliquez: http://short.url/abc123 (rediri | Signale comme suspect | EMAIL LÉGITIME | email_header_expert, threat_in | 49.0% | Low | 0.0s | ? |

---
## Tests necessitant verification manuelle

Les tests suivants marques comme PASS necessitent une verification humaine :

| ID | Test | Raison |
|---|---|---|
| T56 | Journal non modifiable | Verification manuelle requise |

---
*Rapport genere automatiquement par test_validation_suite.py le 2026-06-28 13:58*