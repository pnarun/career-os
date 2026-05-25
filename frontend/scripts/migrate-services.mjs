import fs from "fs"
import path from "path"
import { fileURLToPath } from "url"

const dir = path.join(path.dirname(fileURLToPath(import.meta.url)), "..", "src", "services")
const skip = new Set(["authService.js", "preferencesService.js", "apiClient.js"])

for (const file of fs.readdirSync(dir).filter((f) => f.endsWith(".js"))) {
  if (skip.has(file)) continue
  const full = path.join(dir, file)
  let content = fs.readFileSync(full, "utf8")
  if (!content.includes("API_BASE_URL") && !content.includes('fetch(`${API_BASE_URL')) continue

  content = content.replace(
    /const API_BASE_URL =[\s\S]*?8001"\r?\n\r?\n/,
    ""
  )
  content = content.replace(
    /async function parseErrorMessage\(response\) \{[\s\S]*?\}\r?\n\r?\n/,
    ""
  )
  if (!content.includes('@/lib/apiClient')) {
    content = `import { apiFetch, getApiBaseUrl, parseErrorMessage } from "@/lib/apiClient"\n\n${content}`
  }
  content = content.replaceAll("fetch(`${API_BASE_URL}", "apiFetch(`")
  content = content.replaceAll("${API_BASE_URL}", "${getApiBaseUrl()}")
  fs.writeFileSync(full, content)
  console.log("updated", file)
}
