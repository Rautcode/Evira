"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { login, getSetupStatus } from "@/lib/api";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useToast } from "@/hooks/use-toast";

export function LoginForm() {
  const router = useRouter();
  const { toast } = useToast();
  const [username, setUsername] = React.useState("");
  const [password, setPassword] = React.useState("");
  const [showPassword, setShowPassword] = React.useState(false);
  const [submitting, setSubmitting] = React.useState(false);

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      toast({ title: "Enter your username and password", variant: "destructive" });
      return;
    }
    setSubmitting(true);
    try {
      const res = await login({ username: username.trim(), password });
      if (res?.data?.success && res.data.token) {
        localStorage.setItem("auth_token", res.data.token);
        document.cookie = `auth_token=${res.data.token}; path=/; max-age=86400; SameSite=Lax`;
        // New users (system not configured) go through the guided setup; others
        // land on the dashboard.
        let destination = "/dashboard";
        try {
          const s = await getSetupStatus();
          if (!s.data?.completed) destination = "/setup";
        } catch {
          /* default to dashboard */
        }
        toast({ title: "Welcome back", description: destination === "/setup" ? "Let's finish setting up…" : "Redirecting to your dashboard…" });
        router.push(destination);
      } else {
        throw new Error(res?.data?.detail || "Invalid response from server");
      }
    } catch (err: any) {
      let message = "Invalid username or password";
      if (err?.response?.data?.detail) message = err.response.data.detail;
      else if (err?.message?.includes("Network Error"))
        message = "Cannot reach the server. Please check it is running.";
      toast({ title: "Login failed", description: message, variant: "destructive" });
      setPassword("");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form onSubmit={onSubmit} className="space-y-5">
      <div className="space-y-1.5">
        <label htmlFor="username" className="text-sm font-medium text-foreground">
          Username
        </label>
        <Input
          id="username"
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="Enter your username"
          autoComplete="username"
          autoFocus
          className="h-11"
        />
      </div>

      <div className="space-y-1.5">
        <label htmlFor="password" className="text-sm font-medium text-foreground">
          Password
        </label>
        <div className="relative">
          <Input
            id="password"
            type={showPassword ? "text" : "password"}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter your password"
            autoComplete="current-password"
            className="h-11 pr-10"
          />
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="absolute inset-y-0 right-0 h-full px-3 text-muted-foreground hover:bg-transparent"
            onClick={() => setShowPassword((s) => !s)}
            aria-label={showPassword ? "Hide password" : "Show password"}
            tabIndex={-1}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </Button>
        </div>
      </div>

      <Button
        type="submit"
        className="w-full h-11 text-sm font-semibold bg-blue-600 hover:bg-blue-700 text-white"
        disabled={submitting}
      >
        {submitting ? "Signing in…" : "Sign in"}
      </Button>
    </form>
  );
}
