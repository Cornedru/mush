import { Elysia } from "elysia";
import { StatsService } from "./stats.service";
import { loggerService } from "../utils/logger";
import { StatsSchema } from "../schemas/stats.schema";
import { ErrorSchema } from "../schemas/common.schema";

const statsService = new StatsService();

export const statsRoutes = new Elysia({ prefix: "/stats" })
	.get(
		"/",
		async ({ status }) => {
			try {
				return await statsService.getStats();
			} catch (err) {
				loggerService.logError("StatsController", "getStats", err);
				return status(500, { message: "Failed to get stats" });
			}
		},
		{
			detail: {
				summary: "Get database statistics",
				description: "Returns the count of documents in each collection, this endpoint is available outside of the docker network",
				tags: ["Stats"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: StatsSchema,
							},
						},
					},
					500: {
						description: "Internal server error",
						content: {
							"application/json": {
								schema: ErrorSchema,
							},
						},
					},
				},
			},
		},
	);
