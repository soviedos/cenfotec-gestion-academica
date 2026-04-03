FROM node:22-alpine AS base

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci

COPY . .

# ---- Development ----
FROM base AS development
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "-H", "0.0.0.0"]

# ---- Production ----
FROM base AS production
RUN npm run build
EXPOSE 3000
CMD ["npm", "start"]
