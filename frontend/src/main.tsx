import { StrictMode } from "react"
import { createRoot } from "react-dom/client"
import { QueryClientProvider } from "@tanstack/react-query"

import { AuthProvider } from "@/context/AuthContext"
import { RealtimeProvider } from "@/context/RealtimeContext"
import { queryClient } from "@/lib/queryClient"
import App from "./App.tsx"
import "./index.css"

document.documentElement.classList.add("dark")

if ("serviceWorker" in navigator && import.meta.env.PROD) {
  window.addEventListener("load", () => {
    navigator.serviceWorker.register("/sw.js").catch(() => {})
  })
}

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <RealtimeProvider>
          <App />
        </RealtimeProvider>
      </AuthProvider>
    </QueryClientProvider>
  </StrictMode>
)
