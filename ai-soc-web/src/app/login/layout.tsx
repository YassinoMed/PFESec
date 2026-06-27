import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign In · AI-SOC Platform",
  description:
    "Secure authentication portal for the AI Security Operating Center.",
};

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <>{children}</>;
}
