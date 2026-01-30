FROM oven/bun:1.3.5-alpine

WORKDIR /usr/src

COPY ./package.json ./

RUN bun install

RUN apk add --no-cache wget

COPY . .

CMD ["bun", "run", "src/main.ts"]
