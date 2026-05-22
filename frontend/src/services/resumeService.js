const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8001"

const ALLOWED_EXTENSIONS = [".pdf", ".docx"]
const ALLOWED_MIME_TYPES = [
  "application/pdf",
  "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
]

/**
 * @param {File} file
 * @returns {string|null}
 */
export function validateResumeFile(file) {
  if (!file) {
    return "Please select a resume file."
  }

  const extension = file.name.slice(file.name.lastIndexOf(".")).toLowerCase()
  if (!ALLOWED_EXTENSIONS.includes(extension)) {
    return "Only PDF and DOCX files are supported."
  }

  if (file.type && !ALLOWED_MIME_TYPES.includes(file.type)) {
    return "Invalid file type. Only PDF and DOCX files are supported."
  }

  return null
}

/**
 * @param {Response} response
 * @returns {Promise<string>}
 */
async function parseErrorMessage(response) {
  try {
    const data = await response.json()
    const detail = data?.detail

    if (typeof detail === "string") {
      return detail
    }

    if (detail?.message) {
      return detail.message
    }

    if (Array.isArray(detail) && detail[0]?.msg) {
      return detail[0].msg
    }

    return data?.message ?? `Request failed (${response.status})`
  } catch {
    return `Request failed (${response.status})`
  }
}

/**
 * Upload a resume and return parsed intelligence from the backend.
 *
 * @param {File} file
 * @param {{ onUploading?: () => void, onParsing?: () => void }} [callbacks]
 * @returns {Promise<Record<string, unknown>>}
 */
export async function uploadResume(file, callbacks = {}) {
  const validationError = validateResumeFile(file)
  if (validationError) {
    throw new Error(validationError)
  }

  const formData = new FormData()
  formData.append("file", file)

  callbacks.onUploading?.()

  const response = await fetch(`${API_BASE_URL}/upload-resume`, {
    method: "POST",
    body: formData,
  })

  callbacks.onParsing?.()

  if (!response.ok) {
    const message = await parseErrorMessage(response)
    throw new Error(message)
  }

  return response.json()
}
