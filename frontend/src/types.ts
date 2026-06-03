export interface EntityLabel {
  key: string;       // e.g. "brand"
  label: string;     // e.g. "BRAND"
  color: string;     // Tailwind color class for badges (e.g. "bg-emerald-500/10 text-emerald-400 border-emerald-500/20")
  title: string;     // e.g. "Бренд"
}

export interface PresetSchema {
  id: string;
  name: string;
  description: string;
  labels: EntityLabel[];
  defaultRecords: Record<string, string>[];
}

export interface AugmentationConfig {
  variationsPerRow: number; // сколько вариаций делать на каждую исходную строку
  noiseRatio: number;      // 0 to 1
  typoRatio: number;       // 0 to 1
  shuffleOrder: boolean;
  removeWhitespaces: boolean; // e.g. "25 мг" -> "25мг"
  truncateWords: boolean;     // e.g. "таблетки" -> "таб"
  lowercase: boolean;         // привести все значения к нижнему регистру
}

export interface EntitySpan {
  start: number;
  end: number;
  label: string;
  value: string;
}

export interface SyntheticSample {
  id: string;
  rawText: string;
  entities: EntitySpan[];
  originalRecordId: string;
  cellValues?: Record<string, string>;
}

export interface TrainingMetric {
  epoch: number;
  lossNer: number;
  precision: number;
  recall: number;
  fScore: number;
}

export interface LogLine {
  timestamp: string;
  type: "info" | "success" | "warning" | "error" | "terminal";
  message: string;
}

export interface TrainingModel {
  id: string;
  name: string;
  presetId: string;
  datasetSize: number;
  noiseLevel: number;
  optimizerType: "accuracy" | "efficiency";
  baseModel: string;
  status: "idle" | "training" | "ready" | "failed";
  progress: number; // 0 to 100
  metrics: TrainingMetric[];
  bestFScore: number;
  createdAt: string;
  epochsCount: number;
  logs: LogLine[];
}

export interface ParsingResult {
  text: string;
  entities: {
    label: string;
    text: string;
    start: number;
    end: number;
  }[];
}
