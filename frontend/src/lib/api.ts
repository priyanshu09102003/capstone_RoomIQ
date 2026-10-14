/**
 * Type-safe API Client for RoomIQ FastAPI Backend.
 * Standardized on NEXT_PUBLIC_ROOMIQ_API_URL.
 */

import {
  ConfigUpdateRequest,
  EventsResponse,
  FullConfigResponse,
  HealthResponse,
  MetricsResponse,
  ModelsMetadataResponse,
  PredictResponse,
  SimulationActionResponse,
  SimulationStateSummary,
  SimulationStepResult,
} from "@/types/api";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_ROOMIQ_API_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://127.0.0.1:8000";

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/**
 * Perform a typed HTTP request against the RoomIQ FastAPI backend.
 * Protects against stalled responses using an AbortController timeout.
 */
async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs = 10000
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const headers = {
    "Content-Type": "application/json",
    ...(options.headers || {}),
  };

  try {
    const res = await fetch(url, {
      ...options,
      headers,
      signal: options.signal || controller.signal,
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      let errorDetail = `Request failed (${res.status} ${res.statusText})`;
      try {
        const errorJson = await res.json();
        if (typeof errorJson.detail === "string") {
          errorDetail = errorJson.detail;
        } else if (Array.isArray(errorJson.details)) {
          // Pydantic validation error format
          errorDetail = errorJson.details
            .map((e: { location?: string; message?: string }) => `${e.location}: ${e.message}`)
            .join("; ");
        } else if (errorJson.error) {
          errorDetail = errorJson.error;
        }
      } catch {
        // Fall back to status text
      }
      throw new ApiError(res.status, errorDetail);
    }

    return (await res.json()) as T;
  } catch (err) {
    clearTimeout(timeoutId);
    if (err instanceof ApiError) throw err;
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ApiError(408, `Request to ${endpoint} timed out after ${timeoutMs}ms.`);
    }
    throw new ApiError(
      0,
      `Backend unreachable at ${API_BASE_URL}. Ensure FastAPI is running on port 8000.`
    );
  }
}

export const api = {
  getHealth: (signal?: AbortSignal) =>
    request<HealthResponse>("/api/health", { method: "GET", signal }, 5000),

  getMetrics: (signal?: AbortSignal) =>
    request<MetricsResponse>("/api/metrics", { method: "GET", signal }),

  getModels: (signal?: AbortSignal) =>
    request<ModelsMetadataResponse>("/api/models", { method: "GET", signal }),

  getSimulationStatus: (signal?: AbortSignal) =>
    request<SimulationStateSummary>("/api/simulation/status", { method: "GET", signal }, 5000),

  stepSimulation: () =>
    request<SimulationStepResult>("/api/simulation/step", { method: "POST" }, 8000),

  startSimulation: () =>
    request<SimulationActionResponse>("/api/simulation/start", { method: "POST" }),

  pauseSimulation: () =>
    request<SimulationActionResponse>("/api/simulation/pause", { method: "POST" }),

  resumeSimulation: () =>
    request<SimulationActionResponse>("/api/simulation/resume", { method: "POST" }),

  resetSimulation: () =>
    request<SimulationActionResponse>("/api/simulation/reset", { method: "POST" }),

  getEvents: (limit = 100, device?: string, signal?: AbortSignal) => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (device && device !== "all") params.append("device", device);
    return request<EventsResponse>(`/api/events?${params.toString()}`, { method: "GET", signal });
  },

  getConfig: (signal?: AbortSignal) =>
    request<FullConfigResponse>("/api/config", { method: "GET", signal }),

  updateConfig: (update: ConfigUpdateRequest) =>
    request<FullConfigResponse>("/api/config", {
      method: "PUT",
      body: JSON.stringify(update),
    }),

  predict: (features: Record<string, number>) =>
    request<PredictResponse>("/api/predict", {
      method: "POST",
      body: JSON.stringify({ features }),
    }),

  /**
   * Health check ping that checks both HTTP reachability and model readiness.
   */
  isReachable: async (): Promise<boolean> => {
    try {
      const res = await fetch(`${API_BASE_URL}/api/health`, {
        method: "GET",
        signal: AbortSignal.timeout(3000),
      });
      return res.ok;
    } catch {
      return false;
    }
  },

  /**
   * Execute multiple sequential steps in deterministic order.
   */
  batchStep: async (count: number): Promise<SimulationStepResult[]> => {
    const results: SimulationStepResult[] = [];
    for (let i = 0; i < count; i++) {
      const step = await api.stepSimulation();
      results.push(step);
    }
    return results;
  },
};
