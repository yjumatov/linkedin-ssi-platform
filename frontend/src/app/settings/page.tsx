"use client";

import { useState } from "react";
import { Save, Eye, EyeOff, RefreshCw, CheckCircle } from "lucide-react";
import { triggerScrape, getScrapeRuns } from "@/lib/api";
import type { ScrapeRun } from "@/types";
import { useEffect } from "react";
import { formatDate, cn } from "@/lib/utils";

export default function SettingsPage() {
  const [showPassword, setShowPassword] = useState(false);
  const [saved, setSaved] = useState(false);
  const [runs, setRuns] = useState<ScrapeRun[]>([]);
  const [scraping, setScraping] = useState(false);
  const [scrapeMsg, setScrapeMsg] = useState<string | null>(null);

  useEffect(() => {
    getScrapeRuns(10).then(setRuns).catch(() => {});
  }, []);

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleScrape = async () => {
    setScraping(true);
    setScrapeMsg(null);
    try {
      const result = await triggerScrape();
      setScrapeMsg(result.message);
      const updated = await getScrapeRuns(10);
      setRuns(updated);
    } catch (err: any) {
      setScrapeMsg(err.message ?? "Failed to start scrape");
    } finally {
      setScraping(false);
    }
  };

  const statusColor = (status: string) => {
    if (status === "success") return "text-emerald-600 bg-emerald-50";
    if (status === "failed") return "text-red-600 bg-red-50";
    return "text-amber-600 bg-amber-50";
  };

  return (
    <div className="space-y-6 max-w-2xl">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-500 text-sm mt-1">
          Configure LinkedIn credentials and AI provider settings.
        </p>
      </div>

      <p className="bg-amber-50 border border-amber-200 rounded-lg p-4 text-sm text-amber-700">
        Credentials are stored encrypted in the database. Configure them in the{" "}
        <code className="font-mono bg-amber-100 px-1 rounded">.env</code> file and restart to apply.
        This UI is for reference only.
      </p>

      {/* LinkedIn Credentials */}
      <div className="card">
        <div className="card-header">
          <h3 className="font-semibold text-slate-900">LinkedIn Credentials</h3>
        </div>
        <div className="card-body">
          <form onSubmit={handleSave} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                LinkedIn Email
              </label>
              <input
                type="email"
                placeholder="your@email.com"
                className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0077b5]/30"
                defaultValue={process.env.NEXT_PUBLIC_LINKEDIN_EMAIL ?? ""}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">
                LinkedIn Password
              </label>
              <div className="relative">
                <input
                  type={showPassword ? "text" : "password"}
                  placeholder="••••••••"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0077b5]/30 pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
            <button type="submit" className="btn-primary">
              {saved ? (
                <>
                  <CheckCircle className="w-4 h-4" />
                  Saved!
                </>
              ) : (
                <>
                  <Save className="w-4 h-4" />
                  Save Credentials
                </>
              )}
            </button>
          </form>
        </div>
      </div>

      {/* AI Provider */}
      <div className="card">
        <div className="card-header">
          <h3 className="font-semibold text-slate-900">AI Provider</h3>
        </div>
        <div className="card-body space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">Provider</label>
            <select className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0077b5]/30">
              <option value="openai">OpenAI (GPT-4o)</option>
              <option value="claude">Anthropic Claude (claude-sonnet-4-6)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-700 mb-1">API Key</label>
            <input
              type="password"
              placeholder="sk-... or sk-ant-..."
              className="w-full px-3 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#0077b5]/30"
            />
          </div>
        </div>
      </div>

      {/* Manual Scrape */}
      <div className="card">
        <div className="card-header flex items-center justify-between">
          <h3 className="font-semibold text-slate-900">Scraping</h3>
          <button onClick={handleScrape} disabled={scraping} className="btn-primary">
            <RefreshCw className={cn("w-4 h-4", scraping && "animate-spin")} />
            {scraping ? "Running..." : "Run Scrape Now"}
          </button>
        </div>
        <div className="card-body">
          {scrapeMsg && (
            <div className="mb-4 p-3 bg-blue-50 border border-blue-100 rounded-lg text-sm text-blue-700">
              {scrapeMsg}
            </div>
          )}
          <p className="text-sm text-slate-500 mb-3">
            Automatic scraping runs daily at 09:00 UTC. Recent runs:
          </p>
          {runs.length === 0 ? (
            <p className="text-sm text-slate-400">No runs yet.</p>
          ) : (
            <div className="space-y-2">
              {runs.map((run) => (
                <div
                  key={run.id}
                  className="flex items-center justify-between py-2 border-b border-slate-50 last:border-0"
                >
                  <div className="text-sm">
                    <span className={cn("badge", statusColor(run.status))}>
                      {run.status}
                    </span>
                    <span className="ml-2 text-slate-500">{formatDate(run.started_at)}</span>
                    {run.trigger === "manual" && (
                      <span className="ml-2 text-xs text-slate-400">(manual)</span>
                    )}
                  </div>
                  {run.error_message && (
                    <span className="text-xs text-red-500 max-w-xs truncate" title={run.error_message}>
                      {run.error_message}
                    </span>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Scheduling info */}
      <div className="card">
        <div className="card-header">
          <h3 className="font-semibold text-slate-900">Schedule</h3>
        </div>
        <div className="card-body space-y-2 text-sm text-slate-600">
          <div className="flex justify-between py-1 border-b border-slate-50">
            <span className="text-slate-500">Daily scrape</span>
            <code className="bg-slate-100 px-2 py-0.5 rounded font-mono text-xs">0 9 * * *</code>
          </div>
          <div className="flex justify-between py-1 border-b border-slate-50">
            <span className="text-slate-500">Daily email report</span>
            <code className="bg-slate-100 px-2 py-0.5 rounded font-mono text-xs">0 10 * * *</code>
          </div>
          <p className="text-xs text-slate-400 pt-2">All times UTC. Configure via SCRAPE_CRON / REPORT_CRON env vars.</p>
        </div>
      </div>
    </div>
  );
}
