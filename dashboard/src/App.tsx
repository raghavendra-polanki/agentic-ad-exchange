import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Agents from './pages/Agents';
import Onboarding from './pages/Onboarding';
import DealDetail from './pages/DealDetail';
import SignalOpportunity from './pages/SignalOpportunity';
import BrandsList, { BrandEdit } from './pages/Brands';
import AthletesList, { AthleteDetailPage } from './pages/Athletes';
import './App.css';

function App() {
  return (
    <BrowserRouter>
      <aside className="sidebar">
        <div className="sidebar-logo">
          <h1>AAX</h1>
          <span>Agentic Ad Exchange</span>
        </div>

        <nav className="sidebar-nav">
          <div className="sidebar-section">
            <div className="sidebar-section-title">Exchange</div>
            <NavLink to="/" end className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="7" />
                <rect x="14" y="3" width="7" height="7" />
                <rect x="3" y="14" width="7" height="7" />
                <rect x="14" y="14" width="7" height="7" />
              </svg>
              Dashboard
            </NavLink>
            <NavLink to="/agents" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
                <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                <path d="M16 3.13a4 4 0 0 1 0 7.75" />
              </svg>
              Agents
            </NavLink>
          </div>

          <div className="sidebar-section">
            <div className="sidebar-section-title">Manage</div>
            <NavLink to="/onboard" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="16" />
                <line x1="8" y1="12" x2="16" y2="12" />
              </svg>
              Onboard
            </NavLink>
            <NavLink to="/signal" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
              </svg>
              Signal
            </NavLink>
            <NavLink to="/brands" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z" />
                <line x1="7" y1="7" x2="7.01" y2="7" />
              </svg>
              Brands
            </NavLink>
            <NavLink to="/athletes" className={({ isActive }) => `sidebar-link${isActive ? ' active' : ''}`}>
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="8" r="4" />
                <path d="M6 21v-2a4 4 0 0 1 4-4h4a4 4 0 0 1 4 4v2" />
              </svg>
              Athletes
            </NavLink>
          </div>
        </nav>

        <div className="sidebar-footer">
          <div className="sidebar-status">
            <div className="status-dot" />
            Exchange Online
          </div>
        </div>
      </aside>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/deals/:dealId" element={<DealDetail />} />
          <Route path="/agents" element={<Agents />} />
          <Route path="/onboard" element={<Onboarding />} />
          <Route path="/signal" element={<SignalOpportunity />} />
          <Route path="/brands" element={<BrandsList />} />
          <Route path="/brands/:agentId" element={<BrandEdit />} />
          <Route path="/athletes" element={<AthletesList />} />
          <Route path="/athletes/:athleteId" element={<AthleteDetailPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  );
}

export default App;
