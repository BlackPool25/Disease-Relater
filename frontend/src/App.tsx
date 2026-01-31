/**
 * Disease Visualizer - Main Application Component
 * 
 * Entry point for the disease network visualization application.
 * Sets up routing and the main layout structure.
 */

import { useEffect, useState } from 'react';
import { Routes, Route, Link, useLocation } from 'react-router-dom';
import { API_BASE_URL, API_ENDPOINTS } from './utils/constants';
import { UserInputForm } from './pages';

// API health status indicator
function ApiStatus({ isConnected }: { isConnected: boolean | null }) {
  if (isConnected === null) {
    return (
      <span className="inline-flex items-center gap-1.5 text-slate-400">
        <span className="w-2 h-2 rounded-full bg-slate-400 animate-pulse"></span>
        Connecting...
      </span>
    );
  }
  
  return (
    <span className={`inline-flex items-center gap-1.5 ${isConnected ? 'text-green-400' : 'text-red-400'}`}>
      <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-green-400' : 'bg-red-400'}`}></span>
      {isConnected ? 'API Connected' : 'API Disconnected'}
    </span>
  );
}

// Landing page component
function LandingPage() {
  return (
    <>
      {/* Welcome Card */}
      <div className="glass rounded-xl p-8 mb-8">
        <h2 className="text-2xl font-bold mb-4 gradient-text">
          Welcome to Disease Visualizer
        </h2>
        <p className="text-slate-300 mb-6 max-w-2xl">
          Explore disease relationships and comorbidity patterns through an interactive 
          3D network visualization. Calculate personalized risk scores based on your 
          existing conditions and demographics.
        </p>
        
        {/* Feature Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <div className="w-10 h-10 rounded-lg bg-cyan-500/10 flex items-center justify-center mb-3">
              <svg className="w-5 h-5 text-cyan-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <h3 className="font-semibold text-slate-100 mb-1">Search Diseases</h3>
            <p className="text-sm text-slate-400">
              Find diseases by ICD-10 code or name
            </p>
          </div>
          
          <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
            <div className="w-10 h-10 rounded-lg bg-teal-500/10 flex items-center justify-center mb-3">
              <svg className="w-5 h-5 text-teal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 10l-2 1m0 0l-2-1m2 1v2.5M20 7l-2 1m2-1l-2-1m2 1v2.5M14 4l-2-1-2 1M4 7l2-1M4 7l2 1M4 7v2.5M12 21l-2-1m2 1l2-1m-2 1v-2.5M6 18l-2-1v-2.5M18 18l2-1v-2.5" />
              </svg>
            </div>
            <h3 className="font-semibold text-slate-100 mb-1">3D Network</h3>
            <p className="text-sm text-slate-400">
              Interactive 3D disease relationship map
            </p>
          </div>
          
          <Link
            to="/risk-calculator"
            className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50 hover:border-rose-500/50 hover:bg-slate-800/70 transition-all duration-200 cursor-pointer group"
          >
            <div className="w-10 h-10 rounded-lg bg-rose-500/10 flex items-center justify-center mb-3 group-hover:bg-rose-500/20 transition-colors">
              <svg className="w-5 h-5 text-rose-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
              </svg>
            </div>
            <h3 className="font-semibold text-slate-100 mb-1 group-hover:text-rose-400 transition-colors">
              Risk Calculator →
            </h3>
            <p className="text-sm text-slate-400">
              Personalized comorbidity risk assessment
            </p>
          </Link>
        </div>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="glass rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-cyan-400">1,080</div>
          <div className="text-sm text-slate-400">ICD-10 Codes</div>
        </div>
        <div className="glass rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-teal-400">9,232</div>
          <div className="text-sm text-slate-400">Relationships</div>
        </div>
        <div className="glass rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-cyan-400">21</div>
          <div className="text-sm text-slate-400">ICD Chapters</div>
        </div>
        <div className="glass rounded-lg p-4 text-center">
          <div className="text-2xl font-bold text-teal-400">8.9M</div>
          <div className="text-sm text-slate-400">Patients Analyzed</div>
        </div>
      </div>
    </>
  );
}

function App() {
  const [apiStatus, setApiStatus] = useState<boolean | null>(null);
  const location = useLocation();

  // Check API health on mount
  useEffect(() => {
    const checkHealth = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}${API_ENDPOINTS.health}`);
        setApiStatus(response.ok);
      } catch {
        setApiStatus(false);
      }
    };
    
    checkHealth();
    
    // Check health periodically
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Check if we're on the risk calculator page
  const isRiskCalculator = location.pathname === '/risk-calculator';

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 z-50 glass border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo & Title */}
            <Link to="/" className="flex items-center gap-3 hover:opacity-80 transition-opacity">
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-cyan-500 to-teal-500 flex items-center justify-center">
                <svg 
                  className="w-6 h-6 text-white" 
                  fill="none" 
                  viewBox="0 0 24 24" 
                  stroke="currentColor"
                >
                  <path 
                    strokeLinecap="round" 
                    strokeLinejoin="round" 
                    strokeWidth={2} 
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" 
                  />
                </svg>
              </div>
              <div>
                <h1 className="text-lg font-semibold gradient-text">Disease Visualizer</h1>
                <p className="text-xs text-slate-400">
                  {isRiskCalculator ? 'Risk Calculator' : '3D Comorbidity Network Explorer'}
                </p>
              </div>
            </Link>
            
            {/* Navigation & Status */}
            <div className="flex items-center gap-6">
              {isRiskCalculator && (
                <Link 
                  to="/" 
                  className="text-sm text-slate-400 hover:text-cyan-400 transition-colors"
                >
                  ← Back to Home
                </Link>
              )}
              <div className="text-sm">
                <ApiStatus isConnected={apiStatus} />
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-20 pb-8 px-4 sm:px-6 lg:px-8">
        <div className="max-w-7xl mx-auto">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/risk-calculator" element={<UserInputForm />} />
          </Routes>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-6 px-4">
        <div className="max-w-7xl mx-auto text-center text-sm text-slate-500">
          <p>Disease Visualizer • Built with React + Three.js</p>
          <p className="mt-1">Data from Austrian Hospital Records (1997-2014)</p>
        </div>
      </footer>
    </div>
  );
}

export default App;
