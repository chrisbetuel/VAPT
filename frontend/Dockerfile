# =============================================================================
# VAPT Frontend - Dockerfile (Multi-stage)
# =============================================================================
# Base stage
FROM node:18-alpine AS base
RUN apk add --no-cache libc6-compat curl
WORKDIR /app

# Dependencies stage
FROM base AS deps
COPY package.json ./
RUN npm install

# Development stage
FROM base AS development
ENV NODE_ENV=development
COPY --from=deps /app/node_modules ./node_modules
COPY . .
EXPOSE 5173
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Build stage
FROM base AS build
COPY --from=deps /app/node_modules ./node_modules
COPY . .
ENV NODE_ENV=production
RUN npm run build

# Production stage - Nginx
FROM nginx:1.25-alpine AS production
ENV NODE_ENV=production
RUN apk add --no-cache curl

# Copy nginx config
COPY infrastructure/nginx/nginx.conf /etc/nginx/nginx.conf
COPY infrastructure/nginx/sites/default.conf /etc/nginx/conf.d/default.conf

# Copy built assets
COPY --from=build /app/dist /usr/share/nginx/html

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost/health || exit 1

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
