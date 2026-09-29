import React, { useState } from 'react';
import { ZoomIn, ZoomOut, Maximize, RotateCcw, Image as ImageIcon } from 'lucide-react';
import { RenderResponse, STORAGE_BASE } from '../../lib/api';

interface VisualNoteViewerProps {
  renderResult: RenderResponse;
}

const ZOOM_LEVELS = [50, 75, 100, 125, 150, 200];

export function VisualNoteViewer({ renderResult }: VisualNoteViewerProps) {
  const [zoomLevel, setZoomLevel] = useState(100);

  const handleZoomIn = () => {
    const nextIdx = ZOOM_LEVELS.findIndex((z) => z > zoomLevel);
    if (nextIdx !== -1) setZoomLevel(ZOOM_LEVELS[nextIdx]);
  };

  const handleZoomOut = () => {
    const nextIdx = ZOOM_LEVELS.slice().reverse().findIndex((z) => z < zoomLevel);
    if (nextIdx !== -1) setZoomLevel(ZOOM_LEVELS[ZOOM_LEVELS.length - 1 - nextIdx]);
  };

  const handleResetZoom = () => setZoomLevel(100);
  const handleFit = () => setZoomLevel(50); // simplistic fit-to-screen for now

  return (
    <div className="flex flex-col h-full bg-slate-100 rounded-lg overflow-hidden border border-slate-200">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-2 bg-white border-b border-slate-200">
        <div className="flex items-center gap-1">
          <button
            onClick={handleZoomOut}
            disabled={zoomLevel === ZOOM_LEVELS[0]}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded disabled:opacity-50"
            aria-label="Zoom out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
          <span className="text-xs font-medium text-slate-600 w-12 text-center">
            {zoomLevel}%
          </span>
          <button
            onClick={handleZoomIn}
            disabled={zoomLevel === ZOOM_LEVELS[ZOOM_LEVELS.length - 1]}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded disabled:opacity-50"
            aria-label="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
        </div>
        <div className="flex items-center gap-1 border-l border-slate-200 pl-2">
          <button
            onClick={handleResetZoom}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded"
            aria-label="Reset zoom"
            title="Reset zoom"
          >
            <RotateCcw className="w-4 h-4" />
          </button>
          <button
            onClick={handleFit}
            className="p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-100 rounded"
            aria-label="Fit to screen"
            title="Fit to screen"
          >
            <Maximize className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Viewer Canvas */}
      <div className="flex-1 overflow-auto p-4 flex items-center justify-center relative bg-slate-50">
        <div
          className="transition-transform duration-200 ease-out origin-top flex items-center justify-center"
          style={{ transform: `scale(${zoomLevel / 100})` }}
        >
          {renderResult.image_url ? (
            <img
              src={`${STORAGE_BASE}${renderResult.image_url}`}
              alt={renderResult.page_title}
              className="max-w-none shadow-xl border border-slate-200 bg-white"
            />
          ) : renderResult.html_url ? (
            <iframe
              src={`${STORAGE_BASE}${renderResult.html_url}`}
              title={renderResult.page_title}
              className="border-0 shadow-xl bg-white"
              style={{ width: '1200px', height: '1600px' }}
            />
          ) : renderResult.svg_content ? (
            <div
              dangerouslySetInnerHTML={{ __html: renderResult.svg_content }}
              className="shadow-xl border border-slate-200 bg-white"
            />
          ) : (
            <div className="flex flex-col items-center justify-center text-slate-400 gap-3 py-20 px-32 bg-white rounded-xl border border-slate-200 shadow-sm">
              <ImageIcon className="w-12 h-12 text-slate-300" />
              <p>Visual Note content unavailable.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
