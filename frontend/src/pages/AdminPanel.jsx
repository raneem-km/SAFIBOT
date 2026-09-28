import React, { useState, useEffect } from 'react';
import {
  extractAnnouncement,
  publishAnnouncement,
  uploadDocument,
  syncWebsite,
  fetchLearningQueue,
  resolveLearningQueueItem,
  ignoreLearningQueueItem,
  fetchAdminFeedback,
  createManualEvent,
  createManualNotice
} from '../services/api';
import {
  UploadCloud,
  MessageSquareCode,
  CheckCircle2,
  AlertCircle,
  FileText,
  Sparkles,
  Send,
  Globe,
  RefreshCw,
  HelpCircle,
  ThumbsUp,
  ThumbsDown,
  Check,
  X,
  Calendar,
  Bell,
  Clock,
  Layers,
  ShieldAlert
} from 'lucide-react';

export default function AdminPanel({ onDocumentUploaded }) {
  const [activeSection, setActiveSection] = useState('whatsapp'); // 'whatsapp', 'pdf', 'website', 'learning', 'manual'

  // WhatsApp announcement state
  const [rawText, setRawText] = useState(
    'Python workshop tomorrow at 2 PM in Lab 3. BCA students can participate. Registration closes Thursday.'
  );
  const [extracting, setExtracting] = useState(false);
  const [extractedData, setExtractedData] = useState(null);
  const [publishStatus, setPublishStatus] = useState(null);

  // PDF Upload state
  const [pdfFile, setPdfFile] = useState(null);
  const [pdfTitle, setPdfTitle] = useState('');
  const [docType, setDocType] = useState('syllabus');
  const [pdfCourse, setPdfCourse] = useState('BCA');
  const [pdfSem, setPdfSem] = useState('3');
  const [pdfDept, setPdfDept] = useState('Computer Applications');
  const [pdfSource, setPdfSource] = useState('Department Board of Studies');
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(null);

  // Website Sync state
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState(null);

  // Diagnostic Retrieval state (Section 4)
  const [diagQuery, setDiagQuery] = useState('What programmes are offered by the Department of Computer Applications?');
  const [diagLoading, setDiagLoading] = useState(false);
  const [diagResult, setDiagResult] = useState(null);
  const [diagError, setDiagError] = useState(null);

  // Learning Queue & Feedback state
  const [queueItems, setQueueItems] = useState([]);
  const [queueLoading, setQueueLoading] = useState(false);
  const [resolvingId, setResolvingId] = useState(null);
  const [verifiedAnswerText, setVerifiedAnswerText] = useState('');
  const [verifiedSourceText, setVerifiedSourceText] = useState('College Administration');
  const [feedbackStats, setFeedbackStats] = useState(null);

  // Manual Notice/Event state
  const [manualType, setManualType] = useState('notice');
  const [manualForm, setManualForm] = useState({
    title: '',
    description: '',
    category: 'Academic',
    date: '2026-10-15',
    time: '10:00 AM',
    venue: 'Seminar Hall',
    organizer: 'College Council',
    target_course: 'ALL',
    target_semester: 'ALL',
    deadline: '',
    source: 'Official College Circular'
  });
  const [manualStatus, setManualStatus] = useState(null);

  // Fetch learning queue when switching to learning tab
  useEffect(() => {
    if (activeSection === 'learning') {
      loadLearningQueue();
    }
  }, [activeSection]);

  const loadLearningQueue = async () => {
    setQueueLoading(true);
    try {
      const [queue, fb] = await Promise.all([
        fetchLearningQueue(),
        fetchAdminFeedback()
      ]);
      setQueueItems(queue);
      setFeedbackStats(fb.stats);
    } catch (err) {
      console.error('Failed to load learning queue:', err);
    } finally {
      setQueueLoading(false);
    }
  };

  // 1. Handle Announcement Extraction
  const handleExtract = async () => {
    if (!rawText.trim()) return;
    setExtracting(true);
    setPublishStatus(null);
    try {
      const res = await extractAnnouncement(rawText);
      setExtractedData(res);
    } catch (err) {
      alert(`Extraction failed: ${err.message}`);
    } finally {
      setExtracting(false);
    }
  };

  // 2. Handle Publish Announcement
  const handlePublish = async () => {
    if (!extractedData) return;
    try {
      const res = await publishAnnouncement(extractedData);
      setPublishStatus({
        type: 'success',
        message: res.message || 'Announcement approved and published successfully!'
      });
      setExtractedData(null);
      setRawText('');
    } catch (err) {
      setPublishStatus({
        type: 'error',
        message: `Publish failed: ${err.message}`
      });
    }
  };

  // 3. Handle PDF Upload
  const handlePdfSubmit = async (e) => {
    e.preventDefault();
    if (!pdfFile || !pdfTitle) {
      alert('Please select a PDF file and provide a document title.');
      return;
    }

    setUploading(true);
    setUploadSuccess(null);

    const formData = new FormData();
    formData.append('file', pdfFile);
    formData.append('title', pdfTitle);
    formData.append('document_type', docType);
    formData.append('course', pdfCourse);
    if (pdfSem) formData.append('semester', pdfSem);
    formData.append('department', pdfDept);
    formData.append('source', pdfSource);

    try {
      const res = await uploadDocument(formData);
      setUploadSuccess(`Document "${res.title}" successfully ingested and indexed into ChromaDB! (Pages: ${res.total_pages})`);
      setPdfFile(null);
      setPdfTitle('');
      if (onDocumentUploaded) onDocumentUploaded();
    } catch (err) {
      alert(`Upload failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  // 4. Handle Website Sync
  const handleSyncWebsite = async () => {
    setSyncing(true);
    setSyncResult(null);
    try {
      const res = await syncWebsite();
      setSyncResult({
        type: 'success',
        data: res
      });
    } catch (err) {
      setSyncResult({
        type: 'error',
        message: err.message
      });
    } finally {
      setSyncing(false);
    }
  };

  // 4b. Diagnostic Retrieval Tester (Section 4)
  const handleRunDiagnostic = async (overrideQuery = null) => {
    const q = overrideQuery || diagQuery;
    if (!q.trim()) return;
    setDiagLoading(true);
    setDiagError(null);
    try {
      const res = await fetch('/api/chat/diagnose', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: q })
      });
      if (!res.ok) throw new Error(`HTTP error ${res.status}`);
      const data = await res.json();
      setDiagResult(data);
    } catch (err) {
      setDiagError(err.message || 'Failed to execute diagnostic query');
    } finally {
      setDiagLoading(false);
    }
  };

  // 5. Handle Learning Queue Resolve
  const handleResolveQuestion = async (itemId) => {
    if (!verifiedAnswerText.trim()) {
      alert('Please provide a verified answer.');
      return;
    }

    try {
      await resolveLearningQueueItem(itemId, {
        verified_answer: verifiedAnswerText,
        added_source: verifiedSourceText || 'College Administration',
        index_to_chroma: true
      });
      setResolvingId(null);
      setVerifiedAnswerText('');
      loadLearningQueue();
    } catch (err) {
      alert(`Failed to resolve question: ${err.message}`);
    }
  };

  // 6. Handle Learning Queue Ignore
  const handleIgnoreQuestion = async (itemId) => {
    try {
      await ignoreLearningQueueItem(itemId);
      loadLearningQueue();
    } catch (err) {
      alert(`Failed to ignore question: ${err.message}`);
    }
  };

  // 7. Handle Manual Entry
  const handleManualSubmit = async (e) => {
    e.preventDefault();
    setManualStatus(null);
    try {
      if (manualType === 'notice') {
        await createManualNotice({
          title: manualForm.title,
          category: manualForm.category,
          content: manualForm.description,
          target_course: manualForm.target_course,
          target_department: 'ALL',
          target_semester: manualForm.target_semester,
          date: manualForm.date,
          deadline: manualForm.deadline || null,
          source: manualForm.source,
          source_type: 'Notice Board',
          is_approved: 1
        });
      } else {
        await createManualEvent({
          title: manualForm.title,
          description: manualForm.description,
          date: manualForm.date,
          time: manualForm.time,
          venue: manualForm.venue,
          organizer: manualForm.organizer,
          target_course: manualForm.target_course,
          target_department: 'ALL',
          target_semester: manualForm.target_semester,
          registration_deadline: manualForm.deadline || null,
          source: manualForm.source,
          is_approved: 1
        });
      }
      setManualStatus({ type: 'success', message: `${manualType === 'notice' ? 'Notice' : 'Event'} successfully created!` });
      setManualForm({ ...manualForm, title: '', description: '' });
    } catch (err) {
      setManualStatus({ type: 'error', message: err.message });
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Top Header */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-xs">
        <div className="flex items-center gap-3.5">
          <img 
            src="/safibot-logo.svg" 
            alt="SafiBot Logo" 
            className="w-12 h-12 object-contain rounded-xl shrink-0" 
          />
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-xl font-bold text-slate-900">Admin Control Panel</h2>
              <span className="text-[10px] font-bold bg-slate-900 text-white px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                Role: Admin
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              Manage official college knowledge, documents, announcements, and continuous learning
            </p>
          </div>
        </div>

        {/* Section Tabs */}
        <div className="bg-slate-100 p-1 rounded-xl flex flex-wrap items-center gap-1 self-start sm:self-auto">
          <button
            onClick={() => setActiveSection('whatsapp')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeSection === 'whatsapp' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Announcement Parser
          </button>
          <button
            onClick={() => setActiveSection('pdf')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeSection === 'pdf' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Upload Documents
          </button>
          <button
            onClick={() => setActiveSection('website')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeSection === 'website' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Website Ingestion
          </button>
          <button
            onClick={() => setActiveSection('learning')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeSection === 'learning' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Knowledge Improvement
          </button>
          <button
            onClick={() => setActiveSection('manual')}
            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
              activeSection === 'manual' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Create Notice/Event
          </button>
        </div>
      </div>

      {/* SECTION 1: WhatsApp Announcement Ingestion */}
      {activeSection === 'whatsapp' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4 shadow-xs">
            <div className="flex items-center justify-between">
              <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                <MessageSquareCode className="w-4 h-4 text-emerald-600" />
                <span>Paste Announcement Text</span>
              </h3>
              <span className="text-[11px] text-slate-500">Unstructured WhatsApp / Notice Text</span>
            </div>

            <textarea
              rows={6}
              value={rawText}
              onChange={(e) => setRawText(e.target.value)}
              placeholder="e.g. Python workshop tomorrow at 2 PM in Lab 3. BCA students can participate..."
              className="w-full bg-slate-50 border border-slate-300 rounded-xl p-3.5 text-xs text-slate-800 placeholder-slate-400 focus:outline-hidden focus:ring-2 focus:ring-emerald-500 focus:bg-white font-mono leading-relaxed"
            />

            <button
              onClick={handleExtract}
              disabled={extracting || !rawText.trim()}
              className="w-full bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white text-xs font-semibold py-2.5 rounded-xl flex items-center justify-center gap-2 cursor-pointer transition-colors"
            >
              <Sparkles className="w-4 h-4 text-amber-400" />
              <span>{extracting ? 'Extracting Fields with LLM...' : 'Extract Fields with SafiBot'}</span>
            </button>

            {publishStatus && (
              <div
                className={`p-3.5 rounded-xl border text-xs flex items-center gap-2 ${
                  publishStatus.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'
                }`}
              >
                <CheckCircle2 className="w-4 h-4 shrink-0" />
                <span>{publishStatus.message}</span>
              </div>
            )}
          </div>

          {/* Extracted Preview & Approval */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4 shadow-xs">
            <h3 className="font-bold text-slate-900 text-sm flex items-center justify-between">
              <span>Admin Review & Approval</span>
              {extractedData && (
                <span className="text-[10px] bg-emerald-100 text-emerald-800 font-semibold px-2 py-0.5 rounded-full uppercase">
                  Ready to Publish
                </span>
              )}
            </h3>

            {extractedData ? (
              <div className="space-y-3 bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs">
                <div>
                  <span className="text-slate-500 font-semibold block mb-0.5">Title</span>
                  <input
                    type="text"
                    value={extractedData.title}
                    onChange={(e) => setExtractedData({ ...extractedData, title: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs font-medium text-slate-800"
                  />
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-slate-500 font-semibold block mb-0.5">Type</span>
                    <select
                      value={extractedData.type}
                      onChange={(e) => setExtractedData({ ...extractedData, type: e.target.value })}
                      className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs"
                    >
                      <option value="event">Event</option>
                      <option value="notice">Notice</option>
                    </select>
                  </div>
                  <div>
                    <span className="text-slate-500 font-semibold block mb-0.5">Target Course</span>
                    <input
                      type="text"
                      value={extractedData.target_course}
                      onChange={(e) => setExtractedData({ ...extractedData, target_course: e.target.value })}
                      className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div>
                    <span className="text-slate-500 font-semibold block mb-0.5">Date</span>
                    <input
                      type="text"
                      value={extractedData.date || ''}
                      onChange={(e) => setExtractedData({ ...extractedData, date: e.target.value })}
                      className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs"
                    />
                  </div>
                  <div>
                    <span className="text-slate-500 font-semibold block mb-0.5">Time</span>
                    <input
                      type="text"
                      value={extractedData.time || ''}
                      onChange={(e) => setExtractedData({ ...extractedData, time: e.target.value })}
                      className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs"
                    />
                  </div>
                </div>

                <div>
                  <span className="text-slate-500 font-semibold block mb-0.5">Venue</span>
                  <input
                    type="text"
                    value={extractedData.venue || ''}
                    onChange={(e) => setExtractedData({ ...extractedData, venue: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs"
                  />
                </div>

                <div>
                  <span className="text-slate-500 font-semibold block mb-0.5">Registration Deadline</span>
                  <input
                    type="text"
                    value={extractedData.registration_deadline || ''}
                    onChange={(e) => setExtractedData({ ...extractedData, registration_deadline: e.target.value })}
                    className="w-full bg-white border border-slate-300 rounded-lg p-2 text-xs"
                  />
                </div>

                <button
                  onClick={handlePublish}
                  className="w-full mt-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold py-2.5 rounded-xl flex items-center justify-center gap-2 cursor-pointer transition-colors shadow-sm"
                >
                  <Send className="w-4 h-4" />
                  <span>Approve & Publish Officially</span>
                </button>
              </div>
            ) : (
              <div className="h-64 flex flex-col items-center justify-center border-2 border-dashed border-slate-200 rounded-xl text-center p-6 text-slate-400">
                <FileText className="w-8 h-8 mb-2 opacity-50" />
                <p className="text-xs">Paste an announcement on the left and click "Extract Fields" to review.</p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SECTION 2: PDF Upload & Processing */}
      {activeSection === 'pdf' && (
        <div className="max-w-2xl mx-auto bg-white rounded-2xl border border-slate-200 p-6 space-y-5 shadow-xs">
          <div>
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <UploadCloud className="w-5 h-5 text-emerald-600" />
              <span>Official Academic PDF Ingestion (PyMuPDF + ChromaDB)</span>
            </h3>
            <p className="text-xs text-slate-500 mt-1">
              Uploads original documents intact, vectorizes page chunks into ChromaDB, and extracts timetable rows into SQLite.
            </p>
          </div>

          <form onSubmit={handlePdfSubmit} className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Select PDF File *</label>
              <input
                type="file"
                accept=".pdf"
                onChange={(e) => setPdfFile(e.target.files[0])}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs file:mr-4 file:py-1 file:px-3 file:rounded-md file:border-0 file:text-xs file:font-semibold file:bg-emerald-600 file:text-white hover:file:bg-emerald-700 cursor-pointer"
              />
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Document Title *</label>
              <input
                type="text"
                value={pdfTitle}
                onChange={(e) => setPdfTitle(e.target.value)}
                placeholder="e.g. BCA Semester 3 Data Structures Syllabus"
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2 text-xs"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Document Type</label>
                <select
                  value={docType}
                  onChange={(e) => setDocType(e.target.value)}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2 text-xs"
                >
                  <option value="syllabus">Syllabus</option>
                  <option value="exam_timetable">Exam Timetable</option>
                  <option value="class_timetable">Class Timetable</option>
                  <option value="academic_calendar">Academic Calendar</option>
                  <option value="regulations">College Regulations</option>
                  <option value="prospectus">Prospectus</option>
                </select>
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Course</label>
                <input
                  type="text"
                  value={pdfCourse}
                  onChange={(e) => setPdfCourse(e.target.value)}
                  placeholder="e.g. BBA or BCA or ALL"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2 text-xs"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Semester (Optional)</label>
                <input
                  type="number"
                  value={pdfSem}
                  onChange={(e) => setPdfSem(e.target.value)}
                  placeholder="e.g. 3"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2 text-xs"
                />
              </div>

              <div>
                <label className="text-xs font-semibold text-slate-700 block mb-1">Department</label>
                <input
                  type="text"
                  value={pdfDept}
                  onChange={(e) => setPdfDept(e.target.value)}
                  placeholder="e.g. Computer Applications"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2 text-xs"
                />
              </div>
            </div>

            <div>
              <label className="text-xs font-semibold text-slate-700 block mb-1">Official Source / Issuing Authority</label>
              <input
                type="text"
                value={pdfSource}
                onChange={(e) => setPdfSource(e.target.value)}
                placeholder="e.g. Office of the Controller of Examinations"
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5 text-xs"
              />
            </div>

            <button
              type="submit"
              disabled={uploading || !pdfFile || !pdfTitle}
              className="w-full bg-emerald-600 hover:bg-emerald-700 disabled:opacity-50 text-white text-xs font-semibold py-3 rounded-xl flex items-center justify-center gap-2 cursor-pointer transition-colors shadow-sm"
            >
              <UploadCloud className="w-4 h-4" />
              <span>{uploading ? 'Processing PDF & Vectorizing...' : 'Upload & Process with PyMuPDF'}</span>
            </button>
          </form>

          {uploadSuccess && (
            <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{uploadSuccess}</span>
            </div>
          )}
        </div>
      )}

      {/* SECTION 3: College Website Ingestion */}
      {activeSection === 'website' && (
        <div className="max-w-2xl mx-auto bg-white rounded-2xl border border-slate-200 p-6 space-y-5 shadow-xs">
          <div className="flex items-center gap-3 pb-4 border-b border-slate-100">
            <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-700 flex items-center justify-center">
              <Globe className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-base">College Website Knowledge Synchronization</h3>
              <p className="text-xs text-slate-500">
                Synchronizes verified information from official website: <span className="font-semibold text-teal-700">https://sias.edu.in/</span>
              </p>
            </div>
          </div>

          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs text-slate-600 space-y-2">
            <p className="font-semibold text-slate-800">Approved Public Target Pages:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Homepage: Autonomy status, NAAC grade, Vision & Trust details</li>
              <li>Admission Portal: 27 Academic Programmes (UG, PG, ITEP, PhD)</li>
              <li>Facilities: Campus infrastructure, Labs, ICT classrooms, Sports</li>
              <li>Library & Information Centre: OPAC, Plagiarism CheckerX, timings</li>
              <li>Student Support Zone: Advisory scheme, Scholarships, Placement Cell</li>
            </ul>
          </div>

          <button
            onClick={handleSyncWebsite}
            disabled={syncing}
            className="w-full bg-slate-900 hover:bg-slate-800 disabled:opacity-50 text-white text-xs font-semibold py-3 rounded-xl flex items-center justify-center gap-2 cursor-pointer transition-colors shadow-sm"
          >
            <RefreshCw className={`w-4 h-4 text-emerald-400 ${syncing ? 'animate-spin' : ''}`} />
            <span>{syncing ? 'Fetching & Synchronizing SIAS Website...' : 'SYNC COLLEGE WEBSITE NOW'}</span>
          </button>

          {syncResult && (
            <div
              className={`p-4 rounded-xl border text-xs ${
                syncResult.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-900' : 'bg-red-50 border-red-200 text-red-900'
              }`}
            >
              {syncResult.type === 'success' ? (
                <div className="space-y-2">
                  <div className="font-bold flex items-center gap-1.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span>{syncResult.data.message}</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-emerald-200 text-center font-mono">
                    <div className="bg-white p-2 rounded-lg">
                      <div className="text-base font-bold text-emerald-700">{syncResult.data.programmes_updated}</div>
                      <div className="text-[10px] text-slate-500">Programmes</div>
                    </div>
                    <div className="bg-white p-2 rounded-lg">
                      <div className="text-base font-bold text-emerald-700">{syncResult.data.departments_updated}</div>
                      <div className="text-[10px] text-slate-500">Departments</div>
                    </div>
                    <div className="bg-white p-2 rounded-lg">
                      <div className="text-base font-bold text-emerald-700">{syncResult.data.faculty_updated}</div>
                      <div className="text-[10px] text-slate-500">Faculty/HODs</div>
                    </div>
                    <div className="bg-white p-2 rounded-lg">
                      <div className="text-base font-bold text-emerald-700">{syncResult.data.chunks_indexed}</div>
                      <div className="text-[10px] text-slate-500">Chroma Chunks</div>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-2">
                  <AlertCircle className="w-4 h-4 shrink-0 text-red-600" />
                  <span>{syncResult.message}</span>
                </div>
              )}
            </div>
          )}

          {/* Interactive Retrieval Diagnostic Console (Section 4) */}
          <div className="mt-8 pt-6 border-t border-slate-200">
            <div className="flex items-center justify-between mb-3">
              <div>
                <h4 className="font-bold text-slate-900 text-sm flex items-center gap-2">
                  <Search className="w-4 h-4 text-emerald-600" />
                  Website Knowledge Diagnostic & Query Router Tester
                </h4>
                <p className="text-xs text-slate-500 mt-0.5">
                  Inspect the internal retrieval pipeline: Question &rarr; Intent &rarr; DB Query / Retrieval Method &rarr; Retrieved Records &rarr; Sources &rarr; Answer.
                </p>
              </div>
            </div>

            {/* Quick Test Presets */}
            <div className="flex flex-wrap gap-1.5 mb-3">
              <span className="text-[11px] font-semibold text-slate-400 self-center mr-1">Presets:</span>
              {[
                "How many UG programmes are available?",
                "What programmes are offered by the Department of Computer Applications?",
                "Who is the HOD of Computer Applications?",
                "What departments are available?",
                "What are the admission requirements?",
                "What facilities does the college provide?",
                "Give me information about the Computer Applications department.",
                "What is the tuition fee structure for aeronautical engineering at SIAS?"
              ].map((preset, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => {
                    setDiagQuery(preset);
                    handleRunDiagnostic(preset);
                  }}
                  className="text-[11px] bg-slate-100 hover:bg-emerald-50 hover:text-emerald-700 text-slate-600 px-2.5 py-1 rounded-md transition-colors border border-slate-200 font-medium"
                >
                  {preset.length > 32 ? preset.slice(0, 32) + '...' : preset}
                </button>
              ))}
            </div>

            {/* Input Form */}
            <div className="flex gap-2">
              <input
                type="text"
                value={diagQuery}
                onChange={(e) => setDiagQuery(e.target.value)}
                placeholder="Enter test question (e.g., What programmes are offered by Computer Applications?)"
                className="flex-1 text-xs border border-slate-300 rounded-xl px-3.5 py-2.5 focus:outline-none focus:ring-2 focus:ring-emerald-500 bg-white"
                onKeyDown={(e) => e.key === 'Enter' && handleRunDiagnostic()}
              />
              <button
                type="button"
                onClick={() => handleRunDiagnostic()}
                disabled={diagLoading}
                className="bg-emerald-700 hover:bg-emerald-800 text-white text-xs font-semibold px-4 py-2.5 rounded-xl transition-all shadow-xs flex items-center gap-1.5 disabled:opacity-50 shrink-0"
              >
                {diagLoading ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Search className="w-3.5 h-3.5" />}
                <span>{diagLoading ? 'Diagnosing...' : 'Test Retrieval'}</span>
              </button>
            </div>

            {/* Diagnostic Output View */}
            {diagError && (
              <div className="mt-3 p-3 bg-rose-50 border border-rose-200 rounded-xl text-rose-700 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{diagError}</span>
              </div>
            )}

            {diagResult && (
              <div className="mt-4 bg-slate-900 text-slate-100 rounded-xl p-4 text-xs font-mono space-y-3 shadow-md border border-slate-800">
                <div className="flex items-center justify-between border-b border-slate-800 pb-2">
                  <span className="text-[11px] font-bold text-emerald-400 uppercase tracking-wider">
                    Pipeline Execution Diagnostic
                  </span>
                  <span className="px-2 py-0.5 rounded text-[10px] bg-emerald-900/60 text-emerald-300 border border-emerald-700">
                    Intent: {diagResult.detected_intent}
                  </span>
                </div>

                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-sans font-semibold">
                    1. Retrieval Method:
                  </div>
                  <div className="text-amber-300 mt-0.5 font-sans font-medium">{diagResult.retrieval_method}</div>
                </div>

                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-sans font-semibold">
                    2. Query Executed:
                  </div>
                  <div className="bg-black/50 p-2 rounded-lg text-emerald-300 mt-1 break-all">
                    {diagResult.query_executed}
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-2 text-[11px]">
                  <div className="bg-slate-800/80 p-2 rounded-lg">
                    <span className="text-slate-400">Structured Records:</span>{' '}
                    <span className="font-bold text-white">
                      {Array.isArray(diagResult.retrieved_records) ? diagResult.retrieved_records.length : 'Object'}
                    </span>
                  </div>
                  <div className="bg-slate-800/80 p-2 rounded-lg">
                    <span className="text-slate-400">ChromaDB Chunks:</span>{' '}
                    <span className="font-bold text-white">{diagResult.retrieved_chunks?.length || 0}</span>
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-sans font-semibold">
                    3. Source URLs:
                  </div>
                  <div className="text-cyan-300 mt-0.5 break-all">
                    {diagResult.source_urls?.length ? diagResult.source_urls.join(', ') : 'None (No fabricated sources)'}
                  </div>
                </div>

                <div>
                  <div className="text-[10px] text-slate-400 uppercase tracking-wider font-sans font-semibold">
                    4. Final Synthesized Answer:
                  </div>
                  <div className="bg-slate-950 p-3 rounded-lg text-slate-200 font-sans whitespace-pre-line mt-1 border border-slate-800">
                    {diagResult.final_answer}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* SECTION 4: Continuous Knowledge Improvement / Learning Queue */}
      {activeSection === 'learning' && (
        <div className="space-y-6">
          
          {/* Header & Stats Banner */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                Unanswered Questions
              </span>
              <div className="text-2xl font-bold text-amber-600 font-mono">
                {queueItems.filter((q) => q.status === 'UNANSWERED').length}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Pending administrative answer verification</p>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                Resolved & Verified
              </span>
              <div className="text-2xl font-bold text-emerald-600 font-mono">
                {queueItems.filter((q) => q.status === 'RESOLVED').length}
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Indexed into SafiBot knowledge base</p>
            </div>

            <div className="bg-white border border-slate-200 rounded-2xl p-4 shadow-xs">
              <span className="text-[11px] font-semibold text-slate-500 uppercase tracking-wider block mb-1">
                Student Feedback Rating
              </span>
              <div className="text-base font-bold text-slate-800 flex items-center gap-3">
                <span className="flex items-center gap-1 text-emerald-600">
                  <ThumbsUp className="w-4 h-4" /> {feedbackStats?.helpful || 0}
                </span>
                <span className="flex items-center gap-1 text-rose-600">
                  <ThumbsDown className="w-4 h-4" /> {feedbackStats?.not_helpful || 0}
                </span>
              </div>
              <p className="text-[11px] text-slate-400 mt-1">Interactive 👍 / 👎 student ratings</p>
            </div>
          </div>

          {/* Learning Queue List */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 space-y-4 shadow-xs">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <HelpCircle className="w-5 h-5 text-amber-500" />
                <h3 className="font-bold text-slate-900 text-sm">Learning Queue (Controlled Self-Learning)</h3>
              </div>
              <button
                onClick={loadLearningQueue}
                className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1 cursor-pointer"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${queueLoading ? 'animate-spin' : ''}`} />
                <span>Refresh</span>
              </button>
            </div>

            {queueItems.length === 0 ? (
              <div className="p-8 text-center text-slate-400 text-xs">
                No questions currently in the learning queue.
              </div>
            ) : (
              <div className="space-y-3">
                {queueItems.map((item) => (
                  <div
                    key={item.id}
                    className={`p-4 rounded-xl border text-xs space-y-2 transition-all ${
                      item.status === 'UNANSWERED'
                        ? 'bg-amber-50/50 border-amber-200'
                        : item.status === 'RESOLVED'
                        ? 'bg-emerald-50/50 border-emerald-200'
                        : 'bg-slate-50 border-slate-200 opacity-60'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div className="font-semibold text-slate-900 text-sm">
                        "{item.question}"
                      </div>
                      <span
                        className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider shrink-0 ${
                          item.status === 'UNANSWERED'
                            ? 'bg-amber-100 text-amber-800'
                            : item.status === 'RESOLVED'
                            ? 'bg-emerald-100 text-emerald-800'
                            : 'bg-slate-200 text-slate-700'
                        }`}
                      >
                        {item.status}
                      </span>
                    </div>

                    <div className="text-[11px] text-slate-500 flex items-center gap-3">
                      <span>Asked by: <strong className="text-slate-700">{item.user_id || 'Anonymous'}</strong></span>
                      <span>•</span>
                      <span>{item.timestamp}</span>
                    </div>

                    {item.status === 'RESOLVED' && (
                      <div className="bg-white p-3 rounded-lg border border-emerald-200 text-xs mt-2">
                        <span className="font-bold text-emerald-900 block mb-0.5">Verified Answer:</span>
                        <p className="text-slate-700">{item.verified_answer}</p>
                        <div className="text-[10px] text-slate-500 mt-1">
                          Source: {item.added_source} • Resolved by: {item.resolved_by}
                        </div>
                      </div>
                    )}

                    {/* Actions for Unanswered Item */}
                    {item.status === 'UNANSWERED' && (
                      <div className="pt-2">
                        {resolvingId === item.id ? (
                          <div className="bg-white p-3.5 rounded-xl border border-slate-200 space-y-2.5 mt-2">
                            <span className="font-bold text-xs text-slate-900 block">Provide Verified Answer:</span>
                            <textarea
                              rows={3}
                              value={verifiedAnswerText}
                              onChange={(e) => setVerifiedAnswerText(e.target.value)}
                              placeholder="Type official verified answer to be indexed into SafiBot..."
                              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2.5 text-xs text-slate-800"
                            />
                            <input
                              type="text"
                              value={verifiedSourceText}
                              onChange={(e) => setVerifiedSourceText(e.target.value)}
                              placeholder="Official Source (e.g. Transportation Office)"
                              className="w-full bg-slate-50 border border-slate-300 rounded-lg p-2 text-xs"
                            />
                            <div className="flex items-center gap-2 pt-1">
                              <button
                                onClick={() => handleResolveQuestion(item.id)}
                                className="px-3.5 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold cursor-pointer"
                              >
                                Save & Index Knowledge
                              </button>
                              <button
                                onClick={() => setResolvingId(null)}
                                className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 rounded-lg text-xs font-semibold cursor-pointer"
                              >
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center gap-2">
                            <button
                              onClick={() => {
                                setResolvingId(item.id);
                                setVerifiedAnswerText('');
                              }}
                              className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-lg flex items-center gap-1.5 cursor-pointer"
                            >
                              <Check className="w-3.5 h-3.5" />
                              <span>Add Verified Answer</span>
                            </button>
                            <button
                              onClick={() => handleIgnoreQuestion(item.id)}
                              className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg flex items-center gap-1.5 cursor-pointer"
                            >
                              <X className="w-3.5 h-3.5" />
                              <span>Ignore</span>
                            </button>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* SECTION 5: Manual Notice / Event Entry */}
      {activeSection === 'manual' && (
        <div className="max-w-2xl mx-auto bg-white rounded-2xl border border-slate-200 p-6 space-y-4 shadow-xs">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <h3 className="font-bold text-slate-900 text-sm flex items-center gap-2">
              <Calendar className="w-4 h-4 text-emerald-600" />
              <span>Direct Event & Notice Publishing</span>
            </h3>
            <div className="flex items-center gap-1 bg-slate-100 p-1 rounded-lg text-xs">
              <button
                type="button"
                onClick={() => setManualType('notice')}
                className={`px-2.5 py-1 rounded-md font-semibold cursor-pointer ${manualType === 'notice' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600'}`}
              >
                Notice
              </button>
              <button
                type="button"
                onClick={() => setManualType('event')}
                className={`px-2.5 py-1 rounded-md font-semibold cursor-pointer ${manualType === 'event' ? 'bg-white text-slate-900 shadow-2xs' : 'text-slate-600'}`}
              >
                Event
              </button>
            </div>
          </div>

          <form onSubmit={handleManualSubmit} className="space-y-3 text-xs">
            <div>
              <label className="font-semibold text-slate-700 block mb-1">Title *</label>
              <input
                type="text"
                required
                value={manualForm.title}
                onChange={(e) => setManualForm({ ...manualForm, title: e.target.value })}
                placeholder={manualType === 'notice' ? 'e.g. End Semester Exam Registration Notice' : 'e.g. Inter-Collegiate Hackathon 2026'}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5"
              />
            </div>

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Content / Description *</label>
              <textarea
                rows={3}
                required
                value={manualForm.description}
                onChange={(e) => setManualForm({ ...manualForm, description: e.target.value })}
                placeholder="Details of the official notice or event..."
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2.5"
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Target Course</label>
                <input
                  type="text"
                  value={manualForm.target_course}
                  onChange={(e) => setManualForm({ ...manualForm, target_course: e.target.value })}
                  placeholder="e.g. BCA or ALL"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Target Semester</label>
                <input
                  type="text"
                  value={manualForm.target_semester}
                  onChange={(e) => setManualForm({ ...manualForm, target_semester: e.target.value })}
                  placeholder="e.g. 3 or ALL"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Date</label>
                <input
                  type="text"
                  value={manualForm.date}
                  onChange={(e) => setManualForm({ ...manualForm, date: e.target.value })}
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2"
                />
              </div>
              <div>
                <label className="font-semibold text-slate-700 block mb-1">Deadline / Last Date</label>
                <input
                  type="text"
                  value={manualForm.deadline}
                  onChange={(e) => setManualForm({ ...manualForm, deadline: e.target.value })}
                  placeholder="e.g. 2026-10-25"
                  className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2"
                />
              </div>
            </div>

            {manualType === 'event' && (
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Time</label>
                  <input
                    type="text"
                    value={manualForm.time}
                    onChange={(e) => setManualForm({ ...manualForm, time: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2"
                  />
                </div>
                <div>
                  <label className="font-semibold text-slate-700 block mb-1">Venue</label>
                  <input
                    type="text"
                    value={manualForm.venue}
                    onChange={(e) => setManualForm({ ...manualForm, venue: e.target.value })}
                    className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2"
                  />
                </div>
              </div>
            )}

            <div>
              <label className="font-semibold text-slate-700 block mb-1">Source / Issuing Department</label>
              <input
                type="text"
                value={manualForm.source}
                onChange={(e) => setManualForm({ ...manualForm, source: e.target.value })}
                className="w-full bg-slate-50 border border-slate-300 rounded-xl p-2"
              />
            </div>

            <button
              type="submit"
              className="w-full bg-emerald-600 hover:bg-emerald-700 text-white font-semibold py-2.5 rounded-xl cursor-pointer transition-colors shadow-sm"
            >
              Publish {manualType === 'notice' ? 'Notice' : 'Event'}
            </button>
          </form>

          {manualStatus && (
            <div
              className={`p-3 rounded-xl border text-xs flex items-center gap-2 ${
                manualStatus.type === 'success' ? 'bg-emerald-50 border-emerald-200 text-emerald-800' : 'bg-red-50 border-red-200 text-red-800'
              }`}
            >
              <CheckCircle2 className="w-4 h-4 shrink-0" />
              <span>{manualStatus.message}</span>
            </div>
          )}
        </div>
      )}

    </div>
  );
}
