import React from 'react';
import { Bell, Calendar, Clock, FileText } from 'lucide-react';

export default function NoticeCard({ notice }) {
  const getCategoryColor = (cat) => {
    switch (cat?.toLowerCase()) {
      case 'examination':
        return 'bg-amber-100 text-amber-800 border-amber-200';
      case 'academic':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'scholarship':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-md transition-shadow relative overflow-hidden flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <span className={`text-[11px] font-semibold uppercase px-2.5 py-0.5 rounded-full border ${getCategoryColor(notice.category)}`}>
            {notice.category}
          </span>
          <span className="text-xs text-slate-600 flex items-center gap-1">
            <Clock className="w-3.5 h-3.5" />
            {notice.date}
          </span>
        </div>

        <h4 className="font-semibold text-slate-900 text-sm mb-1.5 leading-snug">
          {notice.title}
        </h4>

        <p className="text-xs text-slate-600 line-clamp-3 mb-3 leading-relaxed">
          {notice.content}
        </p>
      </div>

      <div className="pt-2.5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
        {notice.deadline ? (
          <div className="flex items-center gap-1 text-red-600 font-medium">
            <Calendar className="w-3.5 h-3.5" />
            <span>Deadline: {notice.deadline}</span>
          </div>
        ) : (
          <span className="text-slate-600">No deadline</span>
        )}

        <div className="text-[11px] text-slate-600 flex items-center gap-2">
          {notice.file_path && (
            <a
              href={notice.file_path}
              target="_blank"
              rel="noreferrer"
              className="font-semibold text-emerald-700 hover:text-emerald-800 hover:underline flex items-center gap-1"
            >
              <span>View Official PDF ↗</span>
            </a>
          )}
          <span className="truncate max-w-[140px]" title={notice.source}>
            {notice.source || 'Notice Board'}
          </span>
        </div>
      </div>
    </div>
  );
}
