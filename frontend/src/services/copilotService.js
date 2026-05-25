import { apiFetch, getApiBaseUrl, parseErrorMessage } from "@/lib/apiClient"

export async function getCopilotOverview() {
  const response = await apiFetch(`/copilot/overview`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function sendCopilotMessage(message, sessionId = "") {
  const response = await apiFetch(`/copilot/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function runCopilotQuickAction(actionId, sessionId = "") {
  const response = await apiFetch(`/copilot/quick-action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action_id: actionId, session_id: sessionId }),
  })
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export async function getCopilotHistory(limit = 20) {
  const response = await apiFetch(`/copilot/history?limit=${limit}`)
  if (!response.ok) throw new Error(await parseErrorMessage(response))
  return response.json()
}

export const SUGGESTED_PROMPTS = [
  "Which jobs fit me best?",
  "Why is my match score low?",
  "What skills should I learn next?",
  "Why am I not getting interviews?",
  "Which provider works best for me?",
  "Should I focus on backend or DevOps?",
]
