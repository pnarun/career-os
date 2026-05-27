export function SiteFooter({ className = "", compact = false }) {
  return (
    <footer className={className}>
      <div
        className={
          compact
            ? "mx-auto flex w-full flex-wrap items-center justify-center gap-x-2 gap-y-1 text-xs"
            : "mx-auto flex w-full flex-wrap items-center justify-center gap-x-2 gap-y-1 text-sm"
        }
      >
        <span>
          A{" "}
          <a
            href="https://career-lens.in"
            target="_blank"
            rel="noopener noreferrer"
            className="font-semibold underline-offset-4 hover:underline"
          >
            Career Lens
          </a>{" "}
          product
        </span>
        <span aria-hidden>•</span>
        <span>Powered by</span>
        <a
          href="https://elvatech.in"
          target="_blank"
          rel="noopener noreferrer"
          className="font-semibold underline-offset-4 hover:underline"
        >
          ELVA Tech
        </a>
      </div>
    </footer>
  )
}
