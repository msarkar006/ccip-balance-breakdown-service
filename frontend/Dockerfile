FROM node:22 AS build

WORKDIR /app/frontend

# Copy dependency files (relative to repo root context)
COPY frontend/package.json frontend/package-lock.json ./

# Install dependencies
RUN npm ci

# Copy source code
COPY frontend/ ./

# Build application
RUN npm run build

# Runtime stage
FROM nginx:alpine

# ARG for backend host (overridable at build time)
ARG BACKEND_HOST=backend
ENV BACKEND_HOST=${BACKEND_HOST}

# Copy nginx configuration template
COPY frontend/nginx.conf.template /etc/nginx/templates/default.conf.template

# Copy built assets from build stage
COPY --from=build /app/frontend/dist /usr/share/nginx/html

# Expose port
EXPOSE 80
