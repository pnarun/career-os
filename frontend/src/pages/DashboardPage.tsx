import {
  Briefcase,
  MousePointerClick,
  Radar,
  Send,
} from "lucide-react"

import { StatCard } from "@/components/dashboard/StatCard"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"

const stats = [
  {
    title: "Jobs Found",
    value: "—",
    description: "Total jobs discovered in the last scan",
    icon: Briefcase,
  },
  {
    title: "Easy Apply Jobs",
    value: "—",
    description: "Jobs eligible for one-click apply",
    icon: MousePointerClick,
  },
  {
    title: "Applications Sent",
    value: "—",
    description: "Submitted applications this cycle",
    icon: Send,
  },
  {
    title: "Scan Status",
    value: "Idle",
    description: "Current automation scan state",
    icon: Radar,
  },
]

export function DashboardPage() {
  return (
    <div className="space-y-6">
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.title} {...stat} />
        ))}
      </div>
      <Card>
        <CardHeader>
          <CardTitle>Activity</CardTitle>
          <CardDescription>
            Placeholder panel for upcoming scan and application logs
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex min-h-[200px] items-center justify-center rounded-lg border border-dashed border-border bg-muted/30">
            <p className="text-sm text-muted-foreground">
              Connect backend services to populate this area
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
