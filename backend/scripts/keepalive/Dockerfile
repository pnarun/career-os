FROM curlimages/curl:8.7.1
ENV API_HEALTH_URL=https://career-os-pd9g.onrender.com/health
CMD ["sh", "-c", "curl -fsS --max-time 45 \"${API_HEALTH_URL}\" && echo keepalive-ok"]
