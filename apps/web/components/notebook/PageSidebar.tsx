import React from 'react';
import { FileImage } from 'lucide-react';
import { RenderResponse } from '../../lib/api';

interface PageSidebarProps {
  renderResult: RenderResponse;
  currentPage: number;
  onPageChange: (page: number) => void;
}

export function PageSidebar({ renderResult, currentPage, onPageChange }: PageSidebarProps) {
  // Currently we only have a single rendered page in RenderResponse.
  // In the future, this might be an array of pages.
  const pages = [1];

  return (
    <div className="w-64 flex-shrink-0 bg-slate-50 border-r border-slate-200 flex flex-col h-full overflow-hidden hidden md:flex">
      <div className="p-4 border-b border-slate-200">
        <h2 className="text-sm font-semibold text-slate-800 uppercase tracking-wider">Pages</h2>
      </div>
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {pages.map((p) => (
          <button
            key={p}
            onClick={() => onPageChange(p)}
            className={`w-full text-left rounded-lg overflow-hidden border-2 transition-all group focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 ${
              currentPage === p
                ? 'border-indigo-500 shadow-md ring-2 ring-indigo-500/20'
                : 'border-transparent hover:border-slate-300 shadow-sm'
            }`}
            aria-label={`Go to page ${p}`}
          >
            <div className="aspect-[3/4] bg-white border border-slate-200 rounded flex items-center justify-center relative overflow-hidden pointer-events-none">
              {/* Minimal preview thumbnail */}
              <div className="absolute inset-0 flex items-center justify-center opacity-10 group-hover:opacity-20 transition-opacity">
                <FileImage className="w-10 h-10" />
              </div>
              <span className="relative z-10 text-xl font-bold text-slate-300">{p}</span>
            </div>
            <div className={`mt-2 text-xs font-medium text-center ${currentPage === p ? 'text-indigo-600' : 'text-slate-500'}`}>
              Page {p}
            </div>
          </button>
        ))}
      </div>
    </div>
  );
}
