import type { Metadata } from "next";
import "./globals.css";
import { SentinelBackground } from "@/components/sentinel/SentinelBackground";

export const metadata: Metadata = {
  title: "Sentinel Command · AI Security Council",
  description:
    "Centre de commandement SOC temps réel — orchestration IA, feed agents live, consensus engine et preuves RAG.",
};

export default function SentinelLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="sentinel-root relative h-screen overflow-hidden">
      <SentinelBackground />
      {children}
    </div>
  );
}
