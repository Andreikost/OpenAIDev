import { useEffect, useState } from 'react';
import { api, authToken, clearAuthToken, storeAuthToken } from './api';
import type { AuthConfig, AuthUser } from './types';

declare global {
  interface Window {
    google?: { accounts: { oauth2: { initTokenClient: (options: { client_id: string; scope: string; callback: (response: { access_token?: string; error?: string }) => void }) => { requestAccessToken: () => void } } } };
  }
}

async function loadGoogleIdentity() {
  if (window.google?.accounts?.oauth2) return;
  await new Promise<void>((resolve, reject) => {
    const existing = document.querySelector<HTMLScriptElement>('script[data-google-identity]');
    if (existing) {
      existing.addEventListener('load', () => resolve(), { once: true });
      existing.addEventListener('error', () => reject(new Error('Google Identity could not load')), { once: true });
      return;
    }
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.async = true;
    script.defer = true;
    script.dataset.googleIdentity = 'true';
    script.onload = () => resolve();
    script.onerror = () => reject(new Error('Google Identity could not load'));
    document.head.appendChild(script);
  });
}

export function AuthControls({ onUser }: { onUser: (user: AuthUser | null) => void }) {
  const [config, setConfig] = useState<AuthConfig | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    api.authConfig().then(setConfig).catch(() => setMessage('Login configuration unavailable.'));
    if (authToken()) {
      api.authMe().then(({ user: restored }) => { setUser(restored); onUser(restored); }).catch(() => { clearAuthToken(); onUser(null); });
    }
  }, [onUser]);

  async function login() {
    if (!config?.googleEnabled) { setMessage('Google persistence is not configured yet.'); return; }
    setBusy(true);
    setMessage('Opening Google…');
    try {
      await loadGoogleIdentity();
      const client = window.google!.accounts.oauth2.initTokenClient({
        client_id: config.googleClientId,
        scope: 'openid email profile',
        callback: async (response) => {
          if (!response.access_token) { setBusy(false); setMessage(response.error || 'Google did not return an access token.'); return; }
          try {
            const session = await api.googleLogin(response.access_token);
            storeAuthToken(session.token);
            setUser(session.user);
            onUser(session.user);
            setMessage('Persistent experiment workspace connected.');
          } catch { setMessage('Google could not be verified by ColonyMind.'); }
          finally { setBusy(false); }
        },
      });
      client.requestAccessToken();
    } catch { setBusy(false); setMessage('Google Identity Services could not load.'); }
  }

  function logout() {
    clearAuthToken();
    setUser(null);
    onUser(null);
    setMessage('Anonymous mode: versions disappear on refresh.');
  }

  return <div className="auth-controls">
    {user ? <>
      {user.picture && <img src={user.picture} alt="" referrerPolicy="no-referrer" />}
      <span><b>{user.name || user.email}</b><small>PERSISTENT LAB</small></span>
      <button className="outline" onClick={logout}>Sign out</button>
    </> : <button className="outline google-login" disabled={busy || config?.googleEnabled === false} onClick={() => void login()}>{busy ? 'Connecting…' : 'Continue with Google'}</button>}
    {message && <i>{message}</i>}
  </div>;
}
