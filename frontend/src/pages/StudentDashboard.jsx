import React, { useState, useEffect } from 'react';
import { fetchDashboard } from '../services/api';
import NoticeCard from '../components/NoticeCard';
import EventCard from '../components/EventCard';
import { 
  GraduationCap, Calendar, Clock, AlertCircle, Sparkles, BookOpen, 
  MessageSquare, ChevronRight, Terminal, Cpu, Binary, Layers, 
  Award, Briefcase, Zap, ShieldCheck, Building2, User, ExternalLink, Code 
} from 'lucide-react';

const DEPARTMENT_PROFILES = {
  bca: {
    type: 'bca',
    shortName: 'BCA Honours',
    deptName: 'Department of Computer Applications',
    tagline: 'AICTE Approved • Software Engineering, Full-Stack Web Technologies & Cloud Systems',
    heroGradient: 'from-slate-950 via-teal-950 to-emerald-950',
    heroGlow: 'from-emerald-500/15 via-teal-500/10 to-transparent',
    accentText: 'text-emerald-400',
    accentBorder: 'border-emerald-500/30',
    badgeClass: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
    cardBorder: 'hover:border-emerald-400/50',
    hod: {
      name: 'Mr. Muhammed Haneesh K.P',
      designation: 'Head of Department (HOD) & Assistant Professor',
      lab: 'Computer Applications Software Labs 1 & 2',
      email: 'haneesh@sias.edu.in',
    },
    features: [
      { label: 'Lab Terminals', val: '120 High-Speed Dual-OS Terminals' },
      { label: 'Accreditation', val: 'Approved by AICTE & Univ of Calicut' },
      { label: 'Core Domains', val: 'Full-Stack, Python, Cloud & DBMS' },
    ],
    quickActions: [
      { 
        title: 'BCA Practical Lab & Coding', 
        desc: 'Data structures, C++, PHP & Web Practical exercises', 
        query: 'What are the practical lab exercises for BCA Semester 3 and 5?',
        icon: Terminal,
        tag: 'Practical Lab'
      },
      { 
        title: 'Project Submission Desk', 
        desc: 'Mini-project guidelines, guide signoffs & submission dates', 
        query: 'What are the BCA project submission guidelines, deadlines and requirements?',
        icon: Layers,
        tag: 'Academic'
      },
      { 
        title: 'Tech Fest 2026', 
        desc: 'SAFI Innovate Tech Fest organized by Computer Applications', 
        query: 'Give me details about SAFI Innovate Tech Fest 2026 events and registration',
        icon: Zap,
        tag: 'Annual Fest'
      },
      { 
        title: 'BCA Timetable & Electives', 
        desc: 'Calicut University BCA syllabus, regular classes & exam routine', 
        query: 'Show me the official BCA timetable and subjects',
        icon: BookOpen,
        tag: 'Schedule'
      },
    ]
  },

  cs: {
    type: 'cs',
    shortName: 'B.Sc. Computer Science',
    deptName: 'Department of Computer Science',
    tagline: '4-Year Honours with Research • Theoretical Computing, Linux Architecture & Algorithms',
    heroGradient: 'from-slate-950 via-slate-900 to-indigo-950',
    heroGlow: 'from-indigo-500/20 via-blue-500/10 to-transparent',
    accentText: 'text-indigo-400',
    accentBorder: 'border-indigo-500/30',
    badgeClass: 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30',
    cardBorder: 'hover:border-indigo-400/50',
    hod: {
      name: 'Department of Computer Science Faculty Desk',
      designation: 'Head of Department & Research Board',
      lab: 'CS Computing & Systems Architecture Lab',
      email: 'cs@sias.edu.in',
    },
    features: [
      { label: 'Computing Lab', val: 'Dedicated Linux Terminal & Hardware Lab' },
      { label: 'Curriculum', val: '4-Year Honours with Research Track' },
      { label: 'Core Domains', val: 'Algorithms, OS, Systems & C/C++' },
    ],
    quickActions: [
      { 
        title: 'Algorithms & Systems Lab', 
        desc: 'C programming, Linux terminal, discrete mathematics & data structures', 
        query: 'What programming courses and algorithms are taught in BSc Computer Science?',
        icon: Cpu,
        tag: 'Core CS'
      },
      { 
        title: 'Campus Placement Drive', 
        desc: 'Pre-placement aptitude & interview schedules with Infosys & TCS', 
        query: 'Tell me details about the Infosys and TCS campus placement drive for CS students',
        icon: Award,
        tag: 'Placement'
      },
      { 
        title: 'B.Sc. CS Exam Timetable', 
        desc: 'End semester exam dates, subject codes & hall allocations', 
        query: 'What is the examination timetable for BSc Computer Science?',
        icon: Calendar,
        tag: 'Exams'
      },
      { 
        title: 'Research & Honours Track', 
        desc: 'Honours research electives, seminar topics & journal papers', 
        query: 'What are the research project requirements for B.Sc. Computer Science Honours?',
        icon: BookOpen,
        tag: 'Research'
      },
    ]
  },

  ai: {
    type: 'ai',
    shortName: 'B.Sc. Artificial Intelligence',
    deptName: 'Department of Computer Science — AI Division',
    tagline: 'Autonomous AI, Deep Learning, Neural Networks & Cognitive Robotics',
    heroGradient: 'from-slate-950 via-purple-950 to-indigo-950',
    heroGlow: 'from-purple-500/25 via-fuchsia-500/15 to-transparent',
    accentText: 'text-purple-400',
    accentBorder: 'border-purple-500/30',
    badgeClass: 'bg-purple-500/20 text-purple-300 border border-purple-500/30',
    cardBorder: 'hover:border-purple-400/50',
    hod: {
      name: 'AI & Data Science Faculty Board',
      designation: 'Department of Computer Science (AI Division)',
      lab: 'High-Performance GPU AI & Robotics Sandbox',
      email: 'ai@sias.edu.in',
    },
    features: [
      { label: 'AI Hardware', val: 'NVIDIA GPU Accelerated Workstations' },
      { label: 'Frameworks', val: 'PyTorch, TensorFlow, OpenCV, HuggingFace' },
      { label: 'Specialization', val: 'Deep Learning, NLP & Computer Vision' },
    ],
    quickActions: [
      { 
        title: 'Python & Neural Net Hub', 
        desc: 'Machine learning datasets, tensor models & training notebooks', 
        query: 'What machine learning frameworks, Python libraries and models are taught in AI Honours?',
        icon: Binary,
        tag: 'Machine Learning'
      },
      { 
        title: 'GPU Lab & Robotics Desk', 
        desc: 'NVIDIA workstation access, robotics kits & model training specs', 
        query: 'What computing hardware and GPU facilities are available in the college AI lab?',
        icon: Cpu,
        tag: 'GPU Lab'
      },
      { 
        title: 'AI Hackathons & Competitions', 
        desc: 'Inter-college AI challenges, model evaluation & tech prizes', 
        query: 'What AI hackathons and technical competitions can I participate in at SAFI?',
        icon: Zap,
        tag: 'Competitions'
      },
      { 
        title: 'B.Sc. AI Exam Timetable', 
        desc: 'End semester exam dates, ML subjects & examination halls', 
        query: 'What is the examination schedule for B.Sc. Artificial Intelligence Honours?',
        icon: Calendar,
        tag: 'Exams'
      },
    ]
  },

  general: {
    type: 'general',
    shortName: 'General Campus',
    deptName: 'SIAS Academic Department Portal',
    tagline: 'Academic Excellence, Continuous Knowledge & Student Welfare',
    heroGradient: 'from-slate-900 via-slate-800 to-teal-950',
    heroGlow: 'from-emerald-500/15 to-transparent',
    accentText: 'text-emerald-400',
    accentBorder: 'border-emerald-500/30',
    badgeClass: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
    cardBorder: 'hover:border-slate-300',
    hod: {
      name: 'Academic Affairs Board',
      designation: 'College Administrative & Faculty Council',
      lab: 'SIAS Main Academic Complex',
      email: 'info@sias.edu.in',
    },
    features: [
      { label: 'Campus Life', val: '15 UG Honours & 9 PG Departments' },
      { label: 'Affiliation', val: 'University of Calicut & NAAC Accredited' },
      { label: 'Support', val: 'College Scholarship & Placement Cell' },
    ],
    quickActions: [
      { 
        title: 'Ask SafiBot AI', 
        desc: 'Instant official answers regarding college rules, courses and campus', 
        query: 'What are the main rules, programmes and facilities at SAFI college?',
        icon: MessageSquare,
        tag: 'AI Assistant'
      },
      { 
        title: 'College Scholarship Scheme', 
        desc: 'Merit-cum-means scholarship criteria, application & deadlines', 
        query: 'Tell me details about the College Scholarship Scheme and how to apply',
        icon: Award,
        tag: 'Scholarship'
      },
      { 
        title: 'Academic Calendar & Dates', 
        desc: 'Key college dates, working days, examinations and holidays', 
        query: 'What are the important dates and events in the academic calendar?',
        icon: Calendar,
        tag: 'Schedule'
      },
      { 
        title: 'Official Syllabus & PDFs', 
        desc: 'Course curriculum, university regulations and syllabus overview', 
        query: 'How can I access my course syllabus and exam regulations?',
        icon: BookOpen,
        tag: 'Curriculum'
      },
    ]
  }
};

export default function StudentDashboard({ activeStudent, setTab }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!activeStudent) return;
    setLoading(true);
    setError(null);
    const identifier = activeStudent.admission_number || activeStudent.id || 'guest';
    fetchDashboard(identifier)
      .then((res) => {
        setData(res);
        setLoading(false);
      })
      .catch((err) => {
        console.error('Dashboard load error:', err);
        setError(err.message);
        setLoading(false);
      });
  }, [activeStudent]);

  const handleQuickAction = (query) => {
    sessionStorage.setItem('safibot_prefill_query', query);
    setTab('chat');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600"></div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="p-8 text-center bg-white rounded-2xl border border-slate-200 shadow-sm max-w-lg mx-auto my-12">
        <AlertCircle className="w-10 h-10 mx-auto mb-3 text-amber-500" />
        <h3 className="text-base font-semibold text-slate-800 mb-1">Unable to load dashboard</h3>
        <p className="text-xs text-slate-500 mb-4">{error || 'Please check your connection and try again.'}</p>
        <button
          onClick={() => {
            setError(null);
            setLoading(true);
            const identifier = activeStudent?.admission_number || activeStudent?.id || 'guest';
            fetchDashboard(identifier)
              .then((res) => {
                setData(res);
                setLoading(false);
              })
              .catch((err) => {
                setError(err.message);
                setLoading(false);
              });
          }}
          className="px-4 py-2 bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold rounded-xl transition-all cursor-pointer shadow-xs"
        >
          Try Again
        </button>
      </div>
    );
  }

  const student = data?.student || activeStudent || {};
  const notices = data?.notices || [];
  const events = data?.events || [];
  const deadlines = data?.deadlines || [];
  const next_exam = data?.next_exam || null;

  // Determine which specialized department profile applies based on registered student course/department
  const courseStr = `${student.course || ''} ${student.department || ''}`.toLowerCase();
  let currentDeptKey = 'general';
  if (courseStr.includes('artificial intelligence') || courseStr.includes(' ai') || courseStr.includes('ai honours')) {
    currentDeptKey = 'ai';
  } else if (courseStr.includes('computer application') || courseStr.includes('bca')) {
    currentDeptKey = 'bca';
  } else if (courseStr.includes('computer science') || courseStr.includes('bsc cs')) {
    currentDeptKey = 'cs';
  }

  const deptProfile = DEPARTMENT_PROFILES[currentDeptKey] || DEPARTMENT_PROFILES.general;

  return (
    <div className="space-y-6">
      
      {/* Specialized Department Welcome Banner */}
      <div className={`bg-gradient-to-r ${deptProfile.heroGradient} text-white rounded-2xl p-6 sm:p-8 shadow-md relative overflow-hidden transition-all duration-300`}>
        <div className={`absolute right-0 top-0 bottom-0 w-1/2 bg-radial ${deptProfile.heroGlow} pointer-events-none`}></div>
        <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex items-start gap-4">
            <img 
              src="/safibot-logo.svg" 
              alt="SafiBot Logo" 
              className="w-16 h-16 sm:w-20 sm:h-20 object-contain rounded-2xl bg-white/10 p-2 backdrop-blur-xs border border-white/15 shrink-0" 
            />
            <div>
              <div className="flex flex-wrap items-center gap-2 mb-2">
                <span className={`text-xs px-2.5 py-0.5 rounded-full font-medium ${deptProfile.badgeClass}`}>
                  {deptProfile.deptName}
                </span>
                <span className="bg-white/10 text-slate-200 border border-white/10 text-xs px-2.5 py-0.5 rounded-full font-mono">
                  {student.id === 'guest' ? 'Campus Visitor' : `Adm: ${student.admission_number || student.id}`}
                </span>
                {student.roll_number && student.id !== 'guest' && (
                  <span className="bg-white/10 text-slate-200 border border-white/10 text-xs px-2.5 py-0.5 rounded-full font-mono">
                    Roll: {student.roll_number}
                  </span>
                )}
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
                {student.id === 'guest' 
                  ? `Welcome to ${deptProfile.shortName} Portal` 
                  : `Welcome back, ${student.name}`}
              </h2>
              <p className="text-slate-300 text-xs sm:text-sm mt-1 max-w-2xl leading-relaxed">
                {deptProfile.tagline}
              </p>
              {student.id !== 'guest' && (
                <p className="text-slate-400 text-xs mt-2">
                  Enrolled Course: <strong className="text-slate-200">{student.course}</strong> • Semester: <strong className="text-slate-200">{student.semester}</strong> • Batch: <strong className="text-slate-200">{student.batch}</strong>
                </p>
              )}
            </div>
          </div>

          <div className="flex flex-wrap gap-2.5">
            <button
              onClick={() => setTab('chat')}
              className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold flex items-center gap-2 shadow-sm transition-all cursor-pointer"
            >
              <MessageSquare className="w-4 h-4" />
              Ask SafiBot
            </button>
            <button
              onClick={() => setTab('documents')}
              className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 text-white text-xs font-semibold flex items-center gap-2 backdrop-blur-xs transition-all cursor-pointer border border-white/10"
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
              <strong>Browsing as Guest:</strong> You can explore department portals, interact with SafiBot AI, and inspect college circulars. Log in with your student credentials to view your personalized exam timetable.
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

      {/* Department Quick Action Launchpad */}
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Zap className={`w-4 h-4 ${deptProfile.accentText}`} />
            <h3 className="font-bold text-slate-900 text-base">
              {deptProfile.shortName} Quick Launchpad
            </h3>
          </div>
          <span className="text-xs text-slate-500">Interactive Department Hub</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5">
          {deptProfile.quickActions.map((qa, idx) => {
            const IconComponent = qa.icon;
            return (
              <div
                key={idx}
                onClick={() => handleQuickAction(qa.query)}
                className={`bg-white rounded-xl border border-slate-200 p-4 hover:shadow-md transition-all cursor-pointer group flex flex-col justify-between ${deptProfile.cardBorder}`}
              >
                <div>
                  <div className="flex items-center justify-between mb-2.5">
                    <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-700 group-hover:scale-105 transition-transform">
                      <IconComponent className="w-4 h-4" />
                    </div>
                    <span className="text-[10px] font-semibold bg-slate-100 text-slate-600 px-2 py-0.5 rounded-full">
                      {qa.tag}
                    </span>
                  </div>
                  <h4 className="font-bold text-slate-900 text-xs group-hover:text-emerald-700 transition-colors">
                    {qa.title}
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-1 leading-relaxed">
                    {qa.desc}
                  </p>
                </div>
                <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-[11px] font-semibold text-emerald-700 group-hover:translate-x-0.5 transition-transform">
                  <span>Ask SafiBot</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Department Leadership & Laboratory Facility Overview */}
      <div className="bg-white rounded-2xl border border-slate-200 p-5 shadow-xs grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-3">
          <div className="flex items-center gap-2">
            <Building2 className="w-4 h-4 text-slate-600" />
            <h4 className="font-bold text-slate-900 text-sm">
              Department Leadership & Contact Desk
            </h4>
          </div>
          <div className="bg-slate-50 rounded-xl p-4 border border-slate-100 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3">
            <div>
              <h5 className="font-bold text-slate-900 text-xs sm:text-sm">{deptProfile.hod.name}</h5>
              <p className="text-xs text-slate-600 mt-0.5">{deptProfile.hod.designation}</p>
              <p className="text-xs text-slate-500 mt-1 font-mono">Email: {deptProfile.hod.email}</p>
            </div>
            <button
              onClick={() => handleQuickAction(`Who is the HOD and faculty of ${deptProfile.deptName}?`)}
              className="px-3 py-1.5 bg-white border border-slate-200 hover:border-slate-300 text-slate-800 text-xs font-semibold rounded-lg shrink-0 transition-colors cursor-pointer shadow-2xs"
            >
              View Faculty Info
            </button>
          </div>
          <p className="text-xs text-slate-500">
            <strong>Assigned Lab Facility:</strong> {deptProfile.hod.lab}
          </p>
        </div>

        <div className="space-y-2 border-t lg:border-t-0 lg:border-l border-slate-100 lg:pl-6 pt-4 lg:pt-0">
          <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider text-slate-500">
            Infrastructure Highlights
          </h4>
          <div className="space-y-2">
            {deptProfile.features.map((feat, idx) => (
              <div key={idx} className="bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <span className="text-[10px] uppercase font-bold text-slate-500 block">{feat.label}</span>
                <span className="text-xs font-semibold text-slate-800">{feat.val}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

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
                Course: <strong>{next_exam.course}</strong> (Sem {next_exam.semester}) • Time: <strong>{next_exam.time}</strong> • Room: <strong>{next_exam.room}</strong>
              </p>
            </div>
          </div>
          <button
            onClick={() => handleQuickAction(`Show my complete examination timetable for ${student.course || 'my course'}`)}
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
              <h3 className="font-bold text-slate-900 text-lg">Official Notices</h3>
              <span className="text-xs bg-slate-200 text-slate-700 px-2 py-0.5 rounded-full font-semibold">
                {notices.length}
              </span>
            </div>
            <span className="text-xs text-slate-600">Personalized Feed</span>
          </div>

          {notices.length === 0 ? (
            <p className="text-xs text-slate-600 bg-white p-6 rounded-xl border border-slate-200 text-center">
              No specific notices for your department right now.
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
              <h3 className="font-bold text-slate-900 text-lg">Campus & Department Events</h3>
              <span className="text-xs bg-teal-100 text-teal-800 px-2 py-0.5 rounded-full font-semibold">
                {events.length}
              </span>
            </div>
            <span className="text-xs text-slate-600">Eligible Events</span>
          </div>

          {events.length === 0 ? (
            <p className="text-xs text-slate-600 bg-white p-6 rounded-xl border border-slate-200 text-center">
              No events scheduled for your department right now.
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
