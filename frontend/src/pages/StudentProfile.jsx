import React from 'react';
import { User, Hash, Mail, BookOpen, Building2, GraduationCap, Calendar, Sparkles, ShieldCheck, LogOut, LayoutDashboard, MessageSquare } from 'lucide-react';

export default function StudentProfile({ student, setTab, onLogout }) {
  if (!student) {
    return (
      <div className="p-8 text-center text-slate-500">
        No student profile loaded.
      </div>
    );
  }

  const interestList = student.interests
    ? student.interests.split(',').map((i) => i.trim()).filter(Boolean)
    : [];

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      
      {/* Top Profile Card */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
          
          <div className="flex items-center gap-4">
            <div className="w-16 h-16 rounded-2xl bg-gradient-to-tr from-emerald-600 to-teal-500 text-white flex items-center justify-center text-2xl font-bold shadow-md shadow-emerald-500/20">
              {student.name.charAt(0)}
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h1 className="text-2xl font-bold text-slate-900 tracking-tight">{student.name}</h1>
                <span className="inline-flex items-center gap-1 text-[11px] font-semibold bg-emerald-100 text-emerald-800 px-2.5 py-0.5 rounded-full">
                  <ShieldCheck className="w-3 h-3" />
                  <span>Authenticated Student</span>
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">
                {student.course} • Semester {student.semester} • {student.department}
              </p>
            </div>
          </div>

          <button
            onClick={onLogout}
            className="flex items-center gap-1.5 px-3.5 py-2 text-xs font-semibold text-rose-600 hover:text-white bg-rose-50 hover:bg-rose-600 border border-rose-200 hover:border-rose-600 rounded-xl transition-all cursor-pointer"
          >
            <LogOut className="w-3.5 h-3.5" />
            <span>Sign Out</span>
          </button>
        </div>

        {/* Profile Details Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-4 pt-6">
          
          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
              <Hash className="w-3.5 h-3.5 text-emerald-600" />
              <span>Admission Number</span>
            </div>
            <div className="text-sm font-bold text-slate-800 font-mono">
              {student.admission_number || student.id || 'N/A'}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
              <Hash className="w-3.5 h-3.5 text-teal-600" />
              <span>Class Roll Number</span>
            </div>
            <div className="text-sm font-bold text-slate-800 font-mono">
              {student.roll_number || 'N/A'}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
              <Mail className="w-3.5 h-3.5 text-sky-600" />
              <span>Email Address</span>
            </div>
            <div className="text-xs font-semibold text-slate-800 truncate">
              {student.email || 'N/A'}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
              <BookOpen className="w-3.5 h-3.5 text-indigo-600" />
              <span>Degree & Programme</span>
            </div>
            <div className="text-sm font-bold text-slate-800">
              {student.course}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
              <Building2 className="w-3.5 h-3.5 text-amber-600" />
              <span>Department</span>
            </div>
            <div className="text-sm font-bold text-slate-800">
              {student.department}
            </div>
          </div>

          <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-100">
            <div className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider mb-1 flex items-center gap-1">
              <GraduationCap className="w-3.5 h-3.5 text-purple-600" />
              <span>Semester & Batch</span>
            </div>
            <div className="text-sm font-bold text-slate-800">
              Semester {student.semester} ({student.batch})
            </div>
          </div>

        </div>

        {/* Interests */}
        <div className="mt-6 pt-5 border-t border-slate-100">
          <div className="text-xs font-semibold text-slate-700 mb-2 flex items-center gap-1.5">
            <Sparkles className="w-4 h-4 text-emerald-600" />
            <span>Academic & Activity Interests</span>
          </div>
          {interestList.length > 0 ? (
            <div className="flex flex-wrap gap-2">
              {interestList.map((interest, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-medium"
                >
                  {interest}
                </span>
              ))}
            </div>
          ) : (
            <p className="text-xs text-slate-400 italic">No specific interests registered.</p>
          )}
        </div>

      </div>

      {/* Quick Launch Shortcuts */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        
        <div
          onClick={() => setTab('dashboard')}
          className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs hover:border-emerald-500 transition-all cursor-pointer flex items-center gap-4"
        >
          <div className="w-12 h-12 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center shrink-0">
            <LayoutDashboard className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Personalized Dashboard</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              View your notices, deadlines, timetable & events
            </p>
          </div>
        </div>

        <div
          onClick={() => setTab('chat')}
          className="p-5 bg-white border border-slate-200 rounded-2xl shadow-xs hover:border-emerald-500 transition-all cursor-pointer flex items-center gap-4"
        >
          <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center shrink-0">
            <MessageSquare className="w-6 h-6" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">SafiBot AI Assistant</h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Ask questions about your syllabus, timetable, or college website
            </p>
          </div>
        </div>

      </div>

    </div>
  );
}
