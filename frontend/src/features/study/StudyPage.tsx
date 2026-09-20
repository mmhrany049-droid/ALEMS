/** Study — منابع/کتاب. Phase 2: TOC-only import + tree (doc 09). */
import { Page } from '../../components/Page'
import { EmptyState } from '../../components/EmptyState'
import { Button } from '../../components/Button'

export function StudyPage() {
  return (
    <Page title="مطالعه" subtitle="کتاب‌ها، فهرست‌ها و درخت مباحث">
      <EmptyState
        icon="book"
        text="هنوز کتابی import نشده. در فاز ۲ می‌توانی کتاب را حتی فقط‌فهرست (TOC-only) ثبت کنی."
        action={<Button variant="soft" to="/">برو به امروز</Button>}
      />
    </Page>
  )
}
