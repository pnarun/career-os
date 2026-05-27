import { AppModal } from "@/components/ui/AppModal"
import { Button } from "@/components/ui/button"

/**
 * Standard yes/no confirmation (centered, full backdrop).
 */
export function ConfirmDialog({
  open,
  onClose,
  onConfirm,
  title = "Are you sure?",
  message,
  confirmLabel = "Confirm",
  cancelLabel = "Cancel",
  confirmVariant = "destructive",
  loading = false,
  size = "sm",
}) {
  return (
    <AppModal
      open={open}
      onClose={loading ? undefined : onClose}
      title={title}
      description={message}
      size={size}
      placement="top"
      backdrop="glass"
      showClose={!loading}
      footer={
        <>
          <Button
            type="button"
            variant="outline"
            className="w-full sm:w-auto"
            disabled={loading}
            onClick={onClose}
          >
            {cancelLabel}
          </Button>
          <Button
            type="button"
            variant={confirmVariant}
            className="w-full sm:w-auto"
            disabled={loading}
            onClick={() => void onConfirm?.()}
          >
            {loading ? "Please wait…" : confirmLabel}
          </Button>
        </>
      }
    />
  )
}
