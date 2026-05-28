import { Component } from "react"

import { Button } from "@/components/ui/button"

/**
 * Isolates page-level crashes without taking down the full app shell.
 */
export class PageErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error("[Career OS] page error", error, info)
  }

  render() {
    if (this.state.error) {
      return (
        <div className="mx-auto max-w-lg rounded-lg border border-destructive/30 bg-destructive/10 p-6 text-center">
          <p className="text-sm font-medium text-foreground">This section failed to load</p>
          <p className="mt-2 text-xs text-muted-foreground">
            {this.state.error?.message || "An unexpected error occurred."}
          </p>
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="mt-4"
            onClick={() => this.setState({ error: null })}
          >
            Try again
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}
