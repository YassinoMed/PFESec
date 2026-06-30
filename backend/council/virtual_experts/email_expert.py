"""Expert 2 — Email Header & Protocol Analysis Specialist.
Implements:
  - RÈGLE-T09: Multi-URL extraction with per-URL risk scoring
  - RÈGLE-T10: Spearphishing brand impersonation detection
  - RÈGLE-T72: Short email confidence calibration
"""
import re
from typing import Dict, List, Tuple
from backend.council.virtual_experts.base import VirtualExpert


# ── RÈGLE-T10: Domaines légitimes des grandes marques ──────────────

LEGIT_BRAND_DOMAINS: Dict[str, List[str]] = {
    "microsoft": ["microsoft.com", "office.com", "outlook.com", "azure.com",
                  "live.com", "hotmail.com", "msn.com", "microsoft365.com",
                  "office365.com", "onenote.com", "sharepoint.com"],
    "google":    ["google.com", "gmail.com", "youtube.com", "googlemail.com",
                  "googleapis.com", "googlecloud.com", "gmail.com"],
    "apple":     ["apple.com", "icloud.com", "me.com", "mac.com",
                  "appleid.com", "appstore.com"],
    "amazon":    ["amazon.com", "amazon.co.uk", "amazon.de", "amazon.fr",
                  "aws.amazon.com", "amazonaws.com", "primevideo.com"],
    "paypal":    ["paypal.com", "paypal.fr", "paypal.de", "paypal.co.uk"],
    "facebook":  ["facebook.com", "fb.com", "messenger.com",
                  "instagram.com", "whatsapp.com"],
    "linkedin":  ["linkedin.com", "linkedin.cn", "linkedin.org"],
    "twitter":   ["twitter.com", "t.co", "x.com", "twimg.com"],
}

ALL_LEGIT_DOMAINS: List[str] = [d for domains in LEGIT_BRAND_DOMAINS.values() for d in domains]


def _levenshtein(a: str, b: str) -> int:
    """Distance de Levenshtein entre deux chaînes."""
    if len(a) < len(b):
        a, b = b, a
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a):
        curr = [i + 1]
        for j, cb in enumerate(b):
            curr.append(min(curr[j] + 1, prev[j + 1] + 1, prev[j] + (ca != cb)))
        prev = curr
    return prev[-1]


def _domain_similarity(domain: str, legit: str) -> float:
    """Score de similarité normalisé entre 0 et 1."""
    d = _levenshtein(domain.lower(), legit.lower())
    max_len = max(len(domain), len(legit))
    if max_len == 0:
        return 0.0
    return 1.0 - (d / max_len)


def _extract_all_urls(text: str) -> List[str]:
    """RÈGLE-T09: Extraction exhaustive de toutes les URLs."""
    patterns = [
        r'https?://[^\s<>"{}|\\^`\[\]]+',
        r'(?:https?://)?(?:www\.)?[a-z0-9\-]+\.(?:xyz|ru|cn|tk|pw|cc|top|club|ga|ml|cf|gq|tk|loan|work|party|click|download|review|trade|science|webcam|casino|win|bid|date|men|racing|faith|loan|site|space|store|tech|online|press|shop|host|wiki|name|pro|info|biz|mobi|tel|asia|eu|berlin|tokyo|vip|live|news|video|art|top|work|today|wang|cc|icu|fun|monster|gdn|bid|trade|webcam|science|date|loan|racing|faith|men|mom|party|click|download|review|trade|work|site|win|moscow|durban|capetown|joburg|amsterdam|brussels|london|cologne|moscow|paris|stockholm|tokyo|vienna|wales|berlin|boston|chicago|dallas|miami|nyc|vegas|sydney|melbourne|perth|hongkong|taipei|seoul|tokyo|shanghai|beijing|delhi|mumbai|bangkok|kuala lumpur|jakarta|manila|singapore|hanoi|ho chi minh|saigon)+[^\s<>"{}|\\^`\[\]]*',
    ]
    urls = []
    for pat in patterns:
        urls.extend(re.findall(pat, text, re.IGNORECASE))
    seen = set()
    unique = []
    for u in urls:
        norm = u.rstrip(".,;:!?)]}>\"'")
        if norm not in seen:
            seen.add(norm)
            unique.append(norm)
    return unique


def _extract_sender_domain(text: str) -> str:
    """Extrait le domaine expéditeur (From: ... ou premier email trouvé)."""
    m = re.search(r'from:\s*\S+@(\S+)', text, re.IGNORECASE)
    if m:
        return m.group(1).lower().rstrip(">")
    m = re.search(r'[\w.%-]+@([\w.-]+\.[a-z]{2,})', text)
    if m:
        return m.group(1).lower()
    return ""


def _score_url(url: str) -> Dict:
    """Calcule un score de risque individuel pour une URL (RÈGLE-T09)."""
    domain_match = re.search(r'https?://([^/?#]+)', url)
    domain = domain_match.group(1).lower() if domain_match else url.lower()

    # Indicateurs de risque
    risk = 0
    signals = []

    # Domaine suspect (TLD exotiques)
    suspicious_tlds = {"xyz", "tk", "pw", "cc", "top", "club", "ga", "ml",
                       "cf", "gq", "loan", "work", "party", "click", "download",
                       "review", "trade", "science", "webcam", "casino", "win",
                       "bid", "date", "men", "racing", "faith", "site", "space",
                       "store", "tech", "online", "press", "shop"}
    tld = domain.rsplit(".", 1)[-1] if "." in domain else ""
    if tld in suspicious_tlds:
        risk += 30
        signals.append(f"TLD suspect: .{tld}")

    # Sous-domaines nombreux
    parts = domain.split(".")
    if len(parts) > 3:
        risk += 15
        signals.append("Multiples sous-domaines")

    # Typosquatting / similarité avec marques
    for brand, legit_domains in LEGIT_BRAND_DOMAINS.items():
        for legit in legit_domains:
            sim = _domain_similarity(domain, legit)
            if sim > 0.7 and domain != legit:
                risk += 35
                signals.append(f"Typosquatting: {domain} simule {legit} ({sim:.0%})")
                break
        if risk >= 35:
            break

    # IP brute dans l'URL
    if re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b', domain):
        risk += 25
        signals.append("IP brute dans l'URL")

    # URL courte
    shorteners = {"bit.ly", "tinyurl.com", "shorturl.at", "t.co", "ow.ly",
                  "buff.ly", "is.gd", "tiny.cc", "tr.im", "cutt.ly",
                  "rb.gy", "bl.ink", "shortcm.xyz", "shortlink"}
    for s in shorteners:
        if s in domain:
            risk += 10
            signals.append(f"Raccourcisseur: {s}")
            break

    # Caractères encodés / obfusqués
    if any(c in url for c in ("%", ";", "@", "\\")):
        risk += 15
        signals.append("Caractères d'obfuscation")

    score = min(risk, 95)

    # Technique MITRE
    if score >= 60:
        mitre = "T1566.002 - Spearphishing Link"
    elif score >= 30:
        mitre = "T1566 - Phishing"
    else:
        mitre = "None"

    return {
        "url_brute": url,
        "domaine": domain,
        "tld": tld,
        "score_risque": score,
        "signaux": signals,
        "technique_mitre": mitre,
    }


def _detect_spearphishing(sender_domain: str, text: str, urls: List[str]) -> Tuple[bool, float, List[str]]:
    """RÈGLE-T10: Détection d'usurpation de marque."""
    signals = []
    confidence_bonus = 0.0
    is_spear = False

    if not sender_domain:
        return False, 0.0, []

    # 1. Vérifier si le domaine expéditeur est dans la liste légitime
    is_legit_sender = sender_domain in ALL_LEGIT_DOMAINS

    brand_mentioned = None
    for brand, legit_domains in LEGIT_BRAND_DOMAINS.items():
        brand_lower = brand.lower()
        if brand_lower in text or any(d.split(".")[0] in text for d in legit_domains):
            brand_mentioned = brand
            signals.append(f"Marque mentionnée: {brand}")
            break

    if not brand_mentioned:
        return False, 0.0, []

    legit_domains = LEGIT_BRAND_DOMAINS.get(brand_mentioned, [])
    brand_name = brand_mentioned

    # 2. Signaux d'usurpation
    usurpation_signals = 0

    # Signal 1: Domaine expéditeur ≠ domaine légitime de la marque
    if not is_legit_sender:
        usurpation_signals += 1
        signals.append(f"Expéditeur {sender_domain} ≠ domaine {brand_name}")

        # Similarité avec domaine légitime
        for legit in legit_domains:
            sim = _domain_similarity(sender_domain, legit)
            if sim > 0.7:
                usurpation_signals += 1
                signals.append(f"Similarité {sim:.0%} avec {legit} — typosquatting")
                confidence_bonus = max(confidence_bonus, 85.0)
                break

    # Signal 2: URLs dans l'email pointent vers des domaines tiers
    for url_info in urls:
        for legit in legit_domains:
            sim = _domain_similarity(url_info["domaine"], legit)
            if sim > 0.7 and url_info["domaine"] != legit:
                usurpation_signals += 1
                signals.append(f"URL {url_info['domaine']} simule {legit}")
                break

    # Signal 3: Urgence artificielle + marque
    urgency = ["desactivé", "suspendu", "bloqué", "vérification requise",
               "immediate action", "account suspended", "verify now",
               "désactivé", "suspend", "urgent", "menace"]
    if any(w in text for w in urgency):
        usurpation_signals += 1
        signals.append("Urgence artificielle associée à la marque")

    # Signal 4: Lien de connexion → domaine tiers
    login_indicators = ["login", "sign in", "connexion", "connecter",
                        "account", "compte", "verify", "vérifier",
                        "authenticate", "s'authentifier"]
    if any(w in text for w in login_indicators):
        for url_info in urls:
            legit_match = any(url_info["domaine"] == d for d in legit_domains)
            if not legit_match and url_info["score_risque"] >= 30:
                usurpation_signals += 1
                signals.append(f"Lien de connexion → {url_info['domaine']} (non {brand_name})")
                break

    # Signal 5: Mention de produits spécifiques
    product_keywords = {
        "microsoft": ["microsoft 365", "onedrive", "azure ad", "teams", "outlook"],
        "google":    ["gmail", "google drive", "google docs", "google cloud"],
        "apple":     ["icloud", "apple id", "app store", "apple pay"],
        "amazon":    ["amazon pay", "prime", "aws", "amazon account"],
        "paypal":    ["paypal account", "paypal payment", "wallet"],
    }
    products = product_keywords.get(brand_mentioned, [])
    product_hits = [p for p in products if p in text]
    if product_hits and not is_legit_sender:
        usurpation_signals += 1
        signals.append(f"Produits {brand_name} mentionnés ({', '.join(product_hits[:2])}) mais domaine ≠ {brand_name}")

    # Décision RÈGLE-T10
    if usurpation_signals >= 3:
        is_spear = True
        confidence_bonus = max(confidence_bonus, 85.0)
        signals.append(f"SPEARPHISHING_CONFIRMÉ ({usurpation_signals}/5 signaux)")

    return is_spear, confidence_bonus, signals


def _calibrate_short_email(query: str, confidence: float) -> Tuple[float, str, bool, Dict]:
    """RÈGLE-T72: Calibration de confiance pour les emails courts."""
    words = query.split()
    word_count = len(words)
    char_count = len(query)
    calibration_info = {
        "calibration_appliquee": False,
        "raison_limitation": "",
        "confiance_plafonnee_a": confidence,
    }

    # Détecter si contenu ambigu (pas de lien, pas d'IOC identifiable)
    has_url = bool(re.search(r'https?://', query))
    has_attachment = any(w in query for w in ["piece jointe", "attachment", "pdf", ".docx", ".xlsx"])
    has_ioc = bool(re.search(r'\b(?:\d{1,3}\.){3}\d{1,3}\b|CVE-\d{4}-\d{4,7}|[a-fA-F0-9]{32,64}', query))
    has_meaningful_content = has_url or has_attachment or has_ioc

    if word_count < 20:
        confidence = min(confidence, 45.0)
        calibration_info = {
            "calibration_appliquee": True,
            "raison_limitation": f"Contenu insuffisant pour analyse fiable — email trop court ({word_count} mots)",
            "confiance_plafonnee_a": 45.0,
        }
        return confidence, "INCONCLUSIVE", True, calibration_info

    if word_count < 50 and not has_meaningful_content:
        confidence = min(confidence, 60.0)
        calibration_info = {
            "calibration_appliquee": True,
            "raison_limitation": f"Email court ({word_count} mots) sans IOC, lien ou pièce jointe identifiable",
            "confiance_plafonnee_a": 60.0,
        }
        return confidence, "INCONCLUSIVE", True, calibration_info

    if char_count < 200 and not has_meaningful_content:
        confidence = min(confidence, 60.0)
        calibration_info = {
            "calibration_appliquee": True,
            "raison_limitation": f"Email très court ({char_count} caractères) sans contenu exploitable",
            "confiance_plafonnee_a": 60.0,
        }
        return confidence, "INCONCLUSIVE", True, calibration_info

    return confidence, "", False, calibration_info


class EmailHeaderExpert(VirtualExpert):
    expert_id = "email_header_expert"
    expert_name = "Email Protocol Analyst"
    category = "email_security"
    capabilities = ["spf_dkim_dmarc", "email_headers", "sender_analysis",
                    "email_authentication", "multi_url_analysis", "brand_impersonation"]
    MITRE_TECHNIQUES = ["T1566 - Phishing", "T1534 - Internal Spearphishing",
                        "T1566.001 - Spearphishing Attachment",
                        "T1566.002 - Spearphishing Link",
                        "T1078.004 - Valid Accounts: Cloud Accounts"]

    HIGH_CONF_KEYWORDS = [
        "dmarc fail", "spf fail", "dkim fail", "no-reply", "noreply",
        "spoofed", "forged", "header", "from:", "reply-to:", "return-path:",
        "x-mailer", "x-originating", "received:", "envelope-from",
        "spearphishing", "usurpation", "typosquatting",
    ]
    MED_CONF_KEYWORDS = [
        "email", "smtp", "imap", "outlook", "gmail", "mail", "sender",
        "recipient", "subject", "body", "attachment", "inbox",
        "url", "lien", "multiple", "domaine",
    ]

    def _analyze_query(self, query: str, context: Dict) -> Dict:
        confidence = self._compute_confidence(query, self.HIGH_CONF_KEYWORDS, self.MED_CONF_KEYWORDS)
        iocs = self._extract_iocs(query)
        evidence = []
        conclusion = "UNKNOWN"
        severity = "UNKNOWN"
        recommendations = []
        mitre_techniques = list(self.MITRE_TECHNIQUES)
        url_details = []
        spearphishing_signals = []
        calibration_info = {}

        # ── RÈGLE-T72: Calibration emails courts (appliquée en premier) ──
        calibrated_confidence, calibrated_verdict, needs_escalation, calibration_info = \
            _calibrate_short_email(query, confidence)
        if calibration_info["calibration_appliquee"]:
            evidence.append(calibration_info["raison_limitation"])
            # Cap confidence but DO NOT skip URL/spearphishing analysis —
            # a short email can still contain phishing indicators
            confidence = calibrated_confidence

        # ── RÈGLE-T09: Extraction et analyse multi-URL ──────────────────
        all_urls = _extract_all_urls(query)
        if len(all_urls) >= 2:
            evidence.append(f"[RÈGLE-T09] {len(all_urls)} URLs détectées dans l'email")
            for u in all_urls:
                info = _score_url(u)
                url_details.append(info)
                if info["signaux"]:
                    evidence.append(f"  URL: {info['domaine']} — score: {info['score_risque']}% ({'; '.join(info['signaux'][:2])})")

            # Score global = max des scores (une URL malveillante suffit)
            global_url_score = max(info["score_risque"] for info in url_details) if url_details else 0
            most_risky = max(url_details, key=lambda x: x["score_risque"]) if url_details else None

            evidence.append(f"Score URLs: max={global_url_score}% sur {len(url_details)} URLs")

            # Impact sur la confiance
            if global_url_score >= 60:
                confidence = min(confidence + 20, 95)
                if "T1566.002" not in mitre_techniques:
                    mitre_techniques.append("T1566.002 - Spearphishing Link")
            elif global_url_score >= 30:
                confidence = min(confidence + 10, 95)

            url_context = {
                "urls_detectees": all_urls,
                "url_la_plus_risquee": most_risky["url_brute"] if most_risky else "",
                "score_global_urls": global_url_score,
                "verdict_par_url": {u["url_brute"][:60]: {"domaine": u["domaine"], "score": u["score_risque"],
                                                           "signaux": u["signaux"]} for u in url_details},
            }

        elif len(all_urls) == 1:
            info = _score_url(all_urls[0])
            url_details.append(info)
            if info["score_risque"] >= 30:
                evidence.append(f"URL suspecte: {info['domaine']} (score: {info['score_risque']}%)")
                confidence = min(confidence + 10, 95)
            url_context = {"urls_detectees": all_urls, "url_la_plus_risquee": all_urls[0],
                           "score_global_urls": info["score_risque"]}
        else:
            url_context = {"urls_detectees": [], "score_global_urls": 0}

        # ── RÈGLE-T10: Détection spearphishing par usurpation ──────────
        sender_domain = _extract_sender_domain(query)
        is_spear, spear_bonus, spear_signals = _detect_spearphishing(
            sender_domain, query, url_details
        )
        spearphishing_signals = spear_signals

        if is_spear:
            evidence.append(f"[RÈGLE-T10] SPEARPHISHING CONFIRMÉ — usurpation de marque détectée")
            for s in spear_signals:
                evidence.append(f"  Signal: {s}")
            confidence = max(confidence, spear_bonus)
            if "T1566.001" not in mitre_techniques:
                mitre_techniques.append("T1566.001 - Spearphishing Link")
            if "T1078.004" not in mitre_techniques:
                mitre_techniques.append("T1078.004 - Valid Accounts: Cloud Accounts")

        if spear_signals and not is_spear:
            for s in spear_signals:
                evidence.append(f"  Signal potentiel: {s}")

        # ── Analyses existantes (DMARC, SPF, DKIM) ─────────────────────
        if "dmarc" in query:
            if "fail" in query or "none" in query:
                evidence.append("DMARC: politique défaillante — risque de spoofing")
                confidence = min(confidence + 20, 95)
        if "spf" in query and "fail" in query:
            evidence.append("SPF: echec de validation — expéditeur non autorisé")
            confidence = min(confidence + 20, 95)
        if "dkim" in query and "fail" in query:
            evidence.append("DKIM: signature invalide — email potentiellement altéré")
            confidence = min(confidence + 20, 95)

        email_iocs = [i for i in iocs if i["type"] == "email"]
        if email_iocs:
            evidence.append(f"Adresse email suspecte: {email_iocs[0]['value']}")

        # Expert supplémentaire si spearphishing
        if is_spear:
            recommendations.append("ACTIVER IOC Expert — analyse complémentaire nécessaire")
            capabilities = self.capabilities + ["ioc_analysis"]
        else:
            capabilities = self.capabilities

        # ── Décision finale ────────────────────────────────────────────
        if confidence >= 55:
            conclusion = "BLOCK"
            severity = "HIGH" if confidence >= 80 else "MEDIUM"
        elif confidence >= 25:
            conclusion = "UNKNOWN"
            severity = "MEDIUM"
        else:
            conclusion = "ACCEPT"
            severity = "INFORMATIONAL"

        if needs_escalation and conclusion == "ACCEPT":
            severity = "LOW"
            if "Escalade humaine requise" not in recommendations:
                recommendations.append("Escalade humaine requise — email trop court")

        recs = []
        if conclusion == "BLOCK":
            recs = ["Vérifier la configuration DMARC du domaine expéditeur",
                    "Mettre à jour les règles SPF/DKIM", "Bloquer le domaine si spoofing confirmé"]
            if is_spear:
                recs = ["SPEARPHISHING CONFIRMÉ — Alerter le SOC immédiatement",
                        "Vérifier si d'autres utilisateurs ont reçu le même email",
                        "Analyser les URLs avec sandboxing",
                        "Réinitialiser les credentials si compromise suspectée"] + recs
        elif "email" in query:
            recs = ["Analyser les en-têtes complets de l'email", "Vérifier les enregistrements DNS du domaine"]
        if url_details:
            recs.append(f"{len(all_urls)} URL(s) analysée(s) — surveiller le trafic sortant")
        if needs_escalation:
            recs.append("Escalade humaine — email trop court pour analyse fiable")
        if calibration_info.get("calibration_appliquee"):
            recs.append(f"Calibration appliquée: {calibration_info['raison_limitation']}")

        response_parts = [f"Analyse protocolaire email: {conclusion}."]
        if is_spear:
            response_parts.append("SPEARPHISHING CONFIRMÉ par usurpation de marque.")
        if url_details:
            response_parts.append(f"{len(all_urls)} URL(s) analysée(s). Score max: {url_context.get('score_global_urls', 0)}%.")

        return {
            "response": " ".join(response_parts),
            "conclusion": conclusion,
            "confidence": confidence,
            "evidence": evidence,
            "limitations": ["Analyse sans accès aux en-têtes bruts complets"],
            "recommendations": recs,
            "iocs": iocs,
            "mitre_techniques": mitre_techniques[:5],
            "severity": severity,
            "url_analysis": url_context,
            "spearphishing_analysis": {
                "detected": is_spear,
                "signals": spearphishing_signals,
                "sender_domain": sender_domain,
            },
            "calibration": calibration_info,
        }
