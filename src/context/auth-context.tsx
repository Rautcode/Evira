"use client";

import * as React from "react";

export type Role = "operator" | "engineer" | "admin";

interface AuthState {
  user: string | null;
  role: Role;
}

interface AuthContextValue extends AuthState {
  setAuth: (user: string, role: Role) => void;
  clearAuth: () => void;
  isAtLeast: (min: Role) => boolean;
}

const RANK: Record<Role, number> = { operator: 1, engineer: 2, admin: 3 };

const AuthContext = React.createContext<AuthContextValue>({
  user: null,
  role: "operator",
  setAuth: () => {},
  clearAuth: () => {},
  isAtLeast: () => false,
});

function readStorage(): AuthState {
  if (typeof window === "undefined") return { user: null, role: "operator" };
  return {
    user: localStorage.getItem("auth_user") || null,
    role: (localStorage.getItem("auth_role") as Role) || "operator",
  };
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [state, setState] = React.useState<AuthState>({ user: null, role: "operator" });

  React.useEffect(() => {
    setState(readStorage());
  }, []);

  const setAuth = React.useCallback((user: string, role: Role) => {
    localStorage.setItem("auth_user", user);
    localStorage.setItem("auth_role", role);
    setState({ user, role });
  }, []);

  const clearAuth = React.useCallback(() => {
    localStorage.removeItem("auth_user");
    localStorage.removeItem("auth_role");
    localStorage.removeItem("auth_token");
    setState({ user: null, role: "operator" });
  }, []);

  const isAtLeast = React.useCallback(
    (min: Role) => RANK[state.role] >= RANK[min],
    [state.role],
  );

  return (
    <AuthContext.Provider value={{ ...state, setAuth, clearAuth, isAtLeast }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return React.useContext(AuthContext);
}
