"""Response Plan Engine — Generates structured incident response plans.

Produces actionable 4-phase response plans: Containment, Eradication, Recovery, Prevention.
Plans are tailored to the detected incident type and risk level.
"""

from typing import List

from backend.council.types import (
    ExpertAnalysis,
    ResponseAction,
    ResponsePlan,
    RiskAssessment,
)


def _action(phase: str, priority: int, action: str, desc: str,
            responsible: str = "SOC", time: str = "immediate",
            automated: bool = False) -> ResponseAction:
    return ResponseAction(
        phase=phase, priority=priority, action=action,
        description=desc, responsible=responsible,
        estimated_time=time, automated=automated,
    )


# ── Phase templates ───────────────────────────────────────────────────────────

_PHISHING_PLAN = {
    "containment": [
        _action("containment", 1, "Isoler l'email malveillant",
                "Supprimer le message de toutes les boîtes de réception affectées via la console admin email.",
                responsible="Email Admin", time="immédiat", automated=True),
        _action("containment", 2, "Bloquer l'URL / domaine malveillant",
                "Ajouter le domaine/URL détecté à la blocklist du proxy et du firewall.",
                responsible="Network Team", time="< 15 min"),
        _action("containment", 3, "Réinitialiser les credentials exposés",
                "Forcer la réinitialisation du mot de passe des utilisateurs ayant cliqué le lien.",
                responsible="IAM Team", time="< 30 min"),
    ],
    "eradication": [
        _action("eradication", 1, "Scanner les endpoints exposés",
                "Lancer un scan EDR sur les postes ayant reçu l'email pour détecter les indicateurs de compromission.",
                responsible="Endpoint Team", time="< 1 heure"),
        _action("eradication", 2, "Révoquer les sessions actives",
                "Invalider toutes les sessions SSO/OAuth pour les comptes potentiellement compromis.",
                responsible="IAM Team", time="< 30 min", automated=True),
        _action("eradication", 3, "Analyser les logs d'accès",
                "Vérifier les logs d'authentification pour identifier des connexions suspectes post-phishing.",
                responsible="SOC Analyst", time="< 2 heures"),
    ],
    "recovery": [
        _action("recovery", 1, "Restaurer les comptes compromis",
                "Réinitialiser les comptes après vérification d'identité multi-facteur.",
                responsible="IAM Team", time="< 1 heure"),
        _action("recovery", 2, "Vérifier l'intégrité des données",
                "Contrôler que aucune donnée sensible n'a été exfiltrée pendant la fenêtre de compromission.",
                responsible="Data Team", time="< 4 heures"),
        _action("recovery", 3, "Communiquer aux utilisateurs",
                "Envoyer une notification aux utilisateurs affectés avec les instructions de sécurité.",
                responsible="Communications", time="< 2 heures"),
    ],
    "prevention": [
        _action("prevention", 1, "Renforcer le filtrage email",
                "Activer DMARC strict, DKIM et SPF. Augmenter le niveau de scan des pièces jointes.",
                responsible="Email Admin", time="< 24 heures"),
        _action("prevention", 2, "Former les utilisateurs",
                "Lancer une simulation de phishing et une formation de sensibilisation.",
                responsible="Security Awareness", time="< 1 semaine"),
        _action("prevention", 3, "Déployer MFA universel",
                "Exiger l'authentification multi-facteur pour tous les services exposés.",
                responsible="IAM Team", time="< 1 semaine"),
    ],
    "monitoring": [
        "Surveiller les connexions depuis des IPs inconnues dans les 72h",
        "Alerter sur toute tentative de réinitialisation de mot de passe non sollicitée",
        "Monitorer l'accès aux données sensibles par les comptes exposés",
    ],
}

_MALWARE_PLAN = {
    "containment": [
        _action("containment", 1, "Isoler les systèmes infectés",
                "Déconnecter immédiatement les endpoints compromis du réseau (quarantaine réseau).",
                responsible="Network Team", time="immédiat"),
        _action("containment", 2, "Bloquer les communications C2",
                "Ajouter les IP/domaines C2 détectés à la blacklist firewall.",
                responsible="Network Team", time="< 15 min", automated=True),
        _action("containment", 3, "Suspendre les comptes compromis",
                "Désactiver les comptes utilisés par le malware pour se propager.",
                responsible="IAM Team", time="< 30 min"),
    ],
    "eradication": [
        _action("eradication", 1, "Exécuter l'analyse forensique",
                "Capturer une image mémoire et disque des systèmes infectés avant nettoyage.",
                responsible="DFIR Team", time="< 2 heures"),
        _action("eradication", 2, "Supprimer les artifacts malveillants",
                "Utiliser l'EDR pour supprimer le malware, les persistances et les artefacts.",
                responsible="Endpoint Team", time="< 4 heures"),
        _action("eradication", 3, "Patcher les vulnérabilités exploitées",
                "Appliquer les patches de sécurité correspondant aux CVE utilisées par le malware.",
                responsible="Patch Management", time="< 24 heures"),
    ],
    "recovery": [
        _action("recovery", 1, "Restaurer depuis une sauvegarde saine",
                "Restaurer les systèmes depuis la dernière sauvegarde validée (avant infection).",
                responsible="IT Ops", time="< 8 heures"),
        _action("recovery", 2, "Valider la santé du système restauré",
                "Vérifier l'intégrité des systèmes restaurés avant reconnexion au réseau.",
                responsible="DFIR Team", time="< 2 heures"),
        _action("recovery", 3, "Reconnexion graduelle au réseau",
                "Reconnecter les systèmes par phases avec surveillance EDR renforcée.",
                responsible="Network Team", time="< 24 heures"),
    ],
    "prevention": [
        _action("prevention", 1, "Renforcer les politiques EDR",
                "Activer le mode prévention strict sur l'EDR pour tous les endpoints.",
                responsible="Endpoint Team", time="< 24 heures"),
        _action("prevention", 2, "Segmenter le réseau",
                "Implémenter la microsegmentation pour limiter la propagation laterale.",
                responsible="Network Team", time="< 1 semaine"),
        _action("prevention", 3, "Mettre à jour les règles Sigma/SIEM",
                "Créer des règles de détection basées sur les IOC et TTPs identifiés.",
                responsible="SOC", time="< 48 heures"),
    ],
    "monitoring": [
        "Surveillance 24/7 des IOC extraits pendant 30 jours",
        "Alerter sur toute communication vers les IP/domaines C2 détectés",
        "Surveiller les tentatives d'escalade de privilège sur les endpoints",
    ],
}

_RANSOMWARE_PLAN = {
    "containment": [
        _action("containment", 1, "ISOLEMENT IMMÉDIAT — Couper le réseau",
                "Déconnecter IMMÉDIATEMENT tous les systèmes du réseau. Activer le plan de continuité.",
                responsible="CISO / IT Director", time="immédiat"),
        _action("containment", 2, "Identifier l'étendue du chiffrement",
                "Déterminer quels systèmes et fichiers ont été chiffrés (Shadow Copies, backups).",
                responsible="DFIR Team", time="< 30 min"),
        _action("containment", 3, "Préserver les Shadow Copies",
                "Tenter de préserver les Shadow Copies Windows avant que le ransomware les supprime.",
                responsible="IT Ops", time="immédiat"),
    ],
    "eradication": [
        _action("eradication", 1, "Identifier et stopper le vecteur initial",
                "Identifier comment le ransomware est entré (phishing, RDP, exploit) et fermer le vecteur.",
                responsible="DFIR Team", time="< 2 heures"),
        _action("eradication", 2, "Supprimer le ransomware des systèmes",
                "Utiliser des outils forensiques pour supprimer le ransomware et ses persistances.",
                responsible="DFIR Team", time="< 8 heures"),
        _action("eradication", 3, "Vérifier la non-compromission du backup",
                "S'assurer que les sauvegardes n'ont pas été chiffrées ou supprimées.",
                responsible="IT Ops", time="< 1 heure"),
    ],
    "recovery": [
        _action("recovery", 1, "Restauration depuis backup hors-ligne",
                "Restaurer les données depuis les sauvegardes offline/immutables. Priorité aux systèmes critiques.",
                responsible="IT Ops", time="< 24 heures"),
        _action("recovery", 2, "Tester les décrypteurs publics",
                "Vérifier sur nomoreransom.org si un décrypteur existe pour la variante identifiée.",
                responsible="DFIR Team", time="< 4 heures"),
        _action("recovery", 3, "Notification réglementaire (CNIL/ANSSI)",
                "Notifier les autorités compétentes dans les 72h (RGPD) si des données personnelles sont impactées.",
                responsible="DPO / Legal", time="< 72 heures"),
    ],
    "prevention": [
        _action("prevention", 1, "Sauvegardes 3-2-1 immutables",
                "Implémenter la règle 3-2-1 avec des sauvegardes immutables hors ligne.",
                responsible="IT Ops", time="< 1 semaine"),
        _action("prevention", 2, "Désactiver RDP exposé",
                "Fermer RDP sur Internet. Utiliser un VPN avec MFA pour l'accès distant.",
                responsible="Network Team", time="< 24 heures"),
        _action("prevention", 3, "Exercice de simulation ransomware",
                "Planifier un exercice de simulation (tabletop exercise) ransomware.",
                responsible="CISO", time="< 1 mois"),
    ],
    "monitoring": [
        "Surveiller les tentatives de suppression des Shadow Copies",
        "Alerter sur les accès massifs aux fichiers (file encryption signature)",
        "Monitorer les connexions RDP depuis des IP externes",
    ],
}

_GENERIC_PLAN = {
    "containment": [
        _action("containment", 1, "Identifier et isoler les systèmes affectés",
                "Déterminer le périmètre de l'incident et isoler les systèmes concernés.",
                responsible="SOC", time="< 1 heure"),
        _action("containment", 2, "Bloquer les vecteurs identifiés",
                "Bloquer les IPs, domaines ou payloads identifiés dans les outils de sécurité.",
                responsible="SOC", time="< 30 min", automated=True),
    ],
    "eradication": [
        _action("eradication", 1, "Analyser l'origine de l'incident",
                "Effectuer une analyse forensique pour identifier la cause racine.",
                responsible="DFIR Team", time="< 4 heures"),
        _action("eradication", 2, "Supprimer les artefacts malveillants",
                "Nettoyer les systèmes affectés et appliquer les correctifs nécessaires.",
                responsible="IT Ops", time="< 8 heures"),
    ],
    "recovery": [
        _action("recovery", 1, "Restaurer les services affectés",
                "Restaurer les services depuis des sauvegardes validées.",
                responsible="IT Ops", time="< 8 heures"),
        _action("recovery", 2, "Vérifier l'intégrité post-restauration",
                "Valider que les systèmes restaurés sont exempts de compromission.",
                responsible="DFIR Team", time="< 2 heures"),
    ],
    "prevention": [
        _action("prevention", 1, "Mettre à jour les règles de détection",
                "Créer des règles SIEM/EDR basées sur les IOC et TTPs identifiés.",
                responsible="SOC", time="< 48 heures"),
        _action("prevention", 2, "Effectuer un retour d'expérience",
                "Organiser un post-mortem pour identifier les améliorations de sécurité.",
                responsible="CISO", time="< 1 semaine"),
    ],
    "monitoring": [
        "Surveillance continue des IOC identifiés pendant 30 jours",
        "Revue hebdomadaire des alertes SIEM liées à cet incident",
    ],
}


class ResponsePlanEngine:
    """
    Generates structured 4-phase incident response plans based on incident type and risk.
    """

    def generate(
        self,
        query: str,
        classification: str,
        analyses: List[ExpertAnalysis],
        risk: RiskAssessment,
    ) -> ResponsePlan:
        corpus = " ".join([query.lower()] + [str(a.response or "").lower() for a in analyses])

        # Select appropriate plan template
        if "ransomware" in corpus or "encrypt" in corpus and "ransom" in corpus:
            template = _RANSOMWARE_PLAN
            incident_type = "ransomware"
        elif "malware" in corpus or "trojan" in corpus or "backdoor" in corpus:
            template = _MALWARE_PLAN
            incident_type = "malware"
        elif "phishing" in classification or "phish" in corpus or "email" in classification:
            template = _PHISHING_PLAN
            incident_type = "phishing"
        else:
            template = _GENERIC_PLAN
            incident_type = classification or "unknown"

        # Add expert-specific recommendations as additional containment actions
        expert_recs = []
        for a in analyses:
            if a.status == "completed" and a.recommendations:
                for rec in a.recommendations[:2]:
                    expert_recs.append(_action(
                        "containment", 3, f"Recommandation Expert: {a.expert_name}",
                        rec, responsible="SOC", time="< 2 heures"
                    ))

        escalation = risk.priority <= 2 or risk.severity in ("CRITICAL", "HIGH")
        resolution_time = {
            "CRITICAL": "< 4 heures (RTO critique)",
            "HIGH": "< 8 heures",
            "MEDIUM": "< 24 heures",
            "LOW": "< 72 heures",
        }.get(risk.severity, "à déterminer")

        return ResponsePlan(
            incident_type=incident_type,
            containment=template["containment"] + expert_recs[:2],
            eradication=template["eradication"],
            recovery=template["recovery"],
            prevention=template["prevention"],
            monitoring=template["monitoring"],
            escalation_required=escalation,
            estimated_resolution_time=resolution_time,
        )
