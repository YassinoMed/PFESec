import { fileURLToPath } from "url";
import path from "path";

const __dirname = path.dirname(fileURLToPath(import.meta.url));

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // Scope le tracing/output au répertoire ai-soc-web uniquement
  outputFileTracingRoot: path.join(__dirname),

  // NOTE : on n'utilise PAS le proxy Next.js (rewrites).
  // L'app effectue ses appels directement côté client vers l'URL du backend.
  // Le backend inference_server.py renvoie déjà les headers CORS nécessaires
  // (Access-Control-Allow-Origin: *). Si le backend est éteint, le client
  // attrape l'erreur réseau et bascule automatiquement en mode démo.
  //
  // Surcharge l'URL du backend via la variable d'env BACKEND_URL
  // (défaut : http://localhost:8000).
};

export default nextConfig;
