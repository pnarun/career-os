# Chrome Web Store Plan

## Scope for first release

- LinkedIn auth/session bridge only
- Popup-based connect + resync controls
- Pairing code connect UI (production API baked in)
- No scraping/content scripts

## Compliance checklist

- [ ] Privacy policy page published at `https://<your-domain>/privacy-policy` (set `CAREER_OS_PRIVACY_URL` in `extension/config.js`)
- [ ] Terms of service updated with extension usage
- [ ] Permission justification documented (`cookies`, `storage`, `tabs`)
- [ ] Screenshots prepared (popup connected/disconnected states)
- [ ] Security review completed (no password collection, no history tracking)

## Listing metadata draft

- **Name:** Career Lens
- **Short description:** Sync your LinkedIn login securely to Career OS cloud automation.
- **Category:** Productivity

## Store assets

- App icons: `16`, `48`, `128`
- Promo screenshots:
  - Not connected state
  - Connected state with last sync
  - Pairing code entry

## Review notes

- Explain why `cookies` permission is required (LinkedIn session bridge)
- Explain why `tabs` is required (open LinkedIn login when not authenticated)
- Confirm no sale/share of personal data

## Post-launch roadmap

- Token bootstrap from Career OS web session (reduce manual token paste)
- Signed sync payloads + key rotation
- In-product onboarding handoff between web app and extension
