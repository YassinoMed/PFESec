#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Test rapide du serveur d'inference."""
import os, sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
import urllib.request
import json
import sys

BASE = "http://localhost:8000"

def api(path, data=None):
    url = BASE + path
    if data:
        body = json.dumps(data).encode()
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
    else:
        req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.loads(r.read())

print("=" * 60)
print("TEST DU SERVEUR SECURERAG HUB")
print("=" * 60)

# 1. Liste modeles
print("\n[1] Modeles disponibles :")
models = api("/api/models")["models"]
for m in models:
    icon = m.get('type','?').upper()
    print(f"   [{icon}] {m['name']:30s} | {m['status']:12s} | loaded={m['loaded']}")

# 2. GPU
print("\n[2] Statut GPU :")
gpu = api("/api/gpu-status")
if gpu["available"]:
    d = gpu["devices"][0]
    print(f"   {d['name']} — {d['total_gb']} GB total — {d['free_gb']} GB libre")
else:
    print("   Aucun GPU CUDA")

# 3. Charger CySecBERT
print("\n[3] Chargement de CySecBERT en VRAM...")
r = api("/api/load-model", {"model": "cysecbert"})
print(f"   -> {r}")

# 4. Inférence test phishing
print("\n[4] Test inférence phishing (CySecBERT)...")
test_email = "URGENT: Your PayPal account has been limited. Click here to verify: http://paypa1-secure.xyz/verify"
result = api("/api/predict", {"model": "cysecbert", "prompt": test_email})
print(f"   Verdict  : {result.get('verdict', 'N/A')}")
print(f"   Prediction: {result.get('prediction', 'N/A')}")
print(f"   Confiance : {result.get('confidence', 0)*100:.1f}%")
print(f"   Threat    : {result.get('threat_score', 0)}%")
print(f"   Temps     : {result.get('elapsed_s', 0)}s")

# 5. Inférence safe
print("\n[5] Test inférence email safe (CySecBERT)...")
safe_email = "Hi John, please find attached the Q3 report. Let me know if you have questions. Best, Sarah"
result2 = api("/api/predict", {"model": "cysecbert", "prompt": safe_email})
print(f"   Verdict  : {result2.get('verdict', 'N/A')}")
print(f"   Prediction: {result2.get('prediction', 'N/A')}")
print(f"   Confiance : {result2.get('confidence', 0)*100:.1f}%")
print(f"   Threat    : {result2.get('threat_score', 0)}%")

# 6. GPU apres chargement
print("\n[6] VRAM apres chargement :")
gpu2 = api("/api/gpu-status")
if gpu2["available"]:
    d = gpu2["devices"][0]
    print(f"   {d['allocated_gb']} GB alloues / {d['total_gb']} GB ({d['utilization_pct']}%)")
    print(f"   Modeles en VRAM: {gpu2['loaded_models']}")

print("\n" + "=" * 60)
print("TOUS LES TESTS OK")
print("Interface web: http://localhost:8000/")
print("=" * 60)
