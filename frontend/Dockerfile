FROM node:22-alpine AS build

WORKDIR /app

ARG VITE_API_URL=
ENV VITE_API_URL=$VITE_API_URL

COPY package*.json ./
COPY tsconfig*.json ./
COPY vite.config.ts ./
COPY index.html ./

RUN npm install

COPY src ./src
COPY public ./public

RUN npm run build

FROM nginx:1.27-alpine AS runtime

WORKDIR /usr/share/nginx/html

COPY --from=build /app/dist ./
COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

EXPOSE 80

# BACKEND_ORIGIN set at runtime (docker-compose: http://backend:8000, ECS: internal ALB URL)
CMD ["/docker-entrypoint.sh"]

