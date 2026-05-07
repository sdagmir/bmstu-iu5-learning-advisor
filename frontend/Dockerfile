# --- Стадия 1: сборка SPA через Vite ---
FROM node:22-alpine AS builder

WORKDIR /app

# Кэш слоёв npm: сначала только манифест и lockfile.
COPY package.json package-lock.json ./
RUN npm ci

# Исходники + конфиги.
COPY tsconfig*.json vite.config.ts eslint.config.js components.json index.html ./
COPY public ./public
COPY src ./src

# В прод бандле API дёргается по относительному пути /api/v1 — nginx ниже
# проксирует его на backend-контейнер. Если нужен другой base — переопределить
# через --build-arg VITE_API_BASE_URL=...
ARG VITE_API_BASE_URL=/api/v1
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

RUN npm run build

# --- Стадия 2: nginx раздаёт статику + проксирует /api/v1 на backend ---
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

# nginx-образ из коробки запускает nginx в foreground — CMD не нужен.
