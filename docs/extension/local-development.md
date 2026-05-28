# Career Lens Extension Local Development

## Prerequisites

- Chrome browser
- Career OS backend running locally (`http://localhost:8001`)
- Career OS user account (logged in via web app)

## Load extension locally

1. Open `chrome://extensions`
2. Enable **Developer mode**
3. Click **Load unpacked**
4. Select the `extension/` folder from this repo

## Local API (developers only)

The extension ships with the production API URL in `extension/utils/storage.js`. For local backend testing, temporarily change `CAREER_OS_API_URL` there and reload the unpacked extension.

**Privacy policy URL** for store listing and popup links: `extension/config.js` → `CAREER_OS_PRIVACY_URL` (must match production, e.g. `https://<vercel-app>/privacy-policy`).

## Test flow

1. Log into LinkedIn in Chrome
2. In Career OS web app, open Scans & Automation and generate a 6-digit pairing code
3. Open extension popup and enter the code
4. Click **Connect**
5. Confirm status changes to **LinkedIn connected**
6. Verify session in Career OS Automation page (`/automation/linkedin/status`)

## Expected behavior

- If not logged into LinkedIn, extension opens LinkedIn and shows instruction
- If logged in, extension syncs LinkedIn cookies to backend
- Backend persists session in MongoDB for cloud Playwright usage
