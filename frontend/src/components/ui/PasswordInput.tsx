import { useState, type InputHTMLAttributes } from "react"
import { Eye, EyeOff } from "lucide-react"

import { cn } from "@/lib/utils"

type PasswordInputProps = Omit<InputHTMLAttributes<HTMLInputElement>, "type"> & {
  inputClassName?: string
}

export function PasswordInput({
  className,
  inputClassName,
  ...props
}: PasswordInputProps) {
  const [visible, setVisible] = useState(false)

  return (
    <div className={cn("relative", className)}>
      <input
        {...props}
        type={visible ? "text" : "password"}
        className={cn(
          "flex h-10 w-full rounded-lg border border-input bg-background px-3 pr-10 text-sm",
          inputClassName
        )}
      />
      <button
        type="button"
        tabIndex={-1}
        aria-label={visible ? "Hide password" : "Show password"}
        className="absolute right-2 top-1/2 -translate-y-1/2 rounded p-1 text-muted-foreground hover:text-foreground"
        onClick={() => setVisible((v) => !v)}
      >
        {visible ? <EyeOff className="size-4" /> : <Eye className="size-4" />}
      </button>
    </div>
  )
}
