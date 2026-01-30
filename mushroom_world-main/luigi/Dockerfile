FROM oven/bun:1.3.5-alpine

WORKDIR /usr/src

COPY ./package.json ./

RUN bun install

COPY . .

EXPOSE 4200

CMD ["bun", "run", "src/main.ts"]
