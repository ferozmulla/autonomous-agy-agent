# --- Stage 1: Build the React app ---
FROM node:20-slim AS build
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm ci --no-audit --no-fund
COPY . .
RUN npm run build

# --- Stage 2: Serve with nginx ---
FROM nginx:1.25-alpine
# Remove default config
RUN rm /etc/nginx/conf.d/default.conf
# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Copy built assets from stage 1
COPY --from=build /app/dist /usr/share/nginx/html
# Cloud Run uses port 8080
EXPOSE 8080
CMD ["nginx", "-g", "daemon off;"]
