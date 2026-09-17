'use client';

import React, { useState } from 'react';
import {
  Sparkles,
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertCircle,
  Clock,
  Layers,
  Layout,
  ExternalLink,
  ChevronRight,
  BookOpen,
} from 'lucide-react';
import { runPipeline, PipelineRunResponse, STORAGE_BASE } from '../../lib/api';

const SAMPLES = {
  os: {
    title: 'Operating Systems',
    desc: 'Process scheduling, virtual memory, and kernel abstractions',
    text: `An Operating System is system software that manages computer hardware and software resources and provides common services for computer programs. The fundamental purpose of an operating system is to execute user programs and make solving user problems easier. The core components of an operating system include process management, memory management, file system management, and I/O device management. In process management, the CPU scheduler allocates CPU time slices to active processes. Memory management tracks every byte in main memory and allocates addresses dynamically. Virtual memory allows processes to execute beyond physical RAM limits using paging and swapping. Operating systems also provide a protective layer between user space and kernel space through system calls and privileged CPU instructions.`,
  },
  dbms: {
    title: 'Relational Databases',
    desc: 'SQL, normalization, ACID properties vs NoSQL',
    text: `A Relational Database Management System organizes data into one or more tables consisting of columns and rows. Each table possesses a primary key that uniquely identifies each record. Structured Query Language, or SQL, is the standard language for storing, manipulating, and retrieving data. In contrast to NoSQL systems, relational databases enforce strict ACID properties: Atomicity, Consistency, Isolation, and Durability, ensuring transaction reliability. Normalization is the systematic process of organizing tables to eliminate data redundancy and undesirable insertion anomalies.`,
  },
  networks: {
    title: 'TCP Handshake',
    desc: 'Three-way handshake, SYN, SYN-ACK, ACK sequencing',
    text: `The Transmission Control Protocol utilizes a deterministic three-way handshake mechanism to establish a reliable connection between client and server. In step one, the client sends a SYN packet with an initial sequence number. In step two, the server receives the SYN and responds with a SYN-ACK packet, acknowledging the client's sequence number and providing its own sequence number. In step three, the client replies with an ACK packet confirming receipt. Once this exchange completes, a reliable full-duplex TCP socket is opened and application data transmission begins.`,
  },
  ml: {
    title: 'Machine Learning Metrics',
    desc: 'Precision, Recall, and F1 harmonic mean formulas',
    text: `In machine learning classification, accuracy is often misleading for imbalanced datasets. Precision and Recall provide a balanced evaluation. Precision is defined by the formula: Precision = TP / (TP + FP), measuring the fraction of positive predictions that were true. Recall is defined by the formula: Recall = TP / (TP + FN), measuring the fraction of actual positives that were found. The F1 Score harmonic mean combines both metrics: F1 = 2 * (Precision * Recall) / (Precision + Recall).`,
  },
};

const STAGES = [
  { id: 'created', label: 'Initialized' },
  { id: 'transcribing', label: 'Transcribing' },
  { id: 'analyzing', label: 'Extracting Concepts' },
  { id: 'planning', label: 'Visual Planning' },
  { id: 'rendering', label: 'Deterministic Rendering' },
  { id: 'completed', label: 'Complete' },
];

export default function CreatePage() {
  const [inputMode, setInputMode] = useState<'sample' | 'paste' | 'upload'>('sample');
  const [selectedSample, setSelectedSample] = useState<keyof typeof SAMPLES>('os');
  const [customText, setCustomText] = useState('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [theme, setTheme] = useState('clean_handwritten');
  const [learningLevel, setLearningLevel] = useState('INTERMEDIATE');

  const [loading, setLoading] = useState(false);
  const [currentStage, setCurrentStage] = useState<string>('created');
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<PipelineRunResponse | null>(null);
  const [activeTab, setActiveTab] = useState<'preview' | 'concepts' | 'plan' | 'transcript'>('preview');

  const handleStartPipeline = async () => {
    setLoading(true);
    setError(null);
    setCurrentStage('transcribing');

    try {
      let rawText = '';
      if (inputMode === 'sample') {
        rawText = SAMPLES[selectedSample].text;
      } else if (inputMode === 'paste') {
        rawText = customText.trim();
        if (!rawText) throw new Error('Please enter transcript text.');
      }

      const response = await runPipeline({
        rawText: inputMode === 'upload' ? undefined : rawText,
        file: inputMode === 'upload' ? selectedFile : undefined,
        theme,
        learningLevel,
        mockMode: true,
      });

      if (response.status === 'FAILED') {
        throw new Error(response.error || 'Pipeline failed during processing.');
      }

      setResult(response);
      setCurrentStage(response.current_stage || 'completed');
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Pipeline execution encountered an error.';
      setError(message);
      setCurrentStage('failed');
    } finally {
      setLoading(false);
    }
  };

  const getStageIndex = (stage: string) => {
    return STAGES.findIndex((s) => s.id === stage);
  };

  return (
    <div className="min-h-screen bg-[#0b0f19] text-slate-100 pb-20">
      {/* Top Navigation / Brand */}
      <header className="border-b border-slate-800 bg-[#0f172a]/70 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center shadow-lg shadow-indigo-500/30">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-white flex items-center gap-2">
                VisualNote AI
                <span className="text-[11px] font-semibold uppercase px-2 py-0.5 rounded-full bg-indigo-500/20 text-indigo-400 border border-indigo-500/30">
                  Phase 1 Tracer Bullet
                </span>
              </span>
            </div>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className="inline-flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500"></span>
              Deterministic AI Engine
            </span>
          </div>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 pt-8">
        {/* Intro */}
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-white tracking-tight">
            Turn Educational Content into Visual Notes
          </h1>
          <p className="text-slate-400 mt-2 max-w-2xl text-sm leading-relaxed">
            Phase 1 Core AI Pipeline test bench: extract structured concepts, calculate deterministic importance,
            and generate verified visual note sheets without hallucinated text.
          </p>
        </div>

        {/* Pipeline Input Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Input Settings */}
          <div className="lg:col-span-5 space-y-6">
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-6 shadow-xl space-y-6">
              <h2 className="text-base font-semibold text-white flex items-center gap-2">
                <Sparkles className="w-4 h-4 text-indigo-400" />
                Select Ingestion Source
              </h2>

              {/* Mode Tabs */}
              <div className="flex rounded-lg bg-slate-800/80 p-1 border border-slate-700/60">
                <button
                  type="button"
                  onClick={() => setInputMode('sample')}
                  className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
                    inputMode === 'sample'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Presets
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode('paste')}
                  className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
                    inputMode === 'paste'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Paste Text
                </button>
                <button
                  type="button"
                  onClick={() => setInputMode('upload')}
                  className={`flex-1 py-1.5 text-xs font-medium rounded-md transition-all ${
                    inputMode === 'upload'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-400 hover:text-slate-200'
                  }`}
                >
                  Upload File
                </button>
              </div>

              {/* Mode 1: Presets */}
              {inputMode === 'sample' && (
                <div className="space-y-2.5">
                  {(Object.keys(SAMPLES) as Array<keyof typeof SAMPLES>).map((key) => (
                    <button
                      key={key}
                      type="button"
                      onClick={() => setSelectedSample(key)}
                      className={`w-full text-left p-3 rounded-lg border text-sm transition-all ${
                        selectedSample === key
                          ? 'border-indigo-500 bg-indigo-950/30 text-white'
                          : 'border-slate-800 bg-slate-800/30 text-slate-300 hover:border-slate-700'
                      }`}
                    >
                      <div className="font-medium text-white">{SAMPLES[key].title}</div>
                      <div className="text-xs text-slate-400 mt-0.5">{SAMPLES[key].desc}</div>
                    </button>
                  ))}
                </div>
              )}

              {/* Mode 2: Paste */}
              {inputMode === 'paste' && (
                <div>
                  <textarea
                    rows={7}
                    value={customText}
                    onChange={(e) => setCustomText(e.target.value)}
                    placeholder="Paste an educational lecture transcript, notes, or concept explanations here..."
                    className="w-full bg-slate-950 border border-slate-800 rounded-lg p-3 text-sm text-slate-200 focus:outline-none focus:border-indigo-500"
                  />
                  <div className="text-right text-xs text-slate-500 mt-1">
                    {customText.trim().split(/\s+/).filter(Boolean).length} words
                  </div>
                </div>
              )}

              {/* Mode 3: Upload */}
              {inputMode === 'upload' && (
                <div className="border-2 border-dashed border-slate-700 rounded-lg p-6 text-center hover:border-indigo-500 transition-colors">
                  <UploadCloud className="w-8 h-8 text-indigo-400 mx-auto mb-2" />
                  <p className="text-sm font-medium text-slate-300">
                    {selectedFile ? selectedFile.name : 'Choose audio or video file'}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">
                    Supported: .mp4, .mov, .webm, .mp3, .wav, .m4a (Max 100MB)
                  </p>
                  <input
                    type="file"
                    accept=".mp4,.mov,.webm,.mp3,.wav,.m4a"
                    onChange={(e) => {
                      if (e.target.files && e.target.files[0]) {
                        setSelectedFile(e.target.files[0]);
                      }
                    }}
                    className="mt-3 block w-full text-xs text-slate-400 file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-indigo-600 file:text-white hover:file:bg-indigo-700 cursor-pointer"
                  />
                </div>
              )}

              {/* Theme & Style Config */}
              <div className="grid grid-cols-2 gap-3 pt-2 border-t border-slate-800">
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5">
                    Visual Style
                  </label>
                  <select
                    value={theme}
                    onChange={(e) => setTheme(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md py-1.5 px-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="clean_handwritten">Clean Handwritten</option>
                    <option value="notebook">Notebook Paper</option>
                    <option value="chalkboard">Chalkboard Dark</option>
                    <option value="minimal">Clean Minimal</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-semibold text-slate-400 mb-1.5">
                    Learning Level
                  </label>
                  <select
                    value={learningLevel}
                    onChange={(e) => setLearningLevel(e.target.value)}
                    className="w-full bg-slate-950 border border-slate-800 rounded-md py-1.5 px-2.5 text-xs text-slate-200 focus:outline-none focus:border-indigo-500"
                  >
                    <option value="BEGINNER">Beginner</option>
                    <option value="INTERMEDIATE">Intermediate</option>
                    <option value="ADVANCED">Advanced</option>
                    <option value="EXAM">Exam Revision</option>
                  </select>
                </div>
              </div>

              {/* Action Button */}
              <button
                type="button"
                onClick={handleStartPipeline}
                disabled={loading}
                className="w-full py-3 px-4 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-semibold text-sm shadow-lg shadow-indigo-600/30 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                    Processing Pipeline...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4" />
                    Execute Tracer Bullet Pipeline
                  </>
                )}
              </button>
            </div>
          </div>

          {/* Right Column: Execution Status & Output View */}
          <div className="lg:col-span-7 space-y-6">
            {/* Live Stepper */}
            <div className="bg-slate-900/80 border border-slate-800 rounded-xl p-5 shadow-xl">
              <h3 className="text-xs font-semibold text-slate-400 uppercase tracking-wider mb-3">
                Pipeline Lifecycle
              </h3>
              <div className="grid grid-cols-3 sm:grid-cols-6 gap-2">
                {STAGES.map((s, idx) => {
                  const currIdx = getStageIndex(currentStage);
                  const isDone = currIdx >= idx && currentStage !== 'failed';
                  const isCurrent = currentStage === s.id;

                  return (
                    <div
                      key={s.id}
                      className={`text-center p-2 rounded-lg border text-xs transition-all ${
                        isCurrent
                          ? 'border-indigo-500 bg-indigo-950/40 text-indigo-300 font-semibold shadow-sm'
                          : isDone
                          ? 'border-emerald-500/40 bg-emerald-950/20 text-emerald-400'
                          : 'border-slate-800/80 bg-slate-950/40 text-slate-500'
                      }`}
                    >
                      <div className="truncate">{s.label}</div>
                    </div>
                  );
                })}
              </div>
            </div>

            {/* Error Message */}
            {error && (
              <div className="p-4 rounded-xl bg-red-950/40 border border-red-800 text-red-300 text-sm flex items-start gap-3">
                <AlertCircle className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" />
                <div>
                  <strong className="font-semibold block">Processing Failed</strong>
                  <span>{error}</span>
                </div>
              </div>
            )}

            {/* Results Viewer */}
            {result && (
              <div className="bg-slate-900/80 border border-slate-800 rounded-xl shadow-xl overflow-hidden">
                {/* Tabs */}
                <div className="flex border-b border-slate-800 bg-slate-950/50 px-4 pt-2 gap-2">
                  <button
                    type="button"
                    onClick={() => setActiveTab('preview')}
                    className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 flex items-center gap-1.5 ${
                      activeTab === 'preview'
                        ? 'border-indigo-500 text-white bg-slate-900'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Layout className="w-3.5 h-3.5" />
                    Visual Note Preview
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('concepts')}
                    className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 flex items-center gap-1.5 ${
                      activeTab === 'concepts'
                        ? 'border-indigo-500 text-white bg-slate-900'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Layers className="w-3.5 h-3.5" />
                    Concepts ({result.concepts?.length || 0})
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('plan')}
                    className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 flex items-center gap-1.5 ${
                      activeTab === 'plan'
                        ? 'border-indigo-500 text-white bg-slate-900'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Visual Plan
                  </button>
                  <button
                    type="button"
                    onClick={() => setActiveTab('transcript')}
                    className={`px-3 py-2 text-xs font-semibold rounded-t-lg transition-colors border-b-2 flex items-center gap-1.5 ${
                      activeTab === 'transcript'
                        ? 'border-indigo-500 text-white bg-slate-900'
                        : 'border-transparent text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    <Clock className="w-3.5 h-3.5" />
                    Transcript Segments
                  </button>
                </div>

                <div className="p-6">
                  {/* Tab 1: Visual Note Preview */}
                  {activeTab === 'preview' && result.render_result && (
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-semibold text-white text-base">
                            {result.render_result.page_title}
                          </h4>
                          <p className="text-xs text-slate-400">
                            Deterministic HTML/CSS/SVG render captured to PNG
                          </p>
                        </div>
                        {result.render_result.html_url && (
                          <a
                            href={`${STORAGE_BASE}${result.render_result.html_url}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-xs font-semibold text-indigo-400 hover:text-indigo-300 bg-indigo-950/40 border border-indigo-800/60 px-2.5 py-1.5 rounded-md"
                          >
                            Open Clean HTML <ExternalLink className="w-3.5 h-3.5" />
                          </a>
                        )}
                      </div>

                      {/* Embed rendered output */}
                      <div className="rounded-lg overflow-hidden border border-slate-700 bg-white shadow-2xl">
                        {result.render_result.image_url ? (
                          <img
                            src={`${STORAGE_BASE}${result.render_result.image_url}`}
                            alt="Visual Note Page"
                            className="w-full h-auto object-contain max-h-[600px]"
                          />
                        ) : result.render_result.html_url ? (
                          <iframe
                            src={`${STORAGE_BASE}${result.render_result.html_url}`}
                            title="Visual Note"
                            className="w-full h-[550px] border-0"
                          />
                        ) : (
                          <div
                            className="p-4"
                            dangerouslySetInnerHTML={{
                              __html: result.render_result.svg_content || '',
                            }}
                          />
                        )}
                      </div>
                    </div>
                  )}

                  {/* Tab 2: Extracted Concepts */}
                  {activeTab === 'concepts' && (
                    <div className="space-y-4">
                      {result.concepts?.map((c, i) => (
                        <div
                          key={c.id || i}
                          className="p-4 rounded-lg bg-slate-950 border border-slate-800 space-y-2"
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center gap-2">
                              <span className="text-xs uppercase font-bold px-2 py-0.5 rounded bg-indigo-600/30 text-indigo-400 border border-indigo-500/30">
                                {c.concept_type}
                              </span>
                              <span className="font-semibold text-white">{c.title}</span>
                            </div>
                            <span className="text-xs text-slate-400">
                              Score: <strong className="text-slate-200">{c.importance_score}</strong>
                            </span>
                          </div>
                          <p className="text-sm text-slate-300">{c.explanation}</p>
                          {c.supporting_points && c.supporting_points.length > 0 && (
                            <ul className="text-xs text-slate-400 space-y-1 list-disc list-inside pt-1">
                              {c.supporting_points.map((pt, idx) => (
                                <li key={idx}>{pt}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 3: Visual Plan */}
                  {activeTab === 'plan' && result.visual_plan && (
                    <div className="space-y-3">
                      <div className="text-xs text-slate-400 mb-2">
                        Theme: <span className="text-slate-200 font-semibold">{result.visual_plan.theme}</span>
                      </div>
                      {result.visual_plan.sections.map((sec) => (
                        <div
                          key={sec.id}
                          className="p-3 rounded-lg bg-slate-950 border border-slate-800 flex items-center justify-between"
                        >
                          <div>
                            <span className="text-xs text-indigo-400 font-mono font-semibold mr-2">
                              #{sec.priority}
                            </span>
                            <span className="text-sm font-semibold text-white">{sec.title}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <span className="text-xs px-2 py-0.5 rounded bg-slate-800 text-slate-300 font-mono">
                              {sec.visual_type}
                            </span>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Tab 4: Transcript */}
                  {activeTab === 'transcript' && result.transcript && (
                    <div className="space-y-2 max-h-[450px] overflow-y-auto pr-2">
                      {result.transcript.segments?.map((seg, i) => (
                        <div
                          key={i}
                          className="p-2.5 rounded-lg bg-slate-950/60 border border-slate-800/80 flex items-start gap-3"
                        >
                          <span className="text-[11px] font-mono font-semibold text-indigo-400 bg-indigo-950/50 px-2 py-0.5 rounded border border-indigo-900 flex-shrink-0">
                            {seg.start.toFixed(1)}s – {seg.end.toFixed(1)}s
                          </span>
                          <span className="text-xs text-slate-300 leading-relaxed">{seg.text}</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
