# 🧠 AI-SOC Platform — Frontend Next.js

Frontend de l'**AI Security Operating Center** pour SecureRAG Hub.
Transforme le serveur d'inférence multi-modèles (`inference_server.py`) en une
plateforme de surveillance et gouvernance de sécurité IA.

## ✨ Fonctionnalités

| Route | Module | Rôle |
|---|---|---|
| `/` | **SOC Command Center** | Vue d'orchestrateur : flotte de modèles, santé système, GPU live, KPIs |
| `/analyze` | **Threat Analysis** | Analyse multi-modèles avec **consensus de vote** + radar des menaces |
| `/sandbox` | **Single-Model Sandbox** | Inférence isolée sur un modèle, vue détaillée |
| `/batch` | **Batch Evaluation** | Suite de tests + **precision / recall / F1 / confusion matrix** |
| `/gpu` | **GPU Observatory** | Télémétrie continue : jauges VRAM, courbes de charge (time-series) |
| `/governance` | **AI Governance** | Inventaire et comparatif des modèles pour l'audit IA |

## 🚀 Démarrage rapide

```bash
cd security/ai-soc-web
npm install
npm run dev
```

→ Dashboard sur **http://localhost:3000**

### Avec le backend réel (recommandé)

Lance d'abord le serveur d'inférence (dans le dossier parent) :

```bash
python inference_server.py        # écoute sur :8000
```

Puis `npm run dev`. Le frontend consomme automatiquement l'API via un proxy
(`/api/*` → `http://localhost:8000/api/*`). Aucun réglage CORS nécessaire.

### Mode démo (sans backend)

Si `inference_server.py` n'est pas lancé, le dashboard bascule **automatiquement**
sur des données simulées réalistes — un bandeau « Mode démo » vous avertit.
Idéal pour présenter le projet sans GPU.

> Pour pointer vers un autre backend : `BACKEND_URL=http://host:port npm run dev`

## 🏗️ Architecture

```
ai-soc-web/
├─ src/
│  ├─ app/                     # App Router Next.js
│  │  ├─ layout.tsx            # Layout racine (sidebar + topbar + fonts)
│  │  ├─ page.tsx              # / Command Center
│  │  ├─ analyze/              # /analyze
│  │  ├─ sandbox/              # /sandbox
│  │  ├─ batch/                # /batch
│  │  ├─ gpu/                  # /gpu
│  │  ├─ governance/           # /governance
│  │  └─ globals.css           # Design system cyber
│  ├─ components/
│  │  ├─ ui/                   # Card, StatCard, VerdictPill, ThreatBar, RadialGauge…
│  │  ├─ layout/               # Sidebar, Topbar, PageHeader
│  │  ├─ inference/            # ResultCard
│  │  └─ Providers.tsx         # React Query
│  ├─ hooks/useApi.ts          # Hooks avec bascule auto backend↔mock
│  ├─ lib/
│  │  ├─ api.ts                # Client fetch typé
│  │  ├─ metrics.ts            # Calcul precision/recall/F1/confusion
│  │  ├─ mock.ts               # Données simulées (mode démo)
│  │  └─ utils.ts              # cn(), threatTier(), verdictColor()
│  └─ types/api.ts             # Types = schémas exacts du backend
├─ next.config.mjs             # Proxy /api → backend
├─ tailwind.config.ts          # Tokens cyber (#050810, glassmorphism)
└─ package.json
```

## 🎨 Design system

Esthétique **cyber sombre + glassmorphism** (héritée de l'UI existante) :

- Fond `#050810` + glows ambiants (bleu / vert / rouge)
- Couleurs sémantiques : bleu primaire · vert **ACCEPT** · rouge **BLOCK** · ambre **UNCERTAIN**
- Typographies : **Outfit** (titres) · **Inter** (corps) · **Fira Code** (terminal)
- Composants : cartes translucides `backdrop-blur`, jauges SVG, graphiques Recharts

## 📊 Métriques calculées côté client

Le backend (`test_runner.py`) ne fournit que l'**accuracy**. Pour enrichir le
tableau de bord, `src/lib/metrics.ts` dérive depuis `test_results[]` :

- **Precision / Recall / F1** (modèle binaire phishing/safe)
- **Matrice de confusion 2×2**
- **Performance par catégorie** (PHISH, SAFE, ADV, SOC…) extraite du préfixe d'id

## 🔌 API consommée

Tous les endpoints de `inference_server.py` (port 8000) :

| Endpoint | Usage |
|---|---|
| `GET /api/models` | Liste + statut des modèles |
| `GET /api/gpu-status` | Télémétrie GPU (polling 5s) |
| `POST /api/predict` | Inférence mono-modèle |
| `POST /api/predict-all` | Inférence multi-modèles + consensus |
| `POST /api/run-tests` | Exécution suite de tests |
| `GET /api/test-scripts` | Liste des scripts de test |

## 🛠️ Stack

- **Next.js 15** (App Router) + **TypeScript** strict
- **Tailwind CSS** + **TanStack Query** (polling / cache)
- **Recharts** (radar, aires, barres) · **lucide-react** (icônes)

## 📦 Scripts

```bash
npm run dev      # développement (http://localhost:3000)
npm run build    # build production
npm run start    # serveur production
npm run lint     # ESLint
```
