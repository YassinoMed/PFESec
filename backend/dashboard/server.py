"""Dashboard Server — Interface temps réel de l'architecture Multi-Master AI.

Serve WebSocket + HTTP statique pour visualiser :
- Global Coordinator AI
- Masters AI actifs
- Experts interrogés
- Échanges inter-Masters
- Discussion temps réel
- Consensus pondéré
- Rapport final
"""

import asyncio
import json
import os
import sys
import time
from typing import Optional, Set

import aiohttp
from aiohttp import web

# Ajouter la racine du projet au path pour les imports
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from backend.council.multi_master.discussion_journal import DiscussionJournal


class DashboardServer:
    """Serveur Dashboard avec WebSocket temps réel.

    Points clés :
    - Diffusion en temps réel des entrées du DiscussionJournal
    - Pas d'authentification (environnement local/SOC)
    - Route REST pour les sessions passées
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8090):
        self.host = host
        self.port = port
        self._app: Optional[web.Application] = None
        self._websockets: Set[web.WebSocketResponse] = set()
        self._journal: Optional[DiscussionJournal] = None
        self._session_history: list = []

    def attach_journal(self, journal: DiscussionJournal):
        """Attache un journal de discussion pour diffusion en temps réel."""
        self._journal = journal
        journal.add_listener(self._broadcast_entry)

    def _broadcast_entry(self, entry: dict):
        """Callback appelé à chaque nouvelle entrée du journal."""
        asyncio.ensure_future(self._broadcast(entry))

    async def _broadcast(self, entry: dict):
        """Diffuse une entrée à tous les clients WebSocket connectés."""
        payload = json.dumps(entry, ensure_ascii=False, default=str)
        dead = set()
        for ws in self._websockets:
            try:
                await ws.send_str(payload)
            except Exception:
                dead.add(ws)
        self._websockets -= dead

    # ── Routes ─────────────────────────────────────────────────────────────

    async def _handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        ws = web.WebSocketResponse()
        await ws.prepare(request)
        self._websockets.add(ws)

        try:
            # Envoyer l'historique au nouveau client
            if self._journal:
                for entry in self._journal.get_all():
                    try:
                        await ws.send_str(json.dumps(entry, ensure_ascii=False, default=str))
                    except Exception:
                        break

            # Maintenir la connexion
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.ERROR:
                    break
                if msg.type == aiohttp.WSMsgType.TEXT:
                    # Accepter les commandes simples
                    try:
                        data = json.loads(msg.data)
                        if data.get("action") == "ping":
                            await ws.send_str(json.dumps({"type": "pong", "source": "dashboard"}))
                    except Exception:
                        pass

        except Exception:
            pass
        finally:
            self._websockets.discard(ws)

        return ws

    async def _handle_history(self, request: web.Request) -> web.Response:
        """Retourne l'historique complet des sessions."""
        entries = self._journal.get_all() if self._journal else []
        return web.json_response(entries, dumps=lambda o: json.dumps(o, ensure_ascii=False, default=str))

    async def _handle_status(self, request: web.Request) -> web.Response:
        """Retourne le statut du serveur."""
        return web.json_response({
            "status": "running",
            "websocket_clients": len(self._websockets),
            "journal_entries": len(self._journal.get_all()) if self._journal else 0,
            "uptime_s": round(time.time() - self._started_at, 1) if hasattr(self, '_started_at') else 0,
        })

    async def _handle_index(self, request: web.Request) -> web.Response:
        """Page d'accueil du dashboard."""
        html_path = os.path.join(os.path.dirname(__file__), "static", "index.html")
        if os.path.exists(html_path):
            return web.FileResponse(html_path)
        return web.Response(text="Dashboard not found", status=404)

    # ── Démarrage ──────────────────────────────────────────────────────────

    async def start(self):
        self._started_at = time.time()
        self._app = web.Application()
        self._app.router.add_get("/", self._handle_index)
        self._app.router.add_get("/ws", self._handle_websocket)
        self._app.router.add_get("/api/history", self._handle_history)
        self._app.router.add_get("/api/status", self._handle_status)

        runner = web.AppRunner(self._app)
        await runner.setup()
        site = web.TCPSite(runner, self.host, self.port)
        await site.start()
        print(f"[Dashboard] Serveur démarré sur http://{self.host}:{self.port}")
        return runner

    async def stop(self):
        if self._app:
            for ws in self._websockets:
                await ws.close()
            self._websockets.clear()


# ── Point d'entrée autonome pour test ─────────────────────────────────────

async def main():
    journal = DiscussionJournal()
    server = DashboardServer()
    server.attach_journal(journal)

    # Simulation d'activité
    async def simulate():
        await asyncio.sleep(1)
        journal.coordinator_opened("Session de démonstration.")
        await asyncio.sleep(0.5)
        journal.master_activated("threat_master", "Threat Master", "Analyse phishing")
        await asyncio.sleep(0.3)
        journal.expert_queried("threat_master", "Phishing Expert", "Analysez l'email")
        await asyncio.sleep(0.3)
        journal.expert_responded("threat_master", "Phishing Expert", "Phishing confirmé (92%)")
        await asyncio.sleep(0.3)
        journal.master_activated("soc_master", "SOC Master", "Analyse MITRE")
        await asyncio.sleep(0.3)
        journal.master_discussion(1, "Threat Master", "SOC Master",
                                  "Ma conclusion diffère de la tienne.")
        await asyncio.sleep(0.3)
        journal.consensus_reached(87.5, "BLOCK", "Poids: threat=0.40, soc=0.35, rag=0.25")
        await asyncio.sleep(0.3)
        journal.report_generated("Rapport final: PHISHING CONFIRMÉ - Score: 87.5%")

    await server.start()
    asyncio.create_task(simulate())
    print("Dashboard accessible sur http://localhost:8090")
    print("WebSocket: ws://localhost:8090/ws")
    print("Appuyez sur Ctrl+C pour arrêter.")

    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    finally:
        await server.stop()


if __name__ == "__main__":
    asyncio.run(main())
