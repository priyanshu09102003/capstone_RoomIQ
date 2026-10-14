/**
 * TypeScript schemas matching the RoomIQ FastAPI backend models.
 * System Classification: DATASET REPLAY / SIMULATION
 */

export interface HealthResponse {
  system_label: string;
  status: "healthy" | "degraded" | string;
  api_status: string;
  models_ready: boolean;
  data_ready: boolean;
  timestamp: string;
  version: string;
  details: {
    predictor_ready?: boolean;
    simulator_ready?: boolean;
    horizon_minutes?: number;
    features_count?: number;
    error?: string;
    [key: string]: unknown;
  };
}

export interface SensorSnapshot {
  timestamp: string;
  temperature: number;
  humidity: number;
  light: number;
  co2: number;
  humidity_ratio: number;
}

export interface PredictionPayload {
  forecast_temperature: number;
  forecast_humidity: number;
  predicted_occupancy: 0 | 1;
  occupancy_probability: number;
  prediction_horizon_minutes: number;
}

export interface ApplianceState {
  fan_on: boolean;
  light_on: boolean;
  fan_last_switched_at?: string | null;
  light_last_switched_at?: string | null;
  last_occupied_at?: string | null;
}

export interface TransitionEvent {
  timestamp: string;
  device: "fan" | "light" | string;
  previous_state: boolean;
  new_state: boolean;
  decision_reason: string;
  sensor_readings: Record<string, number>;
  forecast_outputs: Record<string, unknown>;
}

export interface RetrospectiveComparison {
  prediction_timestamp: string;
  target_timestamp: string;
  predicted_occupancy: number;
  actual_occupancy: number;
  occupancy_correct: boolean;
  forecast_temperature: number;
  actual_temperature: number;
  temperature_error: number;
  forecast_humidity: number;
  actual_humidity: number;
  humidity_error: number;
}

export interface SimulationStepResult {
  step_index: number;
  timestamp: string;
  system_label: string;
  sensor_snapshot: SensorSnapshot;
  prediction: PredictionPayload;
  appliance_state: ApplianceState;
  transition_events: TransitionEvent[];
  retrospective_evaluation?: RetrospectiveComparison | null;
  future_ground_truth?: {
    target_timestamp?: string;
    target_occupancy?: number;
    target_temperature?: number;
    target_humidity?: number;
    target_light?: number;
    target_co2?: number;
    [key: string]: unknown;
  } | null;
}

export type SimulationStatus = "IDLE" | "RUNNING" | "PAUSED" | "COMPLETED";

export interface SimulationStateSummary {
  system_label: string;
  status: SimulationStatus;
  current_index: number;
  total_records: number;
  current_timestamp?: string | null;
  playback_speed: number;
  appliance_state: ApplianceState;
  events_count: number;
  completed: boolean;
}

export interface SimulationActionResponse {
  system_label: string;
  status: SimulationStatus;
  message: string;
  current_index: number;
  timestamp: string;
}

export interface ControlConfig {
  fan_temp_on_threshold: number;
  fan_temp_off_threshold: number;
  fan_min_switching_interval_seconds: number;
  light_lux_threshold: number;
  light_vacancy_delay_seconds: number;
}

export interface FullConfigResponse {
  system_label: string;
  control_config: ControlConfig;
  playback_speed: number;
  split_name: string;
  start_index: number;
}

export interface ConfigUpdateRequest {
  fan_temp_on_threshold?: number;
  fan_temp_off_threshold?: number;
  fan_min_switching_interval_seconds?: number;
  light_lux_threshold?: number;
  light_vacancy_delay_seconds?: number;
  playback_speed?: number;
}

export interface EventsResponse {
  system_label: string;
  events: TransitionEvent[];
  total_count: number;
}

export interface ModelsMetadataResponse {
  system_label: string;
  prediction_horizon_minutes: number;
  features: string[];
  total_features: number;
  training_timestamp?: string | null;
  sample_counts?: Record<string, number>;
  date_ranges?: Record<string, { start: string; end: string }>;
}

export interface MetricsResponse {
  system_label: string;
  training_timestamp?: string | null;
  validation_metrics: {
    occupancy?: {
      model?: {
        accuracy: number;
        precision: number;
        recall: number;
        f1: number;
        roc_auc?: number | null;
        confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
        sample_count: number;
      };
      baseline?: { accuracy: number };
    };
    temperature?: {
      model?: { mae: number; rmse: number; r2: number };
      baseline?: { mae: number; rmse: number; r2: number };
    };
    humidity?: {
      model?: { mae: number; rmse: number; r2: number };
      baseline?: { mae: number; rmse: number; r2: number };
    };
  };
  test1_metrics: Record<string, unknown>;
  test2_metrics: {
    occupancy?: {
      model?: {
        accuracy: number;
        precision: number;
        recall: number;
        f1: number;
        roc_auc?: number | null;
        confusion_matrix: { tn: number; fp: number; fn: number; tp: number };
        sample_count: number;
      };
      baseline?: { accuracy: number };
    };
    temperature?: {
      model?: { mae: number; rmse: number; r2: number };
      baseline?: { mae: number; rmse: number; r2: number };
    };
    humidity?: {
      model?: { mae: number; rmse: number; r2: number };
      baseline?: { mae: number; rmse: number; r2: number };
    };
  };
}

export interface PredictResponse {
  system_label: string;
  prediction_horizon_minutes: number;
  future_occupancy: number;
  occupancy_probability: number;
  future_temperature: number;
  future_humidity: number;
  timestamp: string;
}
