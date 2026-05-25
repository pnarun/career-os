import { scoreColor, scoreRingColor } from "@/services/interviewAiService"

export function ReadinessGauge({ score, label, size = 100 }) {
  const radius = (size - 12) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference

  return (
    <div className="relative flex flex-col items-center" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle cx={size / 2} cy={size / 2} r={radius} fill="none" stroke="currentColor" strokeWidth="8" className="text-muted/30" />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={scoreRingColor(score)}
          strokeWidth="8"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-xl font-bold ${scoreColor(score)}`}>{score}</span>
        <span className="text-[10px] text-muted-foreground">{label}</span>
      </div>
    </div>
  )
}

export function TopicConfidenceBars({ topics = [] }) {
  if (!topics.length) return <p className="text-sm text-muted-foreground">No topic data yet.</p>
  return (
    <div className="space-y-2">
      {topics.map((item) => (
        <div key={item.topic} className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">{item.topic}</span>
            <span className={scoreColor(item.confidence)}>{item.confidence}%</span>
          </div>
          <div className="h-1.5 overflow-hidden rounded-full bg-muted/40">
            <div
              className="h-full rounded-full bg-indigo-500 transition-all"
              style={{ width: `${item.confidence}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  )
}

export function PrepProgressBar({ completed, total }) {
  const pct = total ? Math.round((completed / total) * 100) : 0
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs text-muted-foreground">
        <span>Preparation progress</span>
        <span>{pct}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted/40">
        <div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
