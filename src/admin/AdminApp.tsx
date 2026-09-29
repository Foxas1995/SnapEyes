// The owner's admin panel (/admin): the login with the admin key (scripts/mint_admin.py), then five pages. The key is
// kept in this browser's localStorage and sent only to /api/admin; nothing here is linked from the public site.
import { useCallback, useEffect, useState } from 'react';
import type React from 'react';
import { adminCall, dropKey, KEY_RE, loadKey, saveKey } from './api';
import type { Me, Reply } from './api';
import { explain, fmtDate } from './format';
import { BTN, GOLD, INPUT, MUTED, Notice, Spinner } from './ui';
import { SummaryPage } from './Summary';
import { OrdersPage } from './Orders';
import { OrderDetailPage } from './OrderDetail';
import { LabPage } from './Lab';
import { StatsPage } from './Stats';
import { ErrorsPage } from './Errors';

export type Call = <T>(action: string, body?: Record<string, unknown>, timeoutMs?: number) => Promise<Reply<T>>;

type Route = { page: 'summary' | 'orders' | 'order' | 'lab' | 'stats' | 'errors'; order?: string };

function readRoute(): Route {
  const raw = (typeof location !== 'undefined' ? location.hash : '').replace(/^#\/?/, '');
  // a malformed hash (a stray "%") must not blank the panel: it simply opens the summary
  let h = '';
  try { h = decodeURIComponent(raw); } catch { h = ''; }
  const m = /^order\/([a-z0-9][a-z0-9-]{3,63})$/.exec(h);
  if (m) return { page: 'order', order: m[1] };
  if (h === 'orders' || h === 'lab' || h === 'stats' || h === 'errors') return { page: h };
  return { page: 'summary' };
}

const TABS: [Route['page'], string][] = [
  ['summary', 'Suvestinė'], ['orders', 'Užsakymai'], ['lab', 'Laboratorija'], ['stats', 'Statistika'], ['errors', 'Klaidos'],
];

const Login: React.FC<{ onIn: (key: string, me: Me) => void; message: string }> = ({ onIn, message }) => {
  const [key, setKey] = useState('');
  const [show, setShow] = useState(false);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(message);
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    const k = key.trim();
    if (!KEY_RE.test(k)) { setErr('Tai ne administratoriaus raktas. Jis atrodo taip: admin-v1.1790000000.<32 ženklai>.'); return; }
    setBusy(true); setErr('');
    const r = await adminCall<Me>('me', {}, k, 20_000);
    setBusy(false);
    if (r.ok && r.data) { saveKey(k); setKey(''); onIn(k, r.data); } else setErr(explain(r));
  };
  return (
    <main className="min-h-screen flex items-center justify-center px-4 py-10">
      <form onSubmit={submit} className="w-full max-w-md bg-[#0b0e17] border border-white/10 rounded-2xl p-5 flex flex-col gap-4">
        <div>
          <p className="text-xs tracking-[0.2em] uppercase text-[#f5c542]/80">SnapEyes</p>
          <h1 className="text-xl font-bold mt-1" style={{ fontFamily: "'Plus Jakarta Sans', sans-serif" }}>Administravimas</h1>
        </div>
        <p className={`text-sm ${MUTED}`}>
          Įklijuok administratoriaus raktą. Jį sukuria <code className="text-white/80">python scripts/mint_admin.py</code>.
          Raktas lieka tik šioje naršyklėje ir siunčiamas tik šiam puslapiui.
        </p>
        <label className="flex flex-col gap-1 text-sm">
          <span>Raktas</span>
          <div className="flex gap-2">
            <input className={INPUT} type={show ? 'text' : 'password'} value={key} onChange={(e) => setKey(e.target.value)}
              autoComplete="off" spellCheck={false} name="admin-key" aria-label="Administratoriaus raktas" />
            <button type="button" className={BTN} onClick={() => setShow((s) => !s)}>{show ? 'Slėpti' : 'Rodyti'}</button>
          </div>
        </label>
        {err && <Notice>{err}</Notice>}
        <button type="submit" className={GOLD} disabled={busy || !key.trim()}>{busy && <Spinner />}Prisijungti</button>
      </form>
    </main>
  );
};

export const AdminApp: React.FC = () => {
  const [key, setKey] = useState(loadKey);
  const [me, setMe] = useState<Me | null>(null);
  const [checking, setChecking] = useState(() => !!loadKey());
  const [message, setMessage] = useState('');
  const [route, setRoute] = useState<Route>(readRoute);
  const [attempt, setAttempt] = useState(0);

  useEffect(() => {
    const on = () => setRoute(readRoute());
    window.addEventListener('hashchange', on);
    return () => window.removeEventListener('hashchange', on);
  }, []);

  const logout = useCallback((why = '') => { dropKey(); setKey(''); setMe(null); setMessage(why); }, []);

  useEffect(() => {
    if (!key || me) return;
    let live = true;
    adminCall<Me>('me', {}, key, 20_000).then((r) => {
      if (!live) return;
      setChecking(false);
      if (r.ok && r.data) setMe(r.data);
      // only a key the server refuses as such is forgotten; a 429 (wait), a refusal by the platform or a server
      // that is not set up keeps it, so the owner can simply try again
      else if (r.status === 403 && r.reason === 'admin_denied') logout(explain(r));
      else setMessage(explain(r));
    });
    return () => { live = false; };
  }, [key, me, logout, attempt]);

  const call: Call = useCallback(async <T,>(action: string, body: Record<string, unknown> = {}, timeoutMs?: number) => {
    const r = await adminCall<T>(action, body, key, timeoutMs);
    if (r.status === 403 && r.reason === 'admin_denied') logout(explain(r));
    return r;
  }, [key, logout]);

  if (!key || (!me && !checking && !message)) {
    return <Login message={message} onIn={(k, m) => { setKey(k); setMe(m); setMessage(''); }} />;
  }
  if (!me) {
    return (
      <main className="min-h-screen flex flex-col items-center justify-center gap-3 px-4">
        {message ? <Notice>{message}</Notice> : <p className="flex items-center gap-2 text-sm"><Spinner />Tikrinamas raktas...</p>}
        {message && (
          <div className="flex flex-wrap justify-center gap-2">
            <button type="button" className={BTN} onClick={() => { setMessage(''); setChecking(true); setAttempt((a) => a + 1); }}>Bandyti dar kartą</button>
            <button type="button" className={BTN} onClick={() => logout('')}>Įvesti kitą raktą</button>
          </div>
        )}
      </main>
    );
  }
  const active = route.page === 'order' ? 'orders' : route.page;
  return (
    <div className="min-h-screen">
      <header className="border-b border-white/10 bg-[#07090e]/95 sticky top-0 z-40 backdrop-blur">
        <div className="max-w-6xl mx-auto px-4 py-3 flex flex-wrap items-center justify-between gap-2">
          <div className="min-w-0">
            <p className="text-sm font-bold"><span className="text-[#f5c542]">SnapEyes</span> administravimas</p>
            <p className="text-[11px] text-white/50">Raktas galioja iki {fmtDate(me.expires_at)}</p>
          </div>
          <button type="button" className={BTN} onClick={() => logout('Atsijungta.')}>Atsijungti</button>
        </div>
        <nav className="max-w-6xl mx-auto px-4 pb-2 flex flex-wrap gap-1.5" aria-label="Skyriai">
          {TABS.map(([p, label]) => (
            <a key={p} href={`#${p}`} aria-current={active === p ? 'page' : undefined}
              className={`px-3 py-1.5 rounded-lg text-sm font-semibold border ${active === p ? 'bg-[#f5c542] text-black border-[#f5c542]' : 'border-white/10 text-white/80 hover:bg-white/5'}`}>
              {label}
            </a>
          ))}
        </nav>
      </header>
      <main className="max-w-6xl mx-auto px-4 py-5">
        {route.page === 'summary' && <SummaryPage call={call} />}
        {route.page === 'orders' && <OrdersPage call={call} />}
        {route.page === 'order' && route.order && <OrderDetailPage key={route.order} call={call} order={route.order} />}
        {route.page === 'lab' && <LabPage call={call} />}
        {route.page === 'stats' && <StatsPage call={call} />}
        {route.page === 'errors' && <ErrorsPage call={call} />}
      </main>
    </div>
  );
};
