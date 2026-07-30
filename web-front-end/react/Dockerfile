# syntax=docker/dockerfile:1

# ---- Stage 1: build the CRA bundle ----
FROM node:20-alpine AS build

WORKDIR /app

# Build-time configuration baked into the bundle by src/env.ts.
# The tenant is mandatory; service URLs fall back to http://<hostname>:<port>
# when left empty, and are overridden with the ALB URL by the CD pipeline.
ARG REACT_APP_TENANT_ID=acme_corp
ARG REACT_APP_ACCOUNT_SERVICE_URL=
ARG REACT_APP_TRADING_SERVICE_URL=
ARG REACT_APP_POSITION_SERVICE_URL=
ARG REACT_APP_REFERENCE_DATA_SERVICE_URL=
ARG REACT_APP_PEOPLE_SERVICE_URL=

ENV REACT_APP_TENANT_ID=$REACT_APP_TENANT_ID \
    REACT_APP_ACCOUNT_SERVICE_URL=$REACT_APP_ACCOUNT_SERVICE_URL \
    REACT_APP_TRADING_SERVICE_URL=$REACT_APP_TRADING_SERVICE_URL \
    REACT_APP_POSITION_SERVICE_URL=$REACT_APP_POSITION_SERVICE_URL \
    REACT_APP_REFERENCE_DATA_SERVICE_URL=$REACT_APP_REFERENCE_DATA_SERVICE_URL \
    REACT_APP_PEOPLE_SERVICE_URL=$REACT_APP_PEOPLE_SERVICE_URL \
    CI=false \
    GENERATE_SOURCEMAP=false

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# ---- Stage 2: serve with nginx (non-root, uid 101, port 8080) ----
FROM nginxinc/nginx-unprivileged:alpine

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 8080

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD wget -q -O- http://127.0.0.1:8080/healthz || exit 1
