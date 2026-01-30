import { Elysia, t } from "elysia";
import { staticPlugin } from "@elysiajs/static";
import { intra_hook } from "./hooks/intra_hook.module";
import { YOSHI_ENDPOINT, REQUIRED_ENV_VARS } from "./utils/config";

async function proxyToYoshi({ request, set }: { request: Request; set: any }) {
	const url = new URL(request.url);
	const path = url.pathname + url.search;

	if (path !== "/docs" && path !== "/docs/json" && path !== "/stats") {
		set.status = 403;
		return { message: "Forbidden" };
	}

	const yoshiUrl = `${YOSHI_ENDPOINT}${path}`;
	try {
		const controller = new AbortController();
		const timeoutId = setTimeout(() => controller.abort(), 10000);

		const response = await fetch(yoshiUrl, {
			signal: controller.signal,
		});
		clearTimeout(timeoutId);

		const headers = new Headers();
		response.headers.forEach((value, key) => {
			headers.set(key, value);
		});

		return new Response(await response.text(), {
			status: response.status,
			headers: headers,
		});
	} catch (error) {
		if (error instanceof Error && error.name === "AbortError") {
			console.error("Proxy timeout:", yoshiUrl);
			set.status = 504;
			return { message: "Gateway Timeout" };
		}
		console.error("Proxy error:", error);
		if (error instanceof Error) {
			console.error("Error stack:", error.stack);
		}
		set.status = 502;
		return { message: "Bad Gateway" };
	}
}

const app = new Elysia()
	.use(staticPlugin({
		assets: "./public",
		prefix: "/"
	}))
	.get("/", () => "running")
	.get("/health", async () => {
		try {
			const response = await fetch(`${YOSHI_ENDPOINT}/health`, {
				signal: AbortSignal.timeout(5000),
			});
			const yoshiHealth = await response.json().catch(() => ({ status: "unknown" }));
			return {
				status: "ok",
				yoshi: yoshiHealth,
			};
		} catch (error) {
			return {
				status: "degraded",
				yoshi: { status: "unreachable" },
			};
		}
	})
	.get("/docs", proxyToYoshi)
	.get("/docs/json", proxyToYoshi)
	.get("/stats", proxyToYoshi)
	.post("/h/intra", intra_hook, {
		body: t.Object({}, { additionalProperties: true }),
	})
	.onError(({ code, error, set }) => {
		if (code === "VALIDATION") {
			set.status = 422;
			return { message: error.message };
		}
		if (code === "NOT_FOUND") {
			set.status = 404;
			return { message: "Not Found" };
		}
		console.error("Error:", code, error);
		if (error instanceof Error) {
			console.error("Error stack:", error.stack);
		}
		set.status = 500;
		return { message: "Internal Server Error" };
	});

function validateEnvironmentVariables(): void {
	const missingVars: string[] = [];
	for (const envVar of REQUIRED_ENV_VARS) {
		if (!Bun.env[envVar]) {
			missingVars.push(envVar);
		}
	}

	if (missingVars.length > 0) {
		console.error("Missing required environment variables:", missingVars.join(", "));
		Bun.exit(1);
	}
}

async function bootstrap(): Promise<void> {
	try {
		validateEnvironmentVariables();
		app.listen(4200);
		console.log("Server started on port 4200");
	} catch (err) {
		console.error("Failed to start server:", err);
		if (err instanceof Error) {
			console.error("Error stack:", err.stack);
		}
		Bun.exit(1);
	}
}

bootstrap().catch((err) => {
	console.error("Unhandled error in bootstrap:", err);
	if (err instanceof Error) {
		console.error("Error stack:", err.stack);
	}
	Bun.exit(1);
});
