import { Elysia } from "elysia";
import { openapi } from "@elysiajs/openapi";
import { studentsRoutes } from "./students/students.routes";
import { projectsRoutes } from "./projects/projects.routes";
import { pushesRoutes } from "./pushes/pushes.routes";
import { correctionsRoutes } from "./corrections/corrections.routes";
import { statsRoutes } from "./stats/stats.routes";
import { activeSessionsRoutes } from "./active-sessions/active-sessions.routes";
import { slotsRoutes } from "./slots/slots.routes";
import { flagsRoutes } from "./flags/flags.routes";
import { DatabaseService } from "./db/database.service";
import { connectDatabase, disconnectDatabase, isDatabaseConnected } from "./db";
import { REQUIRED_ENV_VARS } from "./utils/config";

const app = new Elysia()
	.use(openapi({
		path: "/docs",
		documentation: {
			info: {
				title: "Yoshi API docs",
				version: "0.0.1"

			},
			servers: [
				{
					url: "http://yoshi:3000",
					description: "Yoshi API server"
				}
			]
		}
	}))
	.onRequest(({ request }) => {
		const url = new URL(request.url);
		const pathname = url.pathname;
		if (pathname.startsWith("/docs")) {
			console.log(`[DOCS] [${request.method}] ${pathname}${url.search}`);
		} else {
			console.log(`[${request.method}] ${pathname}`);
		}
	})
	.get("/", () => "Hello from Yoshi API")
	.get("/health", async () => {
		const dbConnected = isDatabaseConnected();
		return {
			status: dbConnected ? "ok" : "degraded",
			database: dbConnected ? "connected" : "disconnected",
		};
	})
	.use(studentsRoutes)
	.use(projectsRoutes)
	.use(pushesRoutes)
	.use(correctionsRoutes)
	.use(statsRoutes)
	.use(activeSessionsRoutes)
	.use(slotsRoutes)
	.use(flagsRoutes)
	.onError(({ code, error, set, request }) => {
		const url = new URL(request.url);
		const method = request.method;
		const route = url.pathname;

		if (code === "VALIDATION") {
			console.error(`[ERROR] Validation failed - [${method}] ${route}:`, error.message);
			set.status = 422;
			return { message: error.message };
		}
		if (code === "NOT_FOUND") {
			console.error(`[ERROR] Not found - [${method}] ${route}`);
			set.status = 404;
			return { message: "Not Found" };
		}

		console.error(`[ERROR] ${code} - [${method}] ${route}:`, error);
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

		await connectDatabase();

		const dbService = new DatabaseService();
		await dbService.seedStudents();

		app.listen(3000);
		console.log(`Server started on port 3000`);
	} catch (err) {
		console.error("Failed to start server:", err);
		if (err instanceof Error) {
			console.error("Error stack:", err.stack);
		}
		Bun.exit(1);
	}
}

function setupShutdown(): void {
	const shutdown = async (signal: string) => {
		console.log(`Received ${signal}, shutting down...`);
		
		const shutdownTimeout = setTimeout(() => {
			console.error("Shutdown timeout exceeded, forcing exit");
			Bun.exit(1);
		}, 10000);

		try {
			await disconnectDatabase();
			clearTimeout(shutdownTimeout);
			console.log("Shutdown completed");
			Bun.exit(0);
		} catch (err) {
			clearTimeout(shutdownTimeout);
			console.error("Error during shutdown:", err);
			Bun.exit(1);
		}
	};

	process.on("SIGTERM", () => shutdown("SIGTERM"));
	process.on("SIGINT", () => shutdown("SIGINT"));
}

setupShutdown();
bootstrap().catch((err) => {
	console.error("Unhandled error in bootstrap:", err);
	Bun.exit(1);
});
