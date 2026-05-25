import { apiFetch, parseErrorMessage } from "@/lib/apiClient"

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

  const response = await apiFetch(`/upload-resume`, {
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
