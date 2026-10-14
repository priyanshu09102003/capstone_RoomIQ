/**
 * Centralized formatting utilities for RoomIQ sensor telemetry,
 * predictions, timestamps, and model evaluation metrics.
 */

export function formatTemp(celsius: number | null | undefined): string {
  if (celsius === null || celsius === undefined || Number.isNaN(celsius)) {
    return "-- °C";
  }
  return `${celsius.toFixed(2)} °C`;
}

export function formatHumidity(pct: number | null | undefined): string {
  if (pct === null || pct === undefined || Number.isNaN(pct)) {
    return "-- %";
  }
  return `${pct.toFixed(2)} %`;
}

export function formatLux(lux: number | null | undefined): string {
  if (lux === null || lux === undefined || Number.isNaN(lux)) {
    return "-- Lux";
  }
  return `${Math.round(lux).toLocaleString()} Lux`;
}

export function formatCO2(ppm: number | null | undefined): string {
  if (ppm === null || ppm === undefined || Number.isNaN(ppm)) {
    return "-- ppm";
  }
  return `${Math.round(ppm).toLocaleString()} ppm`;
}

export function formatHumidityRatio(hr: number | null | undefined): string {
  if (hr === null || hr === undefined || Number.isNaN(hr)) {
    return "-- kg/kg";
  }
  return `${hr.toFixed(6)} kg/kg`;
}

export function formatPercent(ratio: number | null | undefined, decimals = 1): string {
  if (ratio === null || ratio === undefined || Number.isNaN(ratio)) {
    return "--%";
  }
  return `${(ratio * 100).toFixed(decimals)}%`;
}

export function formatMetricScore(score: number | null | undefined, decimals = 3): string {
  if (score === null || score === undefined || Number.isNaN(score)) {
    return "--";
  }
  return score.toFixed(decimals);
}

export function formatTimestamp(isoString: string | null | undefined): string {
  if (!isoString) return "Awaiting timestamp";
  try {
    const d = new Date(isoString);
    if (Number.isNaN(d.getTime())) return isoString;
    return d.toLocaleString(undefined, {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return isoString;
  }
}

export function formatTimeOnly(isoString: string | null | undefined): string {
  if (!isoString) return "--:--:--";
  try {
    const d = new Date(isoString);
    if (Number.isNaN(d.getTime())) return isoString;
    return d.toLocaleTimeString(undefined, {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    });
  } catch {
    return isoString;
  }
}
