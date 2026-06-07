// Клиент HTTP API бэкенда NERForge.
// База берётся из VITE_API_URL, по умолчанию локальный бэкенд.

const API_BASE = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

// Параметры генерации датасета (шаг 1).
export interface GenerateConfig {
  variationsPerRow: number;
  noiseRatio: number;
  typoRatio: number;
  removeWhitespaces: boolean;
  truncateWords: boolean;
  shuffleOrder: boolean;
  lowercase: boolean;
}

// Параметры обучения (шаг 2).
export interface TrainParams {
  baseModel: string;
  epochs: number;
  dropout: number;
}

// Статус задачи обучения (приходит по SSE и через GET).
export interface TrainingStatus {
  id: number;
  status: "pending" | "generating" | "training" | "succeeded" | "failed";
  progress: number;
  label_names: string[];
  base_model: string;
  metrics: { ents_f: number | null; ents_p: number | null; ents_r: number | null } | null;
  error: string | null;
  created_at: string;
  updated_at: string;
}

// Результат разбора текста (шаг 3).
export interface ParseResult {
  text: string;
  entities: { label: string; text: string; start: number; end: number }[];
  labels: string[];
}

// Извлекает текст ошибки из ответа бэкенда.
async function readError(response: Response): Promise<string> {
  try {
    const data = await response.json();
    return data?.detail ?? response.statusText;
  } catch {
    return response.statusText;
  }
}

// Шаг 1: отправляет эталонный CSV и получает зашумлённый CSV.
export async function generateDataset(referenceCsv: File, config: GenerateConfig): Promise<Blob> {
  const form = new FormData();
  form.append("file", referenceCsv);
  form.append("variations_per_row", String(config.variationsPerRow));
  form.append("noise_ratio", String(config.noiseRatio));
  form.append("typo_ratio", String(config.typoRatio));
  form.append("remove_whitespaces", String(config.removeWhitespaces));
  form.append("truncate_words", String(config.truncateWords));
  form.append("shuffle_order", String(config.shuffleOrder));
  form.append("lowercase", String(config.lowercase));

  const response = await fetch(`${API_BASE}/generate/`, { method: "POST", body: form });
  if (!response.ok) throw new Error(await readError(response));
  return await response.blob();
}

// Базовая модель spaCy и флаг, установлена ли она на сервере.
export interface BaseModelInfo {
  value: string;
  installed: boolean;
}

// Список базовых моделей с признаком установки.
export async function getBaseModels(): Promise<BaseModelInfo[]> {
  const response = await fetch(`${API_BASE}/train/base-models`);
  if (!response.ok) throw new Error(await readError(response));
  return await response.json();
}

// Шаг 2: запускает обучение на загруженном CSV, возвращает id задачи.
export async function startTraining(trainingCsv: File, params: TrainParams): Promise<TrainingStatus> {
  const form = new FormData();
  form.append("file", trainingCsv);
  form.append("base_model", params.baseModel);
  form.append("epochs", String(params.epochs));
  form.append("dropout", String(params.dropout));

  const response = await fetch(`${API_BASE}/train/`, { method: "POST", body: form });
  if (!response.ok) throw new Error(await readError(response));
  return await response.json();
}

// Открывает SSE-поток статуса обучения. onStatus вызывается на каждое событие.
export function openTrainingStream(
  jobId: number,
  onStatus: (status: TrainingStatus) => void
): EventSource {
  const source = new EventSource(`${API_BASE}/train/${jobId}/stream`);
  source.addEventListener("status", (event) => {
    onStatus(JSON.parse((event as MessageEvent).data));
  });
  return source;
}

// Прямая ссылка на скачивание zip обученной модели.
export function modelDownloadUrl(jobId: number): string {
  return `${API_BASE}/train/${jobId}/model`;
}

// Шаг 3: отправляет zip модели и текст, получает разбивку.
export async function parseText(modelZip: File, text: string): Promise<ParseResult> {
  const form = new FormData();
  form.append("model", modelZip);
  form.append("text", text);

  const response = await fetch(`${API_BASE}/parse/`, { method: "POST", body: form });
  if (!response.ok) throw new Error(await readError(response));
  return await response.json();
}

// Сохраняет Blob как файл в браузере.
export function saveBlob(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
