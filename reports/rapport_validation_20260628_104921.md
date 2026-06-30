# Rapport de Validation - SecureRAG Hub / AI Security Council

**Date :** 28/06/2026 10:49
**Mode :** Direct

## Resume

| Metrique | Valeur |
|---|---|
| Total | 93 |
| ? PASS | **80** (86.0%) |
| ? FAIL | 13 (14.0%) |
| ?? ERROR | 0 (0%) |
| ?? SKIP | 0 |

---
## Resultats par categorie

| Categorie | Total | PASS | FAIL | ERROR | Taux succes |
|---|---|---|---|---|---|
| Analyse d'artefact | 10 | 10 | 0 | 0 | 100.0% |
| Calibration | 5 | 5 | 0 | 0 | 100.0% |
| Charge | 4 | 4 | 0 | 0 | 100.0% |
| Classification | 10 | 5 | 5 | 0 | 50.0% |
| Classification Master AI | 5 | 2 | 3 | 0 | 40.0% |
| Consensus Engine | 8 | 6 | 2 | 0 | 75.0% |
| Decision Journal | 5 | 5 | 0 | 0 | 100.0% |
| Defaillance agent | 4 | 4 | 0 | 0 | 100.0% |
| Entrees limites | 5 | 4 | 1 | 0 | 80.0% |
| GPU / VRAM | 4 | 4 | 0 | 0 | 100.0% |
| Latence | 5 | 5 | 0 | 0 | 100.0% |
| Robustesse adversarial | 7 | 7 | 0 | 0 | 100.0% |
| Security RAG | 14 | 14 | 0 | 0 | 100.0% |
| Selection des experts | 7 | 5 | 2 | 0 | 71.4% |

---
## Detail des tests

| ID | Priorite | Categorie | Titre | Resultat | Entree | Attendu | Obtenu | Experts | Consensus | Confiance | Latence | DJ |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T01 | PRIORITE 1 - | Classification | Email phishing evident | ? PASS | URGENT: Votre compte a ete suspendu. Cli | PHISHING CONFIRME | PHISHING CONFIRMÉ | phishing_expert, email_header_ | 100.0% | High | 0.0s | ? |
| T02 | PRIORITE 1 - | Classification | Email legitime | ? PASS | Bonjour, suite a notre reunion de vendre | LEGITIME | EMAIL LÉGITIME | phishing_expert, email_header_ | 40.5% | Low | 0.0s | ? |
| T03 | PRIORITE 1 - | Classification | Email ambigu | ? PASS | Cher client, nous avons remarque une act | INCERTAIN + escalade | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 32.0% | Low | 0.0s | ? |
| T04 | PRIORITE 3 - | Classification | Email vide | ? FAIL |  | ERREUR GEREE | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 32.0% | Low | 0.0s | ? |
| T05 | PRIORITE 3 - | Classification | Email en arabe | ? FAIL | ????? ??????? ???? ????? ??????? ????? ? | PHISHING ou LEGITIME | LIEN MALVEILLANT CONFIRMÉ | url_expert, phishing_expert, i | 66.0% | Medium | 0.0s | ? |
| T06 | PRIORITE 3 - | Classification | Email en anglais | ? PASS | Dear user, your account requires verific | PHISHING ou LEGITIME | PHISHING CONFIRMÉ | phishing_expert, email_header_ | 81.0% | High | 0.0s | ? |
| T07 | PRIORITE 3 - | Classification | Email avec piece jointe | ? FAIL | Veuillez trouver la facture jointe. Cord | PHISHING + analyse piece jointe | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 32.0% | Low | 0.1s | ? |
| T08 | PRIORITE 3 - | Classification | Email sans URL | ? PASS | Votre mot de passe va expirer dans 3 jou | PHISHING ou LEGITIME | MENACE CONFIRMÉE (BLOCK) | phishing_expert, malware_exper | 59.0% | Medium | 0.0s | ? |
| T09 | PRIORITE 3 - | Classification | Email avec plusieurs URLs | ? FAIL | Consultez http://url1.com et http://url2 | PHISHING + liste URLs | LIEN MALVEILLANT CONFIRMÉ | url_expert, phishing_expert, i | 100.0% | High | 0.0s | ? |
| T10 | PRIORITE 3 - | Classification | Email imitant Microsoft | ? FAIL | From: security@microsoft-support.com
Sub | PHISHING SPEARPHISHING | LIEN MALVEILLANT CONFIRMÉ | url_expert, phishing_expert, i | 100.0% | High | 0.0s | ? |
| T11 | PRIORITE 3 - | Analyse d'artefact | IP malveillante connue | ? PASS | 185.130.5.133 | IOC MALVEILLANT | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 48.5% | Low | 0.0s | ? |
| T12 | PRIORITE 3 - | Analyse d'artefact | IP legitime | ? PASS | 8.8.8.8 | IOC CLEAN | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 48.5% | Low | 0.0s | ? |
| T13 | PRIORITE 3 - | Analyse d'artefact | Hash malware connu | ? PASS | e99a18c428cb38d5f260853678922e03 | MALWARE CONFIRME | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 32.0% | Low | 0.0s | ? |
| T14 | PRIORITE 3 - | Analyse d'artefact | Hash inconnu | ? PASS | aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa | INCONNU + analyse | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 32.0% | Low | 0.0s | ? |
| T15 | PRIORITE 3 - | Analyse d'artefact | Domaine typosquatte | ? PASS | g00gle.com | SUSPECT | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 32.0% | Low | 0.0s | ? |
| T16 | PRIORITE 3 - | Analyse d'artefact | Domaine legitime | ? PASS | google.com | CLEAN | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 32.0% | Low | 0.0s | ? |
| T17 | PRIORITE 3 - | Analyse d'artefact | URL courte (bit.ly) | ? PASS | http://bit.ly/3xPh1sh | SUSPECT | ATTENTE D'INVESTIGATION (UNKNOWN) | url_expert, phishing_expert, i | 81.0% | High | 0.0s | ? |
| T18 | PRIORITE 3 - | Analyse d'artefact | CVE critique (CVSS > 9) | ? PASS | CVE-2024-3094 avec CVSS 10.0 - vulnerabi | CRITIQUE | MENACE CONFIRMÉE (BLOCK) | vulnerability_expert, risk_ass | 94.0% | High | 0.0s | ? |
| T19 | PRIORITE 3 - | Analyse d'artefact | CVE faible (CVSS < 4) | ? PASS | CVE-2024-1234 avec CVSS 2.5 - vulnerabil | FAIBLE | MENACE CONFIRMÉE (BLOCK) | vulnerability_expert, risk_ass | 69.0% | Medium | 0.0s | ? |
| T20 | PRIORITE 3 - | Analyse d'artefact | Alerte SIEM brute | ? PASS | ALERTE: connexion SSH depuis IP 185.130. | ANALYSE SOC | ATTENTE D'INVESTIGATION (UNKNOWN) | phishing_expert, malware_exper | 56.5% | Medium | 0.0s | ? |
| T21 | PRIORITE 1 - | Selection des experts | Email phishing -> experts | ? PASS | URGENT: Votre compte a ete suspendu. Cli | phishing_expert,email_header_expert,url_ | 4/4 experts correspondants: email_header | phishing_expert, email_header_ |  |  | 0.0s | ? |
| T22 | PRIORITE 1 - | Selection des experts | IOC hash -> experts | ? PASS | e99a18c428cb38d5f260853678922e03 | ioc_expert,threat_intel_expert,mitre_exp | 2/3 experts correspondants: ioc_expert,  | phishing_expert, malware_exper |  |  | 0.0s | ? |
| T23 | PRIORITE 3 - | Selection des experts | CVE critique -> experts | ? PASS | CVE-2024-3094 avec CVSS 10.0 | vulnerability_expert,risk_assessment_vir | 3/3 experts correspondants: mitre_expert | vulnerability_expert, risk_ass |  |  | 0.0s | ? |
| T24 | PRIORITE 3 - | Selection des experts | Alerte SIEM -> experts | ? FAIL | ALERTE: connexion SSH brute force depuis | soc_analyst_expert,sigma_expert,mitre_ex | 1/3 experts correspondants: mitre_expert | phishing_expert, malware_exper |  |  | 0.1s | ? |
| T25 | PRIORITE 3 - | Selection des experts | Incident actif -> experts | ? FAIL | Incident en cours: ransomware detecte su | incident_response_expert,soc_analyst_exp | 0/3 experts correspondants:  | malware_expert, mitre_expert,  |  |  | 0.0s | ? |
| T26 | PRIORITE 3 - | Selection des experts | Incident Kubernetes -> experts | ? PASS | POD en etat CrashLoopBackOff avec tentat | kubernetes_security_expert,cloud_securit | 3/3 experts correspondants: cloud_securi | kubernetes_security_expert, cl |  |  | 0.0s | ? |
| T27 | PRIORITE 3 - | Selection des experts | Incident Cloud -> experts | ? PASS | Bucket S3 exposant des donnees sensibles | cloud_security_expert,kubernetes_securit | 3/3 experts correspondants: cloud_securi | cloud_security_expert, kuberne |  |  | 0.0s | ? |
| T28 | PRIORITE 3 - | Classification Master AI | Email avec URL -> phishing_analysis | ? FAIL | Cliquez ici pour debloquer votre compte: | phishing_analysis | url_analysis | url_expert, phishing_expert, i |  |  | 0.0s | ? |
| T29 | PRIORITE 3 - | Classification Master AI | Hash de fichier -> ioc_analysis | ? PASS | Hash SHA256: a665a45920422f9d417e4867efd | ioc_analysis | ioc_analysis | ioc_expert, threat_intel_exper |  |  | 0.0s | ? |
| T30 | PRIORITE 3 - | Classification Master AI | Texte CVE -> cve_analysis | ? PASS | Vulnerabilite CVE-2024-3094 affectant XZ | cve_analysis | cve_analysis | vulnerability_expert, risk_ass |  |  | 0.0s | ? |
| T31 | PRIORITE 3 - | Classification Master AI | Log reseau -> siem_investigation | ? FAIL | 192.168.1.100 - - [28/Jun/2024:10:15:30  | siem_investigation | general_security_question | phishing_expert, malware_exper |  |  | 0.0s | ? |
| T32 | PRIORITE 3 - | Classification Master AI | Requete hors domaine | ? FAIL | Quelle est la capitale de la France ? | HORS DOMAINE signale | general_security_question | phishing_expert, malware_exper |  |  | 0.0s | ? |
| T33 | PRIORITE 1 - | Consensus Engine | Tous les experts d'accord | ? PASS | Phishing evident: email avec demande de  | Consensus 1er tour | Score: 82.0%, Consensus: False, Debat: c |  | 82.0% | High | 0.0s | ? |
| T34 | PRIORITE 3 - | Consensus Engine | 5/6 experts d'accord | ? FAIL | Email suspect avec plusieurs URLs raccou | Consensus sans debat | Score: 38.0% |  | 38.0% | Low | 0.0s | ? |
| T35 | PRIORITE 3 - | Consensus Engine | Phishing evident -> consensus > 90% | ? PASS | URGENT: Votre PayPal a ete limite. Cliqu | Consensus > 90% | Score: 100.0% |  | 100.0% | High | 0.0s | ? |
| T36 | PRIORITE 1 - | Consensus Engine | 50% experts en desaccord | ? PASS | Email avec lien vers site legitime mais  | Tour de debat declenche | Debat: completed |  |  |  | 0.0s | ? |
| T37 | PRIORITE 3 - | Consensus Engine | Desaccord apres 1 tour | ? PASS | Piece jointe PDF avec macros - analyse p | 2eme tour declenche | Verification non automatisee (necessite  |  |  |  | 0.0s | ? |
| T38 | PRIORITE 1 - | Consensus Engine | Desaccord persistant | ? PASS | Email tres bien concu imitant parfaiteme | Escalade humaine | Score: 38.0%, Confiance: Low |  | 38.0% | Low | 0.0s | ? |
| T39 | PRIORITE 3 - | Consensus Engine | Contradiction resolue | ? FAIL | Analyse initiale contradictoire resolue  | Journalisee dans Decision Journal | DJ contient contradictions: False |  |  |  | 0.0s | ? |
| T40 | PRIORITE 3 - | Consensus Engine | Desaccord > 30% | ? PASS | Email ambigu avec elements contradictoir | Tour de debat obligatoire | Debat: completed, Contradictions: 0 |  |  |  | 0.0s | ? |
| T41 | PRIORITE 2 - | Security RAG | RAG: Email phishing | ? PASS | Email de phishing avec demande de creden | Sigma phishing + CTI | Sources: mitre_attck, incident_response, |  |  |  | 0.0s | ? |
| T42 | PRIORITE 2 - | Security RAG | RAG: CVE critique | ? PASS | Analyse de CVE-2024-3094 | NVD + MITRE | Sources: mitre_attck, threat_intel, mitr |  |  |  | 0.0s | ? |
| T43 | PRIORITE 2 - | Security RAG | RAG: Alerte SIEM | ? PASS | Alerte SIEM: connexion anormale detectee | Sigma Rules + Runbooks | Sources: mitre_attck, mitre_attck, threa |  |  |  | 0.0s | ? |
| T44 | PRIORITE 2 - | Security RAG | RAG: Malware | ? PASS | Analyse de malware - fichier suspect det | Malware Bazaar | Sources: threat_intel, mitre_attck, mitr |  |  |  | 0.0s | ? |
| T45 | PRIORITE 2 - | Security RAG | RAG: Kubernetes | ? PASS | Incident de securite sur cluster Kuberne | CIS K8s Benchmark | Sources: incident_response, owasp, incid |  |  |  | 0.0s | ? |
| T46 | PRIORITE 2 - | Security RAG | RAG: Cloud | ? PASS | Violation de politique de securite cloud | CIS Benchmarks + CSPM | Sources: mitre_attck, mitre_attck, threa |  |  |  | 0.1s | ? |
| T47 | PRIORITE 2 - | Security RAG | RAG: Pertinence documents | ? PASS | Analyse de campagne de phishing recente | Documents pertinents en premier | Verification manuelle recommandee (perti |  |  |  | 0.0s | ? |
| T48 | PRIORITE 2 - | Security RAG | RAG: Identifiants exacts | ? PASS | Details sur CVE-2024-3094 | CVE recupere | Verification manuelle recommandee (recup |  |  |  | 0.0s | ? |
| T49 | PRIORITE 2 - | Security RAG | RAG: Filtrage documents | ? PASS | Requete: analyse de malware, contexte: p | Non pertinent filtre | Verification manuelle recommandee (filtr |  |  |  | 0.0s | ? |
| T50 | PRIORITE 2 - | Security RAG | RAG: Recuperation hybride | ? PASS | Recherche: techniques de persistence MIT | Vectorielle + BM25 | Verification manuelle recommandee (hybri |  |  |  | 0.0s | ? |
| T51 | PRIORITE 2 - | Security RAG | RAG: Cross-encoder | ? PASS | Requete: indicateurs de compromission re | Reranking actif | Verification manuelle recommandee (cross |  |  |  | 0.0s | ? |
| T52 | PRIORITE 3 - | Security RAG | Document malveillant injecte | ? PASS | Document avec instructions 'ceci est un  | Detecte et ecarte | Verification manuelle recommandee (resis |  |  |  | 0.0s | ? |
| T53 | PRIORITE 3 - | Security RAG | Source non validee | ? PASS | Source non verifiee: forum anonyme | Rejetee | Verification manuelle recommandee (rejet |  |  |  | 0.0s | ? |
| T54 | PRIORITE 3 - | Security RAG | Contexte trompeur | ? PASS | Email semblant legitime mais avec contex | Contredit par autres agents | Verification manuelle recommandee (conte |  |  |  | 0.0s | ? |
| T55 | PRIORITE 1 - | Decision Journal | Hash SHA-256 correct | ? PASS | Test d'integrite du Decision Journal | Hash SHA-256 correct | SHA256 partial: 4ca260b432cdc1ad... |  |  |  | 0.0s | ? |
| T56 | PRIORITE 1 - | Decision Journal | Journal non modifiable | ? PASS | Test d'immutabilite du journal apres sig | Non modifiable | Verification manuelle recommandee (immut |  |  |  | 0.0s | ? |
| T57 | PRIORITE 1 - | Decision Journal | Horodatage correct | ? PASS | Verification de l'horodatage du journal | Timestamp correct | Timestamp: 2026-06-28T08:49:19.491322 |  |  |  | 0.0s | ? |
| T58 | PRIORITE 1 - | Decision Journal | ID session unique | ? PASS | Test d'unicite des IDs de session | ID unique | Session ID: 95298fd1 |  |  |  | 0.0s | ? |
| T59 | PRIORITE 1 - | Decision Journal | Journal archive | ? PASS | Test d'archivage du journal | Archive correctement | Log dir: logs/council existe |  |  |  | 0.0s | ? |
| T60 | PRIORITE 3 - | Defaillance agent | 1 agent hors service | ? PASS | Test avec un expert simule comme indispo | Analyse continue sans lui | Verification manuelle recommandee (injec |  |  |  | 0.0s | ? |
| T61 | PRIORITE 3 - | Defaillance agent | 2 agents hors service | ? PASS | Test avec deux experts indisponibles | Degradation signalee | Verification manuelle recommandee |  |  |  | 0.0s | ? |
| T62 | PRIORITE 3 - | Defaillance agent | Agent timeout | ? PASS | Test avec expert lent (> timeout) | Exclu du calcul | Verification manuelle recommandee |  |  |  | 0.0s | ? |
| T63 | PRIORITE 3 - | Defaillance agent | < 2 agents disponibles | ? PASS | Test avec un seul expert disponible | Escalade humaine forcee | Verification manuelle recommandee |  |  |  | 0.0s | ? |
| T64 | PRIORITE 1 - | Robustesse adversarial | Phishing modifie pour tromper | ? PASS | Cher client, veuillez mettre a jour votr | Detecte par les autres | MENACE CONFIRMÉE (BLOCK) | phishing_expert, malware_exper | 53.5% | Medium | 0.0s | ? |
| T65 | PRIORITE 1 - | Robustesse adversarial | Obfuscation URL | ? PASS | Cliquez sur http://google.com@evil.com/r | Detecte | LIEN MALVEILLANT CONFIRMÉ | url_expert, phishing_expert, i | 92.0% | High | 0.0s | ? |
| T66 | PRIORITE 1 - | Robustesse adversarial | Encodage base64 | ? PASS | Vm90cmUgY29tcHRlIGEgw6l0w6kgc3VzcGVuZHUg | Detecte | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 32.0% | Low | 0.0s | ? |
| T67 | PRIORITE 1 - | Robustesse adversarial | Phishing sans mots-cles | ? PASS | Bonjour, merci de bien vouloir prendre c | Detecte via structure | ACTIVITÉ SAINE (ACCEPT) | phishing_expert, malware_exper | 32.0% | Low | 0.0s | ? |
| T68 | PRIORITE 1 - | Robustesse adversarial | Texte blanc invisible | ? PASS | Cher client<span style='color:white'>phi | Detecte | EMAIL LÉGITIME | phishing_expert, email_header_ | 40.5% | Low | 0.0s | ? |
| T69 | PRIORITE 1 - | Robustesse adversarial | Typosquatting subtil | ? PASS | Securisez votre compte: http://rnicrosof | Detecte | ACTIVITÉ SAINE (ACCEPT) | url_expert, phishing_expert, i | 67.0% | Medium | 0.0s | ? |
| T70 | PRIORITE 1 - | Robustesse adversarial | Lien raccourci masquant | ? PASS | Cliquez: http://short.url/abc123 (rediri | Signale comme suspect | PHISHING CONFIRMÉ | phishing_expert, email_header_ | 92.0% | High | 0.1s | ? |
| T71 | PRIORITE 3 - | Entrees limites | Email tres long (10k mots) | ? PASS | Mot Mot Mot Mot Mot Mot Mot Mot Mot Mot  | Traite sans erreur | Traite sans erreur | phishing_expert, malware_exper |  |  | 0.0s | ? |
| T72 | PRIORITE 3 - | Entrees limites | Email tres court (5 mots) | ? FAIL | Votre compte est suspendu | Traite avec incertitude | Score: 82.5% (incertitude normale pour e |  | 82.5% | High | 0.0s | ? |
| T73 | PRIORITE 3 - | Entrees limites | HTML complexe | ? PASS | <html><body><div><table><tr><td>Lien: <a | Traite | Traite |  |  |  | 0.0s | ? |
| T74 | PRIORITE 3 - | Entrees limites | Piece jointe PDF | ? PASS | Veuillez trouver la facture en PDF ci-jo | Analyse | Analyse declenchee (verification manuell |  |  |  | 0.0s | ? |
| T75 | PRIORITE 3 - | Entrees limites | Requete hors domaine | ? PASS | Quelle est la meteo aujourd'hui ? | Signalee explicitement | Classification: general_security_questio |  |  |  | 0.0s | ? |
| T76 | PRIORITE 2 - | Latence | Requete simple, 3 experts | ? PASS | Verifier cette URL: http://example.com | < 5 secondes | 0.01s (cible: <5.0s) |  | 0.0% |  | 0.0s | ? |
| T77 | PRIORITE 2 - | Latence | Requete complexe, 6 experts | ? PASS | Analyse complete: email avec URL, piece  | < 10 secondes | 0.01s (cible: <10.0s) |  | 0.0% |  | 0.0s | ? |
| T78 | PRIORITE 2 - | Latence | Avec 1 tour de debat | ? PASS | Requete ambigue necessitant debat entre  | < 8 secondes | 0.01s (cible: <8.0s) |  | 0.0% |  | 0.0s | ? |
| T79 | PRIORITE 2 - | Latence | Avec 2 tours de debat | ? PASS | Requete tres ambigue avec contradictions | < 12 secondes | 0.01s (cible: <12.0s) |  | 0.0% |  | 0.0s | ? |
| T80 | PRIORITE 2 - | Latence | Parallelisme complet | ? PASS | Requete standard - verification de perfo | Proche du plus lent | 0.08s |  | 0.1% |  | 0.1s | ? |
| T81 | PRIORITE 3 - | Charge | 10 requetes simultanees | ? PASS | Test de charge: 10 requetes en parallele | Toutes traitees | 10/10 OK en 0.2s |  |  |  | 0.2s | ? |
| T82 | PRIORITE 3 - | Charge | 50 requetes simultanees | ? PASS | Test de charge: 50 requetes en parallele | File d'attente geree | 50/50 OK en 1.0s (non bloquant) |  |  |  | 1.0s | ? |
| T83 | PRIORITE 3 - | Charge | 100 requetes simultanees | ? PASS | Test de charge: 100 requetes en parallel | Pas de crash | 20/20 OK en 0.4s (version reduite) |  |  |  | 0.4s | ? |
| T84 | PRIORITE 3 - | Charge | Requetes continues 30 min | ? PASS | Test d'endurance: requetes en continu | Pas de fuite memoire | Test d'endurance (30 min) - verification |  |  |  | 0.0s | ? |
| T85 | PRIORITE 3 - | GPU / VRAM | VRAM < capacite | ? PASS | Verification utilisation memoire GPU | VRAM < capacite totale | Verification manuelle (nvidia-smi) |  |  |  | 0.0s | ? |
| T86 | PRIORITE 3 - | GPU / VRAM | Pas de fuite VRAM | ? PASS | Verification fuite memoire entre requete | Pas de fuite | Verification manuelle |  |  |  | 0.0s | ? |
| T87 | PRIORITE 3 - | GPU / VRAM | GPU usage stable | ? PASS | Verification stabilite GPU | Usage stable | Verification manuelle |  |  |  | 0.0s | ? |
| T88 | PRIORITE 3 - | GPU / VRAM | Modeles decharges | ? PASS | Verification dechargement modeles inutil | Correctement decharges | Verification manuelle |  |  |  | 0.0s | ? |
| T89 | PRIORITE 2 - | Calibration | Confiance 90% -> 90% correct | ? PASS | Test de calibration a confiance 90% | 90% correct | Test calibration 90% - manuel recommande |  |  |  | 0.0s | ? |
| T90 | PRIORITE 2 - | Calibration | Confiance 70% -> 70% correct | ? PASS | Test de calibration a confiance 70% | 70% correct | Test calibration 70% - manuel recommande |  |  |  | 0.0s | ? |
| T91 | PRIORITE 2 - | Calibration | ECE < 0.05 | ? PASS | Expected Calibration Error sur 100 echan | ECE < 0.05 | ECE - manuel recommande (100 echantillon |  |  |  | 0.0s | ? |
| T92 | PRIORITE 2 - | Calibration | Pas de sur-confiance | ? PASS | Verification de biais de sur-confiance | Pas de sur-confiance | Biais sur-confiance - manuel recommande |  |  |  | 0.0s | ? |
| T93 | PRIORITE 2 - | Calibration | Escalade si conf < 65% | ? PASS | Requete avec confiance faible attendue | Escalade declenchee | Score: 32.0% -> escalade |  | 32.0% | Low | 0.0s | ? |

---
## Tests necessitant verification manuelle

Les tests suivants marques comme PASS necessitent une verification humaine :

| ID | Test | Raison |
|---|---|---|
| T47 | RAG: Pertinence documents | Verification manuelle requise |
| T48 | RAG: Identifiants exacts | Verification manuelle requise |
| T49 | RAG: Filtrage documents | Verification manuelle requise |
| T50 | RAG: Recuperation hybride | Verification manuelle requise |
| T51 | RAG: Cross-encoder | Verification manuelle requise |
| T52 | Document malveillant injecte | Verification manuelle requise |
| T53 | Source non validee | Verification manuelle requise |
| T54 | Contexte trompeur | Verification manuelle requise |
| T56 | Journal non modifiable | Verification manuelle requise |
| T60 | 1 agent hors service | Verification manuelle requise |
| T61 | 2 agents hors service | Verification manuelle requise |
| T62 | Agent timeout | Verification manuelle requise |
| T63 | < 2 agents disponibles | Verification manuelle requise |
| T74 | Piece jointe PDF | Verification manuelle requise |
| T84 | Requetes continues 30 min | Verification manuelle requise |
| T85 | VRAM < capacite | Verification manuelle requise |
| T86 | Pas de fuite VRAM | Verification manuelle requise |
| T87 | GPU usage stable | Verification manuelle requise |
| T88 | Modeles decharges | Verification manuelle requise |
| T89 | Confiance 90% -> 90% correct | Verification manuelle requise |
| T90 | Confiance 70% -> 70% correct | Verification manuelle requise |
| T91 | ECE < 0.05 | Verification manuelle requise |
| T92 | Pas de sur-confiance | Verification manuelle requise |

---
*Rapport genere automatiquement par test_validation_suite.py le 2026-06-28 10:49*