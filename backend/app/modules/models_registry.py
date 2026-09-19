"""ثبت تمام مدل‌ها برای Alembic autogenerate و metadata کامل."""
from app.modules.activity.models import (  # noqa: F401
    ErrorNote,
    LearningActivity,
    QuestionMark,
    ReviewItem,
    TestRecord,
)
from app.modules.academic.models import (  # noqa: F401
    Chapter,
    Question,
    Resource,
    Subject,
    Topic,
)
from app.modules.exam.models import (  # noqa: F401
    Exam,
    ExamAnswer,
    ExamQuestion,
    ExamResult,
)
from app.modules.identity.models import SessionToken, User  # noqa: F401
from app.modules.planning.models import Goal, Plan, TimeBlock  # noqa: F401
from app.modules.settings.models import AppSetting  # noqa: F401
from app.modules.student.models import StudentProfile, StudentState  # noqa: F401
