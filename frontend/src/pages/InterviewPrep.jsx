import { useCallback, useEffect, useState } from "react"
import {
  AlertCircle,
  BookOpen,
  CheckCircle2,
  Clock,
  Loader2,
  MessageSquare,
  Mic,
  Target,
} from "lucide-react"

import {
  PrepProgressBar,
  ReadinessGauge,
  TopicConfidenceBars,
} from "@/components/interviewPrep/InterviewPrepCharts"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import {
  completeMockSession,
  getInterviewPrepJobs,
  getInterviewPrepOverview,
  recordPractice,
  scoreColor,
  startMockInterview,
} from "@/services/interviewAiService"
import { getStatusBadgeStyle, getStatusLabel } from "@/utils/applicationStatusUtils"

const STATUS_FILTERS = [
  { id: "all", label: "All" },
  { id: "saved", label: "Saved" },
  { id: "applied", label: "Applied" },
  { id: "interview", label: "Interview" },
]

function QuestionList({ items, onPractice, jobId }) {
  if (!items?.length) return <p className="text-sm text-muted-foreground">No questions generated.</p>
  return (
    <ul className="space-y-2">
      {items.map((q, idx) => (
        <li key={`${q.question}-${idx}`} className="rounded-lg border border-border bg-muted/20 p-3 text-sm">
          <p className="font-medium">{q.question}</p>
          {q.tip && <p className="mt-1 text-xs text-muted-foreground">{q.tip}</p>}
          {q.source && (
            <a
              href={q.source}
              target="_blank"
              rel="noopener noreferrer"
              className="mt-1 block truncate text-[10px] text-sky-400 hover:underline"
            >
              Source
            </a>
          )}
          <div className="mt-2 flex items-center justify-between">
            <span className="text-xs capitalize text-indigo-400">{q.category || q.topic}</span>
            {onPractice && (
              <Button
                size="sm"
                variant="ghost"
                className="h-7 text-xs"
                onClick={() => onPractice(q, idx)}
              >
                Mark practiced
              </Button>
            )}
          </div>
        </li>
      ))}
    </ul>
  )
}

export function InterviewPrep() {
  const [loading, setLoading] = useState(true)
  const [detailLoading, setDetailLoading] = useState(false)
  const [error, setError] = useState(null)
  const [jobList, setJobList] = useState([])
  const [statusFilter, setStatusFilter] = useState("all")
  const [selectedJobId, setSelectedJobId] = useState("")
  const [data, setData] = useState(null)
  const [mockSession, setMockSession] = useState(null)
  const [mockBusy, setMockBusy] = useState(false)
  const [currentQ, setCurrentQ] = useState(0)
  const [timer, setTimer] = useState(0)

  const loadJobs = useCallback(async (filter) => {
    setLoading(true)
    setError(null)
    try {
      const result = await getInterviewPrepJobs(filter)
      setJobList(result.jobs || [])
      if (result.jobs?.length > 0) {
        setSelectedJobId((prev) =>
          prev && result.jobs.some((j) => j.job_id === prev) ? prev : result.jobs[0].job_id
        )
      } else {
        setSelectedJobId("")
        setData(null)
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load jobs")
      setJobList([])
    } finally {
      setLoading(false)
    }
  }, [])

  const loadOverview = useCallback(async (jobId) => {
    if (!jobId) {
      setData(null)
      return
    }
    setDetailLoading(true)
    setError(null)
    try {
      const overview = await getInterviewPrepOverview({ job_id: jobId })
      setData(overview)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load interview prep")
      setData(null)
    } finally {
      setDetailLoading(false)
    }
  }, [])

  useEffect(() => {
    loadJobs(statusFilter)
  }, [statusFilter, loadJobs])

  useEffect(() => {
    if (selectedJobId) loadOverview(selectedJobId)
  }, [selectedJobId, loadOverview])

  useEffect(() => {
    if (!mockSession) return undefined
    const interval = setInterval(() => setTimer((t) => t + 1), 1000)
    return () => clearInterval(interval)
  }, [mockSession])

  const onStartMock = async (category = "mixed") => {
    setMockBusy(true)
    try {
      const session = await startMockInterview({
        job_id: data?.job_id || "",
        job_title: data?.job_title || "",
        category,
      })
      setMockSession(session)
      setCurrentQ(0)
      setTimer(0)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mock interview failed")
    } finally {
      setMockBusy(false)
    }
  }

  const onFinishMock = async () => {
    if (!mockSession) return
    try {
      const progress = await completeMockSession({
        job_id: data?.job_id || "",
        session_id: mockSession.session_id,
        category: mockSession.category,
      })
      setData((prev) => (prev ? { ...prev, progress } : prev))
    } catch {
      /* optional */
    }
    setMockSession(null)
    setTimer(0)
  }

  const onPractice = async (q, idx) => {
    try {
      const progress = await recordPractice({
        job_id: data?.job_id || "",
        question_id: `q-${idx}`,
        question_text: q.question,
        category: q.category || "technical",
      })
      setData((prev) => (prev ? { ...prev, progress } : prev))
    } catch {
      /* optional */
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-[40vh] items-center justify-center">
        <Loader2 className="size-8 animate-spin text-muted-foreground" />
      </div>
    )
  }

  const selectedJob = jobList.find((j) => j.job_id === selectedJobId)
  const readiness = data?.readiness
  const questions = data?.questions
  const coding_topics = data?.coding_topics
  const preparation_plan = data?.preparation_plan
  const progress = data?.progress
  const company_patterns = data?.company_patterns
  const practiced = progress?.practiced_questions?.length || 0
  const totalQ = questions?.total_count || 1

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="flex items-center gap-2 text-2xl font-bold">
          <Mic className="size-6 text-violet-400" />
          Interview Prep
        </h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Prepare for interviews across your saved and applied jobs
        </p>
      </div>

      <div className="rounded-lg border border-violet-500/20 bg-violet-500/5 px-4 py-3 text-sm text-muted-foreground">
        Practice mode only — not for use during live interviews.
      </div>

      <div className="flex flex-wrap gap-2">
        {STATUS_FILTERS.map((f) => (
          <Button
            key={f.id}
            size="sm"
            variant={statusFilter === f.id ? "default" : "outline"}
            onClick={() => setStatusFilter(f.id)}
          >
            {f.label}
            {f.id === statusFilter && jobList.length > 0 ? ` (${jobList.length})` : ""}
          </Button>
        ))}
      </div>

      {jobList.length === 0 ? (
        <Card>
          <CardContent className="py-12 text-center">
            <AlertCircle className="mx-auto mb-3 size-10 text-muted-foreground" />
            <p className="font-medium">No jobs in this filter</p>
            <p className="mt-1 text-sm text-muted-foreground">
              Save jobs or mark them as applied from the Jobs page to start interview preparation.
            </p>
            <Button className="mt-4" variant="outline" onClick={() => loadJobs(statusFilter)}>
              Refresh
            </Button>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {jobList.map((job) => (
            <button
              key={job.job_id}
              type="button"
              onClick={() => setSelectedJobId(job.job_id)}
              className={cn(
                "rounded-xl border p-4 text-left transition-colors",
                selectedJobId === job.job_id
                  ? "border-violet-500/50 bg-violet-500/10"
                  : "border-border bg-muted/20 hover:border-violet-500/30"
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                  <p className="truncate font-medium">{job.title}</p>
                  <p className="truncate text-sm text-muted-foreground">{job.company}</p>
                </div>
                <span className={cn("shrink-0 text-lg font-bold", scoreColor(job.readiness_score))}>
                  {job.readiness_score}
                </span>
              </div>
              <div className="mt-2 flex flex-wrap items-center gap-2">
                <span
                  className={cn(
                    "rounded-md border px-2 py-0.5 text-[10px] font-medium",
                    getStatusBadgeStyle(job.status)
                  )}
                >
                  {getStatusLabel(job.status)}
                </span>
                {job.match_score > 0 && (
                  <span className="text-xs text-muted-foreground">{job.match_score}% match</span>
                )}
                {job.practiced_count > 0 && (
                  <span className="text-xs text-muted-foreground">
                    {job.practiced_count} practiced
                  </span>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {error && <p className="text-sm text-destructive">{error}</p>}

      {detailLoading && (
        <div className="flex justify-center py-12">
          <Loader2 className="size-8 animate-spin text-muted-foreground" />
        </div>
      )}

      {!detailLoading && data && readiness && (
        <>
          <div className="rounded-lg border border-border bg-muted/10 px-4 py-3">
            <p className="text-sm text-muted-foreground">Preparing for</p>
            <p className="font-semibold">
              {data.job_title} · {data.company}
            </p>
            {selectedJob?.focus_label && (
              <p className="text-xs text-muted-foreground">{selectedJob.focus_label}</p>
            )}
            {questions?.question_source && (
              <p className="mt-1 text-xs text-sky-400">
                Questions from:{" "}
                {questions.question_source === "web_cache"
                  ? "web (cached)"
                  : questions.question_source}
              </p>
            )}
          </div>

      {/* Readiness */}
      <div className="grid gap-4 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Overall Readiness</CardTitle>
          </CardHeader>
          <CardContent className="flex justify-center">
            <ReadinessGauge score={readiness.readiness_score} label="Ready" size={120} />
          </CardContent>
        </Card>
        <Card>
          <CardContent className="flex flex-wrap justify-center gap-4 pt-6">
            <ReadinessGauge score={readiness.technical_readiness} label="Technical" />
            <ReadinessGauge score={readiness.behavioral_readiness} label="Behavioral" />
            <ReadinessGauge score={readiness.system_design_readiness} label="System Design" />
          </CardContent>
        </Card>
        <Card className="lg:col-span-2">
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Topic Confidence</CardTitle>
            <CardDescription>{readiness.focus_label}</CardDescription>
          </CardHeader>
          <CardContent>
            <TopicConfidenceBars topics={readiness.topic_confidence} />
          </CardContent>
        </Card>
      </div>

      <PrepProgressBar completed={practiced} total={totalQ} />

      {readiness.weak_areas?.length > 0 && (
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Weak Areas</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {readiness.weak_areas.map((area) => (
              <span key={area} className="rounded-md border border-amber-500/30 bg-amber-500/10 px-2 py-1 text-xs">
                {area}
              </span>
            ))}
          </CardContent>
        </Card>
      )}

      {/* Mock Interview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Clock className="size-4" />
            Mock Interview
          </CardTitle>
          <CardDescription>Timed practice — {progress?.mock_sessions_completed || 0} sessions completed</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {!mockSession ? (
            <div className="flex flex-wrap gap-2">
              {["mixed", "technical", "behavioral", "system_design"].map((cat) => (
                <Button key={cat} variant="outline" disabled={mockBusy} onClick={() => onStartMock(cat)}>
                  {mockBusy ? <Loader2 className="mr-1 size-4 animate-spin" /> : null}
                  {cat.replace("_", " ")}
                </Button>
              ))}
            </div>
          ) : (
            <div className="space-y-3 rounded-lg border border-border bg-muted/20 p-4">
              <div className="flex items-center justify-between text-sm">
                <span>{mockSession.round_label}</span>
                <span className="font-mono text-amber-400">{Math.floor(timer / 60)}:{String(timer % 60).padStart(2, "0")}</span>
              </div>
              <p className="text-sm font-medium">
                Q{currentQ + 1}/{mockSession.total_questions}:{" "}
                {mockSession.questions[currentQ]?.question}
              </p>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  disabled={currentQ <= 0}
                  onClick={() => setCurrentQ((q) => q - 1)}
                >
                  Previous
                </Button>
                <Button
                  size="sm"
                  onClick={() => {
                    if (currentQ < mockSession.questions.length - 1) setCurrentQ((q) => q + 1)
                    else onFinishMock()
                  }}
                >
                  {currentQ < mockSession.questions.length - 1 ? "Next" : "Finish session"}
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Questions */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Target className="size-4" />
              Technical Questions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <QuestionList items={questions.technical_questions} onPractice={onPractice} jobId={data.job_id} />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <MessageSquare className="size-4" />
              Behavioral Questions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <QuestionList items={questions.behavioral_questions} onPractice={onPractice} jobId={data.job_id} />
          </CardContent>
        </Card>
      </div>

      {/* Coding topics + Plan */}
      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Coding & System Design Topics</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {coding_topics.dsa_topics?.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">DSA</p>
                <div className="flex flex-wrap gap-1">
                  {coding_topics.dsa_topics.map((t) => (
                    <span key={t} className="rounded bg-muted px-2 py-0.5 text-xs">{t}</span>
                  ))}
                </div>
              </div>
            )}
            {coding_topics.system_design_topics?.length > 0 && (
              <div>
                <p className="mb-1 text-xs font-medium text-muted-foreground">System Design</p>
                <div className="flex flex-wrap gap-1">
                  {coding_topics.system_design_topics.map((t) => (
                    <span key={t} className="rounded bg-muted px-2 py-0.5 text-xs">{t}</span>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <BookOpen className="size-4" />
              Preparation Plan ({preparation_plan.total_days} days)
            </CardTitle>
            <CardDescription>~{preparation_plan.estimated_hours}h total</CardDescription>
          </CardHeader>
          <CardContent className="space-y-3">
            {preparation_plan.days?.map((day) => (
              <div key={day.day} className="rounded-lg border border-border p-3">
                <p className="text-sm font-medium">
                  Day {day.day} → {day.title}
                </p>
                <ul className="mt-1 space-y-0.5 text-xs text-muted-foreground">
                  {day.tasks?.map((task) => (
                    <li key={task} className="flex gap-1">
                      <CheckCircle2 className="mt-0.5 size-3 shrink-0" />
                      {task}
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>

      {company_patterns?.interview_trends?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Company Interview Patterns</CardTitle>
            <CardDescription>{company_patterns.company_type} · {company_patterns.role_emphasis}</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {company_patterns.interview_trends.map((t) => (
              <span key={t} className="rounded-md border border-border px-2 py-1 text-xs">{t}</span>
            ))}
          </CardContent>
        </Card>
      )}
        </>
      )}
    </div>
  )
}
