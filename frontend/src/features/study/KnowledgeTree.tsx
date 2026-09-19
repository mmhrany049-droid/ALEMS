// مرورگر درخت دانش — رشته/پایه ← درس ← فصل ← مبحث ← زیرمبحث + سوالات منبع (AT-06..AT-09)
import { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { errorMessage, get } from '../../lib/api';
import { useToast } from '../../components/Toast';
import { EmptyState, PercentBar, Spinner } from '../../components/ui';
import { useAuth } from '../../hooks/useAuth';
import {
  DIFFICULTY_LABELS, FIELDS, GRADES, type Chapter, type Question, type Resource, type Subject,
  type Topic,
} from '../../types';
import { faNumber, toFaDigits } from '../../lib/jalali';

interface TopicNode {
  id: string;
  title: string;
  question_count: number;
  subtopics: { id: string; title: string; question_count: number; parent_id: string }[];
}

interface TreeData {
  resource: Resource & { question_count: number };
  subject: Subject | null;
  chapters: { id: string; title: string; topics: TopicNode[] }[];
}

export default function KnowledgeTree() {
  const { profile } = useAuth();
  const toast = useToast();

  // فیلتر پیش‌فرض = پایه و رشته دانش‌آموز (الزام ۴)
  const [grade, setGrade] = useState<string>(profile?.grade ?? 'دوازدهم');
  const [field, setField] = useState<string>(profile?.field ?? 'ریاضی');
  useEffect(() => {
    if (profile?.grade) setGrade(profile.grade);
    if (profile?.field) setField(profile.field);
  }, [profile?.grade, profile?.field]);

  const [openSubject, setOpenSubject] = useState<string | null>(null);
  const [openChapter, setOpenChapter] = useState<string | null>(null);
  const [selectedResource, setSelectedResource] = useState<string | null>(null);

  const { data: subjects, isLoading: loadingSubjects } = useQuery({
    queryKey: ['subjects-tree', field, grade],
    queryFn: () => get<Subject[]>('/subjects', { field, grade }),
  });

  const { data: chapters } = useQuery({
    queryKey: ['chapters', openSubject],
    queryFn: () => get<Chapter[]>(`/subjects/${openSubject}/chapters`),
    enabled: !!openSubject,
  });

  const { data: topics } = useQuery({
    queryKey: ['topics', openChapter],
    queryFn: () => get<Topic[]>(`/chapters/${openChapter}/topics`),
    enabled: !!openChapter,
  });

  const { data: resources } = useQuery({
    queryKey: ['resources-of-subject', openSubject],
    queryFn: () => get<Resource[]>('/resources', { subject_id: openSubject ?? undefined }),
    enabled: !!openSubject,
  });

  const { data: tree } = useQuery({
    queryKey: ['resource-tree', selectedResource],
    queryFn: () => get<TreeData>(`/resources/${selectedResource}/tree`),
    enabled: !!selectedResource,
  });

  const { data: questions, isLoading: loadingQuestions } = useQuery({
    queryKey: ['resource-questions', selectedResource],
    queryFn: () => get<Question[]>(`/resources/${selectedResource}/questions`, { page_size: 200 }),
    enabled: !!selectedResource,
  });

  const subjectList = subjects?.data ?? [];

  return (
    <div className="grid gap-5 lg:grid-cols-3">
      {/* ستون فیلتر و دروس */}
      <div className="space-y-4">
        <div className="card !p-4">
          <h3 className="text-sm font-bold text-slate-800 mb-3">فیلتر بر اساس پروفایل من</h3>
          <label className="label !text-xs">پایه</label>
          <div className="flex flex-wrap gap-1 mb-3">
            {GRADES.map((g) => (
              <button key={g}
                className={`chip border cursor-pointer ${grade === g ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-slate-600 border-slate-200'}`}
                onClick={() => { setGrade(g); setOpenSubject(null); setSelectedResource(null); }}>
                {g}
              </button>
            ))}
          </div>
          <label className="label !text-xs">رشته</label>
          <div className="flex flex-wrap gap-1">
            {FIELDS.map((f) => (
              <button key={f}
                className={`chip border cursor-pointer ${field === f ? 'bg-primary-600 text-white border-primary-600' : 'bg-white text-slate-600 border-slate-200'}`}
                onClick={() => { setField(f); setOpenSubject(null); setSelectedResource(null); }}>
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* فهرست دروس */}
        <div className="card !p-2">
          {loadingSubjects ? <Spinner label="" /> : subjectList.length === 0 ? (
            <p className="text-xs text-slate-400 text-center py-6">
              درسی برای «{field} · {grade}» تعریف نشده است.
            </p>
          ) : (
            <ul className="divide-y divide-slate-50">
              {subjectList.map((s) => (
                <li key={s.id}>
                  <button
                    className={`w-full text-right px-3 py-2.5 rounded-xl text-sm transition ${
                      openSubject === s.id ? 'bg-primary-50 text-primary-700 font-semibold' : 'hover:bg-slate-50 text-slate-700'
                    }`}
                    onClick={() => {
                      setOpenSubject(openSubject === s.id ? null : s.id);
                      setOpenChapter(null);
                      setSelectedResource(null);
                    }}>
                    📗 {s.name}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* منابع این درس */}
        {openSubject && (
          <div className="card !p-3">
            <h3 className="text-xs font-bold text-slate-600 mb-2">کتاب‌های تست این درس</h3>
            {(resources?.data ?? []).length === 0 ? (
              <p className="text-xs text-slate-400 py-3 text-center">
                کتابی برای این درس وارد نشده — از بخش «تست‌ها» وارد کن.
              </p>
            ) : (
              <div className="space-y-1">
                {(resources?.data ?? []).map((r) => (
                  <button key={r.id}
                    className={`w-full text-right rounded-lg px-3 py-2 text-xs transition ${
                      selectedResource === r.id ? 'bg-primary-600 text-white' : 'bg-slate-50 text-slate-700 hover:bg-slate-100'
                    }`}
                    onClick={() => setSelectedResource(r.id)}>
                    📘 {r.title}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {/* ستون درخت + سوالات */}
      <div className="lg:col-span-2 space-y-4">
        {/* فصل‌ها و مباحث درس انتخابی */}
        {openSubject && !selectedResource && (
          <div className="card !p-4">
            <h3 className="font-bold text-slate-900 text-sm mb-3">
              درخت محتوا — {subjectList.find((s) => s.id === openSubject)?.name}
            </h3>
            {(chapters?.data ?? []).length === 0 ? (
              <p className="text-sm text-slate-400 py-6 text-center">
                فصلی برای این درس ثبت نشده. با وارد کردن کتاب تست، فصل‌ها و مباحث خودکار ساخته می‌شوند.
              </p>
            ) : (
              <div className="space-y-2">
                {(chapters?.data ?? []).map((ch) => (
                  <div key={ch.id} className="border border-slate-100 rounded-xl overflow-hidden">
                    <button className="w-full text-right px-4 py-2.5 bg-slate-50 hover:bg-slate-100 text-sm font-semibold text-slate-800"
                            onClick={() => setOpenChapter(openChapter === ch.id ? null : ch.id)}>
                      📁 {ch.title}
                    </button>
                    {openChapter === ch.id && (
                      <div className="px-4 py-2 space-y-1">
                        {(topics?.data ?? []).filter((t) => !t.parent_id).length === 0 ? (
                          <p className="text-xs text-slate-400 py-2">مبحثی ثبت نشده.</p>
                        ) : (topics?.data ?? []).filter((t) => !t.parent_id).map((t) => {
                          const subs = (topics?.data ?? []).filter((x) => x.parent_id === t.id);
                          return (
                            <div key={t.id}>
                              <div className="text-sm text-slate-700 py-1">📄 {t.title}</div>
                              <div className="pr-5 space-y-0.5">
                                {subs.map((st) => (
                                  <div key={st.id} className="text-xs text-slate-500 py-0.5">
                                    ↳ {st.title}
                                  </div>
                                ))}
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* درخت کتاب + سوالات */}
        {selectedResource && (
          <>
            <div className="card !p-4">
              <h3 className="font-bold text-slate-900 text-sm mb-3">
                📘 ساختار «{tree?.data?.resource.title ?? '...'}»
              </h3>
              {tree?.data?.chapters.length === 0 ? (
                <p className="text-sm text-slate-400">فصلی یافت نشد.</p>
              ) : (
                <div className="space-y-2">
                  {(tree?.data?.chapters ?? []).map((ch) => (
                    <details key={ch.id} open className="group">
                      <summary className="cursor-pointer select-none px-3 py-2 bg-slate-50 rounded-lg text-sm font-semibold text-slate-800">
                        📁 {ch.title}
                      </summary>
                      <div className="pt-1.5 pr-4 space-y-1.5">
                        {ch.topics.map((t) => (
                          <div key={t.id}>
                            <div className="text-sm text-slate-700">
                              📄 {t.title}
                              <span className="text-[10px] text-slate-400 mr-1">({toFaDigits(t.question_count)} سوال)</span>
                            </div>
                            {t.subtopics.length > 0 && (
                              <div className="pr-5 pt-0.5 space-y-0.5">
                                {t.subtopics.map((st) => (
                                  <div key={st.id} className="text-xs text-slate-500">
                                    ↳ {st.title}
                                    <span className="text-[10px] text-slate-400 mr-1">({toFaDigits(st.question_count)})</span>
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    </details>
                  ))}
                </div>
              )}
            </div>

            {/* لیست سوالات (AT-09) */}
            <div>
              <h3 className="font-bold text-slate-900 text-sm mb-3">
                سوالات کتاب — {faNumber(tree?.data?.resource.question_count ?? 0)} سوال
              </h3>
              {loadingQuestions ? <Spinner /> : (questions?.data ?? []).length === 0 ? (
                <EmptyState icon="❓" title="سوالی یافت نشد" />
              ) : (
                <div className="grid gap-2 md:grid-cols-2">
                  {(questions?.data ?? []).map((q) => (
                    <div key={q.id} className="card !p-3.5">
                      <div className="flex items-center gap-1.5 mb-1.5 flex-wrap">
                        <span className="text-xs font-bold text-primary-700">سوال {toFaDigits(q.number)}</span>
                        {q.topic_title && <span className="chip bg-slate-100 text-slate-600">{q.topic_title}</span>}
                        {q.difficulty && (
                          <span className={`chip ${
                            q.difficulty === 'easy' ? 'bg-emerald-100 text-emerald-700'
                            : q.difficulty === 'medium' ? 'bg-amber-100 text-amber-700'
                            : 'bg-red-100 text-red-700'}`}>
                            {DIFFICULTY_LABELS[q.difficulty]}
                          </span>
                        )}
                        {q.importance > 1 && (
                          <span className="chip bg-purple-50 text-purple-700">اهمیت {toFaDigits(q.importance)}</span>
                        )}
                      </div>
                      {q.text && <p className="text-xs text-slate-500 leading-relaxed">{q.text}</p>}
                      {q.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mt-1.5">
                          {q.tags.map((tag) => (
                            <span key={tag} className="text-[10px] text-slate-400">#{tag}</span>
                          ))}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </>
        )}

        {!openSubject && !selectedResource && (
          <EmptyState
            icon="🌳"
            title="یک درس را انتخاب کن"
            description="درخت دانش بر اساس پایه و رشته پروفایلت فیلتر شده است. برای دیدن فصل‌ها و مباحث، روی درس کلیک کن."
          />
        )}
      </div>
    </div>
  );
}
