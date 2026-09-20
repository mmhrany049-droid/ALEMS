/** Progress — تحلیل. Phase 6: Coverage/Accuracy/Volume جدا + نمودار (doc 12). */
import { Page } from '../../components/Page'
import { EmptyState } from '../../components/EmptyState'
import { Button } from '../../components/Button'

export function ProgressPage() {
  return (
    <Page title="پیشرفت" subtitle="پوشش، دقت و حجم — همیشه جدا از هم">
      <EmptyState
        icon="progress"
        text="داده کافی برای تحلیل نیست. در فاز ۶ سه متریک جدا (Coverage / Accuracy / Volume) با نمودار می‌آیند."
        action={<Button variant="soft" to="/">برو به امروز</Button>}
      />
    </Page>
  )
}
