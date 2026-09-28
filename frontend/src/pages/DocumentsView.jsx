import React, { useState, useEffect } from 'react';
import { fetchDocuments, fetchTimetable } from '../services/api';
import { FileText, Download, Calendar, ExternalLink, Filter, BookOpen } from 'lucide-react';

export default function DocumentsView({ activeStudent }) {
  const [documents, setDocuments] = useState([]);
  const [examRows, setExamRows] = useState([]);
  const [classRows, setClassRows] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('documents'); // 'documents' or 'timetable'
  const [onlyMyCourse, setOnlyMyCourse] = useState(true);

  useEffect(() => {
    loadData();
  }, [activeStudent]);

  const loadData = async () => {
    setLoading(true);
    try {
      const [docs, exams, routine] = await Promise.all([
        fetchDocuments(),
        activeStudent ? fetchTimetable(activeStudent.course, activeStudent.semester, 1) : [],
        activeStudent ? fetchTimetable(activeStudent.course, activeStudent.semester, 0) : []
      ]);
      setDocuments(docs);
      setExamRows(exams);
      setClassRows(routine);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredDocs = onlyMyCourse && activeStudent
    ? documents.filter(d => d.course === 'ALL' || d.course === activeStudent.course)
    : documents;

  return (
    <div className="space-y-6">
      
      {/* Header & Tabs */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Academic Documents & Timetables</h2>
          <p className="text-xs text-slate-500 mt-1">
            Access official curriculum syllabus, exam schedules, and academic calendars
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="bg-slate-100 p-1 rounded-xl flex items-center gap-1">
            <button
              onClick={() => setActiveTab('documents')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'documents'
                  ? 'bg-white text-slate-900 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Official PDFs ({filteredDocs.length})
            </button>
            <button
              onClick={() => setActiveTab('timetable')}
              className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                activeTab === 'timetable'
                  ? 'bg-white text-slate-900 shadow-2xs'
                  : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              My Timetable ({examRows.length + classRows.length})
            </button>
          </div>
        </div>
      </div>

      {loading ? (
        <div className="flex items-center justify-center min-h-[300px]">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
        </div>
      ) : activeTab === 'documents' ? (
        
        /* Documents Grid */
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <label className="flex items-center gap-2 text-xs text-slate-600 cursor-pointer">
              <input
                type="checkbox"
                checked={onlyMyCourse}
                onChange={(e) => setOnlyMyCourse(e.target.checked)}
                className="rounded-sm border-slate-300 text-emerald-600 focus:ring-emerald-500"
              />
              <span>Show documents for <strong>{activeStudent?.course}</strong> only</span>
            </label>
            <span className="text-xs text-slate-600">Total: {filteredDocs.length} documents</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredDocs.map((doc) => (
              <div
                key={doc.id}
                className="bg-white rounded-xl border border-slate-200 p-5 hover:border-emerald-300 hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between gap-2 mb-3">
                    <span className="text-[10px] font-bold uppercase tracking-wider bg-slate-100 text-slate-700 px-2 py-0.5 rounded-md border border-slate-200">
                      {doc.document_type.replace('_', ' ')}
                    </span>
                    <span className="text-xs text-slate-600">
                      {doc.upload_date}
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 text-sm mb-2 leading-snug">
                    {doc.title}
                  </h3>

                  <div className="text-xs text-slate-600 space-y-1 mb-4">
                    <p>Course: <strong className="text-slate-700">{doc.course}</strong> {doc.semester ? `(Sem ${doc.semester})` : ''}</p>
                    <p>Source: <span className="text-slate-600">{doc.source || 'College Portal'}</span></p>
                    <p>Total Pages: <span className="text-slate-700">{doc.total_pages || 1}</span></p>
                  </div>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <a
                    href={`/api/documents/${doc.id}/file`}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-700 hover:text-emerald-800"
                  >
                    <FileText className="w-4 h-4" />
                    <span>View / Download PDF</span>
                  </a>
                </div>
              </div>
            ))}
          </div>
        </div>

      ) : (

        /* Structured Timetable Tables */
        <div className="space-y-6">
          
          {/* Exam Timetable */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-amber-500" />
                  <span>{activeStudent?.course} Semester {activeStudent?.semester} — Examination Timetable</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Retrieved from structured database (SQLite)</p>
              </div>
              <span className="text-xs bg-amber-100 text-amber-800 font-semibold px-2.5 py-1 rounded-full">
                {examRows.length} Scheduled Exams
              </span>
            </div>

            {examRows.length === 0 ? (
              <p className="text-xs text-slate-600 py-4 text-center">No exams scheduled for this course and semester.</p>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="min-w-full text-xs text-left bg-white">
                  <thead className="bg-slate-50 text-slate-700 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">Date</th>
                      <th className="px-4 py-3">Subject</th>
                      <th className="px-4 py-3">Time</th>
                      <th className="px-4 py-3">Hall</th>
                      <th className="px-4 py-3">Source Citation</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {examRows.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50/60">
                        <td className="px-4 py-3 font-semibold text-slate-900 whitespace-nowrap">{r.day_or_date}</td>
                        <td className="px-4 py-3 font-medium text-slate-800">{r.subject}</td>
                        <td className="px-4 py-3 text-slate-600 whitespace-nowrap">{r.time}</td>
                        <td className="px-4 py-3 font-mono text-slate-700">{r.room}</td>
                        <td className="px-4 py-3 text-slate-600 text-[11px]">{r.source}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Regular Class Timetable */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-xs">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <BookOpen className="w-5 h-5 text-teal-600" />
                  <span>{activeStudent?.course} Semester {activeStudent?.semester} — Class Routine</span>
                </h3>
                <p className="text-xs text-slate-500 mt-0.5">Regular lecture and lab schedule</p>
              </div>
            </div>

            {classRows.length === 0 ? (
              <p className="text-xs text-slate-600 py-4 text-center">No regular class lectures recorded.</p>
            ) : (
              <div className="overflow-x-auto rounded-xl border border-slate-200">
                <table className="min-w-full text-xs text-left bg-white">
                  <thead className="bg-slate-50 text-slate-700 font-semibold uppercase text-[10px] tracking-wider border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3">Day</th>
                      <th className="px-4 py-3">Subject</th>
                      <th className="px-4 py-3">Time</th>
                      <th className="px-4 py-3">Classroom</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {classRows.map((r) => (
                      <tr key={r.id} className="hover:bg-slate-50/60">
                        <td className="px-4 py-3 font-semibold text-slate-900">{r.day_or_date}</td>
                        <td className="px-4 py-3 font-medium text-slate-800">{r.subject}</td>
                        <td className="px-4 py-3 text-slate-600">{r.time}</td>
                        <td className="px-4 py-3 font-mono text-slate-700">{r.room}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

        </div>
      )}

    </div>
  );
}
