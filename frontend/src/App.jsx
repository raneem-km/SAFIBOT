import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import StudentDashboard from './pages/StudentDashboard';
import Chatbot from './pages/Chatbot';
import DocumentsView from './pages/DocumentsView';
import AdminPanel from './pages/AdminPanel';
import Login from './pages/Login';
import Register from './pages/Register';
import AdminLogin from './pages/AdminLogin';
import StudentProfile from './pages/StudentProfile';
import { getAuthUser, clearAuth } from './services/api';

const GUEST_USER = {
  id: 'guest',
  name: 'Guest Visitor',
  role: 'GUEST',
  admission_number: 'GUEST',
  roll_number: 'GUEST',
  email: 'guest@sias.edu.in',
  course: 'ALL',
  department: 'Campus Visitor',
  semester: 1,
  batch: '2024-2027',
  interests: 'College Programmes, Facilities & Admissions'
};

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeStudent, setActiveStudent] = useState(null);
  const [currentTab, setCurrentTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Check existing authenticated session
    const savedUser = getAuthUser();
    if (savedUser) {
      setCurrentUser(savedUser);
      setActiveStudent(savedUser);
      if (savedUser.role === 'ADMIN') {
        setCurrentTab('admin');
      } else {
        setCurrentTab('dashboard');
      }
    } else {
      // Default to Guest Mode for instant exploration
      setCurrentUser(GUEST_USER);
      setActiveStudent(GUEST_USER);
      setCurrentTab('dashboard');
    }
    setLoading(false);
  }, []);

  const handleLoginSuccess = (user) => {
    setCurrentUser(user);
    if (user.role === 'STUDENT') {
      setActiveStudent(user);
      setCurrentTab('dashboard');
    } else if (user.role === 'ADMIN') {
      setCurrentTab('admin');
    }
  };

  const handleGuestLogin = () => {
    setCurrentUser(GUEST_USER);
    setActiveStudent(GUEST_USER);
    setCurrentTab('dashboard');
  };

  const handleLogout = () => {
    clearAuth();
    setCurrentUser(GUEST_USER);
    setActiveStudent(GUEST_USER);
    setCurrentTab('login');
  };

  const handleSetTab = (tab) => {
    // Security Route Guards
    if (tab === 'admin') {
      if (!currentUser || currentUser.role !== 'ADMIN') {
        setCurrentTab('admin-login');
        return;
      }
    }
    if (tab === 'profile') {
      if (!currentUser || currentUser.role === 'GUEST') {
        setCurrentTab('login');
        return;
      }
    }
    setCurrentTab(tab);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <img 
            src="/safibot-logo.svg" 
            alt="SafiBot Logo" 
            className="w-20 h-20 object-contain animate-pulse drop-shadow-md" 
          />
          <div className="w-8 h-8 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-xs font-semibold text-slate-600">Starting SafiBot Application...</p>
        </div>
      </div>
    );
  }

  const effectiveStudent = activeStudent || currentUser || GUEST_USER;

  return (
    <div className="min-h-screen bg-slate-50 text-slate-800 flex flex-col font-sans">
      
      {/* Sticky Navigation */}
      <Navbar
        currentUser={currentUser}
        currentTab={currentTab}
        setTab={handleSetTab}
        onLogout={handleLogout}
      />

      {/* Main Content Area */}
      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
        
        {/* Auth Pages */}
        {currentTab === 'login' && (
          <Login
            onLoginSuccess={handleLoginSuccess}
            onNavigateRegister={() => setCurrentTab('register')}
            onNavigateAdminLogin={() => setCurrentTab('admin-login')}
            onGuestLogin={handleGuestLogin}
          />
        )}

        {currentTab === 'register' && (
          <Register
            onRegisterSuccess={handleLoginSuccess}
            onNavigateLogin={() => setCurrentTab('login')}
          />
        )}

        {currentTab === 'admin-login' && (
          <AdminLogin
            onAdminLoginSuccess={handleLoginSuccess}
            onNavigateStudentLogin={() => setCurrentTab('login')}
          />
        )}

        {/* Student / Guest Pages */}
        {currentTab === 'dashboard' && effectiveStudent && (
          <StudentDashboard
            activeStudent={effectiveStudent}
            setTab={handleSetTab}
          />
        )}

        {currentTab === 'chat' && (
          <Chatbot activeStudent={effectiveStudent} />
        )}

        {currentTab === 'documents' && (
          <DocumentsView activeStudent={effectiveStudent} />
        )}

        {currentTab === 'profile' && effectiveStudent && (
          <StudentProfile
            student={effectiveStudent}
            setTab={handleSetTab}
            onLogout={handleLogout}
          />
        )}

        {/* Admin Panel (Strictly protected) */}
        {currentTab === 'admin' && currentUser?.role === 'ADMIN' && (
          <AdminPanel onDocumentUploaded={() => {}} />
        )}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-slate-200 py-4 text-center text-xs text-slate-500">
        <div className="max-w-7xl mx-auto px-4 flex flex-col sm:flex-row items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <span className="font-bold text-slate-800">SafiBot</span>
            <span>•</span>
            <span>AI + Dual-Storage (SQLite + ChromaDB) Architecture</span>
          </div>
          <div className="text-[11px] text-slate-600">
            SAFI Autonomous College • NAAC A++ (2024–2034)
          </div>
        </div>
      </footer>

    </div>
  );
}
