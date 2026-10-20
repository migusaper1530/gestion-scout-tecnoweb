FROM nginx:1.28.0-alpine
COPY gateway/default.conf.template /etc/nginx/templates/default.conf.template
COPY frontend/ /usr/share/nginx/html/
EXPOSE 80
HEALTHCHECK --interval=15s --timeout=5s --retries=5 CMD wget -q -O /dev/null http://127.0.0.1/health || exit 1
