import { Elysia, t } from "elysia";
import { ActiveSessionService } from "./active-sessions.service";
import { loggerService } from "../utils/logger";
import { ActiveSessionSchema, ActiveSessionArraySchema } from "../schemas/active-sessions.schema";
import { ErrorSchema } from "../schemas/common.schema";

const activeSessionService = new ActiveSessionService();

export const activeSessionsRoutes = new Elysia({ prefix: "/active-sessions" })
	.get(
		"/",
		async ({ status }) => {
			try {
				return await activeSessionService.getAll();
			} catch (err) {
				loggerService.logError("ActiveSessionController", "getAll", err);
				return status(500, { message: "Failed to get active sessions" });
			}
		},
		{
			detail: {
				summary: "Get all active sessions",
				description: "Returns a list of all currently connected students",
				tags: ["Active Sessions"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: ActiveSessionArraySchema,
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
		"/:studentId",
		async ({ params, body, status }) => {
			try {
				return await activeSessionService.upsert(Number(params.studentId), body);
			} catch (err) {
				loggerService.logError("ActiveSessionController", "upsert", err);
				return status(500, { message: "Failed to upsert active session" });
			}
		},
		{
			params: t.Object({
				studentId: t.String(),
			}),
			body: t.Object({
				login: t.String(),
				host: t.String(),
				begin_at: t.String(),
			}),
			detail: {
				summary: "Create or update an active session",
				description: "Creates a new active session or updates an existing one for the student",
				tags: ["Active Sessions"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: ActiveSessionSchema,
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
	.delete(
		"/:studentId",
		async ({ params, status }) => {
			try {
				const deletedCount = await activeSessionService.deleteByStudentId(Number(params.studentId));
				return { deleted: deletedCount > 0 };
			} catch (err) {
				loggerService.logError("ActiveSessionController", "delete", err);
				return status(500, { message: "Failed to delete active session" });
			}
		},
		{
			params: t.Object({
				studentId: t.String(),
			}),
			detail: {
				summary: "Delete an active session",
				description: "Removes the active session for a student (when they log out)",
				tags: ["Active Sessions"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: t.Object({ deleted: t.Boolean() }),
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
		"/by-login/:login",
		async ({ params, status }) => {
			try {
				const session = await activeSessionService.getByLogin(params.login);
				if (!session) {
					return status(404, { message: "Active session not found" });
				}
				return session;
			} catch (err) {
				loggerService.logError("ActiveSessionController", "getByLogin", err);
				return status(500, { message: "Failed to get active session" });
			}
		},
		{
			params: t.Object({
				login: t.String(),
			}),
			detail: {
				summary: "Get active session by login",
				description: "Returns the active session for a student by their login",
				tags: ["Active Sessions"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: ActiveSessionSchema,
							},
						},
					},
					404: {
						description: "Active session not found",
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
	);
