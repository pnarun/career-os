import { useCallback, useEffect, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  Loader2,
  Save,
  Settings2,
} from "lucide-react"

import { ProviderPriorityList } from "@/components/settings/ProviderPriorityList"
import { TagCombobox } from "@/components/settings/TagCombobox"
import { SlowLoadingFormHint, SlowLoadingPageCenter } from "@/components/SlowLoadingStatus"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ALL_PROVIDERS } from "@/services/scansService"
import {
  getPreferences,
  listResumes,
  savePreferences,
  updatePreferences,
} from "@/services/preferencesService"

const TIMEZONE_OPTIONS = [
  "Asia/Kolkata",
  "Asia/Dubai",
  "Europe/Berlin",
  "Europe/London",
  "America/New_York",
  "UTC",
]

const CAREER_FOCUS_OPTIONS = [
  { value: "backend", label: "Backend" },
  { value: "fullstack", label: "Full Stack" },
  { value: "devops", label: "DevOps" },
  { value: "ai_ml", label: "AI / ML" },
  { value: "cloud", label: "Cloud" },
  { value: "general", label: "General" },
]

const defaultForm = {
  email: "",
  resume_id: "",
  timezone: "Asia/Kolkata",
  preferred_locations: [],
  remote_only: false,
  min_match_threshold: 50,
  career_focus: "general",
  ai_strictness: "balanced",
  ats_optimization_mode: "standard",
  email_notifications: true,
  in_app_notifications: true,
  scan_completion_alerts: true,
  follow_up_reminders: true,
  interview_reminders: true,
  high_match_alerts: true,
  enabled_providers: ALL_PROVIDERS.map((p) => p.id),
  provider_priority: ALL_PROVIDERS.map((p) => p.id),
  notice_period_days: 30,
  work_authorization: "Authorized to work",
  expected_salary: "",
  target_roles: [],
  target_skills: [],
  target_companies: [],
}

const inputClass =
  "flex h-9 w-full rounded-lg border border-input bg-background px-3 text-sm"

export function Settings() {
  const [form, setForm] = useState(defaultForm)
  const [preferenceId, setPreferenceId] = useState(null)
  const [resumes, setResumes] = useState([])
  const [status, setStatus] = useState("idle")
  const [message, setMessage] = useState(null)
  const [error, setError] = useState(null)

  const loadData = useCallback(async () => {
    setStatus("loading")
    setError(null)
    try {
      const [prefs, resumeList] = await Promise.all([getPreferences(), listResumes()])
      setResumes(resumeList)
      if (prefs) {
        setPreferenceId(prefs.id)
        setForm({
          email: prefs.email ?? "",
          resume_id: prefs.resume_id ?? "",
          timezone: prefs.timezone ?? "Asia/Kolkata",
          preferred_locations: Array.isArray(prefs.preferred_locations)
            ? prefs.preferred_locations
            : String(prefs.preferred_locations || "")
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean),
          remote_only: prefs.remote_only ?? false,
          min_match_threshold: prefs.min_match_threshold ?? 50,
          career_focus: prefs.career_focus ?? "general",
          ai_strictness: prefs.ai_strictness ?? "balanced",
          ats_optimization_mode: prefs.ats_optimization_mode ?? "standard",
          email_notifications: prefs.email_notifications ?? true,
          in_app_notifications: prefs.in_app_notifications ?? true,
          scan_completion_alerts: prefs.scan_completion_alerts ?? true,
          follow_up_reminders: prefs.follow_up_reminders ?? true,
          interview_reminders: prefs.interview_reminders ?? true,
          high_match_alerts: prefs.high_match_alerts ?? true,
          enabled_providers: prefs.enabled_providers ?? ALL_PROVIDERS.map((p) => p.id),
          provider_priority: prefs.provider_priority ?? ALL_PROVIDERS.map((p) => p.id),
          notice_period_days: prefs.notice_period_days ?? 30,
          work_authorization: prefs.work_authorization ?? "Authorized to work",
          expected_salary: prefs.expected_salary ?? "",
          target_roles: prefs.target_roles ?? [],
          target_skills: prefs.target_skills ?? [],
          target_companies: prefs.target_companies ?? [],
        })
      } else if (resumeList.length > 0) {
        setForm((prev) => ({
          ...prev,
          resume_id: resumeList[0].id,
          email: resumeList[0].emails?.[0] ?? prev.email,
        }))
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load settings")
    } finally {
      setStatus("idle")
    }
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  const onChange = (field, value) => {
    setForm((prev) => ({ ...prev, [field]: value }))
    setMessage(null)
    setError(null)
  }

  const toggleProvider = (id) => {
    setForm((prev) => {
      const enabled = prev.enabled_providers.includes(id)
        ? prev.enabled_providers.filter((p) => p !== id)
        : [...prev.enabled_providers, id]
      const priority = prev.provider_priority.includes(id)
        ? prev.provider_priority
        : [...prev.provider_priority, id]
      return { ...prev, enabled_providers: enabled, provider_priority: priority }
    })
  }

  const reorderProviders = (fromId, toId) => {
    setForm((prev) => {
      const from = prev.provider_priority.indexOf(fromId)
      const to = prev.provider_priority.indexOf(toId)
      if (from < 0 || to < 0 || from === to) return prev
      const list = [...prev.provider_priority]
      const [item] = list.splice(from, 1)
      list.splice(to, 0, item)
      return { ...prev, provider_priority: list }
    })
    setMessage(null)
    setError(null)
  }

  const providersById = Object.fromEntries(ALL_PROVIDERS.map((p) => [p.id, p]))

  const buildPayload = (isCreate) => {
    const base = {
      email: form.email.trim(),
      resume_id: form.resume_id,
      timezone: form.timezone,
      preferred_locations: Array.isArray(form.preferred_locations)
        ? form.preferred_locations
        : String(form.preferred_locations || "")
            .split(",")
            .map((s) => s.trim())
            .filter(Boolean),
      remote_only: form.remote_only,
      min_match_threshold: Number(form.min_match_threshold) || 50,
      career_focus: form.career_focus,
      ai_strictness: form.ai_strictness,
      ats_optimization_mode: form.ats_optimization_mode,
      email_notifications: form.email_notifications,
      in_app_notifications: form.in_app_notifications,
      scan_completion_alerts: form.scan_completion_alerts,
      follow_up_reminders: form.follow_up_reminders,
      interview_reminders: form.interview_reminders,
      high_match_alerts: form.high_match_alerts,
      enabled_providers: form.enabled_providers,
      provider_priority: form.provider_priority,
      notice_period_days: Number(form.notice_period_days) || 30,
      work_authorization: form.work_authorization.trim(),
      expected_salary: form.expected_salary.trim(),
      target_roles: form.target_roles.slice(0, 10),
      target_skills: form.target_skills.slice(0, 50),
      target_companies: form.target_companies.slice(0, 20),
    }
    if (isCreate) {
      return {
        ...base,
        scan_time: "08:00",
        frequency: "daily",
        is_active: false,
        digest_frequency: "daily",
        willing_to_relocate: true,
      }
    }
    return base
  }

  const onSave = async () => {
    setStatus("saving")
    setError(null)
    setMessage(null)
    try {
      if (!form.email.trim()) throw new Error("Email address is required")
      if (!form.resume_id) throw new Error("Select a default resume")
      const payload = buildPayload(!preferenceId)
      if (preferenceId) {
        const updated = await updatePreferences(preferenceId, payload)
        setPreferenceId(updated.id)
      } else {
        const saved = await savePreferences(payload)
        setPreferenceId(saved.id)
      }
      setMessage("Preferences saved.")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save")
    } finally {
      setStatus("idle")
    }
  }

  const isLoading = status === "loading"
  const isSaving = status === "saving"

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <div className="flex items-center gap-2">
          <Settings2 className="size-6 text-muted-foreground" />
          <h2 className="text-2xl font-semibold tracking-tight">Settings</h2>
        </div>
        <p className="mt-1 text-sm text-muted-foreground">
          User, AI, notification, and provider preferences. Run scans from the Scans page.
        </p>
      </div>

      {isLoading ? (
        <SlowLoadingPageCenter active messageKey="settings-load" className="min-h-[30vh]" />
      ) : (
        <>
          <Card>
            <CardHeader>
              <CardTitle className="text-base">Job search profile</CardTitle>
              <CardDescription>
                Roles and skills drive scans across LinkedIn, Naukri, Instahyre, and more. Updated
                when you upload a resume; you can edit here.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6 overflow-visible">
              <TagCombobox
                label="Target roles (max 10)"
                hint="e.g. Angular Developer, Senior Full Stack Engineer"
                kind="roles"
                maxItems={10}
                items={form.target_roles}
                onChange={(items) => onChange("target_roles", items)}
                placeholder="Search roles…"
              />
              <TagCombobox
                label="Skills (max 50)"
                hint="Used for matching — jobs are not removed for missing skills"
                kind="skills"
                maxItems={50}
                items={form.target_skills}
                onChange={(items) => onChange("target_skills", items)}
                placeholder="Search skills…"
              />
              <TagCombobox
                label="Target companies"
                hint="Tagged on matching jobs; filter in Jobs feed (e.g. Amazon, Flipkart)"
                kind="companies"
                maxItems={20}
                items={form.target_companies}
                onChange={(items) => onChange("target_companies", items)}
                placeholder="Search companies…"
              />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">User Preferences</CardTitle>
              <CardDescription>Profile and job discovery defaults</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4 overflow-visible">
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Email address</label>
                <input
                  type="email"
                  value={form.email}
                  onChange={(e) => onChange("email", e.target.value)}
                  className={inputClass}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Preferred resume</label>
                <select
                  value={form.resume_id}
                  onChange={(e) => onChange("resume_id", e.target.value)}
                  className={inputClass}
                >
                  <option value="">Select resume</option>
                  {resumes.map((r) => (
                    <option key={r.id} value={r.id}>
                      {r.filename || r.id}
                    </option>
                  ))}
                </select>
              </div>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Timezone</label>
                  <select
                    value={form.timezone}
                    onChange={(e) => onChange("timezone", e.target.value)}
                    className={inputClass}
                  >
                    {TIMEZONE_OPTIONS.map((tz) => (
                      <option key={tz} value={tz}>
                        {tz}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Work authorization</label>
                  <input
                    value={form.work_authorization}
                    onChange={(e) => onChange("work_authorization", e.target.value)}
                    className={inputClass}
                  />
                </div>
              </div>
              <TagCombobox
                label="Default locations"
                hint="Used for scans and location matching (e.g. Bangalore, Remote)"
                kind="locations"
                maxItems={15}
                items={form.preferred_locations}
                onChange={(items) => onChange("preferred_locations", items)}
                placeholder="Search locations…"
              />
              <label className="flex items-center gap-2 text-sm">
                <input
                  type="checkbox"
                  checked={form.remote_only}
                  onChange={(e) => onChange("remote_only", e.target.checked)}
                />
                Prefer remote roles
              </label>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">AI Preferences</CardTitle>
              <CardDescription>Matching and resume optimization behavior</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Match threshold (%)</label>
                  <input
                    type="number"
                    min={0}
                    max={100}
                    value={form.min_match_threshold}
                    onChange={(e) => onChange("min_match_threshold", e.target.value)}
                    className={inputClass}
                  />
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">AI strictness</label>
                  <select
                    value={form.ai_strictness}
                    onChange={(e) => onChange("ai_strictness", e.target.value)}
                    className={inputClass}
                  >
                    <option value="relaxed">Relaxed</option>
                    <option value="balanced">Balanced</option>
                    <option value="strict">Strict</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">ATS optimization</label>
                  <select
                    value={form.ats_optimization_mode}
                    onChange={(e) => onChange("ats_optimization_mode", e.target.value)}
                    className={inputClass}
                  >
                    <option value="conservative">Conservative</option>
                    <option value="standard">Standard</option>
                    <option value="aggressive">Aggressive</option>
                  </select>
                </div>
                <div className="space-y-1.5">
                  <label className="text-sm font-medium">Career focus</label>
                  <select
                    value={form.career_focus}
                    onChange={(e) => onChange("career_focus", e.target.value)}
                    className={inputClass}
                  >
                    {CAREER_FOCUS_OPTIONS.map((o) => (
                      <option key={o.value} value={o.value}>
                        {o.label}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
              <div className="space-y-1.5">
                <label className="text-sm font-medium">Expected salary (optional)</label>
                <input
                  value={form.expected_salary}
                  onChange={(e) => onChange("expected_salary", e.target.value)}
                  className={inputClass}
                />
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Notification Preferences</CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {[
                ["email_notifications", "Email notifications"],
                ["in_app_notifications", "Browser / in-app notifications"],
                ["scan_completion_alerts", "Scan completion alerts"],
                ["follow_up_reminders", "Application follow-up reminders"],
                ["interview_reminders", "Interview reminders"],
                ["high_match_alerts", "High match alerts (85%+)"],
              ].map(([field, label]) => (
                <label key={field} className="flex cursor-pointer items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={form[field]}
                    onChange={(e) => onChange(field, e.target.checked)}
                  />
                  {label}
                </label>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle className="text-base">Provider Preferences</CardTitle>
              <CardDescription>Enable providers and set priority order</CardDescription>
            </CardHeader>
            <CardContent>
              <ProviderPriorityList
                order={form.provider_priority}
                enabledIds={form.enabled_providers}
                providersById={providersById}
                onReorder={reorderProviders}
                onToggle={toggleProvider}
              />
            </CardContent>
          </Card>
        </>
      )}

      {error && (
        <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-3 py-2 text-sm text-destructive">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          {error}
        </div>
      )}
      {message && (
        <div className="flex items-start gap-2 rounded-lg border border-green-500/30 bg-green-500/10 px-3 py-2 text-sm text-green-400">
          <CheckCircle2 className="mt-0.5 size-4 shrink-0" />
          {message}
        </div>
      )}

      <div className="space-y-3">
        <SlowLoadingFormHint active={isSaving} messageKey="settings-save" />
        <Button onClick={onSave} disabled={isSaving || isLoading}>
          {isSaving ? <Loader2 className="size-4 animate-spin" /> : <Save className="size-4" />}
          Save preferences
        </Button>
      </div>
    </div>
  )
}
