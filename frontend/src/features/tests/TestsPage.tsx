/** Tests — موتور تست. Phase 3: session، range/parity، past import (doc 09). */
import { Page } from '../../components/Page'
import { EmptyState } from '../../components/EmptyState'
import { Button } from '../../components/Button'

export function TestsPage() {
  return (
    <Page title="تست‌ها" subtitle="ثبت تست، رنج و زوج/فرد، نتایج قدیمی">
      <EmptyState
        icon="test"
        text="هنوز تستی ثبت نشده. در فاز ۳ موتور تست (range، parity، timed/untimed) می‌رسد."
        action={<Button variant="soft" to="/">برو به امروز</Button>}
      />
    </Page>
  )
}
