import type { ImgHTMLAttributes } from "react"

import { cn } from "@/lib/utils"

/** Brand assets in `frontend/public/`. */
export const LOGO_SRC = {
  /** Wordmark for dark backgrounds (app shell, emails, modals). */
  full: "/career-os-logo-full.png",
  /** Wordmark for light backgrounds (landing page). */
  black: "/career-os-logo-black.png",
  /** Icon only — favicon, sidebar, tight UI slots. */
  symbol: "/career-os-logo-symbol.png",
} as const

/** @deprecated Use LOGO_SRC.full */
export const CAREER_OS_LOGO_SRC = LOGO_SRC.full

export type CareerOsLogoVariant = keyof typeof LOGO_SRC
export type CareerOsLogoSize = "xs" | "sm" | "md" | "lg" | "xl" | "2xl"

const WORDMARK_HEIGHT: Record<CareerOsLogoSize, string> = {
  xs: "h-7",
  sm: "h-8",
  md: "h-10",
  lg: "h-12",
  xl: "h-14",
  "2xl": "h-16",
}

const SYMBOL_SIZE: Record<CareerOsLogoSize, string> = {
  xs: "h-7 w-7",
  sm: "h-8 w-8",
  md: "h-10 w-10",
  lg: "h-12 w-12",
  xl: "h-14 w-14",
  "2xl": "h-16 w-16",
}

type CareerOsLogoProps = {
  size?: CareerOsLogoSize
  /** full = dark bg, black = light bg, symbol = icon-only */
  variant?: CareerOsLogoVariant
  className?: string
  alt?: string
} & Omit<ImgHTMLAttributes<HTMLImageElement>, "src" | "alt" | "className">

/** Career OS logo — pick variant to match background contrast. */
export function CareerOsLogo({
  size = "md",
  variant = "full",
  className,
  alt = "Career OS",
  ...props
}: CareerOsLogoProps) {
  const isSymbol = variant === "symbol"

  return (
    <img
      src={LOGO_SRC[variant]}
      alt={alt}
      className={cn(
        "shrink-0 object-contain",
        isSymbol
          ? cn(SYMBOL_SIZE[size], "object-center")
          : cn("w-auto max-w-full object-left", WORDMARK_HEIGHT[size]),
        className
      )}
      {...props}
    />
  )
}
