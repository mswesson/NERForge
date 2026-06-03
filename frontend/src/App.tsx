import React, { useState, useEffect } from "react";
import { PRESETS } from "./presets";
import { PresetSchema, AugmentationConfig } from "./types";
import DatasetGenerator from "./components/DatasetGenerator";
import ModelTrainer from "./components/ModelTrainer";
import PredictionPlayground from "./components/PredictionPlayground";

export default function App() {
  // Текущий шаг / активная вкладка
  const [activeTab, setActiveTab] = useState<"constructor" | "training" | "testing">("constructor");

  // Состояния параллакса для вкладок навигации
  const [hoveredTab, setHoveredTab] = useState<string | null>(null);
  const [mouseOffset, setMouseOffset] = useState({ x: 0, y: 0 });

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>, tabId: string) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const x = e.clientX - (rect.left + rect.width / 2);
    const y = e.clientY - (rect.top + rect.height / 2);
    setMouseOffset({ x, y });
    setHoveredTab(tabId);
  };

  const handleMouseLeave = () => {
    setHoveredTab(null);
    setMouseOffset({ x: 0, y: 0 });
  };

  const getParallaxStyles = (id: string) => {
    const isHovered = hoveredTab === id;
    return {
      container: {
        transform: isHovered ? `translate3d(${mouseOffset.x * 0.05}px, ${mouseOffset.y * 0.06}px, 0)` : "none",
        transition: isHovered ? "none" : "transform 0.4s cubic-bezier(0.25, 1, 0.5, 1)"
      },
      badge: {
        transform: isHovered ? `translate3d(${mouseOffset.x * 0.16}px, ${mouseOffset.y * 0.2}px, 0)` : "none",
        transition: isHovered ? "none" : "transform 0.4s cubic-bezier(0.25, 1, 0.5, 1)"
      },
      label: {
        transform: isHovered ? `translate3d(${mouseOffset.x * 0.1}px, ${mouseOffset.y * 0.12}px, 0)` : "none",
        transition: isHovered ? "none" : "transform 0.4s cubic-bezier(0.25, 1, 0.5, 1)"
      }
    };
  };

  // Схема набора данных (для шага 1)
  const [activePreset, setActivePreset] = useState<PresetSchema>(PRESETS[0]);

  // Эталонные записи (редактируемые)
  const [cleanRecords, setCleanRecords] = useState<Record<string, string>[]>(PRESETS[0].defaultRecords);

  // Параметры аугментации (шаг 1)
  const [config, setConfig] = useState<AugmentationConfig>({
    variationsPerRow: 5,
    noiseRatio: 0.4,
    typoRatio: 0.15,
    shuffleOrder: true,
    removeWhitespaces: true,
    truncateWords: true,
    lowercase: false
  });

  // Восстановление из localStorage при монтировании
  useEffect(() => {
    try {
      const storedPresetId = localStorage.getItem("nf_active_preset_id");
      const storedRecords = localStorage.getItem("nf_clean_records");
      const storedConfig = localStorage.getItem("nf_config");

      if (storedPresetId) {
        let found = PRESETS.find(p => p.id === storedPresetId);
        if (!found && storedPresetId === "dynamic_csv") {
          const storedPresetData = localStorage.getItem("nf_active_preset_data");
          if (storedPresetData) {
            try {
              found = JSON.parse(storedPresetData);
            } catch (err) {
              console.error("Не удалось разобрать динамическую схему из кэша:", err);
            }
          }
        }
        if (found) {
          setActivePreset(found);
          if (storedRecords) {
            setCleanRecords(JSON.parse(storedRecords));
          } else {
            setCleanRecords(found.defaultRecords);
          }
        }
      }

      if (storedConfig) {
        setConfig(JSON.parse(storedConfig));
      }
    } catch (e) {
      console.warn("Не удалось разобрать кэш localStorage, ставлю значения по умолчанию:", e);
    }
  }, []);

  const handleCleanRecordsChange = (newRecords: Record<string, string>[]) => {
    setCleanRecords(newRecords);
    localStorage.setItem("nf_clean_records", JSON.stringify(newRecords));
  };

  const handleConfigChange = (newConfig: AugmentationConfig) => {
    setConfig(newConfig);
    localStorage.setItem("nf_config", JSON.stringify(newConfig));
  };

  const handlePresetSelectChange = (preset: PresetSchema) => {
    setActivePreset(preset);
    localStorage.setItem("nf_active_preset_id", preset.id);
    localStorage.setItem("nf_active_preset_data", JSON.stringify(preset));
  };

  return (
    <div className="min-h-screen bg-[#f8fafc] text-slate-800 selection:bg-indigo-500/15 selection:text-indigo-900 font-sans leading-normal antialiased relative flex flex-col justify-between" id="ner-master-layout">

      {/* Декоративные градиенты фона */}
      <div className="absolute inset-x-0 top-0 overflow-hidden pointer-events-none -z-10 h-screen max-h-screen w-full">
        <div className="absolute top-[-10rem] left-[5%] w-[45rem] h-[45rem] bg-gradient-to-tr from-indigo-200/40 to-blue-200/20 rounded-full blur-3xl animate-float-slow" />
        <div className="absolute top-[10rem] right-[5%] w-[38rem] h-[38rem] bg-gradient-to-tr from-violet-200/30 to-purple-200/30 rounded-full blur-3xl animate-float-slower" />
      </div>

      {/* ШАПКА */}
      <header className="border-b border-slate-200/40 bg-white/70 backdrop-blur-md sticky top-0 z-50 py-4 px-4 md:px-8 shadow-sm" id="dashboard-navbar">
        <div className="max-w-7xl mx-auto flex flex-col sm:flex-row justify-between items-center gap-4">

          <div className="flex items-center gap-3">
            <svg className="w-8 h-8 filter drop-shadow hover:scale-105 transition-transform duration-300 shrink-0" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" id="app-logo-svg">
              <defs>
                <linearGradient id="logo-grad" x1="0%" y1="0%" x2="100%" y2="100%">
                  <stop offset="0%" stopColor="#6366f1" />
                  <stop offset="100%" stopColor="#3b82f6" />
                </linearGradient>
              </defs>
              <rect x="2" y="2" width="20" height="20" rx="6.5" fill="url(#logo-grad)" />
              <circle cx="8" cy="8" r="2" fill="white" />
              <circle cx="16" cy="8" r="2" fill="white" />
              <circle cx="12" cy="16" r="2" fill="white" />
              <path d="M8.5 8.5 L11.5 15.5 M15.5 8.5 L12.5 15.5 M8.5 8 L15.5 8" stroke="white" strokeWidth="1.25" strokeOpacity="0.8" />
            </svg>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 font-display">
                NerForge
              </h1>
            </div>
          </div>

          {/* Навигация по шагам */}
          <nav className="flex items-center gap-8 md:gap-12" id="tabs-navigation-header">
            {([
              { id: "constructor", num: "1", label: "Конструктор" },
              { id: "training", num: "2", label: "Обучение" },
              { id: "testing", num: "3", label: "Тестирование" }
            ] as const).map(tab => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                onMouseMove={(e) => handleMouseMove(e, tab.id)}
                onMouseLeave={handleMouseLeave}
                style={getParallaxStyles(tab.id).container}
                className="relative py-1 text-sm font-semibold tracking-tight transition-all duration-300 flex items-center gap-2 cursor-pointer group"
                id={`header-tab-${tab.id}`}
              >
                <span
                  style={getParallaxStyles(tab.id).badge}
                  className={`w-5 h-5 rounded-md text-[10px] flex items-center justify-center font-bold transition-all duration-300 select-none ${
                    activeTab === tab.id ? "bg-indigo-600 text-white shadow-sm shadow-indigo-600/20" : "bg-slate-100 text-slate-500 group-hover:bg-slate-200"
                  }`}
                >
                  {tab.num}
                </span>
                <span
                  style={getParallaxStyles(tab.id).label}
                  className={`transition-colors duration-300 select-none ${
                    activeTab === tab.id ? "text-slate-900 font-bold" : "text-slate-500 group-hover:text-slate-800"
                  }`}
                >
                  {tab.label}
                </span>
                {activeTab === tab.id && (
                  <span className="absolute bottom-[-18px] left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500 to-blue-500 rounded-full animate-pulse" />
                )}
              </button>
            ))}
          </nav>

        </div>
      </header>

      {/* ОСНОВНОЙ КОНТЕЙНЕР */}
      <main className="flex-grow max-w-7xl w-full mx-auto px-4 md:px-6 py-8" id="dashboard-core-canvas">
        <section id="workflow-render-area" className="transition-all duration-300">
          {activeTab === "constructor" && (
            <DatasetGenerator
              presets={PRESETS}
              activePreset={activePreset}
              onPresetChange={handlePresetSelectChange}
              cleanRecords={cleanRecords}
              onCleanRecordsChange={handleCleanRecordsChange}
              config={config}
              onConfigChange={handleConfigChange}
            />
          )}

          {activeTab === "training" && <ModelTrainer />}

          {activeTab === "testing" && <PredictionPlayground />}
        </section>
      </main>

      {/* ПОДВАЛ */}
      <footer className="py-5 border-t border-slate-200/40 bg-white/40 text-center text-[11px] tracking-widest font-normal text-slate-400" id="global-footer">
        <div className="max-w-7xl mx-auto px-6 flex flex-col sm:flex-row justify-between items-center gap-2">
          <span>СДЕЛАНО В 2026 ГОДУ</span>
          <span>
            ПОЛЬЗОВАТЕЛЕМ{" "}
            <span className="font-bold text-slate-600 hover:text-indigo-600 transition-colors uppercase">
              @themswesson
            </span>
          </span>
        </div>
      </footer>

    </div>
  );
}
