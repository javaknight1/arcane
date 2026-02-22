"use client";

import {
  createContext,
  useCallback,
  useEffect,
  useState,
} from "react";
import type { UserResponse, TokenResponse } from "@/types/api";
import { getTokens, setTokens, clearTokens } from "@/lib/auth";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AuthContextValue {
  user: UserResponse | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

export const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<UserResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  const fetchUser = useCallback(async (accessToken: string) => {
    try {
      const res = await fetch(`${API_URL}/auth/me`, {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      if (!res.ok) throw new Error("Failed to fetch user");
      const data: UserResponse = await res.json();
      setUser(data);
    } catch {
      clearTokens();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    const { accessToken } = getTokens();
    if (accessToken) {
      fetchUser(accessToken).finally(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }
  }, [fetchUser]);

  const authenticate = useCallback(
    async (endpoint: string, email: string, password: string) => {
      const res = await fetch(`${API_URL}${endpoint}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });
      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: "Request failed" }));
        throw new Error(err.detail || "Authentication failed");
      }
      const tokens: TokenResponse = await res.json();
      setTokens(tokens);
      await fetchUser(tokens.access_token);
    },
    [fetchUser]
  );

  const login = useCallback(
    (email: string, password: string) => authenticate("/auth/login", email, password),
    [authenticate]
  );

  const register = useCallback(
    (email: string, password: string) => authenticate("/auth/register", email, password),
    [authenticate]
  );

  const logout = useCallback(() => {
    clearTokens();
    setUser(null);
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
