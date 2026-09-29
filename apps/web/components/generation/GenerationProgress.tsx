import React from 'react';
import { AlertCircle, RefreshCw } from 'lucide-react';

interface GenerationProgressProps {
  stage: string;
  progress: number;
  error?: string | null;
  onRetry?: () => void;
}

const STAGES = [
  { id: 'created', label: 'Source Created' },
  { id: 'queued', label: 'Queued' },
  { id: 'extracting', label: 'Extracting' },
  { id: 'transcribing', label: 'Transcribing' },
  { id: 'analyzing', label: 'Analyzing' },
  { id: 'planning', label: 'Planning' },
  { id: 'rendering', label: 'Rendering' },
  { id: 'completed', label: 'Completed' },
];

export function GenerationProgress({ stage, progress, error, onRetry }: GenerationProgressProps) {
  const getStageIndex = (s: string) => STAGES.findIndex((st) => st.id === s);
  const currentIdx = getStageIndex(stage);

  return (
    <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 max-w-2xl mx-auto w-full">
      <h3 className="text-lg font-semibold text-slate-800 mb-6 text-center">
        {stage === 'completed' ? 'Generation Complete' : 'Generating Visual Note...'}
      </h3>

      <div className="space-y-4">
        {STAGES.map((s, idx) => {
          const isDone = currentIdx >= idx && stage !== 'failed' && stage !== 'cancelled';
          const isCurrent = stage === s.id;
          const isError = (stage === 'failed' || stage === 'cancelled') && currentIdx === idx;

          return (
            <div key={s.id} className="flex items-center gap-3">
              <div className="flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center">
                {isError ? (
                  <div className="w-2.5 h-2.5 rounded-full bg-red-500" />
                ) : isDone && !isCurrent ? (
                  <svg className="w-4 h-4 text-indigo-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                ) : isCurrent ? (
                  <div className="w-2.5 h-2.5 rounded-full bg-indigo-500 animate-pulse" />
                ) : (
                  <div className="w-2 h-2 rounded-full bg-slate-300" />
                )}
              </div>
              <span className={`text-sm font-medium ${
                isError ? 'text-red-500' :
                isCurrent ? 'text-indigo-600' :
                isDone ? 'text-slate-700' : 'text-slate-400'
              }`}>
                {s.label}
              </span>
            </div>
          );
        })}
      </div>

      {error && (
        <div className="mt-6 p-4 rounded-lg bg-red-50 border border-red-100 flex items-start gap-3">
          <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-red-800">Generation Failed</h4>
            <p className="text-sm text-red-600 mt-1">{error}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="mt-3 px-3 py-1.5 text-xs font-semibold bg-red-100 text-red-700 rounded-md hover:bg-red-200 transition-colors flex items-center gap-1"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Try Again
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
