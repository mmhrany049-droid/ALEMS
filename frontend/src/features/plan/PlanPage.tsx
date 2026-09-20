/** Plan — برنامه‌ریزی. Phase 5: capacity، generate-week، override (doc 11). */
import { Page } from '../../components/Page'
import { EmptyState } from '../../components/EmptyState'
import { Button } from '../../components/Button'

export function PlanPage() {
  return (
    <Page title="برنامه" subtitle="برنامه روز/هفته با ظرفیت واقعی و override دستی">
      <EmptyState
        icon="plan"
        text="برنامه‌ای هنوز تولید نشده. در فاز ۵ هفته‌ات با ظرفیت واقعی و قابل‌ویرایش دستی ساخته می‌شود."
        action={<Button variant="soft" to="/">برو به امروز</Button>}
      />
    </Page>
  )
}
