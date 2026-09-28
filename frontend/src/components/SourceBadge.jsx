import React from 'react';
import { FileText, Bookmark } from 'lucide-react';

export default function SourceBadge({ source }) {
  if (!source) return null;

  return (
    <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md bg-slate-100 border border-slate-200 text-slate-700 text-xs shadow-2xs">
      <FileText className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
      <span className="font-medium truncate max-w-[220px]" title={source.title}>
        {source.title}
      </span>
      {source.page && (
        <span className="bg-emerald-600 text-white font-bold text-[10px] px-1.5 py-0.2 rounded-full">
          p.{source.page}
        </span>
      )}
    </div>
  );
}
