import React, { useState } from 'react';
import { UserPlus, Lock, Mail, User, Hash, BookOpen, GraduationCap, Building2, Calendar, Sparkles, AlertCircle, ArrowLeft } from 'lucide-react';
import { registerStudent } from '../services/api';

const COURSES = [
  { course: 'BBA', dept: 'Management Studies' },
  { course: 'BCA', dept: 'Computer Applications' },
  { course: 'BCom', dept: 'Commerce' },
  { course: 'BSc Computer Science', dept: 'Computer Science' },
  { course: 'BA English Language & Literature', dept: 'English' },
  { course: 'BA Sociology', dept: 'Sociology' },
  { course: 'BSc Biotechnology', dept: 'Biotechnology' },
  { course: 'BSc Microbiology', dept: 'Microbiology' },
  { course: 'BSc Food Technology', dept: 'Food Technology' },
  { course: 'MSc Computer Science', dept: 'Computer Science' },
  { course: 'MCom', dept: 'Commerce' },
  { course: 'MA Journalism & Mass Communication', dept: 'Journalism' },
];

export default function Register({ onRegisterSuccess, onNavigateLogin }) {
  const [formData, setFormData] = useState({
    name: '',
    roll_number: '',
    admission_number: '',
    email: '',
    password: '',
    course: 'BBA',
    department: 'Management Studies',
    semester: 3,
    batch: '2024-2027',
    interests: '',
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleCourseChange = (e) => {
    const selectedCourse = e.target.value;
    const found = COURSES.find((c) => c.course === selectedCourse);
    setFormData((prev) => ({
      ...prev,
      course: selectedCourse,
      department: found ? found.dept : prev.department,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.name.trim() || !formData.admission_number.trim() || !formData.email.trim() || !formData.password.trim()) {
      setError('Please fill in all mandatory fields.');
      return;
    }
    if (formData.password.length < 6) {
      setError('Password should be at least 6 characters long.');
      return;
    }

    setError('');
    setLoading(true);

    try {
      const data = await registerStudent({
        ...formData,
        roll_number: formData.roll_number.trim() || formData.admission_number.trim(),
        semester: Number(formData.semester),
      });
      onRegisterSuccess(data.user);
    } catch (err) {
      setError(err.message || 'Registration failed. Please check your information.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto my-8 p-6 sm:p-8 bg-white border border-slate-200 rounded-2xl shadow-xl shadow-slate-200/50">
      
      {/* Header */}
      <div className="flex items-center justify-between mb-6 pb-4 border-b border-slate-100">
        <div className="flex items-center gap-3">
          <img 
            src="/safibot-logo.svg" 
            alt="SafiBot Logo" 
            className="w-12 h-12 object-contain rounded-xl drop-shadow-sm shrink-0" 
          />
          <div>
            <h2 className="text-xl font-bold text-slate-900 tracking-tight">Student Registration</h2>
            <p className="text-xs text-slate-500">Create your official SafiBot student account</p>
          </div>
        </div>

        <button
          onClick={onNavigateLogin}
          className="text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1 cursor-pointer"
        >
          <ArrowLeft className="w-4 h-4" />
          <span>Back to Login</span>
        </button>
      </div>

      {/* Error alert */}
      {error && (
        <div className="mb-4 p-3.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Registration Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        
        {/* Full Name & Email */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Full Name *
            </label>
            <div className="relative">
              <User className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                required
                placeholder="e.g. Rahul Menon"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              College Email *
            </label>
            <div className="relative">
              <Mail className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="email"
                required
                placeholder="e.g. rahul@sias.edu.in"
                value={formData.email}
                onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              />
            </div>
          </div>
        </div>

        {/* Admission Number & Roll Number */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Admission Number *
            </label>
            <div className="relative">
              <Hash className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                required
                placeholder="e.g. ADM2024BBA01"
                value={formData.admission_number}
                onChange={(e) => setFormData({ ...formData, admission_number: e.target.value })}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-mono"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Class Roll Number
            </label>
            <div className="relative">
              <Hash className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                placeholder="e.g. BBA-24-01"
                value={formData.roll_number}
                onChange={(e) => setFormData({ ...formData, roll_number: e.target.value })}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden font-mono"
              />
            </div>
          </div>
        </div>

        {/* Password */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Password *
          </label>
          <div className="relative">
            <Lock className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="password"
              required
              placeholder="Create a strong password (minimum 6 characters)"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
            />
          </div>
          <p className="text-[10px] text-slate-400 mt-1">
            🔒 Secure bcrypt hashing: Passwords are encrypted before storage and never kept in plain text.
          </p>
        </div>

        {/* Course & Department */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Academic Programme / Course *
            </label>
            <div className="relative">
              <BookOpen className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <select
                value={formData.course}
                onChange={handleCourseChange}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden cursor-pointer"
              >
                {COURSES.map((c) => (
                  <option key={c.course} value={c.course}>
                    {c.course}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Department
            </label>
            <div className="relative">
              <Building2 className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                value={formData.department}
                onChange={(e) => setFormData({ ...formData, department: e.target.value })}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              />
            </div>
          </div>
        </div>

        {/* Semester & Batch */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Current Semester *
            </label>
            <div className="relative">
              <GraduationCap className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <select
                value={formData.semester}
                onChange={(e) => setFormData({ ...formData, semester: Number(e.target.value) })}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden cursor-pointer"
              >
                {[1, 2, 3, 4, 5, 6].map((s) => (
                  <option key={s} value={s}>
                    Semester {s}
                  </option>
                ))}
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1.5">
              Batch Period *
            </label>
            <div className="relative">
              <Calendar className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
              <input
                type="text"
                required
                placeholder="e.g. 2024-2027"
                value={formData.batch}
                onChange={(e) => setFormData({ ...formData, batch: e.target.value })}
                className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
              />
            </div>
          </div>
        </div>

        {/* Interests */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Academic & Extracurricular Interests
          </label>
          <div className="relative">
            <Sparkles className="w-4 h-4 text-slate-400 absolute left-3 top-3" />
            <input
              type="text"
              placeholder="e.g. Artificial Intelligence, Data Science, Web Design, Sports"
              value={formData.interests}
              onChange={(e) => setFormData({ ...formData, interests: e.target.value })}
              className="w-full pl-9 pr-3 py-2 bg-slate-50 border border-slate-300 rounded-xl text-xs text-slate-800 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden"
            />
          </div>
          <p className="text-[10px] text-slate-400 mt-1">
            Used to recommend relevant college events, workshops, and placement drives.
          </p>
        </div>

        {/* Submit */}
        <div className="pt-2">
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white text-sm font-semibold rounded-xl shadow-md shadow-emerald-600/25 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
          >
            {loading ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <>
                <UserPlus className="w-4 h-4" />
                <span>Create Student Account & Enter Dashboard</span>
              </>
            )}
          </button>
        </div>

      </form>

      {/* Footer */}
      <div className="mt-6 pt-4 border-t border-slate-100 text-center text-xs text-slate-500">
        Already registered?{' '}
        <button
          onClick={onNavigateLogin}
          className="font-semibold text-emerald-600 hover:text-emerald-700 underline cursor-pointer"
        >
          Sign in here
        </button>
      </div>

    </div>
  );
}
