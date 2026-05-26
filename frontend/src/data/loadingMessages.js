/** Rotating copy shown when backend work exceeds ~2s (grouped by flow). */

export const AUTH_CHECK_EMAIL_MESSAGES = [
  { title: "Checking your email…", subtitle: "Looking you up in our secure database." },
  { title: "One moment", subtitle: "Verifying whether you already have a Career OS account." },
  { title: "Almost there", subtitle: "We'll route you to sign in or quick onboarding." },
]

export const AUTH_SIGN_IN_MESSAGES = [
  { title: "Verifying your password…", subtitle: "Securely validating your credentials." },
  { title: "Signing you in", subtitle: "Preparing your workspace and preferences." },
  { title: "Welcome back", subtitle: "Loading your dashboard — just a few seconds." },
]

export const AUTH_REGISTER_MESSAGES = [
  { title: "Creating your account…", subtitle: "Setting up your personal career workspace." },
  { title: "Great choice joining Career OS", subtitle: "Configuring defaults for scans and matching." },
  { title: "Almost ready", subtitle: "You'll be on your dashboard shortly." },
]

export const AUTH_RESET_SEND_MESSAGES = [
  { title: "Sending verification code…", subtitle: "Check your inbox in a moment." },
  { title: "Securing your account", subtitle: "Generating a one-time reset code." },
]

export const AUTH_RESET_CONFIRM_MESSAGES = [
  { title: "Updating your password…", subtitle: "Applying your new credentials securely." },
  { title: "Signing you in", subtitle: "You're almost back in — hang tight." },
]

export const JOB_DISCOVERY_MESSAGES = [
  { title: "Great things take time…", subtitle: "We're searching top job boards for roles that fit you." },
  { title: "Looking for the best jobs for you", subtitle: "Scanning LinkedIn, Indeed, Naukri, Instahyre, and more." },
  { title: "Quality over quantity", subtitle: "Filtering out spam listings and weak matches." },
  { title: "Matching your skills & experience", subtitle: "Scoring each role against your resume profile." },
  { title: "Almost there", subtitle: "Ranking opportunities so the best matches rise to the top." },
  { title: "Your curated feed is on the way", subtitle: "Good opportunities are worth the wait." },
]

export const SCAN_RUN_MESSAGES = [
  { title: "Running your job scan…", subtitle: "Fetching roles from multiple providers in parallel." },
  { title: "Great things take time", subtitle: "We're looking for the best matches for your profile." },
  { title: "Scoring & ranking jobs", subtitle: "Comparing listings against your resume and preferences." },
  { title: "Quality filtering", subtitle: "Removing duplicates and low-signal postings." },
  { title: "Almost done", subtitle: "Fresh jobs will appear in your feed soon." },
]

export const SCAN_EMAIL_MESSAGES = [
  { title: "Preparing your digest email…", subtitle: "Selecting top matches from your latest scan." },
  { title: "Composing your job summary", subtitle: "Formatting roles for your inbox." },
  { title: "Sending shortly", subtitle: "Good news travels fast — check your email soon." },
]

export const SCAN_CENTER_LOAD_MESSAGES = [
  { title: "Loading scan center…", subtitle: "Fetching history, schedules, and provider stats." },
  { title: "Syncing automation settings", subtitle: "Almost ready to run or schedule scans." },
]

export const EMAIL_PREVIEW_MESSAGES = [
  { title: "Building email preview…", subtitle: "Rendering your digest with the latest matches." },
]

export const SETTINGS_SAVE_MESSAGES = [
  { title: "Saving your preferences…", subtitle: "Updating scan targets and notification rules." },
  { title: "Syncing your profile", subtitle: "Changes apply to the next scan automatically." },
]

export const SETTINGS_LOAD_MESSAGES = [
  { title: "Loading settings…", subtitle: "Fetching your job search profile and providers." },
]

export const PAGE_LOAD_MESSAGES = [
  { title: "Loading…", subtitle: "Fetching the latest data from the server." },
  { title: "One moment", subtitle: "Your career workspace is almost ready." },
]

export const SESSION_BOOT_MESSAGES = [
  { title: "Restoring your session…", subtitle: "Verifying your secure login token." },
  { title: "Welcome back", subtitle: "Preparing Career OS for you." },
]

export const GENERIC_WAIT_MESSAGES = [
  { title: "Working on it…", subtitle: "This usually takes just a few seconds." },
  { title: "Please wait", subtitle: "We're fetching the latest data from the server." },
  { title: "Almost there", subtitle: "Thanks for your patience." },
]

export const JOB_MATCH_MESSAGES = [
  { title: "Analyzing the job description…", subtitle: "Matching requirements against your resume." },
  { title: "Scoring your fit", subtitle: "Checking skills, experience, and keywords." },
  { title: "Almost done", subtitle: "Your match breakdown is on the way." },
]

export const ASSISTED_APPLY_MESSAGES = [
  { title: "Starting assisted apply…", subtitle: "Opening LinkedIn with your saved session." },
  { title: "Preparing the application", subtitle: "This may take a moment — stay on this screen." },
  { title: "Great things take time", subtitle: "We're helping you apply safely and accurately." },
]

export const RESUME_AI_MESSAGES = [
  { title: "Analyzing your resume with AI…", subtitle: "Computing ATS score, strengths, and keyword gaps." },
  { title: "Reading your experience", subtitle: "Building personalized improvement suggestions." },
  { title: "Almost ready", subtitle: "Your Resume AI dashboard is loading." },
]

export const INTERVIEW_PREP_MESSAGES = [
  { title: "Loading interview prep…", subtitle: "Fetching saved and applied jobs for practice." },
  { title: "Building your prep workspace", subtitle: "Great interviews start with good preparation." },
]

export const INTERVIEW_QUESTIONS_MESSAGES = [
  { title: "Generating interview questions…", subtitle: "Tailoring technical and behavioral prompts for this role." },
  { title: "Analyzing the job & your resume", subtitle: "AI is crafting likely questions for you." },
  { title: "Almost there", subtitle: "Practice questions will appear in a moment." },
]

export const COPILOT_BOOT_MESSAGES = [
  { title: "Starting Career Copilot…", subtitle: "Loading your resume, jobs, and career context." },
  { title: "Grounding AI in your data", subtitle: "So answers reflect your real profile." },
]

export const COPILOT_CHAT_MESSAGES = [
  { title: "Copilot is thinking…", subtitle: "Reviewing your career data before responding." },
  { title: "Crafting guidance for you", subtitle: "This may take a few seconds for detailed answers." },
  { title: "Almost there", subtitle: "Your personalized advice is on the way." },
]

export const NOTIFICATIONS_MESSAGES = [
  { title: "Loading notifications…", subtitle: "Fetching scan alerts and job updates." },
  { title: "Syncing your feed", subtitle: "New high-match roles appear here first." },
]

export const BACKEND_WAKE_MESSAGES = [
  { title: "Waking up our servers…", subtitle: "Render cold starts can take up to a minute on first visit." },
  { title: "Almost ready", subtitle: "We're preparing the API so sign-in and scans work smoothly." },
  { title: "Thanks for waiting", subtitle: "Scheduled scans and emails need a warm backend too." },
]

export const LOADING_MESSAGES_BY_KEY = {
  "check-email": AUTH_CHECK_EMAIL_MESSAGES,
  login: AUTH_SIGN_IN_MESSAGES,
  register: AUTH_REGISTER_MESSAGES,
  "reset-send": AUTH_RESET_SEND_MESSAGES,
  "reset-confirm": AUTH_RESET_CONFIRM_MESSAGES,
  "job-discovery": JOB_DISCOVERY_MESSAGES,
  scan: SCAN_RUN_MESSAGES,
  email: SCAN_EMAIL_MESSAGES,
  "scan-center": SCAN_CENTER_LOAD_MESSAGES,
  "email-preview": EMAIL_PREVIEW_MESSAGES,
  "settings-save": SETTINGS_SAVE_MESSAGES,
  "settings-load": SETTINGS_LOAD_MESSAGES,
  "page-load": PAGE_LOAD_MESSAGES,
  session: SESSION_BOOT_MESSAGES,
  generic: GENERIC_WAIT_MESSAGES,
  "job-match": JOB_MATCH_MESSAGES,
  "assisted-apply": ASSISTED_APPLY_MESSAGES,
  "resume-ai": RESUME_AI_MESSAGES,
  "interview-prep": INTERVIEW_PREP_MESSAGES,
  "interview-questions": INTERVIEW_QUESTIONS_MESSAGES,
  "copilot-boot": COPILOT_BOOT_MESSAGES,
  "copilot-chat": COPILOT_CHAT_MESSAGES,
  notifications: NOTIFICATIONS_MESSAGES,
  "backend-wake": BACKEND_WAKE_MESSAGES,
}

export function getLoadingMessages(key) {
  return LOADING_MESSAGES_BY_KEY[key] ?? GENERIC_WAIT_MESSAGES
}
