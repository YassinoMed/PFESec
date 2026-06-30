#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_batch_1000.py — Génération + exécution de 1000 tests sur tous les modèles

Distribué en 10 catégories x 100 tests :
  1. Phishing         6. CVE
  2. Légitimes        7. Logs/SIEM
  3. URLs             8. Domaines
  4. IPs              9. Adversarial
  5. Hashes          10. Edge cases

Usage :
    python test_batch_1000.py                         # Mode direct (council)
    python test_batch_1000.py --http                  # Via serveur HTTP
    python test_batch_1000.py --quick                 # 200 tests seulement
    python test_batch_1000.py --dry-run               # Générer sans exécuter
"""

import asyncio
import csv
import json
import math
import os
import random
import sys
import time
import traceback
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)

random.seed(42)

# ── Helpers de génération ─────────────────────────────────────────────

def pick(lst: list) -> Any:
    return random.choice(lst)

def pick_n(lst: list, n: int) -> list:
    return random.sample(lst, min(n, len(lst)))

# ── 1. PHISHING (100) ─────────────────────────────────────────────────

PHISHING_SUBJECTS = [
    "URGENT: Votre compte a ete suspendu",
    "Alerte de securite: action requise",
    "Votre mot de passe expire aujourd'hui",
    "Facture impayee - paiement immediat",
    "Colis en attente de livraison",
    "Confirmation de commande #{}",
    "Vous avez recu un message prive",
    "Alerte: connexion suspecte detectee",
    "Offre exceptionnelle - gratuit",
    "Reinitialisation de mot de passe",
]

PHISHING_SENDERS = [
    "securite@paypal-verify.com",
    "support@microsoft-security.tk",
    "comptabilite@facture-urgente.xyz",
    "service-client@banque-verification.ga",
    "livraison@dhl-poste.xyz",
    "no-reply@amazon-commande.tk",
    "message@linkedin-secure.ga",
    "alert@google-security.xyz",
    "promo@bonplan-offre.ga",
    "reset@password-recovery.tk",
]

PHISHING_URLS = [
    "http://bit.ly/3xPh1sh",
    "http://tinyurl.com/verify-account",
    "http://paypal-secure.verify.tk",
    "http://microsoft-support.ga/login",
    "http://banque-verification.xyz/securite",
    "http://dhl-livraison.tk/colis",
    "http://amazon-commande.ga/urgent",
    "http://google-alerts.xyz/verify",
    "http://linkedin-message.tk/notification",
    "http://password-reset.ga/reset",
    "http://rnicrosoft.com/account",  # typosquatting
    "http://g00gle.com/security",
    "http://paypa1.com/login",
    "http://faceb00k.com/verify",
    "http://amaz0n.co/order",
]

def gen_phishing(i: int) -> str:
    subj = pick(PHISHING_SUBJECTS).format(i)
    sender = pick(PHISHING_SENDERS)
    url = pick(PHISHING_URLS)
    bodies = [
        f"Cher client, nous avons detecte une activite suspecte sur votre compte. Cliquez ici pour verifier: {url}",
        f"Bonjour, votre compte sera suspendu sous 24h si vous ne confirmez pas vos informations: {url}",
        f"Veuillez mettre a jour vos coordonnees bancaires via ce lien securise: {url}",
        f"Alerte ! Quelqu'un essaie de se connecter a votre compte. Verifiez: {url}",
        f"Vous devez immediatement securiser votre compte en cliquant sur ce lien: {url}",
    ]
    body = pick(bodies)
    return f"Subject: {subj}\nFrom: {sender}\n\n{body}"

# ── 2. LÉGITIMES (100) ────────────────────────────────────────────────

LEGIT_SUBJECTS = [
    "Compte-rendu reunion {}",
    "Votre facture du mois",
    "Confirmation de rendez-vous",
    "Nouvelle version du document",
    "Invitation evenement equipe",
    "Rappel: date limite projet",
    "Bulletin d'information #{}",
    "Accuse de reception",
    "Mise a jour: planning equipe",
    "Reunion: point hebdomadaire",
]

LEGIT_SENDERS = [
    "jean.dupont@entreprise.com",
    "comptabilite@entreprise.com",
    "secretariat@cabinet-medical.fr",
    "rh@groupe-industrie.com",
    "equipe-projet@techcorp.io",
    "direction@ecole.edu",
    "newsletter@magazine.fr",
    "support@logiciel.com",
    "manager@equipe.org",
    "administration@mairie.fr",
]

def gen_legitimate(i: int) -> str:
    subj = pick(LEGIT_SUBJECTS).format(i)
    sender = pick(LEGIT_SENDERS)
    bodies = [
        f"Bonjour, suite a notre reunion, veuillez trouver le CR ci-joint. Cordialement.",
        f"Cher collaborateur, votre note de frais du mois a ete validee.",
        f"Votre rendez-vous est confirme pour le {random.randint(1,28)}/{random.randint(1,12)}.",
        f"Merci de trouver ci-joint la nouvelle version du document revise.",
        f"N'oubliez pas la reunion d'equipe demain a 10h en salle A.",
    ]
    body = pick(bodies)
    return f"Subject: {subj}\nFrom: {sender}\n\n{body}"

# ── 3. URLs (100) ─────────────────────────────────────────────────────

MALICIOUS_URLS = [
    "http://evil.com/exploit",
    "http://malware-download.xyz/setup.exe",
    "http://phishing-login.ga/account",
    "http://driveby-download.tk/exploit",
    "http://malvertising.xyz/click",
    "http://data-exfil.ga/upload",
    "http://c2-server.tk/beacon",
    "http://ransomware-payload.xyz/encrypt",
    "http://credential-harvest.ga/login",
    "http://malicious-redirect.tk/steal",
    "http://0x7f000001.com/exploit",
    "http://%68%74%74%70%73://evil.com/xss",
    "http://evil.com@legitimate.com/redirect",
    "http://legitimate.com:9999@evil.net/phish",
    "http://microsoft.com.malicious.xyz/account",
    "http://google.com.verify.ga/login",
    "http://safe.com@evil.com (lien legitime en apparence)",
    "http://paypal.com.secure-login.tk/",
    "http://xn--pple-43d.com/phish",  # punycode: apple
    "http://bit.ly/3xPh1sh (redirige vers phishing)",
]

BENIGN_URLS = [
    "http://google.com/search?q=securite",
    "http://github.com/project/security",
    "http://docs.python.org/3/library/",
    "http://stackoverflow.com/questions/123",
    "http://openai.com/blog/security",
    "http://microsoft.com/download/windows",
    "http://npmjs.com/package/express",
    "http://docker.com/products/security",
    "http://cloudflare.com/learning/security",
    "http://ubuntu.com/download/server",
    "http://redhat.com/en/technologies",
    "http://oracle.com/security-alerts/",
    "http://apache.org/security/cves",
    "http://nginx.org/en/security_advisories",
    "http://python.org/downloads/release",
    "http://nodejs.org/en/download/",
    "http://postgresql.org/docs/current/",
    "http://redis.io/documentation",
    "http://mongodb.com/docs/manual/",
    "http://elastic.co/guide/index.html",
]

def gen_url(i: int) -> str:
    if i < 50:
        url = pick(MALICIOUS_URLS)
        return f"Analyser cette URL: {url}"
    else:
        url = pick(BENIGN_URLS)
        return f"Verifier cette URL: {url}"

# ── 4. IPs (100) ──────────────────────────────────────────────────────

MALICIOUS_IPS = [
    "10.0.0.5", "10.0.0.15", "10.0.0.50", "10.0.0.100",
    "10.0.1.5", "10.0.1.25", "10.0.2.10", "10.0.2.50",
    "10.0.3.5", "10.0.3.20", "10.0.4.1", "10.0.4.99",
    "10.0.5.10", "10.0.5.55", "10.0.6.7", "10.0.6.88",
    "10.0.7.1", "10.0.7.33", "10.0.8.44", "10.0.8.77",
    "10.0.9.11", "10.0.9.66", "10.0.10.22", "10.0.10.99",
    "10.0.11.3", "10.0.11.44", "10.0.12.55", "10.0.12.88",
    "10.0.13.7", "10.0.13.77", "10.0.14.9", "10.0.14.66",
    "10.0.15.12", "10.0.15.33", "10.0.16.88", "10.0.16.99",
    "10.0.17.5", "10.0.17.50", "10.0.18.25", "10.0.18.75",
    "10.0.19.8", "10.0.19.42", "10.0.20.15", "10.0.20.63",
    "10.0.21.1", "10.0.21.30", "10.0.22.7", "10.0.22.49",
    "10.0.23.18", "10.0.23.88",
]

BENIGN_IPS = [
    "8.8.8.8", "8.8.4.4", "1.1.1.1", "9.9.9.9",
    "208.67.222.222", "208.67.220.220",
    "185.228.168.168", "185.228.169.168",
    "76.76.19.19", "76.223.122.150",
    "192.168.1.1", "10.0.0.1", "172.16.0.1",
    "192.168.0.100", "10.10.10.1",
    "203.0.113.1", "198.51.100.1",
    "192.0.2.1", "198.18.0.1", "198.19.0.1",
    "169.254.1.1", "127.0.0.1", "::1", "0.0.0.0",
    "224.0.0.1", "240.0.0.1", "255.255.255.255",
]

def gen_ip(i: int) -> str:
    if i < 50:
        ip = pick(MALICIOUS_IPS)
        return f"Alerte: connexion depuis IP {ip} vers serveur DMZ"
    else:
        ip = pick(BENIGN_IPS)
        return f"Verifier IP: {ip}"

# ── 5. HASHES (100) ───────────────────────────────────────────────────

MALICIOUS_HASHES_MD5 = [
    "e99a18c428cb38d5f260853678922e03",
    "c9c5b4c8b8c8c8c8c8c8c8c8c8c8c8c8",
    "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6",
    "deadbeefdeadbeefdeadbeefdeadbeef",
    "1234567890abcdef1234567890abcdef",
]
MALICIOUS_HASHES_SHA1 = [
    "a9993e364706816aba3e25717850c26c9cd0d89d",
    "da39a3ee5e6b4b0d3255bfef95601890afd80709",
    "5baa61e4c9b93f3f0682250b6cf8331b7ee68fd8",
    "e5e9fa1ba31ecd1ae84f75caaa474f3a663f05f4",
    "b1b3773a5c5c0c6c9c9c0c6c5c3773a5b1b3773a",
]
MALICIOUS_HASHES_SHA256 = [
    "a665a45920422f9d417e4867efdc4fb8a04a1f3fff1fa07e998e86f7f7a27ae3",
    "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8",
    "6b3a55e0261b0306c2b0bb5b3b7d5f5b5e7f5c5d5a5b5c5d5e5f6a6b6c6d6e6f",
    "9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
]
CLEAN_HASHES = [
    "00000000000000000000000000000000",
    "11111111111111111111111111111111",
    "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
    "ffffffffffffffffffffffffffffffff",
    "0123456789abcdef0123456789abcdef",
]

def gen_hash(i: int) -> str:
    if i < 60:
        h = pick(MALICIOUS_HASHES_MD5 + MALICIOUS_HASHES_SHA1 + MALICIOUS_HASHES_SHA256)
        return f"Hash detecte: {h}"
    else:
        h = pick(CLEAN_HASHES)
        return f"Verifier ce hash: {h}"

# ── 6. CVE (100) ──────────────────────────────────────────────────────

HIGH_CVES = [
    ("CVE-2024-3094", 10.0, "XZ Utils - backdoor dans liblzma"),
    ("CVE-2023-44487", 9.8, "HTTP/2 Rapid Reset Attack"),
    ("CVE-2024-6387", 9.8, "OpenSSH regreSSHion - RCE"),
    ("CVE-2021-44228", 10.0, "Log4Shell - RCE dans Log4j"),
    ("CVE-2022-22965", 9.8, "Spring4Shell - RCE"),
    ("CVE-2023-34362", 9.1, "MOVEit Transfer - SQLi"),
    ("CVE-2024-27198", 9.8, "JetBrains TeamCity - auth bypass"),
    ("CVE-2024-4577", 9.8, "PHP CGI - RCE Windows"),
    ("CVE-2023-23397", 9.1, "Microsoft Outlook - elevation"),
    ("CVE-2024-1709", 9.1, "ConnectWise ScreenConnect - auth bypass"),
    ("CVE-2023-2868", 9.8, "Barracuda ESG - RCE"),
    ("CVE-2023-34362", 9.1, "MOVEit Transfer - SQL injection"),
    ("CVE-2024-21413", 9.8, "Microsoft Outlook - RCE"),
    ("CVE-2023-46604", 9.8, "Apache ActiveMQ - RCE"),
    ("CVE-2024-20931", 9.8, "Oracle WebLogic - RCE"),
    ("CVE-2023-42793", 9.8, "TeamCity - auth bypass"),
    ("CVE-2024-24919", 9.1, "Check Point - info disclosure"),
    ("CVE-2023-22527", 9.8, "Atlassian Confluence - RCE"),
    ("CVE-2024-27198", 9.8, "JetBrains TeamCity - auth bypass"),
    ("CVE-2023-50164", 9.8, "Apache Struts - RCE"),
]

MEDIUM_CVES = [
    ("CVE-2024-1234", 5.5, "Vulnerabilite mineure dans libfoo"),
    ("CVE-2024-5678", 6.1, "XSS dans application web"),
    ("CVE-2024-9012", 4.3, "CSRF dans module admin"),
    ("CVE-2024-3456", 5.0, "DoS par requetes malformees"),
    ("CVE-2024-7890", 6.5, "Path traversal dans serveur web"),
    ("CVE-2024-2345", 4.8, "Clickjacking dans panneau admin"),
    ("CVE-2024-6789", 5.4, "Open redirect dans module auth"),
    ("CVE-2024-3457", 6.0, "Weak password policy dans SSO"),
    ("CVE-2024-8901", 4.9, "Information disclosure dans headers"),
    ("CVE-2024-2346", 5.7, "Session fixation dans app legacy"),
]

def gen_cve(i: int) -> str:
    if i < 50:
        cve_id, cvss, desc = pick(HIGH_CVES)
        return f"Analyser {cve_id} (CVSS {cvss}) - {desc}"
    else:
        cve_id, cvss, desc = pick(MEDIUM_CVES)
        return f"Verifier {cve_id} (CVSS {cvss}) - {desc}"

# ── 7. LOGS / SIEM (100) ──────────────────────────────────────────────

SIEM_ALERTS = [
    "ALERTE: Connexion SSH depuis IP {} vers serveur DMZ a 03:14 UTC",
    "ALERTE: Brute force SSH detecte - IP {} - 1500 tentatives en 5 minutes",
    "WARNING: Taux d'erreur HTTP 5xx depasse seuil - {} req/s",
    "CRITICAL: Execution de commande suspecte sur {} par utilisateur root",
    "ALERTE: Scan de ports detecte depuis {} vers plage 1-1024",
    "INFO: Nouvelle connexion VPN etablie depuis {}",
    "ALERTE: Telechargement de fichier suspect depuis {}",
    "CRITICAL: Exfiltration de donnees detectee - {} Go sortant",
    "WARNING: Tentative d'acces a ressource interdite depuis {}",
    "ALERTE: Modification de regle firewall par utilisateur non autorise - {}",
]

def gen_log(i: int) -> str:
    ip = pick(MALICIOUS_IPS + BENIGN_IPS)
    alert = pick(SIEM_ALERTS)
    return alert.format(ip)

# ── 8. DOMAINES (100) ─────────────────────────────────────────────────

TYPO_DOMAINS = [
    "g00gle.com", "goolge.com", "go0gle.com", "googl3.com",
    "microsoft.com", "micr0s0ft.com", "microsft.com", "rnicrosoft.com",
    "faceb00k.com", "facebok.com", "faceboook.com", "facebo0k.com",
    "amaz0n.com", "amzon.com", "amazoon.com", "amazzon.com",
    "paypa1.com", "paypl.com", "paypall.com", "paypaI.com",
    "app1e.com", "aple.com", "appple.com", "appl3.com",
    "tw1tter.com", "twiter.com", "twitt3r.com", "twtter.com",
    "1inkedin.com", "linkedn.com", "link3din.com", "linked1n.com",
    "y0utube.com", "youtub3.com", "youtbe.com", "youtubee.com",
    "instagr4m.com", "instagrm.com", "instagraam.com",
]

LEGIT_DOMAINS = [
    "google.com", "microsoft.com", "facebook.com", "amazon.com",
    "paypal.com", "apple.com", "twitter.com", "linkedin.com",
    "youtube.com", "instagram.com", "github.com", "gitlab.com",
    "stackoverflow.com", "reddit.com", "wikipedia.org",
    "openai.com", "python.org", "docker.com", "npmjs.com",
    "cloudflare.com", "ubuntu.com", "oracle.com", "apache.org",
    "nginx.org", "postgresql.org", "redis.io", "mongodb.com",
    "elastic.co", "nodejs.org", "golang.org",
]

def gen_domain(i: int) -> str:
    if i < 50:
        d = pick(TYPO_DOMAINS)
        return f"Verifier ce domaine suspect: {d}"
    else:
        d = pick(LEGIT_DOMAINS)
        return f"Analyser ce domaine: {d}"

# ── 9. ADVERSARIAL (100) ──────────────────────────────────────────────

def gen_adversarial(i: int) -> str:
    variants = [
        # Base64
        f"Email encode: {__import__('base64').b64encode(pick(PHISHING_SUBJECTS).format(i).encode()).decode()[:100]}",
        # White text injection
        f"Cher client, <span style='color:white'>phishing</span> cliquez sur le lien ci-dessous",
        # Zero-width characters
        f"Cher client, cliquez ici: http://evil.com\u200b\u200b\u200b/phishing",
        # Homograph attack
        f"Verifiez votre compte: http://www.micrоsoft.com/login (o cyrillique)",
        # URL shortener
        f"Cliquez: http://short.url/{random.randint(100,999)}",
        # Double encoding
        f"Lien: http://evil.com/%25%33%31%25%36%35/etc",
        # HTML injection
        f"<html><body><a href='http://evil.com'>Cliquez ici</a></body></html>",
        # JavaScript redirect
        f'<script>window.location="http://evil.com"</script>',
        # Punycode
        f"http://xn--pple-43d.com/phishing",
        # Data URI
        f'<img src="data:image/svg+xml;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==">',
        # Mixed content
        f"http://evil.com@google.com/redirection",
        # Tab in domain
        f"http://evil\t.com/phish",
        # Very long subdomain
        f"http://{'a'*50}.evil.com/phish",
        # IP in decimal
        f"http://3232235778/ (192.168.1.2 en decimal)",
        # Fake file extension
        f"http://evil.com/document.pdf.exe",
    ]
    return pick(variants)

# ── 10. EDGE CASES (100) ──────────────────────────────────────────────

def gen_edge(i: int) -> str:
    edge_types = [
        # Empty / minimal
        "",
        " ",
        "a",
        "test",
        # Very short
        "Votre compte",
        "Mot de passe",
        "Cliquez ici",
        "URGENT",
        "ALERTE",
        # Numbers / special chars
        "12345",
        "!@#$%",
        "---",
        "...",
        # Very long (truncated)
        "Mot " * 1000,
        # Unicode
        "\u4e2d\u56fd\u94f6\u884c\u786e\u8ba4",
        "\u0412\u0430\u0448 \u0441\u0447\u0435\u0442",
        "\u062a\u062d\u062f\u064a\u062b \u0627\u0644\u062d\u0633\u0627\u0628",
        # Emails with special chars
        "Subject: Re: Re: Re: Re: Re: Fwd: Fwd: Fwd: test",
        "From: \"test; drop table users\"@evil.com",
        # JSON / XML
        '{"email": "test@test.com", "action": "verify"}',
        "<email><action>verify</action><account>test</account></email>",
        # SQL injection attempt
        "'; DROP TABLE users; --",
        "1' OR '1'='1",
        # Cross-site scripting
        "<script>alert('XSS')</script>",
        "{{7*7}}",
        "${7*7}",
        # Path traversal
        "../../../etc/passwd",
        "..\\..\\..\\windows\\system32\\config",
        # Large numbers
        f"Hash: {'a' * 64}",
        f"IP: {random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}",
        # Formula / spreadsheet
        "=HYPERLINK('http://evil.com')",
        "=CMD('dir')",
        # Mixed languages
        "Bonjour, your account requires verification: http://evil.com",
        "URGENT: あなたのアカウントが停止されました http://evil.com",
    ]
    return pick(edge_types)


# ═══════════════════════════════════════════════════════════════════════
#  Générateur principal
# ═══════════════════════════════════════════════════════════════════════

CATEGORY_GENERATORS = {
    "phishing":    (gen_phishing, "Email"),
    "legitimate":  (gen_legitimate, "Email"),
    "url":         (gen_url, "URL"),
    "ip":          (gen_ip, "IP"),
    "hash":        (gen_hash, "Hash"),
    "cve":         (gen_cve, "CVE"),
    "log":         (gen_log, "Log/SIEM"),
    "domain":      (gen_domain, "Domaine"),
    "adversarial": (gen_adversarial, "Adversarial"),
    "edge":        (gen_edge, "Edge Case"),
}


@dataclass
class BatchTestResult:
    test_id: str
    category: str
    subcategory: str
    input_preview: str
    classification: str = ""
    experts_used: list = field(default_factory=list)
    consensus_score: float = 0.0
    confidence_level: str = ""
    final_decision: str = ""
    latency_s: float = 0.0
    status: str = "UNKNOWN"
    error: str = ""
    dj_present: bool = False

# ═══════════════════════════════════════════════════════════════════════
#  Runner
# ═══════════════════════════════════════════════════════════════════════

class BatchRunner1000:
    def __init__(self, use_http: bool = False, http_url: str = ""):
        self.use_http = use_http
        self.http_url = http_url or "http://localhost:8080/api/v1/security/council"
        self.council = None
        self.results: List[BatchTestResult] = []

        if not use_http:
            self._init_direct()

    def _init_direct(self):
        try:
            from backend.models_registry.registry import get_registry
            from backend.council.config import CouncilConfig
            from backend.council.orchestrator import MasterAIOrchestrator
            reg = get_registry()
            cfg = CouncilConfig.default()
            cfg.max_debate_rounds = 1
            self.council = MasterAIOrchestrator(reg, cfg)
            print("[OK] Council initialise")
        except Exception as e:
            print(f"[WARN] Impossible d'initialiser le council: {e}")
            self.council = None

    def generate_tests(self, total: int = 1000) -> List[tuple]:
        """Génère (test_id, category, subcategory, input_text)"""
        tests = []
        per_cat = total // len(CATEGORY_GENERATORS)
        remainder = total % len(CATEGORY_GENERATORS)

        idx = 0
        for cat_name, (gen_fn, subcat) in CATEGORY_GENERATORS.items():
            count = per_cat + (1 if remainder > 0 else 0)
            if remainder > 0:
                remainder -= 1
            for i in range(count):
                idx += 1
                test_id = f"B{idx:04d}"
                try:
                    if cat_name == "edge" and i > 0:
                        text = gen_fn(i)
                    else:
                        text = gen_fn(idx)
                except Exception:
                    text = f"Test {cat_name} #{i}"
                tests.append((test_id, cat_name, subcat, text))

        # Shuffle for variety
        random.shuffle(tests)
        return tests

    async def run_single(self, test_id: str, category: str, subcat: str, text: str) -> BatchTestResult:
        tr = BatchTestResult(
            test_id=test_id,
            category=category,
            subcategory=subcat,
            input_preview=text[:80],
        )
        t0 = time.time()
        try:
            result = await self._run_council(text)
            tr.latency_s = time.time() - t0

            if result is None:
                tr.status = "ERROR"
                tr.error = "No result from council"
                return tr

            if isinstance(result, dict):
                dj = result.get("decision_journal", {})
                consensus = result.get("consensus", {})
                tr.classification = result.get("classification", "")
                tr.experts_used = result.get("selected_models", [])
                tr.consensus_score = float(consensus.get("global_score", 0)) if isinstance(consensus, dict) else 0
                tr.confidence_level = consensus.get("confidence_level", "") if isinstance(consensus, dict) else ""
                tr.final_decision = dj.get("final_decision", "") if isinstance(dj, dict) else ""
                tr.dj_present = bool(dj and dj.get("session_id"))
            else:
                dj = getattr(result, "decision_journal", None)
                consensus = getattr(result, "consensus", {}) if hasattr(result, "consensus") else {}
                tr.classification = getattr(result, "classification", "")
                tr.experts_used = getattr(result, "selected_models", [])
                tr.consensus_score = float(consensus.get("global_score", 0)) if isinstance(consensus, dict) else 0
                tr.confidence_level = consensus.get("confidence_level", "") if isinstance(consensus, dict) else ""
                tr.final_decision = getattr(dj, "final_decision", "") if dj else ""
                tr.dj_present = bool(dj and getattr(dj, "session_id", ""))

            tr.status = "PASS" if tr.consensus_score > 0 else "FAIL"
            if tr.error:
                tr.status = "ERROR"

        except Exception as e:
            tr.latency_s = time.time() - t0
            tr.status = "ERROR"
            tr.error = f"{type(e).__name__}: {str(e)[:100]}"

        return tr

    async def _run_council(self, query: str):
        if self.use_http:
            return await self._run_http(query)
        if self.council:
            return await self.council.run(query=query, user_role="analyst")
        raise RuntimeError("No backend available")

    async def _run_http(self, query: str):
        import urllib.request
        payload = json.dumps({"query": query, "user_role": "analyst"}).encode()
        req = urllib.request.Request(self.http_url, data=payload,
                                     headers={"Content-Type": "application/json"},
                                     method="POST")
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                return json.loads(resp.read())
        except:
            return None

    def _par_workers(self, total: int) -> int:
        if total <= 100:
            return 5
        elif total <= 500:
            return 10
        return 20

    async def run_batch(self, tests: List[tuple]) -> List[BatchTestResult]:
        total = len(tests)
        workers = self._par_workers(total)
        print(f"\n  Workers paralleles: {workers}")
        print(f"  Execution de {total} tests...\n")

        self.results = []
        sem = asyncio.Semaphore(workers)

        async def worker(test_params: tuple) -> BatchTestResult:
            async with sem:
                return await self.run_single(*test_params)

        done = 0
        batch_size = 50
        for start in range(0, total, batch_size):
            batch = tests[start:start + batch_size]
            tasks = [worker(t) for t in batch]
            batch_results = await asyncio.gather(*tasks)

            for tr in batch_results:
                self.results.append(tr)
                done += 1
                if done % 100 == 0:
                    passed = sum(1 for r in self.results if r.status == "PASS")
                    avg_lat = sum(r.latency_s for r in self.results if r.latency_s) / max(done, 1)
                    print(f"    [{done}/{total}] PASS: {passed}, latence moy: {avg_lat:.2f}s")

        return self.results

    def generate_report(self) -> str:
        results = self.results
        if not results:
            return ""

        total = len(results)
        passed = sum(1 for r in results if r.status == "PASS")
        failed = sum(1 for r in results if r.status == "FAIL")
        errors = sum(1 for r in results if r.status == "ERROR")

        total_ms = sum(r.latency_s for r in results)
        avg_lat = total_ms / total if total else 0
        max_lat = max(r.latency_s for r in results)
        min_lat = min(r.latency_s for r in results)

        # Stats par catégorie
        cats = defaultdict(lambda: {"total": 0, "pass": 0, "fail": 0, "error": 0, "latency": 0.0, "scores": []})
        for r in results:
            c = cats[r.category]
            c["total"] += 1
            c["latency"] += r.latency_s
            if r.status == "PASS": c["pass"] += 1
            elif r.status == "FAIL": c["fail"] += 1
            else: c["error"] += 1
            c["scores"].append(r.consensus_score)

        # Stats par niveau de confiance
        conf_counts = Counter(r.confidence_level for r in results)
        conf_scores = defaultdict(list)
        for r in results:
            conf_scores[r.confidence_level].append(r.consensus_score)

        # Décisions
        decision_counts = Counter(r.final_decision for r in results if r.final_decision)

        # Distribution des experts
        all_experts = []
        for r in results:
            all_experts.extend(r.experts_used)
        expert_counts = Counter(all_experts)

        # Histogramme des scores
        score_buckets = {"0-20": 0, "20-40": 0, "40-60": 0, "60-80": 0, "80-95": 0, "95-100": 0}
        for r in results:
            s = r.consensus_score
            if s < 20: score_buckets["0-20"] += 1
            elif s < 40: score_buckets["20-40"] += 1
            elif s < 60: score_buckets["40-60"] += 1
            elif s < 80: score_buckets["60-80"] += 1
            elif s < 95: score_buckets["80-95"] += 1
            else: score_buckets["95-100"] += 1

        # Top décisions
        top_decisions = decision_counts.most_common(15)

        # Rapport
        lines = [
            f"# Rapport Batch 1000 Tests — SecureRAG Hub / AI Security Council",
            f"",
            f"**Date :** {datetime.now().strftime('%d/%m/%Y %H:%M')}",
            f"**Mode :** {'HTTP' if self.use_http else 'Direct'}",
            f"**Tests :** {total}",
            f"",
            f"---",
            f"## 1. Resume Global",
            f"",
            f"| Metrique | Valeur |",
            f"|---|---|",
            f"| Total tests | {total} |",
            f"| ✅ PASS | **{passed}** ({passed/total*100:.1f}%) |",
            f"| ❌ FAIL | {failed} ({failed/total*100:.1f}%) |",
            f"| ⚠️ ERROR | {errors} ({errors/total*100:.1f}%) |",
            f"| Latence moyenne | {avg_lat:.3f}s |",
            f"| Latence min | {min_lat:.3f}s |",
            f"| Latence max | {max_lat:.3f}s |",
            f"| Temps total | {total_ms:.1f}s |",
            f"| Decision Journal present | {sum(1 for r in results if r.dj_present)}/{total} |",
            f"",
            f"---",
            f"## 2. Resultats par Categorie",
            f"",
            f"| Categorie | Tests | PASS | FAIL | ERROR | Taux succès | Latence moy | Score moy |",
            f"|---|---|---|---|---|---|---|---|",
        ]

        for cat_name, gen_info in CATEGORY_GENERATORS.items():
            _, subcat = gen_info
            c = cats[cat_name]
            rate = c["pass"] / c["total"] * 100 if c["total"] else 0
            avg_s = sum(c["scores"]) / len(c["scores"]) if c["scores"] else 0
            avg_l = c["latency"] / c["total"] if c["total"] else 0
            lines.append(
                f"| {subcat} ({cat_name}) | {c['total']} | {c['pass']} | {c['fail']} | {c['error']} | "
                f"{rate:.1f}% | {avg_l:.3f}s | {avg_s:.1f}% |"
            )

        lines.extend([
            f"",
            f"---",
            f"## 3. Distribution des Scores de Consensus",
            f"",
            f"| Intervalle | Nombre | % |",
            f"|---|---|---|",
        ])
        for bucket, count in score_buckets.items():
            pct = count / total * 100
            bar = "█" * int(pct / 2) + "░" * (50 - int(pct / 2))
            lines.append(f"| {bucket}% | {count} | {pct:.1f}% | {bar} |")

        lines.extend([
            f"",
            f"---",
            f"## 4. Distribution des Niveaux de Confiance",
            f"",
            f"| Niveau | Tests | Score moyen |",
            f"|---|---|---|",
        ])
        for level in ["High", "Medium", "Low"]:
            count = conf_counts.get(level, 0)
            avg_s = sum(conf_scores[level]) / len(conf_scores[level]) if conf_scores[level] else 0
            lines.append(f"| {level} | {count} | {avg_s:.1f}% |")

        lines.extend([
            f"",
            f"---",
            f"## 5. Top 15 Decisions",
            f"",
            f"| Decision | Occurrences | % |",
            f"|---|---|---|",
        ])
        for dec, cnt in top_decisions:
            lines.append(f"| {dec} | {cnt} | {cnt/total*100:.1f}% |")

        lines.extend([
            f"",
            f"---",
            f"## 6. Experts les plus sollicites",
            f"",
            f"| Expert | Utilisations |",
            f"|---|---|",
        ])
        for expert, cnt in expert_counts.most_common(15):
            lines.append(f"| {expert} | {cnt} |")

        # Histogramme latence
        lat_buckets = {"0-0.1s": 0, "0.1-0.5s": 0, "0.5-1s": 0, "1-2s": 0, "2-5s": 0, ">5s": 0}
        for r in results:
            s = r.latency_s
            if s < 0.1: lat_buckets["0-0.1s"] += 1
            elif s < 0.5: lat_buckets["0.1-0.5s"] += 1
            elif s < 1.0: lat_buckets["0.5-1s"] += 1
            elif s < 2.0: lat_buckets["1-2s"] += 1
            elif s < 5.0: lat_buckets["2-5s"] += 1
            else: lat_buckets[">5s"] += 1

        lines.extend([
            f"",
            f"---",
            f"## 7. Distribution des Latences",
            f"",
            f"| Intervalle | Nombre | % |",
            f"|---|---|---|",
        ])
        for bucket, count in lat_buckets.items():
            pct = count / total * 100
            bar = "█" * int(pct)
            lines.append(f"| {bucket} | {count} | {pct:.1f}% | {bar} |")

        lines.extend([
            f"",
            f"---",
            f"## 8. Distribution par type d'entree",
            f"",
            f"| Type | Tests | PASS | Score moy | Latence moy |",
            f"|---|---|---|---|---|",
        ])
        for cat_name, gen_info in CATEGORY_GENERATORS.items():
            _, subcat = gen_info
            c = cats.get(cat_name, {})
            avg_s = sum(c.get("scores", [0])) / max(len(c.get("scores", [0])), 1)
            avg_l = c.get("latency", 0) / max(c.get("total", 1), 1)
            lines.append(f"| {subcat} | {c.get('total', 0)} | {c.get('pass', 0)} | {avg_s:.1f}% | {avg_l:.3f}s |")

        lines.extend([
            f"",
            f"---",
            f"## 9. Echantillon de resultats (20 premiers tests)",
            f"",
            f"| ID | Categorie | Entree | Decision | Score | Confiance | Latence |",
            f"|---|---|---|---|---|---|---|",
        ])
        for r in results[:20]:
            lines.append(
                f"| {r.test_id} | {r.category} | {r.input_preview[:40]} | "
                f"{r.final_decision[:30] or '-'} | {r.consensus_score:.1f}% | "
                f"{r.confidence_level[:6] or '-'} | {r.latency_s:.3f}s |"
            )

        lines.extend([
            f"",
            f"---",
            f"## 10. Tests en Erreur",
            f"",
        ])
        errs = [r for r in results if r.status == "ERROR"]
        if errs:
            lines.append(f"| ID | Categorie | Erreur |")
            lines.append(f"|---|---|---|")
            for r in errs[:20]:
                lines.append(f"| {r.test_id} | {r.category} | {r.error[:60]} |")
        else:
            lines.append("Aucune erreur.")

        lines.extend([
            f"",
            f"---",
            f"*Rapport genere automatiquement par test_batch_1000.py le {datetime.now().strftime('%Y-%m-%d %H:%M')}*",
        ])

        report = "\n".join(lines)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = REPORTS_DIR / f"batch1000_rapport_{ts}.md"
        report_path.write_text(report, encoding="utf-8")
        print(f"\n[OK] Rapport: {report_path}")

        # CSV détaillé
        csv_path = REPORTS_DIR / f"batch1000_resultats_{ts}.csv"
        with open(csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Categorie", "Sous-categorie", "Entree", "Classification",
                             "Experts", "Score", "Confiance", "Decision", "Latence", "Status", "Erreur", "DJ"])
            for r in results:
                writer.writerow([
                    r.test_id, r.category, r.subcategory, r.input_preview,
                    r.classification, " ".join(r.experts_used),
                    f"{r.consensus_score:.1f}%", r.confidence_level, r.final_decision,
                    f"{r.latency_s:.3f}s", r.status, r.error,
                    "OUI" if r.dj_present else "NON"
                ])
        print(f"[OK] CSV: {csv_path}")

        # JSON consolidé
        json_path = REPORTS_DIR / f"batch1000_stats_{ts}.json"
        stats = {
            "total": total, "passed": passed, "failed": failed, "errors": errors,
            "avg_latency_s": round(avg_lat, 4), "max_latency_s": round(max_lat, 4),
            "min_latency_s": round(min_lat, 4), "total_time_s": round(total_ms, 2),
            "categories": {k: {"total": v["total"], "pass": v["pass"], "fail": v["fail"],
                               "error": v["error"],
                               "avg_score": round(sum(v["scores"])/len(v["scores"]), 1) if v["scores"] else 0,
                               "avg_latency": round(v["latency"]/v["total"], 4) if v["total"] else 0}
                          for k, v in cats.items()},
            "conf_distribution": dict(conf_counts),
            "decision_distribution": dict(decision_counts.most_common(20)),
            "expert_distribution": dict(expert_counts.most_common(20)),
            "score_histogram": score_buckets,
            "latency_histogram": lat_buckets,
        }
        json_path.write_text(json.dumps(stats, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[OK] Stats JSON: {json_path}")

        # Résumé console
        print(f"\n{'='*70}")
        print(f"  BATCH 1000 TESTS - RESULTATS")
        print(f"{'='*70}")
        print(f"  Total  : {total}")
        print(f"  PASS   : {passed} ({passed/total*100:.1f}%)")
        print(f"  FAIL   : {failed}")
        print(f"  ERR    : {errors}")
        print(f"  Temps  : {total_ms:.1f}s (moy: {avg_lat:.3f}s/test)")
        print(f"  DJ     : {sum(1 for r in results if r.dj_present)}/{total} avec Decision Journal")
        print(f"{'='*70}")
        print(f"  Fichiers dans reports/")

        return report


# ═══════════════════════════════════════════════════════════════════════
#  Main
# ═══════════════════════════════════════════════════════════════════════

async def main():
    import argparse
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="Batch 1000 tests SecureRAG Hub")
    parser.add_argument("--http", action="store_true", help="Mode HTTP")
    parser.add_argument("--url", default="http://localhost:8080/api/v1/security/council")
    parser.add_argument("--quick", action="store_true", help="200 tests seulement")
    parser.add_argument("--dry-run", action="store_true", help="Generer sans executer")
    parser.add_argument("--count", type=int, default=1000, help="Nombre de tests (defaut: 1000)")
    args = parser.parse_args()

    total = 200 if args.quick else args.count

    runner = BatchRunner1000(use_http=args.http, http_url=args.url)

    print(f"\n{'#'*70}")
    print(f"  Batch 1000 Tests - SecureRAG Hub")
    print(f"  Mode: {'HTTP' if args.http else 'Direct'}")
    print(f"  Tests: {total}")
    if args.dry_run:
        print(f"  Dry-run: OUI (generation uniquement)")
    print(f"{'#'*70}\n")

    print("Generation des donnees de test...")
    tests = runner.generate_tests(total)

    # Stats de génération
    cat_counts = Counter(t[1] for t in tests)
    print(f"\n  Distribution:")
    for cat, cnt in sorted(cat_counts.items()):
        print(f"    {cat}: {cnt} tests")
    print(f"  Total: {len(tests)} tests generes\n")

    if args.dry_run:
        print("[DRY-RUN] Generation terminee. Utilisez --quick ou --count pour executer.")
        return

    print("Execution des tests...")
    t_start = time.time()
    results = await runner.run_batch(tests)
    t_elapsed = time.time() - t_start

    print(f"\nExecution terminee en {t_elapsed:.1f}s")

    runner.generate_report()


if __name__ == "__main__":
    asyncio.run(main())
