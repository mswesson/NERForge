import React, { useState, useRef, useEffect } from "react";
import { Upload, Cpu, Download, Play, Check, FileSpreadsheet } from "lucide-react";
import {
  startTraining,
  openTrainingStream,
  modelDownloadUrl,
  getBaseModels,
  TrainingStatus
} from "../api/client";

// Доступные базовые модели spaCy (соответствуют скачанным в Docker-образ).
const BASE_MODELS = [
  { value: "ru_core_news_sm", title: "Малая (sm)", desc: "Быстрая и компактная" },
  { value: "ru_core_news_md", title: "Средняя (md)", desc: "Статические векторы" },
  { value: "ru_core_news_lg", title: "Большая (lg)", desc: "Высокая точность" }
];

// Человеко-понятные подписи статусов.
const STATUS_LABEL: Record<string, string> = {
  pending: "В очереди...",
  generating: "Подготовка обучающих данных...",
  training: "Идёт обучение модели...",
  succeeded: "Обучение завершено",
  failed: "Обучение завершилось ошибкой"
};

export default function ModelTrainer() {
  const [file, setFile] = useState<File | null>(null);
  const [baseModel, setBaseModel] = useState("ru_core_news_sm");
  const [epochs, setEpochs] = useState(10);
  const [dropout, setDropout] = useState(0.2);

  const [jobId, setJobId] = useState<number | null>(null);
  const [status, setStatus] = useState<TrainingStatus | null>(null);
  const [isTraining, setIsTraining] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Какие базовые модели реально установлены на сервере (value -> installed).
  const [installedMap, setInstalledMap] = useState<Record<string, boolean>>({});

  const fileInputRef = useRef<HTMLInputElement>(null);
  const streamRef = useRef<EventSource | null>(null);

  // Закрываем SSE при размонтировании
  useEffect(() => {
    return () => streamRef.current?.close();
  }, []);

  // Узнаём у бэкенда, какие модели установлены (чтобы не дать выбрать недоступную).
  useEffect(() => {
    getBaseModels()
      .then((models) => {
        const map: Record<string, boolean> = {};
        models.forEach((m) => (map[m.value] = m.installed));
        setInstalledMap(map);
      })
      .catch(() => setInstalledMap({})); // при ошибке не блокируем выбор
  }, []);

  // Модель считаем доступной, если бэкенд явно не сказал, что она не установлена.
  const isModelInstalled = (value: string) => installedMap[value] !== false;
  const selectedInstalled = isModelInstalled(baseModel);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setFile(selected);
      setStatus(null);
      setJobId(null);
      setError(null);
    }
  };

  const isDone = status?.status === "succeeded";
  const isFailed = status?.status === "failed";

  const handleStart = async () => {
    if (!file || !selectedInstalled) return;
    setIsTraining(true);
    setError(null);
    setStatus(null);
    streamRef.current?.close();

    try {
      const job = await startTraining(file, { baseModel, epochs, dropout });
      setJobId(job.id);
      setStatus(job);

      streamRef.current = openTrainingStream(job.id, (update) => {
        setStatus(update);
        if (update.status === "succeeded" || update.status === "failed") {
          streamRef.current?.close();
          setIsTraining(false);
          if (update.status === "failed") setError(update.error ?? "Обучение упало");
        }
      });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Не удалось запустить обучение");
      setIsTraining(false);
    }
  };

  const handleDownload = () => {
    if (jobId !== null) {
      const link = document.createElement("a");
      link.href = modelDownloadUrl(jobId);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    }
  };

  const progress = status?.progress ?? 0;
  const metrics = status?.metrics ?? null;

  return (
    <div className="max-w-4xl mx-auto space-y-8" id="model-trainer-container">

      {/* Загрузка обучающего JSONL */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 space-y-5 shadow-sm">
        <div>
          <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
            <FileSpreadsheet className="w-5 h-5 text-violet-600" />
            Обучающий датасет (JSONL)
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Загрузите JSONL, сгенерированный на шаге «Конструктор».
          </p>
        </div>

        <div
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-slate-200 bg-slate-50/30 hover:border-violet-400 hover:bg-violet-50/30 rounded-2xl p-8 text-center cursor-pointer transition-all flex flex-col items-center gap-3"
        >
          <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".jsonl" className="hidden" />
          <div className="p-3.5 bg-white rounded-full border border-slate-200 shadow-sm">
            <Upload className="w-6 h-6 text-violet-600" />
          </div>
          {file ? (
            <span className="text-xs font-bold text-emerald-600 flex items-center gap-1.5">
              <Check className="w-4 h-4" /> {file.name}
            </span>
          ) : (
            <span className="text-xs font-bold text-slate-700">Выберите JSONL-файл с данными для обучения</span>
          )}
        </div>
      </div>

      {/* Параметры обучения */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm space-y-6">
        <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100">
          <div className="p-2.5 bg-violet-50 text-violet-600 rounded-xl">
            <Cpu className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-base">Параметры обучения</h3>
            <p className="text-xs text-slate-500 mt-1">Базовая модель и гиперпараметры spaCy NER.</p>
          </div>
        </div>

        {/* Базовая модель */}
        <div className="space-y-2">
          <span className="text-xs font-semibold text-slate-700">Базовая языковая модель</span>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {BASE_MODELS.map(m => {
              const installed = isModelInstalled(m.value);
              return (
                <button
                  key={m.value}
                  onClick={() => setBaseModel(m.value)}
                  disabled={isTraining}
                  className={`p-3 text-left rounded-xl border transition-all ${
                    baseModel === m.value
                      ? "bg-violet-50/50 border-violet-500 ring-2 ring-violet-500/10"
                      : "bg-white border-slate-200 hover:border-slate-300"
                  }`}
                >
                  <div className="flex items-center justify-between gap-1">
                    <span className="font-bold text-xs text-slate-900">{m.title}</span>
                    {!installed && (
                      <span className="text-[8px] font-bold uppercase text-amber-600 bg-amber-50 border border-amber-200 rounded px-1 py-0.5">
                        не загружена
                      </span>
                    )}
                  </div>
                  <div className="text-[10px] text-slate-500 mt-1">{m.desc}</div>
                </button>
              );
            })}
          </div>

          {!selectedInstalled && (
            <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-[11px] text-amber-700 leading-relaxed">
              Модель <b>{baseModel}</b> не загружена на сервере. Чтобы её использовать,
              скачайте её на бэкенде:
              <code className="block mt-1 font-mono text-[10px] bg-white/70 rounded px-2 py-1">
                python -m spacy download {baseModel}
              </code>
              или пересоберите Docker-образ с этой моделью. Либо выберите доступную.
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-slate-700 font-semibold">Количество эпох</span>
              <span className="text-violet-600 font-mono font-bold">{epochs}</span>
            </div>
            <input
              type="range" min="1" max="40" step="1"
              value={epochs}
              disabled={isTraining}
              onChange={(e) => setEpochs(parseInt(e.target.value))}
              className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-violet-600"
            />
            <span className="text-[10px] text-slate-400 block">Сколько проходов по датасету сделать</span>
          </div>

          <div className="space-y-1.5">
            <div className="flex justify-between text-xs">
              <span className="text-slate-700 font-semibold">Dropout</span>
              <span className="text-violet-600 font-mono font-bold">{dropout.toFixed(2)}</span>
            </div>
            <input
              type="range" min="0.1" max="0.5" step="0.05"
              value={dropout}
              disabled={isTraining}
              onChange={(e) => setDropout(parseFloat(e.target.value))}
              className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-violet-600"
            />
            <span className="text-[10px] text-slate-400 block">Регуляризация против переобучения</span>
          </div>
        </div>
      </div>

      {/* Запуск и прогресс: контент раскрывается над кнопкой, кнопка — внизу */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 space-y-4 shadow-sm">
        {status && (
          <div className="space-y-3">
            <div className="flex justify-between text-xs font-semibold text-slate-600">
              <span>{STATUS_LABEL[status.status] ?? status.status}</span>
              <span className="font-mono text-violet-600">{progress}%</span>
            </div>
            <div className="w-full h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-violet-500 to-blue-500 transition-all duration-500"
                style={{ width: `${progress}%` }}
              />
            </div>

            {metrics && metrics.ents_f !== null && (
              <div className="grid grid-cols-3 gap-3 pt-2">
                {[
                  { label: "F-score", value: metrics.ents_f },
                  { label: "Precision", value: metrics.ents_p },
                  { label: "Recall", value: metrics.ents_r }
                ].map(m => (
                  <div key={m.label} className="bg-slate-50 rounded-xl p-3 text-center">
                    <div className="text-[10px] text-slate-400 font-semibold uppercase">{m.label}</div>
                    <div className="text-sm font-bold text-slate-800 font-mono">
                      {m.value !== null && m.value !== undefined ? (m.value * 100).toFixed(1) + "%" : "—"}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-600 font-semibold">
            {error}
          </div>
        )}

        {isDone && !isFailed && (
          <div className="p-5 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl text-center space-y-4">
            <div className="flex items-center justify-center gap-2 text-emerald-700">
              <Check className="w-5 h-5 bg-emerald-100 text-emerald-700 rounded-full p-0.5" />
              <span className="text-xs font-bold">Модель готова!</span>
            </div>
            <button
              onClick={handleDownload}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-sm transition-all shadow-md shadow-emerald-600/10 cursor-pointer"
            >
              <Download className="w-4 h-4" />
              <span>Скачать модель (zip)</span>
            </button>
          </div>
        )}

        <button
          onClick={handleStart}
          disabled={isTraining || !file || !selectedInstalled}
          className="w-full flex items-center justify-center gap-2 py-4 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-bold rounded-xl text-sm transition-all shadow-md shadow-violet-600/10 cursor-pointer disabled:opacity-45 disabled:cursor-not-allowed"
        >
          <Play className="w-4 h-4" />
          <span>{isTraining ? "Обучение в процессе..." : "Начать обучение"}</span>
        </button>
      </div>

    </div>
  );
}
