# Web Dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY apps/web/package.json apps/web/pnpm-lock.yaml* apps/web/ .
RUN corepack enable && corepack prepare pnpm@latest --activate
RUN pnpm install --frozen-lockfile || pnpm install
COPY apps/web/ .
RUN pnpm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
