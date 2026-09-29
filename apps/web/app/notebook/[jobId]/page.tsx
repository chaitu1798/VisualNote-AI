'use client';

import React, { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import { ChevronLeft, ChevronRight, AlertCircle, RefreshCcw } from 'lucide-react';
import { getJobStatus, JobDetailResponse } from '../../../lib/api';
import { VisualNoteViewer } from '../../../components/viewer/VisualNoteViewer';
import { PageSidebar } from '../../../components/notebook/PageSidebar';
import { ExportMenu } from '../../../components/notebook/ExportMenu';

export default function NotebookPage({ params }: { params: { jobId: string } }) {
  const router = useRouter();
  const [job, setJob] = useState<JobDetailResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentPage, setCurrentPage] = useState(1);

  const fetchJob = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getJobStatus(params.jobId);
      setJob(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load visual note.');
    } finally {
      setLoading(false);
    }
  }, [params.jobId]);

  useEffect(() => {
    fetchJob();
  }, [fetchJob]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Avoid if user is typing in an input
      if (document.activeElement?.tagName === 'INPUT' || document.activeElement?.tagName === 'TEXTAREA') return;

      if (e.key === 'ArrowLeft') {
        setCurrentPage((prev) => Math.max(1, prev - 1));
      } else if (e.key === 'ArrowRight') {
        setCurrentPage((prev) => prev); // Wait, only 1 page currently
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4 text-slate-500">
          <div className="w-8 h-8 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          <p className="font-medium">Loading your Visual Note...</p>
        </div>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full text-center border border-slate-100">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800 mb-2">Visual Note not found</h1>
          <p className="text-slate-500 mb-8">{error || "We couldn't find the visual note you're looking for."}</p>
          <div className="flex flex-col gap-3">
            <button
              onClick={fetchJob}
              className="w-full py-3 px-4 rounded-xl font-semibold bg-indigo-50 text-indigo-700 hover:bg-indigo-100 transition-colors"
            >
              Try Again
            </button>
            <button
              onClick={() => router.push('/create')}
              className="w-full py-3 px-4 rounded-xl font-semibold text-slate-600 hover:bg-slate-50 transition-colors"
            >
              Create New Note
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (job.status !== 'COMPLETED') {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <div className="bg-white p-8 rounded-2xl shadow-xl max-w-md w-full text-center border border-slate-100">
          <div className="w-16 h-16 bg-amber-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <RefreshCcw className="w-8 h-8 text-amber-500" />
          </div>
          <h1 className="text-2xl font-bold text-slate-800 mb-2">Generation in Progress</h1>
          <p className="text-slate-500 mb-8">This visual note is still being prepared.</p>
          <button
            onClick={() => router.push('/create')}
            className="w-full py-3 px-4 rounded-xl font-semibold bg-indigo-600 text-white hover:bg-indigo-700 transition-colors shadow-md shadow-indigo-200"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  const renderResult = job.result_data?.render_result as any;

  return (
    <div className="h-screen w-full flex flex-col bg-white overflow-hidden text-slate-800 font-sans">
      {/* Top Navigation */}
      <header className="h-14 bg-white border-b border-slate-200 flex items-center justify-between px-4 lg:px-6 flex-shrink-0 z-10 shadow-sm">
        <div className="flex items-center gap-4">
          <div className="font-bold text-lg tracking-tight text-indigo-600 flex items-center gap-2">
            VisualNote AI
          </div>
          <div className="h-4 w-px bg-slate-300 hidden sm:block"></div>
          <h1 className="text-sm font-medium text-slate-600 hidden sm:block truncate max-w-md">
            {renderResult?.page_title || 'Untitled Visual Note'}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => router.push('/create')}
            className="text-sm font-medium text-slate-500 hover:text-slate-800 transition-colors"
          >
            New Note
          </button>
          {renderResult && <ExportMenu renderResult={renderResult} />}
        </div>
      </header>

      {/* Main Content Area */}
      <main className="flex-1 flex overflow-hidden relative bg-slate-50">
        {renderResult && (
          <PageSidebar
            renderResult={renderResult}
            currentPage={currentPage}
            onPageChange={setCurrentPage}
          />
        )}

        <div className="flex-1 flex flex-col min-w-0 p-4 lg:p-6 pb-20 md:pb-6 relative overflow-hidden">
          {renderResult ? (
            <VisualNoteViewer renderResult={renderResult} />
          ) : (
            <div className="flex-1 flex items-center justify-center border-2 border-dashed border-slate-200 rounded-2xl bg-white text-slate-400">
              No visual rendering available for this job.
            </div>
          )}
        </div>
      </main>

      {/* Mobile Bottom Navigation (Visible only on small screens) */}
      <div className="md:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 p-2 flex justify-between items-center shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.05)] z-20">
        <button
          onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
          disabled={currentPage === 1}
          className="p-2 text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Previous Page"
        >
          <ChevronLeft className="w-6 h-6" />
        </button>
        <span className="text-sm font-semibold text-slate-700">
          Page {currentPage} of 1
        </span>
        <button
          disabled={true} // Only 1 page for now
          className="p-2 text-slate-600 disabled:opacity-30 disabled:cursor-not-allowed"
          aria-label="Next Page"
        >
          <ChevronRight className="w-6 h-6" />
        </button>
      </div>
    </div>
  );
}
