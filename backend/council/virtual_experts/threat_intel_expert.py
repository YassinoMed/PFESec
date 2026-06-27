"""Expert 4 — Threat Intelligence & CTI Specialist."""
from typing import Dict
from backend.council.virtual_experts.base import VirtualExpert

# Known APT groups and their keywords
_APT_SIGNATURES = {
    "APT28 (Fancy Bear)": ["apt28", "fancy bear", "sofacy", "x-agent", "gamefish"],
    "APT29 (Cozy Bear)": ["apt29", "cozy bear", "sunburst", "solorigate", "nobelium"],
    "Lazarus Group": ["lazarus", "hidden cobra", "kimsuky", "bluenoroff"],
    "FIN7": ["fin7", "carbanak", "cobalt group"],
    "Conti": ["conti", "ryuk", "trickbot"],
    "LockBit": ["lockbit", "lockbit 2.0", "lockbit 3.0"],
}


class ThreatIntelExpert(VirtualExpert):
    expert_id = "threat_intel_expert"
    expert_name = "Threat Intelligence Analyst"
    category = "threat_intelligence"
    capabilities = ["apt_identification", "ttp_analysis", "ioc_enrichment", "campaign_attribution"]
    MITRE_TECHNIQUES = [
        "T1589 - Gather Victim Identity Information",
        "T1596 - Search Open Technical Databases",
        "T1588 - Obtain Capabilities",
    ]

    HIGH_CONF_KEYWORDS = list(
        kw for group_kws in _APT_SIGNATURES.values() for kw in group_kws
    ) + ["apt", "threat actor", "campaign", "ioc", "ttp", "threat intelligence", "feed"]

    MED_CONF_KEYWORDS = [
        "indicator", "attribution", "nation-state", "cybercrime", "osint",
        "dark web", "underground", "exploit kit", "c2", "botnet",
    ]

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"

        # APT attribution
        attributed_apts = []
        for group, keywords in _APT_SIGNATURES.items():
            if any(kw in query for kw in keywords):
                attributed_apts.append(group)

        if attributed_apts:
            evidence.append(f"Attribution potentielle: {', '.join(attributed_apts)}")
            confidence = min(confidence + 30, 95)

        if iocs:
            types = [i["type"] for i in iocs]
            evidence.append(f"IOC extraits pour enrichissement: {', '.join(set(types))}")

        if "c2" in query or "command and control" in query:
            evidence.append("Infrastructure C2 détectée — serveur de commande et contrôle")
            confidence = min(confidence + 20, 95)

        if "osint" in query or "dark web" in query:
            evidence.append("Source OSINT/Dark Web référencée")

        if confidence >= 55:
            conclusion = "BLOCK"
            severity = "HIGH"
        elif confidence >= 25:
            conclusion = "UNKNOWN"
            severity = "MEDIUM"
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"

        recs = []
        if attributed_apts:
            recs.append(f"Consulter les profils MITRE ATT&CK de {attributed_apts[0]}")
        if iocs:
            recs.append("Enrichir les IOC via VirusTotal, OTX ou MISP")
        if conclusion == "BLOCK":
            recs.append("Partager les IOC avec la communauté ISAC")
            recs.append("Mettre à jour les règles SIEM avec les TTPs identifiés")

        return {
            "response": f"Analyse CTI: {conclusion}. {'; '.join(evidence[:3]) or 'Aucun indicateur de menace avancée.'}",
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Pas d'accès aux feeds TI commerciaux en temps réel"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": self.MITRE_TECHNIQUES,
            "severity": severity,
        }
