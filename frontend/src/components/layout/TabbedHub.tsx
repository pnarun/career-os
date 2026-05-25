import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

export type HubTab = {
  id: string
  label: string
}

type TabbedHubProps = {
  title: string
  description?: string
  tabs: HubTab[]
  activeTab: string
  onTabChange: (tabId: string) => void
  children: ReactNode
  tourId?: string
}

export function TabbedHub({
  title,
  description,
  tabs,
  activeTab,
  onTabChange,
  children,
  tourId,
}: TabbedHubProps) {
  return (
    <div className="mx-auto max-w-6xl space-y-4" data-tour-id={tourId}>
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">{title}</h2>
        {description ? (
          <p className="text-sm text-muted-foreground">{description}</p>
        ) : null}
      </div>

      <div
        role="tablist"
        className="flex flex-wrap gap-1 rounded-lg border border-border bg-muted/20 p-1"
      >
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={activeTab === tab.id}
            data-tour-id={`${tourId}-${tab.id}`}
            onClick={() => onTabChange(tab.id)}
            className={cn(
              "rounded-md px-3 py-2 text-sm font-medium transition-colors",
              activeTab === tab.id
                ? "bg-background text-foreground shadow-sm"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div role="tabpanel">{children}</div>
    </div>
  )
}
