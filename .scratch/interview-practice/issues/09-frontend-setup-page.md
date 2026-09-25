# 09 Setup page

Status: ready-for-agent
Blocked by: 06, 08

Page `/`: form with title (required), industry, seniority select (default mid), job description textarea, difficulty select (default normal). "Recommend settings" button, enabled when the description is non-empty, calls `/recommend-settings` and fills title/industry/seniority; the user can still edit them. "Start interview" posts to `/interviews` and navigates to `/interviews/[id]`. Show inline errors for 503.

Done when a full setup→start flow works against the running backend.
