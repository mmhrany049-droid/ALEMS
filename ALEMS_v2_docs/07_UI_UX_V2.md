# ۷. UI/UX نسخه ۲ — ظاهر جدید و انیمیشن

## ۷.۱ قانون اصلی
ظاهر نسخه ۱ **ادامه داده نشود**.  
نسخه ۲ باید حس محصول ۲۰۲۶ بدهد: خلوت، عمیق، روان، با انیمیشن معنادار.

## ۷.۲ اصول بصری
- RTL کامل، Vazirmatn
- فاصله‌گذاری سخاوتمندانه
- کنتراست بالا در متن اصلی
- کارت‌های نرم با سایه ملایم
- رنگ معنایی: سبز درست، قرمز غلط، آبی مرور، کهربایی مهم
- Dark / Light هردو درجه-یک

## ۷.۳ Design Tokens (اجباری تعریف در کد)
- color.bg, color.surface, color.primary, color.success, color.danger, color.warning
- radius.md = 12px, radius.lg = 16px
- space: 4/8/12/16/24/32
- font: body 14–16, title 18–24, display 28–32
- motion.fast 180ms, normal 280ms, slow 400ms

## ۷.۴ کتابخانه انیمیشن
**Framer Motion** اجباری است.

### الگوهای الزامی
1. **Page transition**: fade + slide جزئی (۸–۱۲px)
2. **List stagger**: آیتم‌های صف مرور و برنامه با تأخیر ۳۰–۴۰ms
3. **Success pulse**: ثبت تست درست — تیک سبز کوتاه
4. **Progress bar**: نرم برای پوشش هفتگی
5. **Today Hub mount**: بلوک‌ها با cascade ورود
6. **Modal/sheet**: scale + fade
7. **Button press**: scale 0.98
8. **Planner build**: مراحل معنادار (تحلیل → ظرفیت → تخصیص → آماده)

### Reduced motion
اگر `prefers-reduced-motion: reduce` → فقط fade ساده یا بدون حرکت.

## ۷.۵ ساختار ناوبری
- Today (خانه)
- Study (منابع/کتاب)
- Tests
- Review
- Plan
- Exams
- Progress
- Settings

موبایل: bottom nav با ۵ آیتم اصلی + more  
دسکتاپ: sidebar باریک + content

## ۷.۶ Today Hub (مهم‌ترین صفحه)
بخش‌ها به‌ترتیب:
1. سلام + check-in سریع انرژی
2. خلاصه ظرفیت امروز
3. کارهای امروز (با checkbox انیمیشنی)
4. صف مرور ضروری
5. آزمون نزدیک
6. پیشنهاد روز (Recommendation) با «چرا؟»
7. خلاصه ۷ روز (sparkline)

## ۷.۷ Focus Mode
- مخفی کردن ناوبری
- فقط تایمر + سوالات/کار جاری
- خروج تأییدشده

## ۷.۸ Empty States
هر صفحه خالی: تصویر/آیکون سبک + یک جمله + یک CTA واضح.

## ۷.۹ بازخورد
- Toast غیرمزاحم
- خطا فارسی و قابل اقدام
- عملیات مخرب: تأیید دومرحله‌ای

## ۷.۱۰ معیار پذیرش UI
- در نگاه اول از V1 قابل تشخیص است
- انیمیشن‌ها هدف دارند نه صرفاً تزئینی
- Today Hub زیر ۲ ثانیه محتوای مفید نشان می‌دهد (داده محلی)
