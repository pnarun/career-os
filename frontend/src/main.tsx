import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { QueryClientProvider } from "@tanstack/react-query"

import { AppErrorBoundary } from "@/components/AppErrorBoundary"
import { AuthProvider } from "@/context/AuthContext"
import { BackendWakeProvider } from "@/context/BackendWakeContext"
import { RealtimeProvider } from "@/context/RealtimeContext"
import { isPublicStandaloneRoute } from "@/lib/publicRoutes"
import { queryClient } from "@/lib/queryClient"
import { PrivacyPolicyPage } from "@/pages/PrivacyPolicyPage"
import App from "./App.tsx"
import "./index.css"

document.documentElement.classList.add("dark")

if ("serviceWorker" in navigator && import.meta.env.PROD) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {})
  })
}

function Root() {
  const isPrivacyPage = isPublicStandaloneRoute()

  return (
    <QueryClientProvider client={queryClient}>
      <BackendWakeProvider>
        <AuthProvider>
          <RealtimeProvider suspendOnPublicPages={isPrivacyPage}>
            {isPrivacyPage ? <PrivacyPolicyPage /> : <App />}
          </RealtimeProvider>
        </AuthProvider>
      </BackendWakeProvider>
    </QueryClientProvider>
  )
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <AppErrorBoundary>
      <Root />
    </AppErrorBoundary>
  </StrictMode>
)
