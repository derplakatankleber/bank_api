# syntax=docker/dockerfile:1
FROM node:20-bookworm-slim AS base

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY node ./node
COPY migration.md README.md ./

ENV NODE_ENV=production \
    PORT=3000 \
    BANK_API_DB=/app/data/bank_data.db

RUN mkdir -p /app/data && chown -R node:node /app

USER node

EXPOSE 3000

CMD ["node", "node/src/api/app.js"]
