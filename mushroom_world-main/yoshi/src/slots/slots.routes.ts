import { Elysia, t } from "elysia";
import { SlotService } from "./slots.service";
import { loggerService } from "../utils/logger";
import { SlotSchema, SlotArraySchema, SlotCleanupSchema } from "../schemas/slots.schema";
import { ErrorSchema } from "../schemas/common.schema";

const slotService = new SlotService();

export const slotsRoutes = new Elysia({ prefix: "/slots" })
	.get(
		"/",
		async ({ status }) => {
			try {
				return await slotService.getAll();
			} catch (err) {
				loggerService.logError("SlotController", "getAll", err);
				return status(500, { message: "Failed to get slots" });
			}
		},
		{
			detail: {
				summary: "Get all slots",
				description: "Returns a list of all slots",
				tags: ["Slots"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: SlotArraySchema,
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
	)
	.get(
		"/:id",
		async ({ params, status }) => {
			try {
				const slot = await slotService.getById(Number(params.id));
				if (!slot) {
					return status(404, {
						message: `Not Found: slot with id '${params.id}'`,
					});
				}
				return slot;
			} catch (err) {
				loggerService.logError("SlotController", "getById", err);
				return status(500, { message: "Failed to get slot" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			detail: {
				summary: "Get slot by ID",
				description: "Returns a single slot by its ID",
				tags: ["Slots"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: SlotSchema,
							},
						},
					},
					404: {
						description: "Slot not found",
						content: {
							"application/json": {
								schema: ErrorSchema,
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
	)
	.put(
		"/:id",
		async ({ params, body, status }) => {
			try {
				return await slotService.upsert(body);
			} catch (err) {
				loggerService.logError("SlotController", "upsert", err);
				return status(500, { message: "Failed to upsert slot" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			body: t.Object({
				id: t.Number(),
				student_id: t.Number(),
				begin_at: t.String(),
				end_at: t.String(),
			}),
			detail: {
				summary: "Upsert a slot",
				description: "Creates a new slot if it doesn't exist, or updates an existing one. Only unbooked slots are stored.",
				tags: ["Slots"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: SlotSchema,
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
	)
	.post(
		"/cleanup",
		async ({ body, status }) => {
			try {
				const deletedCount = await slotService.deleteNotInList(body.slotIds);
				return {
					message: `Cleaned up ${deletedCount} old slots`,
					deletedCount,
				};
			} catch (err) {
				loggerService.logError("SlotController", "cleanup", err);
				return status(500, { message: "Failed to cleanup slots" });
			}
		},
		{
			body: SlotCleanupSchema,
			detail: {
				summary: "Cleanup old slots",
				description: "Deletes all slots whose IDs are not in the provided list",
				tags: ["Slots"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: t.Object({
									message: t.String(),
									deletedCount: t.Number(),
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
		},
	);
