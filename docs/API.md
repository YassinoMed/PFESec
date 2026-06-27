# Documentation de l'API REST — AI Security Council v2

Ce document décrit les points d'entrée de l'API d'orchestration de l'AI Security Council.

---

## 1. AI Security Council Analysis

Déclenche l'orchestration multi-agent du Master AI sur une requête de sécurité.

* **URL** : `/api/v1/security/council`
* **Méthode** : `POST`
* **Headers** : `Content-Type: application/json`

### Exemple de Requête

```json
{
  "query": "URGENT: Votre compte a été suspendu. Vérifiez votre identité via ce lien: http://banque-secure.xyz/login sinon votre compte sera définitivement bloqué."
}
```

### Exemple de Réponse

```json
{
  "query": "URGENT: Votre compte a été suspendu...",
  "classification": "phishing_analysis",
  "selected_models": [
    "phishing_expert",
    "email_header_expert",
    "ioc_expert"
  ],
  "experts": [
    {
      "expert_id": "phishing_expert",
      "expert_name": "Phishing Analyst",
      "category": "phishing",
      "status": "completed",
      "response": "Analyse phishing: BLOCK. Confiance: 95%.",
      "conclusion": "BLOCK",
      "confidence": 95.0,
      "evidence": [
        "Indicateurs phishing détectés: urgent, vérifiez, cliquez"
      ],
      "limitations": [],
      "inference_ms": 1.2
    }
  ],
  "consensus": {
    "global_score": 95.0,
    "confidence_level": "High"
  },
  "reasoning_trace": {
    "incident_type": "phishing_analysis",
    "classification_confidence": 99.0,
    "steps": [
      {
        "step": 1,
        "name": "Query Comprehension",
        "findings": [
          "Type de requête identifié: phishing_analysis"
        ],
        "elapsed_ms": 0.4
      }
    ]
  },
  "attack_timeline": {
    "attack_vector": "Email / Phishing",
    "entry_point": "Malicious URL: http://banque-secure.xyz/login",
    "phases": [
      {
        "phase_id": "TA0001",
        "phase_name": "Initial Access",
        "techniques": [
          "T1566 - Phishing"
        ],
        "confidence": 0.8
      }
    ]
  },
  "risk_assessment": {
    "severity": "HIGH",
    "severity_score": 7.8,
    "probability": 95.0,
    "impact": "MEDIUM",
    "risk_score": 72.0
  },
  "response_plan": {
    "incident_type": "phishing",
    "containment": [
      {
        "phase": "containment",
        "action": "Isoler l'email malveillant",
        "responsible": "Email Admin"
      }
    ]
  },
  "decision_journal": {
    "session_id": "a1b2c3d4",
    "final_decision": "BLOCK",
    "decision_justification": "Décision 'BLOCK' basée sur un consensus de 95%."
  }
}
```

---

## 2. Healthcheck & Statut

* **URL** : `/health`
* **Méthode** : `GET`

### Réponse

```json
{
  "status": "ok",
  "service": "security-ai-orchestrator"
}
```
