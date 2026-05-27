import { Component } from "react"

import { Button } from "@/components/ui/button"

export class AppErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null }
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error("[Career OS] UI error", error, info)
  }

  handleReload = () => {
    window.location.reload()
  }

  render() {
    if (this.state.error) {
      return (
        <div className="neon-app-shell flex min-h-svh flex-col items-center justify-center gap-4 bg-background p-6 text-center">
          <h1 className="text-lg font-semibold">Something went wrong</h1>
          <p className="max-w-md text-sm text-muted-foreground">
            The app hit an unexpected error. Reloading usually fixes this after a new deploy.
          </p>
          <Button type="button" onClick={this.handleReload}>
            Reload Career OS
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}
