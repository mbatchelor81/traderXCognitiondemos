# Stage 1: Build the React app
FROM node:20-slim AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

ARG REACT_APP_TENANT_ID=acme_corp
ARG REACT_APP_API_URL=http://localhost
ENV REACT_APP_TENANT_ID=$REACT_APP_TENANT_ID
ENV REACT_APP_API_URL=$REACT_APP_API_URL

RUN npm run build

# Stage 2: Serve with nginx
FROM nginx:1.25-alpine

RUN addgroup -S appgroup 2>/dev/null || true && \
    adduser -S appuser -G appgroup 2>/dev/null || true

COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget -qO- http://localhost:80/ || exit 1

CMD ["nginx", "-g", "daemon off;"]
