"use client";

import { TagMappingManager } from "@/components/settings/tag-mapping-manager";

export function StepMap() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold text-white">Map tags to machines</h1>
        <p className="mt-1 text-slate-400">
          Confirm how your tag names map to machines and parameters. Smart defaults are pre-loaded — add a rule for your own naming if needed.
        </p>
      </div>
      <TagMappingManager />
    </div>
  );
}
