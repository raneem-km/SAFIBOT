import React from 'react';
import { Bot, User, Shield, BookOpen, LayoutDashboard, MessageSquare, LogOut, UserPlus, LogIn, Compass } from 'lucide-react';

export default function Navbar({
  currentUser,
  currentTab,
  setTab,
  onLogout
}) {
  const isStudent = currentUser && currentUser.role === 'STUDENT';
  const isAdmin = currentUser && currentUser.role === 'ADMIN';
  const isGuest = !currentUser || currentUser.role === 'GUEST' || currentUser.id === 'guest';

  return (
    <header className="bg-white border-b border-slate-200 sticky top-0 z-50 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Branding */}
          <div
            className="flex items-center space-x-3 cursor-pointer"
            onClick={() => setTab(isAdmin ? 'admin' : 'dashboard')}
          >
            <img 
              src="/safibot-logo.svg" 
              alt="SafiBot Logo" 
              className="w-10 h-10 object-contain rounded-lg shrink-0" 
            />
            <div>
              <div className="flex items-center space-x-2">
                <span className="font-bold text-xl text-slate-900 tracking-tight">SafiBot</span>
                <span className="text-[11px] font-semibold bg-emerald-100 text-emerald-800 px-2 py-0.5 rounded-full uppercase tracking-wider">
                  Autonomous
                </span>
              </div>
              <p className="text-xs text-slate-500 hidden sm:block">SAFI College Information & Academic Assistant</p>
            </div>
          </div>

          {/* Navigation Links */}
          <nav className="flex items-center space-x-1 sm:space-x-2">
            
            {/* Authenticated Student Navigation */}
            {isStudent && (
              <>
                <button
                  onClick={() => setTab('dashboard')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                    currentTab === 'dashboard'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  <span className="hidden md:inline">Dashboard</span>
                </button>

                <button
                  onClick={() => setTab('chat')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                    currentTab === 'chat'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <MessageSquare className="w-4 h-4" />
                  <span className="hidden md:inline">Chatbot</span>
                </button>

                <button
                  onClick={() => setTab('documents')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                    currentTab === 'documents'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <BookOpen className="w-4 h-4" />
                  <span className="hidden md:inline">Documents</span>
                </button>

                <button
                  onClick={() => setTab('profile')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                    currentTab === 'profile'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <User className="w-4 h-4" />
                  <span className="hidden md:inline">Profile</span>
                </button>
              </>
            )}

            {/* Admin Navigation */}
            {isAdmin && (
              <>
                <button
                  onClick={() => setTab('admin')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                    currentTab === 'admin'
                      ? 'bg-slate-900 text-white'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Shield className="w-4 h-4" />
                  <span>Admin Panel</span>
                </button>

                <button
                  onClick={() => setTab('documents')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                    currentTab === 'documents'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <BookOpen className="w-4 h-4" />
                  <span>Documents</span>
                </button>

                <button
                  onClick={() => setTab('chat')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                    currentTab === 'chat'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <MessageSquare className="w-4 h-4" />
                  <span>Test Bot</span>
                </button>
              </>
            )}

            {/* Guest Navigation */}
            {isGuest && (
              <>
                <button
                  onClick={() => setTab('dashboard')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                    currentTab === 'dashboard'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <LayoutDashboard className="w-4 h-4" />
                  <span className="hidden md:inline">Dashboard</span>
                </button>

                <button
                  onClick={() => setTab('chat')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                    currentTab === 'chat'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <MessageSquare className="w-4 h-4" />
                  <span className="hidden md:inline">Chatbot</span>
                </button>

                <button
                  onClick={() => setTab('documents')}
                  className={`flex items-center space-x-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors cursor-pointer ${
                    currentTab === 'documents'
                      ? 'bg-emerald-50 text-emerald-700'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <BookOpen className="w-4 h-4" />
                  <span className="hidden md:inline">Documents</span>
                </button>
              </>
            )}

          </nav>

          {/* User Badge & Actions */}
          <div className="flex items-center space-x-3 border-l border-slate-200 pl-3">
            
            {/* Student Logged In */}
            {isStudent && (
              <>
                <div className="hidden lg:flex flex-col text-right">
                  <span className="text-xs font-semibold text-slate-800 leading-tight">
                    {currentUser.name}
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">
                    Adm: {currentUser.admission_number || currentUser.id} | Roll: {currentUser.roll_number || 'N/A'}
                  </span>
                </div>

                <button
                  onClick={onLogout}
                  title="Sign out"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </>
            )}

            {/* Admin Logged In */}
            {isAdmin && (
              <>
                <div className="hidden sm:flex items-center gap-1.5 bg-slate-900 text-white text-[11px] font-semibold px-2.5 py-1 rounded-lg">
                  <Shield className="w-3 h-3 text-emerald-400" />
                  <span>System Administrator</span>
                </div>

                <button
                  onClick={onLogout}
                  title="Sign out"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors cursor-pointer"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </>
            )}

            {/* Guest Mode Controls */}
            {isGuest && (
              <div className="flex items-center gap-2">
                <span className="hidden sm:inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200">
                  <Compass className="w-3.5 h-3.5 text-amber-600" />
                  <span>Guest Mode</span>
                </span>

                <button
                  onClick={() => setTab('login')}
                  className={`flex items-center space-x-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold transition-colors cursor-pointer ${
                    currentTab === 'login'
                      ? 'bg-emerald-600 text-white'
                      : 'bg-emerald-50 text-emerald-700 hover:bg-emerald-100 border border-emerald-200'
                  }`}
                >
                  <LogIn className="w-3.5 h-3.5" />
                  <span>Sign In</span>
                </button>

                <button
                  onClick={() => setTab('register')}
                  className="hidden md:flex items-center space-x-1 px-2.5 py-1.5 rounded-lg text-xs font-semibold text-slate-600 hover:text-slate-900 hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  <UserPlus className="w-3.5 h-3.5" />
                  <span>Register</span>
                </button>

                <button
                  onClick={() => setTab('admin-login')}
                  title="Admin Portal"
                  className="p-1.5 rounded-lg text-slate-400 hover:text-slate-800 hover:bg-slate-100 transition-colors cursor-pointer"
                >
                  <Shield className="w-3.5 h-3.5" />
                </button>
              </div>
            )}

          </div>

        </div>
      </div>
    </header>
  );
}
