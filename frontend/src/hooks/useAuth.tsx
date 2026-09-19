// مدیریت نشست و پروفایل کاربر
import { createContext, useContext, useEffect, useState } from 'react';
import { useQueryClient } from '@tanstack/react-query';
import { get, getToken, setToken } from '../lib/api';
import type { Profile, User } from '../types';

interface AuthContextValue {
  user: User | null;
  profile: Profile | null;
  loading: boolean;
  refresh: () => Promise<void>;
  login: (token: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue>({
  user: null,
  profile: null,
  loading: true,
  refresh: async () => undefined,
  login: async () => undefined,
  logout: () => undefined,
});

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [loading, setLoading] = useState(true);
  const queryClient = useQueryClient();

  const refresh = async () => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    try {
      const me = await get<User>('/auth/me');
      setUser(me.data);
      try {
        const prof = await get<Profile>('/students/me');
        setProfile(prof.data);
      } catch {
        setProfile(null);
      }
    } catch {
      setToken(null);
      setUser(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const login = async (token: string) => {
    setToken(token);
    await refresh();
    queryClient.clear();
  };

  const logout = () => {
    void apiLogout();
    setToken(null);
    setUser(null);
    setProfile(null);
    queryClient.clear();
  };

  return (
    <AuthContext.Provider value={{ user, profile, loading, refresh, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

async function apiLogout() {
  try {
    const { api } = await import('../lib/api');
    await api.post('/auth/logout');
  } catch {
    // ignore
  }
}

export function useAuth() {
  return useContext(AuthContext);
}
