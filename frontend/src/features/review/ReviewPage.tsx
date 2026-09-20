/** Review — صف مرور. Phase 4: spaced 1-3-7-14، cluster (doc 10). */
import { Page } from '../../components/Page'
import { EmptyState } from '../../components/EmptyState'
import { Button } from '../../components/Button'

export function ReviewPage() {
  return (
    <Page title="مرور" subtitle="صف مرور، چرخه ۱-۳-۷-۱۴، مرور خوشه‌ای">
      <EmptyState
        icon="review"
        text="صف مرور خالی است. با ثبت تست و تیک‌ها، مرورهای ضروری اینجا شکل می‌گیرند (فاز ۴)."
        action={<Button variant="soft" to="/">برو به امروز</Button>}
      />
    </Page>
  )
}
