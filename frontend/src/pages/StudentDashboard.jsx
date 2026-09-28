import React, { useState, useEffect } from 'react';
import { fetchDashboard } from '../services/api';
import NoticeCard from '../components/NoticeCard';
import EventCard from '../components/EventCard';
import { GraduationCap, Calendar, Clock, AlertCircle, Sparkles, BookOpen, MessageSquare, ChevronRight } from 'lucide-react';

export default function StudentDashboard({ activeStudent, setTab }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!activeStudent) return;
    setLoading(true);
    fetchDashboard(activeStudent.id)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });
  }, [activeStudent]);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-6 text-center text-red-600">
        <AlertCircle className="w-8 h-8 mx-auto mb-2" />
        <p>Failed to load dashboard: {error}</p>
      </div>
    );
  }

  const { student, notices, events, deadlines, next_exam } = data;

  return (
    <div className="space-y-6">
      
      {/* Student Welcome Banner */}
      <div className="bg-gradient-to-r from-slate-900 via-slate-800 to-teal-950 text-white rounded-2xl p-6 sm:p-8 shadow-md relative overflow-hidden">
        <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-radial from-emerald-500/10 to-transparent pointer-events-none"></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-start gap-4">
            <img 
              src="/safibot-logo.svg" 
              alt="SafiBot Logo" 
              className="w-16 h-16 sm:w-20 sm:h-20 object-contain rounded-2xl bg-white/10 p-1.5 backdrop-blur-xs border border-white/15 shrink-0" 
            />
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-500/30 text-xs px-2.5 py-0.5 rounded-full font-medium">
                  {student.id === 'guest' ? 'Campus Visitor' : student.department}
                </span>
                <span className="bg-white/10 text-slate-200 border border-white/10 text-xs px-2.5 py-0.5 rounded-full font-mono">
                  {student.id === 'guest' ? 'Guest Mode' : `Adm: ${student.admission_number || student.id}`}
                </span>
                {student.roll_number && student.id !== 'guest' && (
                  <span className="bg-white/10 text-slate-200 border border-white/10 text-xs px-2.5 py-0.5 rounded-full font-mono">
                    Roll: {student.roll_number}
                  </span>
                )}
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                {student.id === 'guest' ? 'Welcome to SafiBot' : `Welcome back, ${student.name}`}
              </h2>
              <p className="text-slate-300 text-sm mt-1">
                {student.id === 'guest'
                  ? 'Explore official programmes, departments, campus facilities, and ask our AI assistant anything.'
                  : `Program: ${student.course} (Semester ${student.semester}) • Batch: ${student.batch}`}
              </p>
              {student.interests && student.id !== 'guest' && (
                <p className="text-slate-400 text-xs mt-2 flex items-center gap-1">
                  <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                  Interests: {student.interests}
                </p>
              )}
            </div>
        </div>

          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setTab('chat')}
              className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-2 shadow-sm transition-all cursor-pointer"
            >
              <MessageSquare className="w-4 h-4" />
              Ask SafiBot
            </button>
            <button
              onClick={() => setTab('documents')}
              className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold flex items-center gap-2 backdrop-blur-xs transition-all cursor-pointer"
            >
              <BookOpen className="w-4 h-4" />
              Syllabus & Timetable
            </button>
          </div>
        </div>
      </div>

      {/* Guest Mode Alert Banner */}
      {student.id === 'guest' && (
        <div className="bg-emerald-50 border border-emerald-200 rounded-2xl p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 text-xs text-emerald-950">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-4 h-4 text-emerald-600 shrink-0" />
            <span>
              <strong>Browsing as Guest:</strong> You have full access to SafiBot's AI Chatbot, SIAS website knowledge, and campus events. Log in with your student credentials to view your personalized exam timetable.
            </span>
          </div>
          <button
            onClick={() => setTab('login')}
            className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold rounded-lg shrink-0 transition-colors cursor-pointer shadow-xs"
          >
            Student Login
          </button>
        </div>
      )}

      {/* Next Exam Highlight Card */}
      {next_exam && (
        <div className="bg-amber-50 border border-amber-200 rounded-2xl p-5 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 rounded-xl bg-amber-500 text-white flex items-center justify-center shrink-0 shadow-sm">
              <Calendar className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-amber-900 uppercase tracking-wider">
                  Upcoming Examination
                </span>
                <span className="text-xs text-amber-800 bg-amber-200/60 px-2 py-0.5 rounded-md font-mono">
                  {next_exam.day_or_date}
                </span>
              </div>
              <h3 className="font-bold text-slate-900 text-base mt-0.5">
                {next_exam.subject}
              </h3>
              <p className="text-xs text-slate-600">
                Time: <strong>{next_exam.time}</strong> • Room: <strong>{next_exam.room}</strong>
              </p>
            </div>
          </div>
          <button
            onClick={() => setTab('chat')}
            className="text-xs font-semibold text-amber-900 hover:text-amber-950 flex items-center gap-1 self-end sm:self-auto cursor-pointer"
          >
            <span>Ask for full schedule</span>
            <ChevronRight className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Two-Column Grid: Personalized Notices & Upcoming Events */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Notices Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-900 text-lg">Personalized Notices</h3>
              <span className="text-xs bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full font-semibold">
                {notices.length}
              </span>
            </div>
            <span className="text-xs text-slate-600">Filtered for {student.course} S{student.semester}</span>
          </div>

          {notices.length === 0 ? (
            <p className="text-xs text-slate-600 bg-white p-6 rounded-xl border border-slate-200 text-center">
              No specific notices for your course and semester right now.
            </p>
          ) : (
            <div className="space-y-3">
              {notices.map((notice) => (
                <NoticeCard key={notice.id} notice={notice} />
              ))}
            </div>
          )}
        </div>

        {/* Events Section */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <h3 className="font-bold text-slate-900 text-lg">Campus Events</h3>
              <span className="text-xs bg-teal-100 text-teal-800 px-2 py-0.5 rounded-full font-semibold">
                {events.length}
              </span>
            </div>
            <span className="text-xs text-slate-600">Eligible Events</span>
          </div>

          {events.length === 0 ? (
            <p className="text-xs text-slate-600 bg-white p-6 rounded-xl border border-slate-200 text-center">
              No events scheduled for your course right now.
            </p>
          ) : (
            <div className="space-y-3">
              {events.map((event) => (
                <EventCard key={event.id} event={event} />
              ))}
            </div>
          )}
        </div>

      </div>

      {/* Deadlines Section */}
      {deadlines && deadlines.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs">
          <div className="flex items-center gap-2 mb-3">
            <AlertCircle className="w-5 h-5 text-red-500" />
            <h3 className="font-bold text-slate-900 text-base">Action Required / Deadlines</h3>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {deadlines.map((d) => (
              <div key={d.id} className="p-3.5 rounded-xl bg-red-50/60 border border-red-100 flex items-start justify-between gap-3">
                <div>
                  <h4 className="font-semibold text-slate-900 text-xs">{d.title}</h4>
                  <p className="text-[11px] text-slate-600 line-clamp-2 mt-0.5">{d.content}</p>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-xs font-bold text-red-700 block">{d.deadline}</span>
                  <span className="text-[10px] text-slate-600">{d.source}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

    </div>
  );
}
