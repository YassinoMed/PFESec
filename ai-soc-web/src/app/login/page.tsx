"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import { cn } from "@/lib/utils";
import SecurityCard from "@/components/ui/security-card";
import ShaderBackground from "@/components/ui/shader-background";
import {
  ShieldCheck,
  Eye,
  EyeOff,
  ArrowRight,
  Fingerprint,
  Lock,
  Mail,
  Loader2,
} from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [focusedField, setFocusedField] = useState<string | null>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    // Simulate auth — replace with real auth logic
    setTimeout(() => {
      setIsLoading(false);
      window.location.href = "/";
    }, 2000);
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-[#05030a]">
      {/* Premium WebGL Shader Background */}
      <ShaderBackground />

      {/* Main content */}
      <div className="relative z-10 flex w-full max-w-[1100px] items-center justify-center gap-16 px-6 lg:justify-between">
        {/* Left — Security Card showcase (hidden on mobile) */}
        <motion.div
          className="hidden lg:block"
          initial={{ opacity: 0, x: -40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
        >
          <div className="relative">
            {/* Glow behind the card */}
            <div className="absolute -inset-8 rounded-3xl bg-gradient-to-br from-primary/5 via-transparent to-info/5 blur-2xl" />
            <SecurityCard
              delay={6000}
              name="Admin SOC"
              email="admin@securerag.io"
            />
          </div>
          <motion.p
            className="mt-6 max-w-[350px] text-center text-xs leading-relaxed text-neutral-500"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.6, duration: 0.5 }}
          >
            Biometric face-scan simulation — AI-powered identity verification
            with real-time context signals.
          </motion.p>
        </motion.div>

        {/* Right — Login form */}
        <motion.div
          className="w-full max-w-[420px]"
          initial={{ opacity: 0, y: 24 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.7, ease: [0.16, 1, 0.3, 1], delay: 0.15 }}
        >
          {/* Branding */}
          <div className="mb-8 flex items-center gap-3">
            <motion.div
              className="flex h-12 w-12 items-center justify-center rounded-xl border border-primary/30 bg-primary/10 shadow-glow"
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
            >
              <ShieldCheck className="h-6 w-6 text-primary" />
            </motion.div>
            <div>
              <h1 className="font-display text-xl font-bold text-[#f0f4ff]">
                AI-SOC Platform
              </h1>
              <p className="text-[10px] uppercase tracking-[0.25em] text-neutral-500">
                SecureRAG Hub
              </p>
            </div>
          </div>

          {/* Card */}
          <div className="rounded-2xl border border-white/[0.07] bg-white/[0.02] p-8 backdrop-blur-xl">
            <div className="mb-6">
              <h2 className="font-display text-lg font-semibold text-[#f0f4ff]">
                Connexion sécurisée
              </h2>
              <p className="mt-1 text-sm text-neutral-500">
                Accédez au centre de commande SOC
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-5">
              {/* Email */}
              <div className="group relative">
                <label
                  htmlFor="email"
                  className="mb-1.5 block text-xs font-medium text-neutral-400"
                >
                  Email
                </label>
                <div className="relative">
                  <Mail
                    size={16}
                    className={cn(
                      "absolute left-3 top-1/2 -translate-y-1/2 transition-colors",
                      focusedField === "email"
                        ? "text-primary"
                        : "text-neutral-600",
                    )}
                  />
                  <input
                    id="email"
                    type="email"
                    placeholder="admin@securerag.io"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    onFocus={() => setFocusedField("email")}
                    onBlur={() => setFocusedField(null)}
                    required
                    className={cn(
                      "w-full rounded-lg border bg-white/[0.03] py-3 pl-10 pr-4 text-sm text-[#f0f4ff] placeholder-neutral-600 outline-none transition-all duration-300",
                      focusedField === "email"
                        ? "border-primary/50 shadow-[0_0_0_3px_hsl(220_95%_62%/0.1)]"
                        : "border-white/[0.07] hover:border-white/[0.14]",
                    )}
                  />
                </div>
              </div>

              {/* Password */}
              <div className="group relative">
                <label
                  htmlFor="password"
                  className="mb-1.5 block text-xs font-medium text-neutral-400"
                >
                  Mot de passe
                </label>
                <div className="relative">
                  <Lock
                    size={16}
                    className={cn(
                      "absolute left-3 top-1/2 -translate-y-1/2 transition-colors",
                      focusedField === "password"
                        ? "text-primary"
                        : "text-neutral-600",
                    )}
                  />
                  <input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onFocus={() => setFocusedField("password")}
                    onBlur={() => setFocusedField(null)}
                    required
                    className={cn(
                      "w-full rounded-lg border bg-white/[0.03] py-3 pl-10 pr-12 text-sm text-[#f0f4ff] placeholder-neutral-600 outline-none transition-all duration-300",
                      focusedField === "password"
                        ? "border-primary/50 shadow-[0_0_0_3px_hsl(220_95%_62%/0.1)]"
                        : "border-white/[0.07] hover:border-white/[0.14]",
                    )}
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword(!showPassword)}
                    className="absolute right-3 top-1/2 -translate-y-1/2 text-neutral-500 transition-colors hover:text-neutral-300"
                  >
                    {showPassword ? <EyeOff size={16} /> : <Eye size={16} />}
                  </button>
                </div>
              </div>

              {/* Remember + Forgot */}
              <div className="flex items-center justify-between">
                <label className="flex cursor-pointer items-center gap-2 text-xs text-neutral-500">
                  <input
                    type="checkbox"
                    className="h-3.5 w-3.5 rounded border-white/10 bg-white/[0.03] accent-primary"
                  />
                  Se souvenir de moi
                </label>
                <button
                  type="button"
                  className="text-xs text-primary/70 transition-colors hover:text-primary"
                >
                  Mot de passe oublié ?
                </button>
              </div>

              {/* Submit */}
              <motion.button
                type="submit"
                disabled={isLoading}
                className={cn(
                  "group relative flex w-full items-center justify-center gap-2 rounded-lg py-3 text-sm font-semibold transition-all duration-300",
                  "bg-primary text-white shadow-glow hover:shadow-[0_0_30px_hsl(220_95%_62%/0.5)]",
                  "disabled:cursor-not-allowed disabled:opacity-70",
                )}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.98 }}
              >
                <AnimatePresence mode="wait">
                  {isLoading ? (
                    <motion.div
                      key="loader"
                      initial={{ opacity: 0, scale: 0.8 }}
                      animate={{ opacity: 1, scale: 1 }}
                      exit={{ opacity: 0, scale: 0.8 }}
                      className="flex items-center gap-2"
                    >
                      <Loader2 size={16} className="animate-spin" />
                      Authentification…
                    </motion.div>
                  ) : (
                    <motion.div
                      key="idle"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex items-center gap-2"
                    >
                      <Fingerprint size={16} />
                      Se connecter
                      <ArrowRight
                        size={14}
                        className="transition-transform group-hover:translate-x-1"
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.button>
            </form>

            {/* Divider */}
            <div className="my-6 flex items-center gap-3">
              <div className="h-px flex-1 bg-white/[0.06]" />
              <span className="text-[10px] uppercase tracking-widest text-neutral-600">
                ou
              </span>
              <div className="h-px flex-1 bg-white/[0.06]" />
            </div>

            {/* SSO buttons */}
            <div className="grid grid-cols-2 gap-3">
              <motion.button
                className="flex items-center justify-center gap-2 rounded-lg border border-white/[0.07] bg-white/[0.02] py-2.5 text-xs text-neutral-400 transition-all hover:border-white/[0.14] hover:bg-white/[0.05] hover:text-[#f0f4ff]"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <svg className="h-4 w-4" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M12 2C6.477 2 2 6.477 2 12c0 4.42 2.865 8.164 6.839 9.49.5.09.682-.218.682-.483 0-.237-.009-.866-.013-1.7-2.782.603-3.369-1.342-3.369-1.342-.454-1.155-1.11-1.462-1.11-1.462-.908-.62.069-.608.069-.608 1.003.07 1.531 1.03 1.531 1.03.892 1.529 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.11-4.555-4.943 0-1.091.39-1.984 1.029-2.683-.103-.253-.446-1.27.098-2.647 0 0 .84-.269 2.75 1.025A9.578 9.578 0 0112 6.836c.85.004 1.705.114 2.504.336 1.909-1.294 2.747-1.025 2.747-1.025.546 1.377.203 2.394.1 2.647.64.699 1.028 1.592 1.028 2.683 0 3.842-2.339 4.687-4.566 4.935.359.309.678.919.678 1.852 0 1.336-.012 2.415-.012 2.743 0 .267.18.578.688.48C19.138 20.161 22 16.418 22 12c0-5.523-4.477-10-10-10z"
                  />
                </svg>
                GitHub SSO
              </motion.button>
              <motion.button
                className="flex items-center justify-center gap-2 rounded-lg border border-white/[0.07] bg-white/[0.02] py-2.5 text-xs text-neutral-400 transition-all hover:border-white/[0.14] hover:bg-white/[0.05] hover:text-[#f0f4ff]"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <svg className="h-4 w-4" viewBox="0 0 24 24">
                  <path
                    fill="currentColor"
                    d="M3.064 7.51A9.996 9.996 0 0112 2c2.695 0 4.959.99 6.69 2.605l-2.867 2.868C14.786 6.482 13.468 5.977 12 5.977c-2.605 0-4.81 1.76-5.595 4.123-.2.6-.314 1.24-.314 1.9 0 .66.114 1.3.314 1.9.786 2.364 2.99 4.123 5.595 4.123 1.345 0 2.49-.355 3.386-.955a4.6 4.6 0 001.996-3.018H12v-3.868h9.418c.118.654.182 1.336.182 2.045 0 3.046-1.09 5.61-2.982 7.35C16.964 21.105 14.7 22 12 22A9.996 9.996 0 012 12c0-1.614.386-3.14 1.064-4.49z"
                  />
                </svg>
                Google SSO
              </motion.button>
            </div>
          </div>

          {/* Footer */}
          <motion.p
            className="mt-6 text-center text-[10px] text-neutral-600"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.8 }}
          >
            Protégé par chiffrement E2E · TLS 1.3 · Zero-Trust Architecture
          </motion.p>
        </motion.div>
      </div>

      {/* Corner decorative elements */}
      <div className="pointer-events-none absolute bottom-4 left-4 font-mono text-[10px] text-neutral-700">
        v0.1.0 · AI-SOC SecureRAG
      </div>
      <motion.div
        className="pointer-events-none absolute right-4 top-4 flex items-center gap-2"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 1 }}
      >
        <span className="h-2 w-2 animate-pulse rounded-full bg-accept shadow-[0_0_8px_hsl(142_72%_46%)]" />
        <span className="font-mono text-[10px] text-neutral-600">
          Système sécurisé
        </span>
      </motion.div>
    </div>
  );
}
