import React, { useState, useRef } from "react";
import { Sparkles, Send, Upload, Check } from "lucide-react";
import { parseText, ParseResult } from "../api/client";

// Палитра градиентов для подсветки меток (по индексу метки).
const PALETTE = [
  "from-violet-500/10 to-violet-500/20 text-violet-600 border-violet-500/30",
  "from-blue-500/10 to-blue-500/20 text-blue-600 border-blue-500/30",
  "from-emerald-500/10 to-emerald-500/20 text-emerald-600 border-emerald-500/30",
  "from-amber-500/10 to-amber-500/20 text-amber-600 border-amber-500/30",
  "from-rose-500/10 to-rose-500/20 text-rose-600 border-rose-500/30",
  "from-teal-500/10 to-teal-500/20 text-teal-600 border-teal-500/30",
  "from-sky-500/10 to-sky-500/20 text-sky-600 border-sky-500/30",
  "from-fuchsia-500/10 to-fuchsia-500/20 text-fuchsia-600 border-fuchsia-500/30"
];

export default function PredictionPlayground() {
  const [modelFile, setModelFile] = useState<File | null>(null);
  const [inputText, setInputText] = useState("");
  const [result, setResult] = useState<ParseResult | null>(null);
  const [isParsing, setIsParsing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) {
      setModelFile(selected);
      setResult(null);
      setError(null);
    }
  };

  const handleParse = async () => {
    if (!modelFile || !inputText.trim()) return;
    setIsParsing(true);
    setError(null);
    try {
      const parsed = await parseText(modelFile, inputText.trim());
      setResult(parsed);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Ошибка разбора");
    } finally {
      setIsParsing(false);
    }
  };

  // Цвет метки по её позиции в списке меток модели.
  const colorFor = (label: string): string => {
    const labels = result?.labels ?? [];
    const idx = labels.indexOf(label);
    return PALETTE[(idx >= 0 ? idx : 0) % PALETTE.length];
  };

  // Разбивка текста на куски с подсветкой сущностей.
  const renderHighlighted = () => {
    if (!result) return null;
    const sorted = [...result.entities].sort((a, b) => a.start - b.start);
    const blocks: { text: string; label?: string }[] = [];
    let last = 0;
    sorted.forEach(ent => {
      if (ent.start > last) blocks.push({ text: result.text.substring(last, ent.start) });
      blocks.push({ text: result.text.substring(ent.start, ent.end), label: ent.label });
      last = ent.end;
    });
    if (last < result.text.length) blocks.push({ text: result.text.substring(last) });

    return blocks.map((block, idx) =>
      block.label ? (
        <span
          key={idx}
          className={`inline-flex items-center gap-1 px-2 py-0.5 bg-gradient-to-r ${colorFor(block.label)} border rounded-lg align-middle`}
        >
          <span className="break-words">{block.text}</span>
          <span className="text-[8px] font-mono uppercase opacity-70 shrink-0">{block.label}</span>
        </span>
      ) : (
        <span key={idx} className="text-slate-600 whitespace-pre-wrap break-words">
          {block.text}
        </span>
      )
    );
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8" id="prediction-playground-container">

      {/* Загрузка модели */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 space-y-5 shadow-sm">
        <div>
          <h3 className="font-bold text-slate-900 text-base flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-violet-600" />
            Загрузите обученную модель
          </h3>
          <p className="text-xs text-slate-500 mt-1">
            Выберите zip-файл модели, скачанный на шаге «Обучение».
          </p>
        </div>

        <div
          onClick={() => fileInputRef.current?.click()}
          className="border-2 border-dashed border-slate-200 bg-slate-50/30 hover:border-violet-400 hover:bg-violet-50/30 rounded-2xl p-8 text-center cursor-pointer transition-all flex flex-col items-center gap-3"
        >
          <input type="file" ref={fileInputRef} onChange={handleFileChange} accept=".zip" className="hidden" />
          <div className="p-3.5 bg-white rounded-full border border-slate-200 shadow-sm">
            <Upload className="w-6 h-6 text-violet-600" />
          </div>
          {modelFile ? (
            <span className="text-xs font-bold text-emerald-600 flex items-center gap-1.5">
              <Check className="w-4 h-4" /> {modelFile.name}
            </span>
          ) : (
            <span className="text-xs font-bold text-slate-700">Выберите zip-файл модели</span>
          )}
        </div>
      </div>

      {/* Ввод текста */}
      <div className="bg-white border border-slate-200/80 rounded-2xl p-6 space-y-4 shadow-sm">
        <h3 className="font-bold text-slate-900 text-base">Проверьте модель на тексте</h3>
        <div className="relative">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Например: капсулы 10 шт Вольтарен 12.5мг"
            className="w-full h-36 bg-slate-50 focus:bg-white border border-slate-200 rounded-xl p-4 pr-16 text-sm text-slate-800 focus:outline-none focus:border-violet-500 focus:ring-4 focus:ring-violet-500/10 placeholder-slate-400 resize-none"
          />
          <button
            onClick={handleParse}
            disabled={isParsing || !modelFile || !inputText.trim()}
            className="absolute bottom-4 right-4 p-3.5 bg-gradient-to-r from-violet-600 to-blue-600 hover:from-violet-500 hover:to-blue-500 text-white rounded-xl transition-all shadow-md shadow-violet-600/10 disabled:opacity-40 disabled:cursor-not-allowed"
            title="Разобрать"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
        {!modelFile && (
          <p className="text-[11px] text-slate-400">Сначала загрузите модель выше.</p>
        )}
        {error && (
          <div className="p-3 bg-rose-50 border border-rose-200 rounded-xl text-xs text-rose-600 font-semibold">
            {error}
          </div>
        )}
      </div>

      {/* Результат */}
      {result && (
        <div className="bg-white border border-slate-200/80 rounded-2xl p-6 space-y-5 shadow-sm">
          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2.5">
              Текст с подсветкой сущностей:
            </span>
            <div className="flex flex-wrap items-center gap-x-1 gap-y-2 p-4 bg-slate-50/60 border border-slate-200 rounded-xl text-sm max-h-80 overflow-y-auto">
              {renderHighlighted()}
            </div>
          </div>

          <div>
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-400 block mb-2.5">
              Извлечённые поля:
            </span>
            <div className="space-y-2" id="extracted-values-list">
              {result.labels.map(label => {
                const match = result.entities.find(e => e.label === label);
                return (
                  <div key={label} className="flex items-center justify-between p-3 bg-slate-50/50 border border-slate-200/60 rounded-xl">
                    <div className="flex items-center gap-2">
                      <span className={`w-2.5 h-2.5 rounded-full bg-gradient-to-r ${colorFor(label)}`} />
                      <span className="text-[8px] font-mono text-slate-500 uppercase">{label}</span>
                    </div>
                    <div>
                      {match ? (
                        <span className="font-bold text-xs text-violet-700 bg-violet-50 px-2.5 py-1 rounded-lg">
                          {match.text}
                        </span>
                      ) : (
                        <span className="text-xs text-slate-400 italic">Не обнаружено</span>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
