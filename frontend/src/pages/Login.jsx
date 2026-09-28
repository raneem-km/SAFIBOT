import React, { useState } from 'react';
import { Bot, LogIn, Lock, Mail, ArrowRight, Shield, AlertCircle, Compass } from 'lucide-react';
import { loginStudent } from '../services/api';

export default function Login({ onLoginSuccess, onNavigateRegister, onNavigateAdminLogin, onGuestLogin }) {
  const [identifier, setIdentifier] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!identifier.trim() || !password.trim()) {
      setError('Please provide your Email or Admission Number and Password.');
      return;
    }
    setError('');
    setLoading(true);

    try {
      const data = await loginStudent(identifier, password);
      onLoginSuccess(data.user);
    } catch (err) {
      setError(err.message || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto my-8 p-6 sm:p-8 bg-white border border-slate-200 rounded-2xl shadow-xl shadow-slate-200/50">
      
      {/* Header */}
      <div className="text-center mb-6">
        <img 
          src="/safibot-logo.svg" 
          alt="SafiBot Logo" 
          className="w-20 h-20 mx-auto object-contain mb-3 drop-shadow-md" 
        />
        <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Student Portal Login</h2>
        <p className="text-xs text-slate-500 mt-1">
          Access your personalized SafiBot dashboard, timetable, and documents
        </p>
      </div>

      {/* Error alert */}
      {error && (
        <div className="mb-4 p-3.5 bg-rose-50 border border-rose-200 text-rose-700 rounded-xl text-xs flex items-start gap-2.5">
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}

      {/* Login Form */}
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Email or Admission Number
          </label>
          <div className="relative">
            <Mail className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="text"
              required
              placeholder="e.g. your email or admission number"
              value={identifier}
              onChange={(e) => setIdentifier(e.target.value)}
              className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden transition-all"
            />
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            Password
          </label>
          <div className="relative">
            <Lock className="w-4 h-4 text-slate-400 absolute left-3.5 top-3" />
            <input
              type="password"
              required
              placeholder="Enter your password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full pl-10 pr-3.5 py-2.5 bg-slate-50 border border-slate-300 rounded-xl text-sm text-slate-800 placeholder-slate-400 focus:bg-white focus:ring-2 focus:ring-emerald-500 focus:outline-hidden transition-all"
            />
          </div>
        </div>

        <button
          type="submit"
          disabled={loading}
          className="w-full py-3 px-4 bg-emerald-600 hover:bg-emerald-700 active:bg-emerald-800 text-white text-sm font-semibold rounded-xl shadow-md shadow-emerald-600/25 flex items-center justify-center gap-2 transition-all cursor-pointer disabled:opacity-50"
        >
          {loading ? (
            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          ) : (
            <>
              <LogIn className="w-4 h-4" />
              <span>Log In to Dashboard</span>
            </>
          )}
        </button>
      </form>

      {/* Guest Mode Option */}
      <div className="mt-6 pt-5 border-t border-slate-100">
        <button
          type="button"
          onClick={onGuestLogin}
          className="w-full py-2.5 px-4 bg-slate-50 hover:bg-emerald-50 border border-slate-200 hover:border-emerald-300 text-slate-700 hover:text-emerald-800 text-xs font-semibold rounded-xl flex items-center justify-center gap-2 transition-all cursor-pointer shadow-xs"
        >
          <Compass className="w-4 h-4 text-emerald-600" />
          <span>Explore as Guest (No Login Required)</span>
        </button>
        <p className="text-[11px] text-slate-500 text-center mt-2">
          Ask questions, view college programmes, facilities, and campus circulars.
        </p>
      </div>

      {/* Navigation Footer */}
      <div className="mt-6 pt-4 border-t border-slate-100 flex flex-col gap-2.5 text-center text-xs">
        <p className="text-slate-600">
          New student?{' '}
          <button
            onClick={onNavigateRegister}
            className="font-semibold text-emerald-600 hover:text-emerald-700 underline cursor-pointer"
          >
            Register Student Profile
          </button>
        </p>
        <p className="text-slate-500">
          College Staff or Faculty?{' '}
          <button
            onClick={onNavigateAdminLogin}
            className="font-semibold text-slate-700 hover:text-slate-900 inline-flex items-center gap-1 cursor-pointer"
          >
            <Shield className="w-3 h-3 text-slate-600" />
            <span>Admin Secure Login</span>
          </button>
        </p>
      </div>

    </div>
  );
}
