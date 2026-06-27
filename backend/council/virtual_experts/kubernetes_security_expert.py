"""Expert 13 — Kubernetes & Container Security Specialist."""
from typing import Dict
from backend.council.virtual_experts.base import VirtualExpert


class KubernetesSecurityExpert(VirtualExpert):
    expert_id = "kubernetes_security_expert"
    expert_name = "K8s Security Analyst"
    category = "kubernetes_security"
    capabilities = ["rbac_analysis", "pod_security", "network_policies", "container_security", "k8s_hardening"]
    MITRE_TECHNIQUES = [
        "T1610 - Deploy Container",
        "T1611 - Escape to Host",
        "T1613 - Container and Resource Discovery",
    ]

    HIGH_CONF_KEYWORDS = [
        "kubernetes", "k8s", "kubectl", "pod", "container", "docker",
        "namespace", "rbac", "clusterrole", "rolebinding", "service account",
        "privileged container", "hostpath", "hostnetwork", "runasroot",
        "securitycontext", "pod security", "network policy",
        "exposed dashboard", "etcd", "kubelet",
    ]
    MED_CONF_KEYWORDS = [
        "orchestration", "helm", "operator", "deployment", "daemonset",
        "ingress", "egress", "cni", "calico", "flannel", "cilium",
    ]

    _K8S_RISKS = {
        "privileged": ("Container en mode privilegié — risque d'évasion vers l'hôte", "CRITICAL", "T1611 - Escape to Host"),
        "hostnetwork": ("hostNetwork: true — accès réseau de l'hôte", "HIGH", "T1016 - System Network Configuration Discovery"),
        "hostpath": ("HostPath mount — accès au filesystem de l'hôte", "HIGH", "T1005 - Data from Local System"),
        "runasroot": ("Conteneur s'exécute en root", "HIGH", "T1610 - Deploy Container"),
        "clusteradmin": ("ClusterRole admin accordé inutilement", "CRITICAL", "T1078.004 - Cloud Accounts"),
        "etcd exposed": ("etcd exposé sans authentification TLS", "CRITICAL", "T1565 - Data Manipulation"),
        "dashboard exposed": ("Kubernetes Dashboard exposé publiquement", "HIGH", "T1133 - External Remote Services"),
    }

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"
        mitre_found = list(self.MITRE_TECHNIQUES)

        for keyword, (desc, sev, technique) in self._K8S_RISKS.items():
            if keyword in query:
                evidence.append(f"Risque K8s: {desc}")
                if technique not in mitre_found:
                    mitre_found.append(technique)
                if sev == "CRITICAL":
                    confidence = min(confidence + 35, 95)
                    severity = "CRITICAL"
                elif sev == "HIGH" and severity not in ("CRITICAL",):
                    confidence = min(confidence + 20, 95)
                    severity = "HIGH"

        if not severity or severity == "UNKNOWN":
            severity = "MEDIUM" if confidence > 30 else "INFORMATIONAL"

        if confidence >= 45:
            conclusion = "BLOCK"
        elif confidence >= 20:
            conclusion = "UNKNOWN"
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"

        recs = []
        if severity in ("CRITICAL", "HIGH"):
            recs.append("Appliquer les Pod Security Standards (restricted)")
            recs.append("Auditer les RBAC avec kubectl-who-can ou rakkess")
        if "privileged" in query:
            recs.append("Interdire les conteneurs privilégiés via PodSecurityPolicy/OPA Gatekeeper")
        if "etcd" in query:
            recs.append("Activer l'authentification TLS sur etcd")
        recs.append("Déployer Falco pour la détection runtime des comportements suspects")

        return {
            "response": f"Analyse K8s: {len(evidence)} risque(s) détecté(s). Sévérité: {severity}.",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Sans accès au cluster K8s — analyse basée sur la description"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": mitre_found[:5],
            "severity": severity,
        }
