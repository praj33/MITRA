FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci || npm install

COPY . .

ARG REACT_APP_API_URL
ARG REACT_APP_API_KEY
ARG REACT_APP_AUTH_API_URL
ARG REACT_APP_USER_ID

ENV REACT_APP_API_URL=${REACT_APP_API_URL} \
    REACT_APP_API_KEY=${REACT_APP_API_KEY} \
    REACT_APP_AUTH_API_URL=${REACT_APP_AUTH_API_URL} \
    REACT_APP_USER_ID=${REACT_APP_USER_ID} \
    CI=false

RUN npm run build

FROM node:20-alpine

WORKDIR /app

RUN npm install -g serve

COPY --from=builder /app/build ./build

RUN adduser --disabled-password --gecos "" frontend && \
    chown -R frontend:frontend /app

USER frontend

EXPOSE 3000

CMD ["serve", "-s", "build", "-l", "3000"]
