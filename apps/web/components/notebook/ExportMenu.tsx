import React, { useState } from 'react';
import { Download, ChevronDown, Check, Loader2 } from 'lucide-react';
import { STORAGE_BASE, RenderResponse, exportPdf } from '../../lib/api';

interface ExportMenuProps {
  renderResult: RenderResponse;
  projectId?: string;
}

export function ExportMenu({ renderResult, projectId }: ExportMenuProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [downloading, setDownloading] = useState<string | null>(null);

  const availableFormats: { id: string; label: string; url?: string | null }[] = [
    { id: 'pdf', label: 'Study Pack (PDF)' },
    { id: 'png', label: 'PNG Image', url: renderResult.image_url },
    { id: 'svg', label: 'SVG Vector', url: renderResult.html_url },
  ].filter(f => f.id === 'pdf' ? !!projectId : (!!f.url || (f.id === 'svg' && renderResult.svg_content)));

  const handleDownload = async (format: string, urlOrContent?: string | null) => {
    setDownloading(format);
    try {
      if (format === 'pdf' && projectId) {
        const { url } = await exportPdf(projectId);
        const fullUrl = url.startsWith('http') ? url : `${STORAGE_BASE}${url}`;
        const res = await fetch(fullUrl);
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${renderResult.page_title.replace(/\s+/g, '_')}_StudyPack.pdf`;
        a.click();
        URL.revokeObjectURL(a.href);
      } else if (format === 'svg' && renderResult.svg_content) {
        // Download raw SVG string
        const blob = new Blob([renderResult.svg_content], { type: 'image/svg+xml' });
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${renderResult.page_title.replace(/\s+/g, '_')}.svg`;
        a.click();
        URL.revokeObjectURL(a.href);
      } else {
        // Download URL
        const fullUrl = `${STORAGE_BASE}${urlOrContent}`;
        const res = await fetch(fullUrl);
        const blob = await res.blob();
        const a = document.createElement('a');
        a.href = URL.createObjectURL(blob);
        a.download = `${renderResult.page_title.replace(/\s+/g, '_')}.${format}`;
        a.click();
        URL.revokeObjectURL(a.href);
      }
    } catch (e) {
      console.error('Download failed', e);
      alert(`Failed to download ${format.toUpperCase()}`);
    } finally {
      setDownloading(null);
      setIsOpen(false);
    }
  };

  if (availableFormats.length === 0) return null;

  return (
    <div className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-slate-700 bg-white border border-slate-200 rounded-md hover:bg-slate-50 transition-colors"
      >
        <Download className="w-4 h-4" />
        Export
        <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
      </button>

      {isOpen && (
        <div className="absolute right-0 mt-2 w-48 bg-white border border-slate-200 rounded-lg shadow-lg py-1 z-50">
          {availableFormats.map(f => (
            <button
              key={f.id}
              onClick={() => handleDownload(f.id, f.url || renderResult.svg_content)}
              disabled={!!downloading}
              className="w-full text-left px-4 py-2 text-sm text-slate-700 hover:bg-slate-50 flex items-center justify-between disabled:opacity-50"
            >
              <span>{f.label}</span>
              {downloading === f.id && <Loader2 className="w-3.5 h-3.5 animate-spin text-slate-400" />}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
