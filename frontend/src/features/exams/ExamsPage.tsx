/** Exams — Exam Center. Phase 6: mock/school_subject/free + scoring (doc 12). */
import { Page } from '../../components/Page'
import { EmptyState } from '../../components/EmptyState'
import { Button } from '../../components/Button'

export function ExamsPage() {
  return (
    <Page title="آزمون‌ها" subtitle="آزمایشی و امتحان با درصد کنکوری">
      <EmptyState
        icon="exam"
        text="آزمونی ثبت نشده. در فاز ۶ Exam Center (mock، امتحان درسی) با scoring کنکوری می‌رسد."
        action={<Button variant="soft" to="/">برو به امروز</Button>}
      />
    </Page>
  )
}
