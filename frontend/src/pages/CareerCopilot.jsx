import { useCallback, useEffect, useRef, useState } from "react"
import {
  Bot,
  Loader2,
  Send,
  Sparkles,
  Target,
  TrendingUp,
  User,
  Zap,
} from "lucide-react"

import { SlowLoadingFormHint, SlowLoadingPageCenter } from "@/components/SlowLoadingStatus"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { cn } from "@/lib/utils"
import {
  getCopilotHistory,
  getCopilotOverview,
  runCopilotQuickAction,
  sendCopilotMessage,
  SUGGESTED_PROMPTS,
} from "@/services/copilotService"

function formatMessage(text) {
  if (!text) return null
  return text.split("\n").map((line, i) => {
    const bold = line.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    if (line.startsWith("• ") || line.startsWith("- ")) {
      return (
        <p key={i} className="ml-2 text-sm" dangerouslySetInnerHTML={{ __html: bold.slice(2) }} />
      )
    }
    return (
      <p
        key={i}
        className={cn("text-sm", line.startsWith("**") && "font-medium")}
        dangerouslySetInnerHTML={{ __html: bold }}
      />
    )
  })
}

function RecommendationCard({ card }) {
  const Icon = card.type === "job" ? Target : card.type === "skill" ? TrendingUp : Sparkles

  return (
    <div className="rounded-lg border border-border bg-muted/20 p-3">
      <div className="flex items-start gap-2">
        <Icon className="mt-0.5 size-4 shrink-0 text-indigo-400" />
        <div className="min-w-0 flex-1">
          <p className="text-sm font-medium">{card.title}</p>
          {card.subtitle ? <p className="text-xs text-muted-foreground">{card.subtitle}</p> : null}
          {card.reasons?.length ? (
            <ul className="mt-1 space-y-0.5">
              {card.reasons.slice(0, 3).map((r) => (
                <li key={r} className="text-[11px] text-muted-foreground">
                  · {r}
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      </div>
    </div>
  )
}

export function CareerCopilot() {
  const [overview, setOverview] = useState(null)
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState("")
  const [sessionId, setSessionId] = useState("")
  const [loading, setLoading] = useState(false)
  const [bootLoading, setBootLoading] = useState(true)
  const [error, setError] = useState(null)
  const [history, setHistory] = useState([])
  const bottomRef = useRef(null)

  const loadOverview = useCallback(async () => {
    setBootLoading(true)
    try {
      const [ov, hist] = await Promise.all([
        getCopilotOverview(),
        getCopilotHistory(10).catch(() => ({ history: [] })),
      ])
      setOverview(ov)
      setHistory(hist.history || [])
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load copilot")
    } finally {
      setBootLoading(false)
    }
  }, [])

  useEffect(() => {
    loadOverview()
  }, [loadOverview])

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages, loading])

  const appendExchange = (userMsg, response) => {
    setSessionId(response.session_id || sessionId)
    setMessages((prev) => [
      ...prev,
      { role: "user", content: userMsg },
      {
        role: "assistant",
        content: response.message,
        intent: response.intent,
        reasons: response.reasons,
        recommendations: response.recommendations,
        source: response.source,
      },
    ])
  }

  const send = async (text) => {
    const msg = text.trim()
    if (!msg || loading) return
    setLoading(true)
    setError(null)
    try {
      const response = await sendCopilotMessage(msg, sessionId)
      appendExchange(msg, response)
      setInput("")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message")
    } finally {
      setLoading(false)
    }
  }

  const runAction = async (actionId) => {
    setLoading(true)
    setError(null)
    try {
      const response = await runCopilotQuickAction(actionId, sessionId)
      const action = overview?.quick_actions?.find((a) => a.id === actionId)
      appendExchange(action?.label || actionId, response)
    } catch (err) {
      setError(err instanceof Error ? err.message : "Quick action failed")
    } finally {
      setLoading(false)
    }
  }

  if (bootLoading) {
    return <SlowLoadingPageCenter active messageKey="copilot-boot" />
  }

  const ctx = overview?.context_summary

  return (
    <div className="mx-auto flex h-[calc(100svh-7rem)] max-w-6xl flex-col gap-4 lg:h-[calc(100svh-8rem)] lg:flex-row">
      {/* Sidebar panel */}
      <div className="flex shrink-0 flex-col gap-3 lg:w-72">
        <Card className="border-indigo-500/20 bg-gradient-to-br from-indigo-500/10 via-background to-background">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Bot className="size-4 text-indigo-400" />
              Career Copilot
            </CardTitle>
            <CardDescription>
              {overview?.gemini_enabled ? "AI-enhanced · grounded in your data" : "Grounded career guidance"}
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-1 text-xs text-muted-foreground">
            {ctx ? (
              <>
                <p>{ctx.jobs_in_scan} jobs · {ctx.avg_match}% avg match</p>
                <p>Growth score: {ctx.growth_score} · {ctx.primary_role || "General"}</p>
              </>
            ) : null}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
              Quick Actions
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-1.5">
            {(overview?.quick_actions || []).map((action) => (
              <Button
                key={action.id}
                variant="outline"
                size="sm"
                className="h-auto w-full justify-start whitespace-normal py-2 text-left text-xs"
                disabled={loading}
                onClick={() => runAction(action.id)}
              >
                <Zap className="mr-2 size-3 shrink-0 text-indigo-400" />
                {action.label}
              </Button>
            ))}
          </CardContent>
        </Card>

        {history.length > 0 ? (
          <Card className="hidden lg:block">
            <CardHeader className="pb-2">
              <CardTitle className="text-xs font-medium uppercase tracking-wide text-muted-foreground">
                Recent Insights
              </CardTitle>
            </CardHeader>
            <CardContent className="max-h-40 space-y-2 overflow-y-auto">
              {history.slice(0, 5).map((h) => (
                <p key={h.id} className="truncate text-[11px] text-muted-foreground">
                  {h.user_message || h.message || h.title}
                </p>
              ))}
            </CardContent>
          </Card>
        ) : null}
      </div>

      {/* Chat area */}
      <Card className="flex min-h-0 flex-1 flex-col overflow-hidden">
        <CardHeader className="shrink-0 border-b border-border pb-3">
          <CardTitle className="text-sm">Ask anything about your career</CardTitle>
          <CardDescription>
            Recommendations are based on your resume, jobs, applications, and analytics
          </CardDescription>
        </CardHeader>

        <CardContent className="flex min-h-0 flex-1 flex-col gap-3 p-0">
          <div className="flex-1 space-y-4 overflow-y-auto p-4">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center gap-4 py-8 text-center">
                <Bot className="size-12 text-indigo-400/60" />
                <p className="max-w-md text-sm text-muted-foreground">
                  Ask about job matches, skills to learn, interview prep, application strategy, or market trends.
                </p>
                <div className="flex flex-wrap justify-center gap-2">
                  {SUGGESTED_PROMPTS.map((prompt) => (
                    <button
                      key={prompt}
                      type="button"
                      className="rounded-full border border-border bg-muted/30 px-3 py-1.5 text-xs hover:border-indigo-500/40 hover:bg-indigo-500/10"
                      onClick={() => send(prompt)}
                    >
                      {prompt}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              messages.map((msg, idx) => (
                <div
                  key={`${msg.role}-${idx}`}
                  className={cn("flex gap-3", msg.role === "user" ? "justify-end" : "justify-start")}
                >
                  {msg.role === "assistant" ? (
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-indigo-500/20">
                      <Bot className="size-4 text-indigo-400" />
                    </div>
                  ) : null}
                  <div
                    className={cn(
                      "max-w-[85%] rounded-xl px-4 py-3",
                      msg.role === "user"
                        ? "bg-primary text-primary-foreground"
                        : "border border-border bg-muted/30"
                    )}
                  >
                    {msg.role === "user" ? (
                      <p className="text-sm">{msg.content}</p>
                    ) : (
                      <div className="space-y-2">{formatMessage(msg.content)}</div>
                    )}
                    {msg.recommendations?.length ? (
                      <div className="mt-3 space-y-2">
                        {msg.recommendations.map((card, i) => (
                          <RecommendationCard key={`${card.title}-${i}`} card={card} />
                        ))}
                      </div>
                    ) : null}
                  </div>
                  {msg.role === "user" ? (
                    <div className="flex size-8 shrink-0 items-center justify-center rounded-full bg-muted">
                      <User className="size-4" />
                    </div>
                  ) : null}
                </div>
              ))
            )}
            {loading ? (
              <SlowLoadingFormHint active messageKey="copilot-chat" className="mx-1" />
            ) : null}
            <div ref={bottomRef} />
          </div>

          {error ? (
            <p className="shrink-0 px-4 text-sm text-destructive">{error}</p>
          ) : null}

          <form
            className="flex shrink-0 gap-2 border-t border-border p-4"
            onSubmit={(e) => {
              e.preventDefault()
              send(input)
            }}
          >
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Ask a career question…"
              disabled={loading}
              className="flex-1 rounded-lg border border-border bg-background px-3 py-2 text-sm outline-none focus:border-indigo-500/50 focus:ring-1 focus:ring-indigo-500/30"
            />
            <Button type="submit" disabled={loading || !input.trim()}>
              <Send className="size-4" />
            </Button>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}
