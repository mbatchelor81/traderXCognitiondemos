# Stage 1: Build the React app
FROM node:20-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG REACT_APP_TENANT_ID=acme_corp
ENV REACT_APP_TENANT_ID=${REACT_APP_TENANT_ID}

RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:1.25-alpine

# Remove default nginx user directive to allow non-root
RUN sed -i '/^user /d' /etc/nginx/nginx.conf

# Create non-root user
RUN addgroup -g 1001 -S appuser && adduser -u 1001 -S appuser -G appuser

# Copy built assets
COPY --from=builder /app/build /usr/share/nginx/html

# Write nginx config inline
RUN printf 'server {\n\
    listen 80;\n\
    server_name _;\n\
    root /usr/share/nginx/html;\n\
    index index.html;\n\
\n\
    location / {\n\
        try_files $uri $uri/ /index.html;\n\
    }\n\
\n\
    location ~* \\.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {\n\
        expires 1y;\n\
        add_header Cache-Control "public, immutable";\n\
    }\n\
\n\
    location /health {\n\
        access_log off;\n\
        return 200 '\''{"status": "UP", "service": "frontend"}'\'';\n\
        add_header Content-Type application/json;\n\
    }\n\
}\n' > /etc/nginx/conf.d/default.conf

# Nginx needs to write to certain directories
RUN chown -R appuser:appuser /var/cache/nginx /var/log/nginx && \
    mkdir -p /var/run && chown -R appuser:appuser /var/run && \
    touch /var/run/nginx.pid && chown appuser:appuser /var/run/nginx.pid

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -q --spider http://localhost:80/health || exit 1

USER appuser

CMD ["nginx", "-g", "daemon off;"]
