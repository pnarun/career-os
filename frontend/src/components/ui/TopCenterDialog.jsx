import { AppModal } from "@/components/ui/AppModal"

/**
 * @deprecated Use AppModal — kept for existing imports. Now renders a centered modal.
 */
export function TopCenterDialog(props) {
  return <AppModal {...props} />
}
