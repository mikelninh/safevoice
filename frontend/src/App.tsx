import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import { useState } from 'react'
import type { Lang } from './i18n'
import { t } from './i18n'
import Home from './pages/Home'
import Analyze from './pages/Analyze'
import Cases from './pages/Cases'
import CaseDetail from './pages/CaseDetail'
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import Impressum from './pages/Impressum'
import Datenschutz from './pages/Datenschutz'
import ApiDocs from './pages/ApiDocs'
import SafeExit from './components/SafeExit'
import AcknowledgementBanner from './components/AcknowledgementBanner'

function NavBar({ lang, setLang }: { lang: Lang; setLang: (l: Lang) => void }) {
  const location = useLocation()

  const navLink = (to: string, label: string) => (
    <Link
      to={to}
      className={`text-sm font-medium transition-colors ${
        location.pathname.startsWith(to) && to !== '/'
          ? 'text-indigo-400'
          : location.pathname === '/' && to === '/'
          ? 'text-indigo-400'
          : 'text-slate-400 hover:text-slate-200'
      }`}
    >
      {label}
    </Link>
  )

  return (
    <nav className="border-b border-slate-800 px-4 py-3">
      <div className="max-w-2xl mx-auto flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2">
          <div className="w-7 h-7 bg-indigo-600 rounded-lg flex items-center justify-center">
            <span className="text-white text-xs font-bold">SV</span>
          </div>
          <span className="text-white font-bold">{t(lang, 'app.name')}</span>
        </Link>

        <div className="flex items-center gap-5">
          {navLink('/analyze', t(lang, 'nav.new'))}
          {navLink('/cases', t(lang, 'nav.cases'))}
          {navLink('/dashboard', 'Dashboard')}
          <button
            onClick={() => setLang(lang === 'de' ? 'en' : 'de')}
            className="text-slate-500 hover:text-slate-300 text-xs font-mono border border-slate-700 rounded px-2 py-1 transition-colors"
          >
            {lang === 'de' ? 'EN' : 'DE'}
          </button>
        </div>
      </div>
    </nav>
  )
}

function AppShell() {
  const [lang, setLang] = useState<Lang>('de')

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      <NavBar lang={lang} setLang={setLang} />
      <AcknowledgementBanner lang={lang} />
      <main>
        <Routes>
          <Route path="/" element={<Home lang={lang} />} />
          <Route path="/analyze" element={<Analyze lang={lang} />} />
          <Route path="/cases" element={<Cases lang={lang} />} />
          <Route path="/cases/:id" element={<CaseDetail lang={lang} />} />
          <Route path="/login" element={<Login lang={lang} onLogin={() => {}} />} />
          <Route path="/dashboard" element={<Dashboard lang={lang} />} />
          <Route path="/api" element={<ApiDocs lang={lang} />} />
          {/* PWA share target */}
          <Route path="/share" element={<Analyze lang={lang} />} />
          {/* Legal pages (required in Germany) */}
          <Route path="/impressum" element={<Impressum lang={lang} />} />
          <Route path="/datenschutz" element={<Datenschutz lang={lang} />} />
        </Routes>
      </main>
      <SafeExit lang={lang} />
      {/* Footer — Impressum-grade: operator, update date, source, license, changelog. */}
      <footer className="border-t border-slate-800 mt-12 py-8 px-4">
        <div className="max-w-2xl mx-auto text-sm text-slate-500 space-y-3">
          <p className="text-slate-400">
            {lang === 'de' ? 'Gebaut von ' : 'Built by '}
            {import.meta.env.VITE_OPERATOR_NAME || 'Mikel Ninh'}
            {lang === 'de' ? ', Berlin.' : ', Berlin.'}
          </p>
          <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs">
            <Link to="/impressum" className="hover:text-slate-300 transition-colors">
              {t(lang, 'footer.legal')}
            </Link>
            <Link to="/datenschutz" className="hover:text-slate-300 transition-colors">
              {t(lang, 'footer.privacy')}
            </Link>
            <a
              href="https://github.com/mikelninh/safevoice"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-300 transition-colors"
            >
              {lang === 'de' ? 'Quellcode (GitHub)' : 'Source (GitHub)'}
            </a>
            <a
              href="https://github.com/mikelninh/safevoice#license"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-300 transition-colors"
            >
              {lang === 'de' ? 'Lizenz' : 'License'}
            </a>
            <a
              href="https://github.com/mikelninh/safevoice/blob/main/CHANGELOG.md"
              target="_blank"
              rel="noopener noreferrer"
              className="hover:text-slate-300 transition-colors"
            >
              {lang === 'de' ? 'Änderungsprotokoll' : 'Changelog'}
            </a>
          </div>
          <p className="text-xs text-slate-600">
            {lang === 'de' ? 'Stand: ' : 'Last updated: '}
            {new Date().toISOString().slice(0, 10)}
          </p>
        </div>
      </footer>
    </div>
  )
}

export default function App() {
  return (
    <BrowserRouter>
      <AppShell />
    </BrowserRouter>
  )
}
