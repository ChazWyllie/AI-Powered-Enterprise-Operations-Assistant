import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import { ChatPage, AboutPage, DemoPage, SecurityPage } from './pages';
import './App.css';

export default function App() {
  return (
    <BrowserRouter>
      <div className="app">
        <nav className="app-nav" data-testid="app-nav">
          <div className="nav-brand">⚙️ Enterprise Ops</div>
          <div className="nav-links">
            <NavLink to="/" end>Chat</NavLink>
            <NavLink to="/demo">Demo</NavLink>
            <NavLink to="/about">About</NavLink>
            <NavLink to="/security">Security</NavLink>
          </div>
        </nav>
        <main className="app-main">
          <Routes>
            <Route path="/" element={<ChatPage />} />
            <Route path="/demo" element={<DemoPage />} />
            <Route path="/about" element={<AboutPage />} />
            <Route path="/security" element={<SecurityPage />} />
          </Routes>
        </main>
        <footer className="app-footer">
          <p>AI-Powered Enterprise Operations Assistant — Portfolio Project</p>
        </footer>
      </div>
    </BrowserRouter>
  );
}
