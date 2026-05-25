import { StrictMode } from "react"
import { createRoot } from "react-dom/client"

import { AuthProvider } from "@/context/AuthContext"
import { RealtimeProvider } from "@/context/RealtimeContext"
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
    <AuthProvider>
      <RealtimeProvider>
        <App />
      </RealtimeProvider>
    </AuthProvider>
  </StrictMode>
)
