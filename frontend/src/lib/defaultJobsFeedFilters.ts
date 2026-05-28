/** Default Jobs feed filters — must match initial `Jobs.jsx` / `useJobsFeed` state. */
export const DEFAULT_JOBS_FEED_FILTERS = {
  providers: [] as string[],
  remoteOnly: false,
  easyApplyOnly: false,
  minMatch: 0,
  keyword: "",
  sort: "default",
  strongMatchesOnly: false,
  remoteHighMatch: false,
  easyApplyHighMatch: false,
  company: "",
}
