import React from 'react';
import { Calendar, Clock, MapPin, Users, Award } from 'lucide-react';

export default function EventCard({ event }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 hover:shadow-md transition-shadow flex flex-col justify-between">
      <div>
        <div className="flex items-center justify-between gap-2 mb-2">
          <span className="text-[11px] font-semibold uppercase px-2.5 py-0.5 rounded-full bg-teal-100 text-teal-800 border border-teal-200">
            {event.target_course === 'ALL' ? 'Open to All' : `Target: ${event.target_course}`}
          </span>
          <span className="text-xs text-slate-600 flex items-center gap-1 font-medium">
            <Calendar className="w-3.5 h-3.5 text-teal-600" />
            {event.date}
          </span>
        </div>

        <h4 className="font-semibold text-slate-900 text-sm mb-1.5 leading-snug">
          {event.title}
        </h4>

        <p className="text-xs text-slate-600 line-clamp-2 mb-3 leading-relaxed">
          {event.description}
        </p>

        <div className="space-y-1 text-xs text-slate-600 mb-3">
          <div className="flex items-center gap-2">
            <Clock className="w-3.5 h-3.5 text-slate-600" />
            <span>{event.time}</span>
          </div>
          <div className="flex items-center gap-2">
            <MapPin className="w-3.5 h-3.5 text-slate-600" />
            <span>{event.venue}</span>
          </div>
          <div className="flex items-center gap-2">
            <Users className="w-3.5 h-3.5 text-slate-600" />
            <span className="truncate">{event.organizer}</span>
          </div>
        </div>
      </div>

      <div className="pt-2.5 border-t border-slate-100 flex flex-wrap items-center justify-between gap-2 text-xs">
        {event.registration_deadline ? (
          <div className="text-amber-700 font-medium text-[11px] bg-amber-50 px-2 py-0.5 rounded-md border border-amber-200">
            Reg. Closes: {event.registration_deadline}
          </div>
        ) : (
          <span className="text-slate-600 text-[11px]">Free Entry</span>
        )}

        <span className="text-[11px] text-slate-600 truncate max-w-[130px]" title={event.source}>
          {event.source || 'College Circular'}
        </span>
      </div>
    </div>
  );
}
