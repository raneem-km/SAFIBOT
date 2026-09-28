import React, { useState } from 'react';
import { Shield, Lock, Mail, LogIn, AlertCircle, ArrowLeft, KeyRound } from 'lucide-react';
import { loginAdmin } from '../services/api';

export default function AdminLogin({ onAdminLoginSuccess, onNavigateStudentLogin }) {
  const [identifier, setIdentifier] = useState('admin@sias.edu.in');
  const [password, setPassword] = useState('Admin@Safi2026');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier.trim() || !password.trim()) {
      setError('Please provide administrative credentials.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const data = await loginAdmin(identifier, password);
      onAdminLoginSuccess(data.user);
    } catch (err) {
      setError(err.message || 'Administrative authentication failed. Non-admin accounts are prohibited.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-12 p-6 sm:p-8 bg-white border border-slate-200 rounded-2xl shadow-xl shadow-slate-200/50">
      
      {/* Top Banner */}
      <div className="text-center mb-6">
        <img 
          src="/safibot-logo.svg" 
          alt="SafiBot Logo" 
          className="w-20 h-20 mx-auto object-contain mb-3 drop-shadow-md" 
        />
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Admin Security Portal</h2>
        <p className="text-xs text-slate-500 mt-1">
          Restricted administrative access for college staff & system managers
        </p>
      </div>

      {/* Security alert */}
      <div className="mb-5 p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-[11px] leading-relaxed flex items-start gap-2">
        <KeyRound className="w-4 h-4 shrink-0 text-amber-600 mt-0.5" />
        <div>
          <span className="font-bold">Role-Based Authorization Enforced:</span> Students are strictly prohibited from administrative endpoints. All upload, sync, and publish actions require an admin JWT token.
        </div>
      </div>

      {/* Error alert */}
      {error && (
        <div className="mb-4 p-3.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Admin Email Address
          </label>
          <div className="relative">
            <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              required
              placeholder="e.g. admin@sias.edu.in"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-slate-900 focus:outline-hidden"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Admin Password
          </label>
          <div className="relative">
            <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="password"
              required
              placeholder="Enter admin password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-800 focus:bg-white focus:ring-2 focus:ring-slate-900 focus:outline-hidden"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 px-4 bg-slate-900 hover:bg-slate-800 active:bg-black text-white text-sm font-semibold rounded-xl shadow-md flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <LogIn className="w-4 h-4" />
              <span>Authenticate as Administrator</span>
            </>
          )}
        </button>
      </form>

      {/* Back button */}
      <div className="mt-6 pt-4 border-t border-slate-100 text-center">
        <button
          onClick={onNavigateStudentLogin}
          className="text-xs font-semibold text-slate-600 hover:text-slate-900 inline-flex items-center gap-1 cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Return to Student Login</span>
        </button>
      </div>

    </div>
  );
}
