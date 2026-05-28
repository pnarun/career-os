import { Component } from "react"

import { CareerOsLogo } from "@/components/brand/CareerOsLogo"
import { Button } from "@/components/ui/button"

const PROD_REDIRECT_SECONDS = 5
const LANDING_PAGE_PATH = "/"
const IS_PROD = import.meta.env.PROD

export class AppErrorBoundary extends Component {
  constructor(props) {
    super(props)
    this.state = { error: null, redirectSecondsLeft: PROD_REDIRECT_SECONDS }
    this.redirectIntervalId = null
    this.redirectTimeoutId = null
  }

  static getDerivedStateFromError(error) {
    return { error }
  }

  componentDidCatch(error, info) {
    console.error("[Career OS] UI error", error, info)
  }

  componentDidUpdate(_, prevState) {
    if (!prevState.error && this.state.error) {
      this.startProdRedirectCountdown()
    }
  }

  componentWillUnmount() {
    this.clearRedirectTimers()
  }

  clearRedirectTimers = () => {
    if (this.redirectIntervalId) {
      window.clearInterval(this.redirectIntervalId)
      this.redirectIntervalId = null
    }
    if (this.redirectTimeoutId) {
      window.clearTimeout(this.redirectTimeoutId)
      this.redirectTimeoutId = null
    }
  }

  startProdRedirectCountdown = () => {
    if (!IS_PROD) return
    this.clearRedirectTimers()
    this.setState({ redirectSecondsLeft: PROD_REDIRECT_SECONDS })
    this.redirectIntervalId = window.setInterval(() => {
      this.setState((prev) => ({
        redirectSecondsLeft: Math.max(0, prev.redirectSecondsLeft - 1),
      }))
    }, 1000)
    this.redirectTimeoutId = window.setTimeout(() => {
      window.location.assign(LANDING_PAGE_PATH)
    }, PROD_REDIRECT_SECONDS * 1000)
  }

  handleReload = () => {
    if (IS_PROD) {
      window.location.assign(LANDING_PAGE_PATH)
      return
    }
    window.location.reload()
  }

  render() {
    if (this.state.error) {
      return (
        <div className="neon-app-shell flex min-h-svh flex-col items-center justify-center gap-4 bg-background p-6 text-center">
          <CareerOsLogo variant="full" size="md" className="mx-auto" />
          <h1 className="text-lg font-semibold">Something went wrong</h1>
          <p className="max-w-md text-sm text-muted-foreground">
            {IS_PROD
              ? `We hit a temporary issue and have logged it. We will redirect you to the landing page in ${this.state.redirectSecondsLeft} seconds.`
              : "The app hit an unexpected error. Reloading usually fixes this after code changes."}
          </p>
          <Button type="button" onClick={this.handleReload}>
            {IS_PROD ? "Go to landing page now" : "Reload Career OS"}
          </Button>
        </div>
      )
    }
    return this.props.children
  }
}
