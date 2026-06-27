"use client";

import dynamic from "next/dynamic";

/**
 * Wrapper client pour charger le shader WebGL uniquement côté client.
 * (next/dynamic avec `ssr: false` n'est pas autorisé dans un Server Component.)
 */
const ShaderBackground = dynamic(
  () => import("@/components/ui/shader-background"),
  { ssr: false }
);

export function SentinelBackground() {
  return (
    <>
      <ShaderBackground />
      <div className="sentinel-shader-veil" aria-hidden />
    </>
  );
}
