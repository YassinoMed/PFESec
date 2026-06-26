/**
 * hooks/useApi.ts — Hooks React Query avec bascule auto vers le mock.
 *
 * Principe : on interroge le backend réel. S'il est injoignable
 * (BackendUnreachable), on retombe sur les données simulées et on
 * lève un flag `demo: true` pour que l'UI affiche un bandeau "mode démo".
 */

"use client";

import { useQuery, useMutation } from "@tanstack/react-query";
import { api, BackendUnreachable } from "@/lib/api";
import {
  mockGpu,
  mockModels,
  mockScripts,
} from "@/lib/mock";

export interface ApiState<T> {
  data: T | undefined;
  isLoading: boolean;
  /** true = backend injoignable, données simulées. */
  demo: boolean;
  error: unknown;
}

function withDemo<T>(real: T, demo: boolean): ApiState<T> {
  return { data: real, isLoading: false, demo, error: null };
}

/** Liste des modèles — sert aussi de health check. */
export function useModels(): ApiState<ModelsLike> {
  const q = useQuery({
    queryKey: ["models"],
    queryFn: async () => {
      try {
        return { data: await api.models(), demo: false };
      } catch (e) {
        if (e instanceof BackendUnreachable)
          return { data: mockModels, demo: true };
        throw e;
      }
    },
    refetchInterval: 30000,
    retry: false,
  });
  return {
    data: q.data?.data,
    isLoading: q.isLoading,
    demo: q.data?.demo ?? false,
    error: q.error,
  };
}
type ModelsLike = typeof mockModels;

/** Statut GPU live — polling toutes les 5s (réel) ou figé (démo). */
export function useGpuStatus(): ApiState<typeof mockGpu> {
  const q = useQuery({
    queryKey: ["gpu"],
    queryFn: async () => {
      try {
        return { data: await api.gpuStatus(), demo: false };
      } catch (e) {
        if (e instanceof BackendUnreachable) return { data: mockGpu, demo: true };
        throw e;
      }
    },
    refetchInterval: (query) =>
      query?.state.data?.demo ? false : 5000, // pas de polling en mode démo
    retry: false,
  });
  return {
    data: q.data?.data,
    isLoading: q.isLoading,
    demo: q.data?.demo ?? false,
    error: q.error,
  };
}

/** Liste des scripts de test. */
export function useTestScripts(): ApiState<typeof mockScripts> {
  const q = useQuery({
    queryKey: ["scripts"],
    queryFn: async () => {
      try {
        return { data: await api.testScripts(), demo: false };
      } catch (e) {
        if (e instanceof BackendUnreachable)
          return { data: mockScripts, demo: true };
        throw e;
      }
    },
    retry: false,
  });
  return {
    data: q.data?.data,
    isLoading: q.isLoading,
    demo: q.data?.demo ?? false,
    error: q.error,
  };
}

/* ───────────────────── Mutations (inférence) ─────────────── */

export function usePredictAll() {
  return useMutation({
    mutationFn: async (prompt: string) => {
      try {
        return await api.predictAll(prompt);
      } catch (e) {
        if (e instanceof BackendUnreachable) {
          // Import dynamique pour éviter de charger le mock en prod backend.
          const { mockPredictAll } = await import("@/lib/mock");
          return mockPredictAll(prompt);
        }
        throw e;
      }
    },
  });
}
