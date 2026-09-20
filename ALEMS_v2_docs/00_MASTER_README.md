# ALEMS نسخه ۲ — مستند مادر (Master README)

**Academic Life & Exam Management System — Version 2.0**  
سامانه مدیریت زندگی تحصیلی و مسیر کنکور

---

## هدف نسخه ۲

نسخه ۱ اسکلت و ماژول‌های پایه را ساخت.  
نسخه ۲ باید سیستم را به یک **محصول قابل زندگی روزمره، هوشمند، زیبا و قابل اعتماد** تبدیل کند.

نسخه ۲:
- تمام قابلیت‌های پایدار نسخه ۱ را حفظ یا اصلاح می‌کند
- قابلیت‌های برتر SS459 (V1 تا V3.1) را به‌صورت انتخاب‌شده و عملی وارد می‌کند
- **ظاهر کاملاً جدید** با انیمیشن و تجربه کاربری سطح بالا دارد
- طوری مستند شده که هوش مصنوعی کدساز **کمترین تصمیم آزاد** را بگیرد

---

## قانون طلایی برای کدساز

1. فقط طبق همین بسته اسناد پیاده‌سازی کن؛ حدس نزن.
2. اگر چیزی مبهم است، در `18_OPEN_DECISIONS.md` است — خارج از آن تصمیم جدید نگیر.
3. ظاهر نسخه ۱ را ادامه نده؛ UI نسخه ۲ از صفر طبق `07_UI_UX_V2.md` است.
4. TOC-only import کتاب **اجباری** مجاز است.
5. Coverage ≠ Accuracy ≠ Volume همیشه جدا بمانند.
6. کاربر بر برنامه خودکار اولویت دارد (Manual Override).
7. taught ≠ learned · free time ≠ capacity · not-entered ≠ unanswered.
8. هر فاز را تمام و تست کن؛ سپس به فاز بعد برو.

---

## فهرست اسناد

| فایل | محتوا |
|------|--------|
| `00_MASTER_README.md` | همین فایل |
| `01_VISION_SCOPE_V2.md` | چشم‌انداز، In/Out Scope |
| `02_DOMAIN_REQUIREMENTS_V2.md` | نیازمندی‌های دامنه |
| `03_SYSTEM_ARCHITECTURE_V2.md` | معماری و تکنولوژی |
| `04_MODULE_CATALOG_V2.md` | کاتالوگ ماژول‌ها |
| `05_DATABASE_SPEC_V2.md` | پایگاه داده |
| `06_API_CONTRACT_V2.md` | قرارداد API |
| `07_UI_UX_V2.md` | ظاهر، انیمیشن، UX |
| `08_BUSINESS_RULES_V2.md` | قوانین کسب‌وکار و Edge Cases |
| `09_BOOK_AND_TEST_ENGINE_V2.md` | کتاب، TOC-only، موتور تست |
| `10_REVIEW_AND_LEARNING_V2.md` | مرور، Learning State |
| `11_PLANNING_CAPACITY_V2.md` | برنامه، ظرفیت، Today Hub |
| `12_ANALYTICS_EXAM_GOALS_V2.md` | تحلیل، آزمون، اهداف |
| `13_REWARDS_BEHAVIOR_V2.md` | پاداش، وضعیت، اهمال‌کاری |
| `14_CODING_AGENT_PROMPTS_V2.md` | پرامپت فازبه‌فاز |
| `15_ACCEPTANCE_TESTS_V2.md` | تست‌های پذیرش |
| `16_ROADMAP_PHASES_V2.md` | نقشه راه فازها |
| `17_MIGRATION_FROM_V1.md` | ارتقا از نسخه ۱ |
| `18_OPEN_DECISIONS.md` | تصمیم‌های باز (محدود) |
| `PROJECT_MANIFEST_V2.json` | متادیتا |

---

## استک اجباری نسخه ۲

| بخش | تکنولوژی |
|-----|----------|
| Backend | Python 3.11+ · FastAPI · SQLAlchemy 2 · Pydantic v2 · Alembic · SQLite (PostgreSQL-ready) |
| Frontend | React 18 · Vite · TypeScript · Tailwind CSS · Framer Motion (انیمیشن) |
| تقویم | jalaali-js + dayjs · هفته شنبه تا جمعه · Asia/Tehran |
| فونت | Vazirmatn |
| نمودار | Recharts |
| PDF | ReportLab یا WeasyPrint با RTL |
| Excel | openpyxl |

---

## ترتیب خواندن برای کدساز

1. `00` → `01` → `03` → `04`  
2. `05` → `06` → `08`  
3. `09` → `10` → `11` → `12` → `13`  
4. `07` (UI را جدی بگیر)  
5. `16` + `14` برای اجرا فازبه‌فاز  
6. `15` برای پذیرش  

---

## نسخه

- docs_version: **2.0.0**
- product_target: **ALEMS 2.0**
- تاریخ اسناد: ۱۴۰۴
