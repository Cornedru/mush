import { Elysia, t } from "elysia";
import { FlagService } from "./flags.service";
import { loggerService } from "../utils/logger";
import {
	FlagSchema,
	FlagArraySchema,
	FlagInputSchema,
	FlagBatchInputSchema,
} from "../schemas/flags.schema";
import { ErrorSchema } from "../schemas/common.schema";

const flagService = new FlagService();

export const flagsRoutes = new Elysia({ prefix: "/flags" })
	.get(
		"/by-correction/:correction_id",
		async ({ params, status }) => {
			try {
				return await flagService.getByCorrection(Number(params.correction_id));
			} catch (err) {
				loggerService.logError("FlagController", "getByCorrection", err);
				return status(500, { message: "Failed to get flags" });
			}
		},
		{
			params: t.Object({
				correction_id: t.String(),
			}),
			detail: {
				summary: "Get flags by correction ID",
				description: "Returns all calculated flags for a specific correction",
				tags: ["Flags"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: FlagArraySchema,
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
		}
	)
	.post(
		"/",
		async ({ body, status }) => {
			try {
				return await flagService.upsert(body);
			} catch (err) {
				loggerService.logError("FlagController", "upsert", err);
				return status(500, { message: "Failed to upsert flag" });
			}
		},
		{
			body: FlagInputSchema,
			detail: {
				summary: "Create or update a flag",
				description:
					"Creates a new flag for a correction or updates an existing one",
				tags: ["Flags"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: FlagSchema,
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
		}
	)
	.post(
		"/batch",
		async ({ body, status }) => {
			try {
				return await flagService.upsertMany(body.flags);
			} catch (err) {
				loggerService.logError("FlagController", "upsertMany", err);
				return status(500, { message: "Failed to upsert flags" });
			}
		},
		{
			body: FlagBatchInputSchema,
			detail: {
				summary: "Create or update multiple flags",
				description:
					"Creates or updates multiple flags for a correction in a single request",
				tags: ["Flags"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: FlagArraySchema,
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
		}
	)
	.delete(
		"/by-correction/:correction_id",
		async ({ params, status }) => {
			try {
				const deletedCount = await flagService.deleteByCorrection(
					Number(params.correction_id)
				);
				return { deleted: deletedCount > 0, count: deletedCount };
			} catch (err) {
				loggerService.logError("FlagController", "deleteByCorrection", err);
				return status(500, { message: "Failed to delete flags" });
			}
		},
		{
			params: t.Object({
				correction_id: t.String(),
			}),
			detail: {
				summary: "Delete flags by correction ID",
				description: "Deletes all flags for a specific correction",
				tags: ["Flags"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: t.Object({
									deleted: t.Boolean(),
									count: t.Number(),
								}),
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
		}
	);
