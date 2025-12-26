# Frontend Dockerfile - Multi-stage build
# Supports 'test' (Playwright) and 'production' (Nginx) targets

# ==========================================
# Target: test (Component Tests)
# ==========================================
FROM mcr.microsoft.com/playwright:v1.57.0-jammy AS test
WORKDIR /app

# Install dependencies (Cached Layer)
COPY package*.json ./
RUN npm install

# Copy source code (Frequent changes layer)
COPY . .

# Default command
CMD ["npx", "playwright", "test"]

# ==========================================
# Shared Builder Stage (for Production)
# ==========================================
FROM node:23-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy source code
COPY . .

# Build the app
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# ==========================================
# Target: production (Nginx Server)
# ==========================================
FROM nginx:alpine AS production

# Copy built files from builder stage
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
