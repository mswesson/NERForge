import React, { useState, useEffect, useRef } from "react";
import { PresetSchema, AugmentationConfig, EntityLabel } from "../types";
import { generateDataset, saveBlob } from "../api/client";
import {
  Sliders,
  Trash2,
  RefreshCw,
  Upload,
  Download,
  Check,
  FileSpreadsheet,
  Copy
} from "lucide-react";

interface DatasetGeneratorProps {
  presets: PresetSchema[];
  activePreset: PresetSchema;
  onPresetChange: (preset: PresetSchema) => void;
  cleanRecords: Record<string, string>[];
  onCleanRecordsChange: (records: Record<string, string>[]) => void;
  config: AugmentationConfig;
  onConfigChange: (config: AugmentationConfig) => void;
}

export default function DatasetGenerator({
  presets,
  activePreset,
  onPresetChange,
  cleanRecords,
  onCleanRecordsChange,
  config,
  onConfigChange
}: DatasetGeneratorProps) {
  const [isGenerating, setIsGenerating] = useState(false);
  const [csvRawText, setCsvRawText] = useState("");
  const [showCsvTextArea, setShowCsvTextArea] = useState(false);
  const [generationLogs, setGenerationLogs] = useState<string[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Сгенерированный бэкендом CSV (готов к скачиванию) и счётчик строк
  const [generatedBlob, setGeneratedBlob] = useState<Blob | null>(null);
  const [generatedCount, setGeneratedCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  // Динамический шаблон CSV из активных меток
  const [templateCsv, setTemplateCsv] = useState("");

  useEffect(() => {
    if (activePreset) {
      const headers = activePreset.labels.map(l => l.key).join(";");
      const rows = activePreset.defaultRecords.map(rec =>
        activePreset.labels.map(l => rec[l.key] || "").join(";")
      );
      setTemplateCsv([headers, ...rows].join("\n"));
    }
  }, [activePreset]);

  const resetGenerated = () => {
    setGeneratedBlob(null);
    setGeneratedCount(0);
    setError(null);
  };

  const parseAndApplyCsv = (text: string) => {
    const lines = text.split("\n").map(l => l.trim()).filter(Boolean);
    if (lines.length < 2) return false;

    const delimiter = lines[0].includes(";") ? ";" : (lines[0].includes("\t") ? "\t" : ",");

    const headers = lines[0].split(delimiter).map(h => h.trim().replace(/^["']|["']$/g, ""));
    if (headers.length === 0 || (headers.length === 1 && headers[0] === "")) return false;

    const PALETTE = [
      "from-violet-500/10 to-violet-500/20 text-violet-600 border-violet-500/30",
      "from-blue-500/10 to-blue-500/20 text-blue-600 border-blue-500/30",
      "from-emerald-500/10 to-emerald-500/20 text-emerald-600 border-emerald-500/30",
      "from-indigo-500/10 to-indigo-500/20 text-indigo-600 border-indigo-500/30",
      "from-rose-500/10 to-rose-500/20 text-rose-600 border-rose-500/30",
      "from-teal-500/10 to-teal-500/20 text-teal-600 border-teal-500/30",
      "from-sky-500/10 to-sky-500/20 text-sky-600 border-sky-500/30",
      "from-fuchsia-500/10 to-fuchsia-500/20 text-fuchsia-600 border-fuchsia-500/30",
      "from-orange-500/10 to-orange-500/20 text-orange-600 border-orange-500/30"
    ];

    const derivedLabels: EntityLabel[] = headers.map((header, idx) => {
      const key = header.toLowerCase().replace(/[^a-z0-9а-я\_]/g, "");
      const label = header.toUpperCase().replace(/[^A-Z0-9А-Я\_]/g, "");
      const title = header;
      const color = PALETTE[idx % PALETTE.length];
      return { key, label, color, title };
    });

    const importedRecords: Record<string, string>[] = [];

    for (let i = 1; i < lines.length; i++) {
      const parts = lines[i].split(delimiter).map(p => p.trim().replace(/^["']|["']$/g, ""));
      if (parts.length === 0 || (parts.length === 1 && parts[0] === "")) continue;

      const rec: Record<string, string> = {};
      derivedLabels.forEach((lbl, colIdx) => {
        rec[lbl.key] = parts[colIdx] || "";
      });

      if (Object.values(rec).some(v => v !== "")) {
        importedRecords.push(rec);
      }
    }

    if (importedRecords.length > 0) {
      const dynamicPreset: PresetSchema = {
        id: "dynamic_csv",
        name: "Импортированная CSV схема",
        description: "Автоматически сгенерированная схема на основе импортированных колонок.",
        labels: derivedLabels,
        defaultRecords: importedRecords
      };

      onPresetChange(dynamicPreset);
      onCleanRecordsChange(importedRecords);
      resetGenerated();
      return true;
    }
    return false;
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const text = evt.target?.result as string;
      if (text) parseAndApplyCsv(text);
    };
    reader.readAsText(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => setIsDragging(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (evt) => {
      const text = evt.target?.result as string;
      if (text) parseAndApplyCsv(text);
    };
    reader.readAsText(file);
  };

  const handlePasteSubmit = () => {
    if (parseAndApplyCsv(csvRawText)) {
      setShowCsvTextArea(false);
      setCsvRawText("");
    }
  };

  const handleLoadDemo = () => {
    onCleanRecordsChange(activePreset.defaultRecords);
    resetGenerated();
  };

  const handleClearRecords = () => {
    onCleanRecordsChange([]);
    resetGenerated();
  };

  // Собирает эталонный CSV (колонки = метки) из текущих записей для отправки на бэкенд
  const buildReferenceCsv = (): File => {
    const escape = (v: string) => (/[",\n]/.test(v) ? `"${v.replace(/"/g, '""')}"` : v);
    const headers = activePreset.labels.map(l => l.title);
    const lines = [headers.map(escape).join(",")];
    cleanRecords.forEach(rec => {
      lines.push(activePreset.labels.map(l => escape(rec[l.key] || "")).join(","));
    });
    return new File([lines.join("\n")], "reference.csv", { type: "text/csv" });
  };

  const handleRunGeneration = async () => {
    setIsGenerating(true);
    resetGenerated();
    setGenerationLogs([
      "⚡ Отправка эталонных данных на сервер...",
      `📊 Эталонных записей: ${cleanRecords.length}.`,
      `🔄 Вариаций на строку: ${config.variationsPerRow} → ~${cleanRecords.length * config.variationsPerRow} строк.`
    ]);

    try {
      const referenceCsv = buildReferenceCsv();
      const blob = await generateDataset(referenceCsv, {
        variationsPerRow: config.variationsPerRow,
        noiseRatio: config.noiseRatio,
        typoRatio: config.typoRatio,
        removeWhitespaces: config.removeWhitespaces,
        truncateWords: config.truncateWords,
        shuffleOrder: config.shuffleOrder,
        lowercase: config.lowercase
      });

      // Считаем строки в полученном CSV (без заголовка)
      const csvText = await blob.text();
      const rowCount = csvText.split("\n").filter(Boolean).length - 1;

      setGeneratedBlob(blob);
      setGeneratedCount(Math.max(rowCount, 0));
      setGenerationLogs(prev => [...prev, `✅ Готово! Сгенерировано строк: ${Math.max(rowCount, 0)}.`]);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Неизвестная ошибка";
      setError(message);
      setGenerationLogs(prev => [...prev, `❌ Ошибка генерации: ${message}`]);
    } finally {
      setIsGenerating(false);
    }
  };

  const handleDownloadCsv = () => {
    if (generatedBlob) saveBlob(generatedBlob, "nerforge_dataset.csv");
  };

  const copyTemplateToClipboard = () => navigator.clipboard.writeText(templateCsv);

  return (
    <div className="max-w-4xl mx-auto space-y-8" id="dataset-studio-container">

      {/* Выбор схемы */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm space-y-4" id="preset-selector-card">
        <div>
          <h3 className="font-bold text-slate-900 text-lg">Схема набора данных</h3>
          <p className="text-xs text-slate-500 mt-1">
            Выберите готовую отрасль или импортируйте свой CSV-файл (только колонки-эталоны, без id товара).
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
          {presets.map((p) => (
            <button
              key={p.id}
              onClick={() => {
                onPresetChange(p);
                onCleanRecordsChange(p.defaultRecords);
                resetGenerated();
              }}
              className={`p-4 text-left rounded-xl border transition-all duration-300 ${
                activePreset.id === p.id
                  ? "bg-violet-50/50 border-violet-500 ring-2 ring-violet-500/10"
                  : "bg-white border-slate-200 hover:border-slate-300 hover:bg-slate-50/30"
              }`}
            >
              <div className="font-bold text-xs text-slate-900">{p.name}</div>
              <div className="text-[10px] text-slate-500 mt-1.5 leading-relaxed">{p.description}</div>
            </button>
          ))}
        </div>
      </div>

      {/* Импорт CSV */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 space-y-6 shadow-sm" id="csv-import-card">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-slate-100 pb-4">
          <div>
            <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
              <FileSpreadsheet className="w-5 h-5 text-violet-600" />
              Импорт эталонных данных (CSV)
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Загрузите CSV-таблицу. Колонки автоматически распознаются как сущности.
            </p>
          </div>

          {cleanRecords.length > 0 && (
            <button
              onClick={handleClearRecords}
              className="flex items-center gap-1.5 px-3 py-2 bg-rose-50 hover:bg-rose-100/70 text-rose-600 rounded-xl text-xs font-semibold transition-all"
            >
              <Trash2 className="w-3.5 h-3.5" /> Сбросить данные
            </button>
          )}
        </div>

        {/* Зона drag-and-drop */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all duration-300 flex flex-col items-center justify-center gap-3.5 ${
            isDragging
              ? "border-violet-500 bg-violet-50/40"
              : "border-slate-200 bg-slate-50/30 hover:border-slate-350 hover:bg-slate-50/70"
          }`}
          id="csv-drag-zone"
        >
          <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".csv" className="hidden" />
          <div className="p-3.5 bg-white rounded-full border border-slate-200 text-slate-400 shadow-sm">
            <Upload className="w-6 h-6 text-violet-600" />
          </div>
          <div>
            <span className="text-xs font-bold text-slate-700 block">
              Выберите CSV-файл или перетащите его сюда
            </span>
            <span className="text-[10px] text-slate-500 block mt-1.5 leading-relaxed max-w-md mx-auto">
              Колонки определят типы сущностей. Разделители: точка с запятой (;) или запятая (,)
            </span>
          </div>
        </div>

        {/* Демо и ручной ввод */}
        <div className="bg-slate-50/55 rounded-2xl border border-slate-200/60 p-5">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
            <div className="space-y-1">
              <span className="text-xs font-bold text-slate-800 block">Или используйте демо-шаблон</span>
              <span className="text-[10px] text-slate-500 block">
                Загрузите готовые демо-записи или введите тестовый CSV вручную.
              </span>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleLoadDemo}
                className="px-3.5 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl text-xs font-semibold transition-all shadow-sm"
              >
                Загрузить демо
              </button>
              <button
                onClick={() => setShowCsvTextArea(!showCsvTextArea)}
                className="px-3.5 py-2 bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 rounded-xl text-xs font-semibold transition-all shadow-sm"
              >
                {showCsvTextArea ? "Скрыть ручной ввод" : "Ввести текст вручную"}
              </button>
            </div>
          </div>

          {showCsvTextArea && (
            <div className="mt-4 pt-4 border-t border-slate-200/60 space-y-3.5">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-mono text-slate-500">Пример структуры колонок:</span>
                <button
                  onClick={copyTemplateToClipboard}
                  className="flex items-center gap-1 text-[10px] text-slate-500 hover:text-violet-600 transition"
                  title="Скопировать шаблон"
                >
                  <Copy className="w-3.5 h-3.5" /> Копировать шаблон
                </button>
              </div>
              <pre className="p-3 bg-white border border-slate-200 rounded-xl font-mono text-[10px] text-slate-600 overflow-x-auto leading-relaxed">
                {templateCsv}
              </pre>
              <textarea
                value={csvRawText}
                onChange={(e) => setCsvRawText(e.target.value)}
                placeholder="Вставьте CSV-строки сюда..."
                className="w-full h-32 bg-white border border-slate-200 rounded-xl p-3 font-mono text-xs text-slate-800 focus:outline-none focus:border-violet-500 focus:ring-4 focus:ring-violet-500/10 placeholder-slate-400"
              />
              <div className="flex justify-end">
                <button
                  onClick={handlePasteSubmit}
                  disabled={!csvRawText.trim()}
                  className="px-4 py-2 bg-violet-600 text-white font-bold rounded-xl text-xs hover:bg-violet-500 transition-all disabled:opacity-40 shadow-md shadow-violet-600/10"
                >
                  Импортировать текст
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Превью распознанных колонок */}
        {cleanRecords.length > 0 && (
          <div className="space-y-4 pt-2">
            <div>
              <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2.5">
                Распознанные сущности (колонки):
              </span>
              <div className="flex flex-wrap gap-2 text-slate-100">
                {activePreset.labels.map(lbl => (
                  <span
                    key={lbl.key}
                    className={`px-3 py-1.5 bg-gradient-to-r ${lbl.color} border rounded-lg text-xs font-bold leading-none`}
                  >
                    {lbl.title}
                  </span>
                ))}
              </div>
            </div>

            <div className="flex justify-between items-center">
              <div className="flex items-center gap-2">
                <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span className="text-xs text-slate-600 font-bold">
                  Считано: <span className="text-emerald-600">{cleanRecords.length} записей</span>
                </span>
              </div>
            </div>

            <div className="border border-slate-200/80 bg-white rounded-xl overflow-hidden shadow-sm">
              <table className="w-full text-left text-[11px] text-slate-600">
                <thead className="bg-slate-50 text-slate-500 font-mono border-b border-slate-200/80">
                  <tr>
                    <th className="p-3 w-12 text-center font-bold">#</th>
                    {activePreset.labels.map(l => (
                      <th key={l.key} className="p-3 py-2.5 font-bold uppercase tracking-wider text-[10px]">{l.title}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {cleanRecords.slice(0, 5).map((row, idx) => (
                    <tr key={idx} className="hover:bg-slate-50/50">
                      <td className="p-3 text-center text-slate-400 font-mono">{idx + 1}</td>
                      {activePreset.labels.map(lbl => (
                        <td key={lbl.key} className="p-3 py-2.5 text-slate-700 truncate max-w-[150px]">
                          {row[lbl.key] || "—"}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
              {cleanRecords.length > 5 && (
                <div className="p-2.5 bg-slate-50 border-t border-slate-100 text-center text-[10px] text-slate-400 font-mono">
                  Показано 5 из {cleanRecords.length} записей
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Параметры генерации */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 shadow-sm space-y-6" id="noise-parameters-card">
        <div className="flex items-center gap-2.5 pb-4 border-b border-slate-100">
          <div className="p-2.5 bg-violet-50 text-violet-600 rounded-xl">
            <Sliders className="w-5 h-5" />
          </div>
          <div>
            <h3 className="font-bold text-slate-900 text-base">Генератор шума и аугментации</h3>
            <p className="text-xs text-slate-500 mt-1">
              Настройте искусственные отклонения и опечатки для устойчивости модели к грязному вводу.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-5">
            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-700 font-semibold">Вариаций на строку</span>
                <span className="text-violet-600 font-mono font-bold">{config.variationsPerRow}</span>
              </div>
              <input
                type="range" min="1" max="50" step="1"
                value={config.variationsPerRow}
                onChange={(e) => onConfigChange({ ...config, variationsPerRow: parseInt(e.target.value) })}
                className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-violet-600"
              />
              <span className="text-[10px] text-slate-400 block">
                Сколько вариаций сделать на каждую исходную строку (итого ≈ строк × вариаций)
              </span>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-700 font-semibold">Доля зашумлённых строк</span>
                <span className="text-violet-600 font-mono font-bold">{Math.round(config.noiseRatio * 100)}%</span>
              </div>
              <input
                type="range" min="0" max="1" step="0.05"
                value={config.noiseRatio}
                onChange={(e) => onConfigChange({ ...config, noiseRatio: parseFloat(e.target.value) })}
                className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-violet-600"
              />
              <span className="text-[10px] text-slate-400 block">Доля записей с аббревиатурами, сокращениями и шумом</span>
            </div>

            <div className="space-y-1.5">
              <div className="flex justify-between text-xs">
                <span className="text-slate-700 font-semibold">Вероятность опечаток</span>
                <span className="text-violet-600 font-mono font-bold">{Math.round(config.typoRatio * 100)}%</span>
              </div>
              <input
                type="range" min="0" max="1" step="0.05"
                value={config.typoRatio}
                onChange={(e) => onConfigChange({ ...config, typoRatio: parseFloat(e.target.value) })}
                className="w-full h-1.5 bg-slate-100 rounded-lg appearance-none cursor-pointer accent-violet-600"
              />
              <span className="text-[10px] text-slate-400 block">Внесение опечаток в зашумлённые значения</span>
            </div>
          </div>

          <div className="bg-slate-50/50 p-5 border border-slate-200 rounded-2xl space-y-4">
            <span className="text-xs font-bold text-slate-500 block">Алгоритмы аугментации:</span>

            <label className="flex items-start gap-3 cursor-pointer text-xs text-slate-600 select-none">
              <input
                type="checkbox"
                checked={config.removeWhitespaces}
                onChange={(e) => onConfigChange({ ...config, removeWhitespaces: e.target.checked })}
                className="mt-0.5 rounded border-slate-300 text-violet-600 focus:ring-violet-500/20 bg-white w-4 h-4 accent-violet-600"
              />
              <div>
                <span className="font-bold text-slate-800 block">Сжимать пробелы в числительных</span>
                <span className="text-[10px] text-slate-400">Например, &quot;25мг&quot; вместо &quot;25 мг&quot;</span>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer text-xs text-slate-600 select-none">
              <input
                type="checkbox"
                checked={config.truncateWords}
                onChange={(e) => onConfigChange({ ...config, truncateWords: e.target.checked })}
                className="mt-0.5 rounded border-slate-300 text-violet-600 focus:ring-violet-500/20 bg-white w-4 h-4 accent-violet-600"
              />
              <div>
                <span className="font-bold text-slate-800 block">Сокращать длинные слова</span>
                <span className="text-[10px] text-slate-400">Например, &quot;таблетки&quot; → &quot;таб&quot;</span>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer text-xs text-slate-600 select-none">
              <input
                type="checkbox"
                checked={config.lowercase}
                onChange={(e) => onConfigChange({ ...config, lowercase: e.target.checked })}
                className="mt-0.5 rounded border-slate-300 text-violet-600 focus:ring-violet-500/20 bg-white w-4 h-4 accent-violet-600"
              />
              <div>
                <span className="font-bold text-slate-800 block">Привести всё к нижнему регистру</span>
                <span className="text-[10px] text-slate-400">Обучение только на нижнем регистре (&quot;Супрастин&quot; → &quot;супрастин&quot;)</span>
              </div>
            </label>

            <label className="flex items-start gap-3 cursor-pointer text-xs text-slate-600 select-none">
              <input
                type="checkbox"
                checked={config.shuffleOrder}
                onChange={(e) => onConfigChange({ ...config, shuffleOrder: e.target.checked })}
                className="mt-0.5 rounded border-slate-300 text-violet-600 focus:ring-violet-500/20 bg-white w-4 h-4 accent-violet-600"
              />
              <div>
                <span className="font-bold text-slate-800 block">Перемешивать порядок полей</span>
                <span className="text-[10px] text-slate-400">Имитирует свободный порядок реквизитов; порядок фиксируется в датасете</span>
              </div>
            </label>
          </div>
        </div>
      </div>

      {/* Запуск генерации: контент раскрывается над кнопкой, кнопка — внизу */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 space-y-4 shadow-sm" id="generator-action-box">
        {generationLogs.length > 0 && (
          <div className="bg-slate-900 border border-slate-800 rounded-xl p-4 font-mono text-[11px] text-slate-300 space-y-1.5 max-h-36 overflow-y-auto shadow-inner">
            {generationLogs.map((log, lIdx) => (
              <div key={lIdx} className="text-slate-300 flex items-start gap-1">
                <span className="text-violet-400">›</span>
                <span>{log}</span>
              </div>
            ))}
          </div>
        )}

        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-600 font-semibold">
            {error}
          </div>
        )}

        {generatedBlob && !isGenerating && (
          <div className="p-5 bg-emerald-500/5 border border-emerald-500/10 rounded-2xl text-center space-y-4 shadow-sm" id="download-trigger-container">
            <div className="flex items-center justify-center gap-2 text-emerald-700">
              <Check className="w-5 h-5 bg-emerald-100 text-emerald-700 rounded-full p-0.5" />
              <span className="text-xs font-bold">
                Сгенерировано {generatedCount.toLocaleString()} строк!
              </span>
            </div>

            <button
              onClick={handleDownloadCsv}
              className="w-full sm:w-auto inline-flex items-center justify-center gap-2.5 px-6 py-3 bg-emerald-600 hover:bg-emerald-500 text-white font-bold rounded-xl text-sm transition-all shadow-md shadow-emerald-600/10 cursor-pointer"
              id="download-csv-btn"
            >
              <Download className="w-4 h-4" />
              <span>Скачать готовый датасет (CSV)</span>
            </button>
          </div>
        )}

        <button
          onClick={handleRunGeneration}
          disabled={isGenerating || cleanRecords.length === 0}
          className="w-full flex items-center justify-center gap-2 py-4 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white font-bold rounded-xl text-sm transition-all shadow-md shadow-violet-600/10 cursor-pointer disabled:opacity-45 disabled:cursor-not-allowed"
          id="run-generation-btn"
        >
          <RefreshCw className={`w-4 h-4 ${isGenerating ? "animate-spin" : ""}`} />
          <span>{isGenerating ? "Генерация на сервере..." : "Сгенерировать датасет"}</span>
        </button>
      </div>

    </div>
  );
}
