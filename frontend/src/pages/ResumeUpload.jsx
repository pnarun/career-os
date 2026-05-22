import { useCallback, useRef, useState } from "react"
import {
  AlertCircle,
  CheckCircle2,
  CloudUpload,
  FileText,
  Loader2,
  Mail,
  Sparkles,
} from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"
import { uploadResume, validateResumeFile } from "@/services/resumeService"

const ACCEPTED_FILES = ".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"

function formatTimestamp(iso) {
  if (!iso) return "—"
  try {
    return new Date(iso).toLocaleString(undefined, {
      dateStyle: "medium",
      timeStyle: "short",
    })
  } catch {
    return iso
  }
}

function TagList({ items, emptyLabel }) {
  if (!items?.length) {
    return <p className="text-sm text-muted-foreground">{emptyLabel}</p>
  }

  return (
    <div className="flex flex-wrap gap-2">
      {items.map((item) => (
        <span
          key={item}
          className="rounded-md bg-muted px-2.5 py-1 text-xs font-medium text-foreground"
        >
          {item}
        </span>
      ))}
    </div>
  )
}

function ProfileSection({ title, description, icon: Icon, children }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <div className="flex size-8 items-center justify-center rounded-lg bg-muted">
            <Icon className="size-4 text-muted-foreground" />
          </div>
          <div>
            <CardTitle className="text-base">{title}</CardTitle>
            <CardDescription>{description}</CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  )
}

export function ResumeUpload() {
  const inputRef = useRef(null)
  const [selectedFile, setSelectedFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [status, setStatus] = useState("idle")
  const [processingStep, setProcessingStep] = useState("uploading")
  const [error, setError] = useState(null)
  const [result, setResult] = useState(null)

  const isProcessing = status === "processing"

  const handleFile = useCallback((file) => {
    const validationError = validateResumeFile(file)
    if (validationError) {
      setError(validationError)
      setSelectedFile(null)
      return
    }
    setError(null)
    setSelectedFile(file)
    setResult(null)
    setStatus("idle")
  }, [])

  const onInputChange = (event) => {
    const file = event.target.files?.[0]
    if (file) handleFile(file)
  }

  const onDrop = (event) => {
    event.preventDefault()
    setIsDragging(false)
    const file = event.dataTransfer.files?.[0]
    if (file) handleFile(file)
  }

  const onSubmit = async () => {
    if (!selectedFile) {
      setError("Please select a resume file.")
      return
    }

    setError(null)
    setResult(null)
    setStatus("processing")
    setProcessingStep("uploading")

    try {
      const data = await uploadResume(selectedFile, {
        onUploading: () => setProcessingStep("uploading"),
        onParsing: () => setProcessingStep("parsing"),
      })
      setResult(data)
      setStatus("success")
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed. Please try again.")
      setStatus("error")
    }
  }

  const parsed = result?.parsed_profile
  const resume = result?.resume
  const upload = result?.upload

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <div>
        <h2 className="text-2xl font-semibold tracking-tight">Resume Intelligence</h2>
        <p className="mt-1 text-sm text-muted-foreground">
          Upload a resume to extract skills, contact signals, and experience keywords.
        </p>
      </div>

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Upload resume</CardTitle>
          <CardDescription>PDF or DOCX — processed securely via Cloudinary</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div
            role="button"
            tabIndex={0}
            onDragOver={(e) => {
              e.preventDefault()
              setIsDragging(true)
            }}
            onDragLeave={() => setIsDragging(false)}
            onDrop={onDrop}
            onClick={() => inputRef.current?.click()}
            onKeyDown={(e) => {
              if (e.key === "Enter" || e.key === " ") inputRef.current?.click()
            }}
            className={cn(
              "flex cursor-pointer flex-col items-center justify-center rounded-xl border border-dashed px-6 py-10 text-center transition-colors",
              isDragging
                ? "border-primary bg-primary/5"
                : "border-border bg-muted/20 hover:bg-muted/40"
            )}
          >
            <CloudUpload className="mb-3 size-8 text-muted-foreground" />
            <p className="text-sm font-medium">
              Drag and drop your resume here, or click to browse
            </p>
            <p className="mt-1 text-xs text-muted-foreground">PDF, DOCX — max 10 MB</p>
            {selectedFile && (
              <p className="mt-3 flex items-center gap-2 text-sm text-foreground">
                <FileText className="size-4 shrink-0" />
                {selectedFile.name}
              </p>
            )}
          </div>

          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_FILES}
            className="hidden"
            onChange={onInputChange}
          />

          <div className="flex flex-wrap items-center gap-3">
            <Button onClick={onSubmit} disabled={!selectedFile || isProcessing}>
              {isProcessing ? (
                <>
                  <Loader2 className="size-4 animate-spin" />
                  Processing…
                </>
              ) : (
                <>
                  <Sparkles className="size-4" />
                  Analyze resume
                </>
              )}
            </Button>
            {selectedFile && !isProcessing && (
              <Button
                variant="outline"
                onClick={() => {
                  setSelectedFile(null)
                  setResult(null)
                  setError(null)
                  setStatus("idle")
                  if (inputRef.current) inputRef.current.value = ""
                }}
              >
                Clear
              </Button>
            )}
          </div>

          {isProcessing && (
            <div className="rounded-lg border border-border bg-muted/30 px-4 py-3 text-sm">
              <div className="flex items-center gap-2 text-foreground">
                <Loader2 className="size-4 animate-spin" />
                {processingStep === "uploading"
                  ? "Uploading to Cloudinary…"
                  : "Parsing resume intelligence…"}
              </div>
              <p className="mt-1 text-xs text-muted-foreground">
                Extracting skills, contacts, and experience signals
              </p>
            </div>
          )}

          {status === "success" && (
            <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/30 px-4 py-3 text-sm text-foreground">
              <CheckCircle2 className="size-4 text-green-500" />
              {result?.message ?? "Resume uploaded successfully"}
            </div>
          )}

          {error && (
            <div className="flex items-start gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-sm text-destructive">
              <AlertCircle className="mt-0.5 size-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </CardContent>
      </Card>

      {result && (
        <>
          {/* Parsed Candidate Profile */}
          <div className="space-y-4">
            <h3 className="text-lg font-semibold tracking-tight">Parsed candidate profile</h3>
            <div className="grid gap-4 md:grid-cols-2">
              <ProfileSection
                title="Skills"
                description="Technologies matched from resume text"
                icon={Sparkles}
              >
                <TagList items={parsed?.skills} emptyLabel="No skills detected" />
              </ProfileSection>

              <ProfileSection
                title="Experience keywords"
                description="Role and impact signals"
                icon={FileText}
              >
                <TagList
                  items={parsed?.experience_keywords}
                  emptyLabel="No experience keywords detected"
                />
              </ProfileSection>

              <ProfileSection
                title="Emails"
                description="Contact addresses found in resume"
                icon={Mail}
              >
                {parsed?.emails?.length ? (
                  <ul className="space-y-1 text-sm">
                    {parsed.emails.map((email) => (
                      <li key={email}>
                        <a
                          href={`mailto:${email}`}
                          className="text-primary underline-offset-4 hover:underline"
                        >
                          {email}
                        </a>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">No emails detected</p>
                )}
              </ProfileSection>

              <ProfileSection
                title="Links"
                description="Portfolio and profile URLs"
                icon={CloudUpload}
              >
                {parsed?.links?.length ? (
                  <ul className="space-y-1 text-sm">
                    {parsed.links.map((link) => (
                      <li key={link}>
                        <a
                          href={link}
                          target="_blank"
                          rel="noreferrer"
                          className="break-all text-primary underline-offset-4 hover:underline"
                        >
                          {link}
                        </a>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-muted-foreground">No links detected</p>
                )}
              </ProfileSection>
            </div>
          </div>

          {/* Resume Metadata */}
          <Card>
            <CardHeader>
              <CardTitle>Resume metadata</CardTitle>
              <CardDescription>Stored in MongoDB Atlas after processing</CardDescription>
            </CardHeader>
            <CardContent>
              <dl className="grid gap-4 sm:grid-cols-2">
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">Resume ID</dt>
                  <dd className="mt-1 break-all font-mono text-sm">
                    {result.resume_id ?? resume?.id ?? "—"}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">Filename</dt>
                  <dd className="mt-1 text-sm">{upload?.filename ?? resume?.filename ?? "—"}</dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">Uploaded</dt>
                  <dd className="mt-1 text-sm">
                    {formatTimestamp(resume?.uploaded_at ?? resume?.created_at)}
                  </dd>
                </div>
                <div>
                  <dt className="text-xs font-medium text-muted-foreground">Cloudinary</dt>
                  <dd className="mt-1 flex items-center gap-2 text-sm">
                    {upload?.resume_url ? (
                      <>
                        <CheckCircle2 className="size-4 text-green-500" />
                        <span>Upload successful</span>
                      </>
                    ) : (
                      "—"
                    )}
                  </dd>
                </div>
              </dl>
              {upload?.resume_url && (
                <p className="mt-4 break-all text-xs text-muted-foreground">
                  {upload.resume_url}
                </p>
              )}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  )
}
