# Сборка и раздача фронтенда NERForge (Vite preview).
FROM node:20-alpine

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm install

COPY . .

# URL бэкенда зашивается на этапе сборки (Vite — статика).
ARG VITE_API_URL=http://localhost:8000/v1
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

EXPOSE 3000
CMD ["npm", "run", "preview"]
