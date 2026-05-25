import { scoreColor, scoreRingColor } from "@/services/resumeAiService"

export function AtsScoreGauge({ score, label = "ATS Score", size = 140 }) {
  const radius = (size - 16) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = scoreRingColor(score)

  return (
    <div className="relative flex flex-col items-center gap-2" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="currentColor"
          strokeWidth="10"
          className="text-muted/30"
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={color}
          strokeWidth="10"
          strokeLinecap="round"
          strokeDasharray={circumference}
          strokeDashoffset={offset}
          style={{ transition: "stroke-dashoffset 0.6s ease" }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className={`text-3xl font-bold ${scoreColor(score)}`}>{score}</span>
        <span className="text-xs text-muted-foreground">{label}</span>
      </div>
    </div>
  )
}

export function FactorBar({ label, value }) {
  return (
    <div className="space-y-1">
      <div className="flex justify-between text-xs">
        <span className="text-muted-foreground">{label}</span>
        <span className={scoreColor(value)}>{value}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted/40">
        <div
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-sky-500 transition-all duration-500"
          style={{ width: `${Math.min(100, value)}%` }}
        />
      </div>
    </div>
  )
}

export function SkillRadarChart({ data }) {
  if (!data?.length) return null
  const size = 220
  const center = size / 2
  const maxR = 80
  const angleStep = (2 * Math.PI) / data.length

  const points = data.map((item, i) => {
    const angle = i * angleStep - Math.PI / 2
    const r = (item.score / 100) * maxR
    return {
      x: center + r * Math.cos(angle),
      y: center + r * Math.sin(angle),
      label: item.category,
    }
  })

  const polygon = points.map((p) => `${p.x},${p.y}`).join(" ")

  return (
    <svg width={size} height={size} className="mx-auto">
      {[0.25, 0.5, 0.75, 1].map((scale) => (
        <circle
          key={scale}
          cx={center}
          cy={center}
          r={maxR * scale}
          fill="none"
          stroke="currentColor"
          strokeOpacity={0.15}
        />
      ))}
      <polygon
        points={polygon}
        fill="rgba(99,102,241,0.25)"
        stroke="#818cf8"
        strokeWidth="2"
      />
      {points.map((p) => (
        <text
          key={p.label}
          x={p.x}
          y={p.y}
          textAnchor="middle"
          className="fill-muted-foreground text-[9px]"
          dy={p.y < center ? -8 : 14}
        >
          {p.label}
        </text>
      ))}
    </svg>
  )
}

export function KeywordHeatmap({ missing = [], underrepresented = [] }) {
  const items = [
    ...missing.map((k) => ({ ...k, heat: "high" })),
    ...underrepresented.map((k) => ({ ...k, heat: "medium" })),
  ].slice(0, 12)

  if (!items.length) {
    return <p className="text-sm text-muted-foreground">No keyword gaps detected.</p>
  }

  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
      {items.map((item) => (
        <div
          key={item.keyword}
          className={
            item.heat === "high"
              ? "rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2"
              : "rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-2"
          }
        >
          <p className="text-sm font-medium">{item.keyword}</p>
          <p className="text-xs capitalize text-muted-foreground">{item.status}</p>
        </div>
      ))}
    </div>
  )
}
