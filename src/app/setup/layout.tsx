import * as React from "react";

export default function SetupLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="dark min-h-screen w-full bg-slate-950 text-slate-100" style={{ colorScheme: "dark" }}>
      {children}
    </div>
  );
}
