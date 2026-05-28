import { memo } from "react"
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Funnel,
  FunnelChart,
  LabelList,
  Legend,
  Line,
  LineChart,
  PolarAngleAxis,
  PolarGrid,
  PolarRadiusAxis,
  Radar,
  RadarChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts"

const CHART_TOOLTIP = {
  contentStyle: {
    background: "#1c1917",
    border: "1px solid #f59e0b",
    borderRadius: "8px",
    fontSize: "12px",
    color: "#fde68a",
  },
  labelStyle: { color: "#fbbf24", fontWeight: 600 },
  itemStyle: { color: "#fdba74" },
}

export const GrowthScoreGauge = memo(function GrowthScoreGauge({ score, size = 120 }) {
  const radius = (size - 16) / 2
  const circumference = 2 * Math.PI * radius
  const offset = circumference - (score / 100) * circumference
  const color = score >= 75 ? "#10b981" : score >= 50 ? "#0ea5e9" : "#f59e0b"

  return (
    <div className="relative flex flex-col items-center" style={{ width: size, height: size }}>
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
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-3xl font-bold tabular-nums">{score}</span>
        <span className="text-xs text-muted-foreground">Growth Score</span>
      </div>
    </div>
  )
})

export const SalaryBarChart = memo(function SalaryBarChart({ data }) {
  if (!data?.length) return null
  const chartData = data.slice(0, 8).map((item) => ({
    skill: item.skill?.length > 14 ? `${item.skill.slice(0, 12)}…` : item.skill,
    salary: item.avg_salary,
  }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
        <XAxis dataKey="skill" tick={{ fontSize: 11 }} angle={-30} textAnchor="end" height={60} />
        <YAxis tick={{ fontSize: 11 }} tickFormatter={(v) => `₹${(Number(v) / 100000).toFixed(1)}L`} />
        <Tooltip {...CHART_TOOLTIP} formatter={(v) => [`₹${Number(v).toLocaleString("en-IN")}`, "Avg Salary (INR)"]} />
        <Bar dataKey="salary" fill="#6366f1" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  )
})

export const SkillDemandChart = memo(function SkillDemandChart({ data }) {
  if (!data?.length) return null
  const chartData = data.slice(0, 10).map((item) => ({
    skill: item.skill?.length > 12 ? `${item.skill.slice(0, 10)}…` : item.skill,
    demand: item.demand_pct ?? item.demand_score,
    hasSkill: item.user_has_skill,
  }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} layout="vertical" margin={{ top: 4, right: 16, left: 8, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" horizontal={false} />
        <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
        <YAxis type="category" dataKey="skill" width={80} tick={{ fontSize: 11 }} />
        <Tooltip {...CHART_TOOLTIP} formatter={(v) => [`${v}%`, "Demand"]} />
        <Bar dataKey="demand" radius={[0, 4, 4, 0]}>
          {chartData.map((entry, i) => (
            <Cell key={entry.skill} fill={entry.hasSkill ? "#10b981" : "#6366f1"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
})

export const MarketTrendChart = memo(function MarketTrendChart({ rising, declining }) {
  const combined = [
    ...(rising || []).slice(0, 5).map((r) => ({ tech: r.technology, change: r.change_pct })),
    ...(declining || []).slice(0, 3).map((d) => ({ tech: d.technology, change: d.change_pct })),
  ]
  if (!combined.length) return null

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={combined} margin={{ top: 8, right: 8, left: 0, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
        <XAxis dataKey="tech" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" height={55} />
        <YAxis tick={{ fontSize: 11 }} unit="%" />
        <Tooltip {...CHART_TOOLTIP} formatter={(v) => [`${v > 0 ? "+" : ""}${v}%`, "Change"]} />
        <Bar dataKey="change" radius={[4, 4, 0, 0]}>
          {combined.map((entry) => (
            <Cell key={entry.tech} fill={entry.change >= 0 ? "#10b981" : "#ef4444"} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
})

export const ConversionFunnelChart = memo(function ConversionFunnelChart({ funnel }) {
  if (!funnel?.length) return null
  const data = funnel.map((stage) => ({
    name: stage.stage,
    value: Math.max(stage.count, 1),
    fill: stage.stage === "Offer" ? "#10b981" : stage.stage === "Interview" ? "#0ea5e9" : "#6366f1",
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <FunnelChart>
        <Tooltip {...CHART_TOOLTIP} />
        <Funnel dataKey="value" data={data} isAnimationActive>
          <LabelList position="right" fill="hsl(var(--foreground))" stroke="none" dataKey="name" fontSize={12} />
        </Funnel>
      </FunnelChart>
    </ResponsiveContainer>
  )
})

export const ProviderRadarChart = memo(function ProviderRadarChart({ providers }) {
  if (!providers?.length) return null
  const chartData = providers.slice(0, 6).map((p) => ({
    provider: p.label,
    match: p.avg_match_score,
    remote: p.remote_opportunity_pct,
    quality: p.avg_quality_score,
    conversion: p.interview_conversion_rate,
  }))

  return (
    <ResponsiveContainer width="100%" height={280}>
      <RadarChart data={chartData}>
        <PolarGrid className="stroke-border/40" />
        <PolarAngleAxis dataKey="provider" tick={{ fontSize: 10 }} />
        <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fontSize: 10 }} />
        <Tooltip {...CHART_TOOLTIP} />
        <Legend wrapperStyle={{ fontSize: "11px" }} />
        <Radar name="Match" dataKey="match" stroke="#6366f1" fill="#6366f1" fillOpacity={0.2} />
        <Radar name="Remote" dataKey="remote" stroke="#10b981" fill="#10b981" fillOpacity={0.15} />
        <Radar name="Quality" dataKey="quality" stroke="#0ea5e9" fill="#0ea5e9" fillOpacity={0.15} />
      </RadarChart>
    </ResponsiveContainer>
  )
})

export const LocationHeatmapChart = memo(function LocationHeatmapChart({ heatmap }) {
  if (!heatmap?.length) return null
  const chartData = heatmap.slice(0, 10).map((h) => ({
    location: h.location?.length > 14 ? `${h.location.slice(0, 12)}…` : h.location,
    intensity: h.demand_intensity,
    jobs: h.job_count,
  }))

  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, left: 0, bottom: 40 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
        <XAxis dataKey="location" tick={{ fontSize: 10 }} angle={-25} textAnchor="end" height={55} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip {...CHART_TOOLTIP} />
        <Bar dataKey="intensity" fill="#8b5cf6" radius={[4, 4, 0, 0]} name="Demand intensity" />
      </BarChart>
    </ResponsiveContainer>
  )
})

export const GrowthTimelineChart = memo(function GrowthTimelineChart({ sessions }) {
  if (!sessions?.length) return null
  const chartData = [...sessions].reverse().map((s, i) => ({
    label: `Scan ${i + 1}`,
    jobs: s.qualified_jobs ?? s.qualified ?? 0,
  }))

  return (
    <ResponsiveContainer width="100%" height={200}>
      <LineChart data={chartData} margin={{ top: 8, right: 16, left: 0, bottom: 4 }}>
        <CartesianGrid strokeDasharray="3 3" className="stroke-border/40" />
        <XAxis dataKey="label" tick={{ fontSize: 11 }} />
        <YAxis tick={{ fontSize: 11 }} />
        <Tooltip {...CHART_TOOLTIP} />
        <Line type="monotone" dataKey="jobs" stroke="#6366f1" strokeWidth={2} dot={{ r: 4 }} name="Qualified jobs" />
      </LineChart>
    </ResponsiveContainer>
  )
})
