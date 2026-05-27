FROM curlimages/curl:8.7.1
ENV API_BASE_URL=https://career-os-pd9g.onrender.com
ENV CRON_SECRET=
CMD ["sh", "-c", "curl -fsS --max-time 300 -X POST \"${API_BASE_URL}/internal/cron/scheduled-scans\" -H \"X-Cron-Secret: ${CRON_SECRET}\" && echo scheduled-scans-ok"]
