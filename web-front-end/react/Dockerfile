# Stage 1: Build
FROM node:20-slim AS build

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG REACT_APP_TENANT_ID=acme_corp
ENV REACT_APP_TENANT_ID=${REACT_APP_TENANT_ID}

RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

COPY --from=build /app/build /usr/share/nginx/html

# Custom nginx config for SPA routing and port 18094
RUN echo 'server { \
    listen 18094; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 18094

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD wget -q --spider http://localhost:18094/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
