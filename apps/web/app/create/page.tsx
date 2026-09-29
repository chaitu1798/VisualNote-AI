'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import {
  Sparkles,
  UploadCloud,
  FileText,
  Youtube,
  BookOpen,
  X,
  AlertCircle
} from 'lucide-react';
import {
  createSource,
  createAsyncJob,
  pollJobUntilDone,
  JobDetailResponse,
} from '../../lib/api';
import { GenerationProgress } from '../../components/generation/GenerationProgress';

export default function CreatePage() {
  const router = useRouter();
  const [inputMode, setInputMode] = useState<'upload' | 'paste' | 'youtube'>('upload');

  // Inputs
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [customText, setCustomText] = useState('');
  const [youtubeUrl, setYoutubeUrl] = useState('');

  // Settings
  const [theme, setTheme] = useState('clean_handwritten');

  // State
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeJobId, setActiveJobId] = useState<string | null>(null);

  // Progress State
  const [currentStage, setCurrentStage] = useState<string>('created');
  const [currentProgress, setCurrentProgress] = useState<number>(0);

  // Drag state
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Poll controller to prevent duplicate polling or memory leaks
  const isPollingRef = useRef<boolean>(false);
  const cancelPollingRef = useRef<boolean>(false);

  useEffect(() => {
    return () => {
      cancelPollingRef.current = true;
    };
  }, []);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };
  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };
  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.size > 100 * 1024 * 1024) {
        setError('File size exceeds 100MB limit.');
        return;
      }
      setSelectedFile(file);
      setError(null);
    }
  };

  const handleStartPipeline = async () => {
    setLoading(true);
    setError(null);
    setCurrentStage('queued');
    setCurrentProgress(0);
    cancelPollingRef.current = false;
    isPollingRef.current = true;

    try {
      let sourceId: string | undefined = undefined;
      let rawText: string | undefined = undefined;

      if (inputMode === 'upload') {
        if (!selectedFile) throw new Error('Please select a file to upload.');
        const sourceResp = await createSource({ file: selectedFile, sourceType: 'upload' });
        sourceId = sourceResp.id;
      } else if (inputMode === 'paste') {
        rawText = customText.trim();
        if (!rawText) throw new Error('Please enter transcript or text.');
        if (rawText.length < 50) throw new Error('Please provide more content (at least 50 characters).');
      } else if (inputMode === 'youtube') {
        if (!youtubeUrl.trim()) throw new Error('Please enter a YouTube URL.');
        if (!youtubeUrl.match(/^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/)) {
          throw new Error('Please enter a valid YouTube URL.');
        }
        const sourceResp = await createSource({ sourceUrl: youtubeUrl.trim(), sourceType: 'youtube_reference' });
        sourceId = sourceResp.id;
      }

      // Generate a client-side idempotency key
      const idempotencyKey = `req-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;

      // Create asynchronous background job
      const job = await createAsyncJob({
        sourceId,
        rawText: sourceId ? undefined : rawText,
        theme,
        learningLevel: 'INTERMEDIATE',
        idempotencyKey,
      });

      setActiveJobId(job.id);
      setCurrentStage(job.current_stage || 'queued');
      setCurrentProgress(job.progress || 0);

      // Poll background worker until completion
      const completedJob = await pollJobUntilDone(
        job.id,
        (progressJob: JobDetailResponse) => {
          if (cancelPollingRef.current) return;
          setCurrentStage(progressJob.current_stage);
          setCurrentProgress(progressJob.progress);
        },
        1200,
        300 // increased attempts for longer jobs
      );

      if (cancelPollingRef.current) return;

      if (completedJob.status === 'FAILED') {
        throw new Error(completedJob.error_message || 'Background worker processing failed.');
      }

      if (completedJob.status === 'COMPLETED') {
        setCurrentStage('completed');
        // Small delay to show completion state before navigating
        setTimeout(() => {
          router.push(`/notebook/${completedJob.id}`);
        }, 800);
      }
    } catch (err: unknown) {
      if (cancelPollingRef.current) return;
      const message = err instanceof Error ? err.message : 'Pipeline execution encountered an error.';
      setError(message);
      setCurrentStage('failed');
    } finally {
      if (!cancelPollingRef.current) {
        setLoading(false);
        isPollingRef.current = false;
      }
    }
  };

  const handleRetry = () => {
    setActiveJobId(null);
    setCurrentStage('created');
    setError(null);
  };

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 pb-20 font-sans">
      <header className="border-b border-slate-200 bg-white sticky top-0 z-50">
        <div className="max-w-4xl mx-auto px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-lg bg-indigo-600 flex items-center justify-center shadow-md">
              <BookOpen className="w-5 h-5 text-white" />
            </div>
            <div>
              <span className="font-bold text-lg tracking-tight text-slate-900 flex items-center gap-2">
                VisualNote AI
              </span>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-3xl mx-auto px-4 pt-12">
        {activeJobId ? (
          <div className="mt-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <GenerationProgress
              stage={currentStage}
              progress={currentProgress}
              error={error}
              onRetry={handleRetry}
            />
          </div>
        ) : (
          <div className="space-y-8 animate-in fade-in duration-300">
            <div className="text-center space-y-3">
              <h1 className="text-4xl font-extrabold text-slate-900 tracking-tight">
                Create Visual Note
              </h1>
              <p className="text-slate-500 text-base max-w-lg mx-auto">
                What do you want to learn? Provide educational content and we'll generate structured, deterministic visual notes.
              </p>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl shadow-sm p-8 space-y-8">
              {/* Input Mode Selector */}
              <div className="flex justify-center">
                <div className="flex rounded-xl bg-slate-100 p-1.5 shadow-inner">
                  <button
                    onClick={() => setInputMode('upload')}
                    className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                      inputMode === 'upload' ? 'bg-white text-indigo-700 shadow flex-1' : 'text-slate-600 hover:text-slate-900 flex-1'
                    }`}
                  >
                    <UploadCloud className="w-4 h-4" /> Upload
                  </button>
                  <button
                    onClick={() => setInputMode('paste')}
                    className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                      inputMode === 'paste' ? 'bg-white text-indigo-700 shadow flex-1' : 'text-slate-600 hover:text-slate-900 flex-1'
                    }`}
                  >
                    <FileText className="w-4 h-4" /> Transcript
                  </button>
                  <button
                    onClick={() => setInputMode('youtube')}
                    className={`flex items-center gap-2 px-6 py-2.5 rounded-lg text-sm font-semibold transition-all ${
                      inputMode === 'youtube' ? 'bg-white text-indigo-700 shadow flex-1' : 'text-slate-600 hover:text-slate-900 flex-1'
                    }`}
                  >
                    <Youtube className="w-4 h-4" /> YouTube
                  </button>
                </div>
              </div>

              {/* Input Area */}
              <div className="min-h-[220px]">
                {inputMode === 'upload' && (
                  <div
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onDrop={handleDrop}
                    className={`h-[220px] flex flex-col items-center justify-center border-2 border-dashed rounded-xl transition-colors ${
                      isDragging ? 'border-indigo-500 bg-indigo-50' : 'border-slate-300 hover:border-slate-400 bg-slate-50'
                    }`}
                  >
                    {selectedFile ? (
                      <div className="flex flex-col items-center p-6 text-center">
                        <div className="w-12 h-12 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center mb-3">
                          <FileText className="w-6 h-6" />
                        </div>
                        <p className="font-semibold text-slate-800 truncate max-w-[250px]">{selectedFile.name}</p>
                        <p className="text-xs text-slate-500 mt-1">{(selectedFile.size / 1024 / 1024).toFixed(2)} MB</p>
                        <button
                          onClick={(e) => { e.stopPropagation(); setSelectedFile(null); }}
                          className="mt-4 text-xs font-semibold text-red-600 hover:text-red-700 flex items-center gap-1"
                        >
                          <X className="w-3.5 h-3.5" /> Remove file
                        </button>
                      </div>
                    ) : (
                      <div className="flex flex-col items-center p-6 text-center" onClick={() => fileInputRef.current?.click()}>
                        <div className="w-14 h-14 bg-white border border-slate-200 text-slate-400 rounded-full flex items-center justify-center shadow-sm mb-4 cursor-pointer hover:bg-slate-50">
                          <UploadCloud className="w-6 h-6" />
                        </div>
                        <p className="font-semibold text-slate-800 text-sm">Drop your file here</p>
                        <p className="text-sm text-slate-500 mt-1 mb-4">or <span className="text-indigo-600 cursor-pointer hover:underline">browse files</span></p>
                        <p className="text-xs text-slate-400">Audio or Video (MP4, MP3, WAV, M4A) up to 100MB</p>
                      </div>
                    )}
                    <input
                      type="file"
                      ref={fileInputRef}
                      onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                      className="hidden"
                      accept="video/mp4,video/quicktime,video/webm,audio/mpeg,audio/wav,audio/x-m4a"
                    />
                  </div>
                )}

                {inputMode === 'paste' && (
                  <div className="h-full flex flex-col">
                    <textarea
                      value={customText}
                      onChange={(e) => setCustomText(e.target.value)}
                      placeholder="Paste your educational lecture transcript, notes, or detailed text here..."
                      className="w-full flex-1 min-h-[220px] bg-slate-50 border border-slate-300 rounded-xl p-4 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 resize-none transition-shadow"
                    />
                    <div className="text-right text-xs text-slate-500 mt-2 font-medium">
                      {customText.trim().length > 0 ? customText.trim().split(/\s+/).length : 0} words
                    </div>
                  </div>
                )}

                {inputMode === 'youtube' && (
                  <div className="h-[220px] flex flex-col items-center justify-center space-y-6">
                    <div className="w-16 h-16 bg-red-50 rounded-2xl flex items-center justify-center mb-2 shadow-sm border border-red-100">
                      <Youtube className="w-8 h-8 text-red-500" />
                    </div>
                    <div className="w-full max-w-md space-y-2 text-center">
                      <input
                        type="url"
                        value={youtubeUrl}
                        onChange={(e) => setYoutubeUrl(e.target.value)}
                        placeholder="https://youtube.com/watch?v=..."
                        className="w-full text-center bg-slate-50 border border-slate-300 rounded-xl px-4 py-3 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-red-500 focus:border-red-500 transition-shadow"
                      />
                      <p className="text-xs text-slate-500">Provide a public educational video for metadata ingestion.</p>
                    </div>
                  </div>
                )}
              </div>

              {/* Error Message */}
              {error && (
                <div className="p-4 rounded-xl bg-red-50 border border-red-100 text-red-800 text-sm flex items-start gap-3 animate-in fade-in">
                  <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
                  <span className="font-medium">{error}</span>
                </div>
              )}

              {/* Theme Settings & Submit */}
              <div className="pt-6 border-t border-slate-100 flex flex-col sm:flex-row items-center gap-4 justify-between">
                <div className="w-full sm:w-1/2 flex items-center gap-3 bg-slate-50 border border-slate-200 px-4 py-2.5 rounded-xl">
                  <label className="text-sm font-semibold text-slate-600 whitespace-nowrap">Theme</label>
                  <select
                    value={theme}
                    onChange={(e) => setTheme(e.target.value)}
                    className="w-full bg-transparent border-none text-sm font-medium text-slate-900 focus:ring-0 cursor-pointer outline-none"
                  >
                    <option value="clean_handwritten">Clean Handwritten</option>
                    <option value="notebook">Notebook Paper</option>
                    <option value="chalkboard">Chalkboard Dark</option>
                    <option value="minimal">Minimal</option>
                  </select>
                </div>

                <button
                  onClick={handleStartPipeline}
                  disabled={loading}
                  className="w-full sm:w-1/2 py-3.5 px-6 rounded-xl bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm shadow-lg shadow-indigo-600/20 transition-all flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed transform active:scale-[0.98]"
                >
                  <Sparkles className="w-4 h-4" />
                  Generate Visual Notes
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
