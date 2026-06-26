import type { Metadata } from "next";
import { Inter, Outfit, Fira_Code } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/Providers";
import { Sidebar } from "@/components/layout/Sidebar";
import { Topbar } from "@/components/layout/Topbar";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});
const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});
const fira = Fira_Code({
  subsets: ["latin"],
  variable: "--font-fira",
  display: "swap",
});

export const metadata: Metadata = {
  title: "AI-SOC Platform · SecureRAG Hub",
  description:
    "AI Security Operating Center — orchestration multi-modèles, observabilité GPU et gouvernance IA.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="fr" className={`${inter.variable} ${outfit.variable} ${fira.variable}`}>
      <body className="font-sans antialiased">
        <Providers>
          <div className="flex min-h-screen">
            <Sidebar />
            <div className="flex min-w-0 flex-1 flex-col">
              <Topbar />
              <main className="flex-1 px-6 py-6 lg:px-8">{children}</main>
            </div>
          </div>
        </Providers>
      </body>
    </html>
  );
}
