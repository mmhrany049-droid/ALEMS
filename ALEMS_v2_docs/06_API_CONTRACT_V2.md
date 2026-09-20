# ۶. قرارداد API — ALEMS نسخه ۲

Base: `/api/v1`  
پاکت پاسخ:
```json
{"success": true, "data": {}, "error": null, "meta": {}}
```
خطا:
```json
{"success": false, "data": null, "error": {"code": "...", "message": "فارسی", "details": {}}}
```

## Auth
- POST /auth/register
- POST /auth/login
- POST /auth/logout
- GET /auth/me

## Student
- GET/PUT /students/me
- POST /students/me/checkin
- GET /students/me/state
- GET/PUT /students/me/taught-topics

## Books & Import
- POST /resources/import-book  
  **باید TOC-only را بپذیرد** (questions خالی یا غایب)
- GET /resources/import-book/schema
- GET /resources
- GET /resources/{id}/tree
- GET /subjects/... درخت دروس

## Tests
- POST /test-sessions
- POST /test-sessions/{id}/records
- POST /test-sessions/{id}/finish
- POST /tests/past-import
- GET /test-engine/preview?resource_id&from&to&parity

## Review
- GET /reviews/queue
- POST /reviews/{id}/complete
- POST /reviews/{id}/postpone
- POST /reviews/rebuild
- GET /reviews/cluster-suggestion

## Planning
- GET/POST /goals
- GET/PUT /time-blocks
- GET/PUT /plans/{date}
- POST /plans/generate-week
- GET /today
- GET /capacity?date=
- POST /school-override
- GET /recommendations/today
- GET /priority/week
- POST /recommendations/{id}/respond

## Exam
- CRUD /exams
- POST /exams/{id}/start|submit
- GET /exams/{id}/result

## Analytics & Export
- GET /analytics/overview
- GET /analytics/by-subject|by-topic|difficulty|mistakes
- GET /reports/daily|weekly|monthly
- GET /export/pdf|excel|json

## Rewards
- GET /rewards/summary
- GET /rewards/badges

## Backup
- POST /backup/create
- GET /backup/list
- POST /backup/restore
- GET /backup/download/{id}

## Settings
- GET/PUT /settings

## Share
- POST /share/report
- GET /share/{token}
