import { Elysia, t } from "elysia";
import { CorrectionService } from "./corrections.service";
import { StudentService } from "../students/students.service";
import { PushesService } from "../pushes/pushes.service";
import { loggerService } from "../utils/logger";
import {
	CorrectionSchema,
	CorrectionArraySchema,
} from "../schemas/corrections.schema";
import { ErrorSchema } from "../schemas/common.schema";

const correctionService = new CorrectionService();
const studentService = new StudentService();
const pushesService = new PushesService();

// Helper function to safely parse date strings
function parseDate(dateString: string | null | undefined): Date | undefined {
	if (!dateString || dateString === null) return undefined;
	const date = new Date(dateString);
	if (isNaN(date.getTime())) {
		throw new Error(`Invalid date string: ${dateString}`);
	}
	return date;
}

export const correctionsRoutes = new Elysia({ prefix: "/corrections" })
	.get(
		"/",
		async ({ status }) => {
			try {
				return await correctionService.getAll();
			} catch (err) {
				loggerService.logError("CorrectionController", "getAll", err);
				return status(500, { message: "Failed to get corrections" });
			}
		},
		{
			detail: {
				summary: "Get all corrections",
				description: "Returns a list of all corrections with populated push and corrector data",
				tags: ["Corrections"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: CorrectionArraySchema,
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
				const ret = await correctionService.getOne(Number(params.id));
				if (!ret) {
					return status(404, {
						message: `Not Found: correction with id '${params.id}'`,
					});
				}
				return ret;
			} catch (err) {
				loggerService.logError("CorrectionController", "getById", err);
				return status(500, { message: "Failed to get correction" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			detail: {
				summary: "Get a correction by ID",
				description: "Returns a single correction with populated push and corrector data",
				tags: ["Corrections"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: CorrectionSchema,
							},
						},
					},
					404: {
						description: "Correction not found",
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
	.get(
		"/by_push/:push_id",
		async ({ params, status }) => {
			try {
				const push = await pushesService.getOne(Number(params.push_id));
				if (!push) {
					return status(404, {
						message: `Not Found: push with id '${params.push_id}'`,
					});
				}
				return await correctionService.getByPush(Number(params.push_id));
			} catch (err) {
				loggerService.logError("CorrectionController", "getByPush", err);
				return status(500, { message: "Failed to get corrections by push" });
			}
		},
		{
			params: t.Object({
				push_id: t.String(),
			}),
			detail: {
				summary: "Get corrections by push ID",
				description: "Returns all corrections for a specific push",
				tags: ["Corrections"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: CorrectionArraySchema,
							},
						},
					},
					404: {
						description: "Push not found",
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
	.get(
		"/by_corrector/:user_id",
		async ({ params, status }) => {
			try {
				if (!(await studentService.getOne(Number(params.user_id)))) {
					return status(404, {
						message: `Not Found: corrector with id '${params.user_id}'`,
					});
				}
				return await correctionService.getByCorrector(Number(params.user_id));
			} catch (err) {
				loggerService.logError("CorrectionController", "getByCorrector", err);
				return status(500, { message: "Failed to get corrections by corrector" });
			}
		},
		{
			params: t.Object({
				user_id: t.String(),
			}),
			detail: {
				summary: "Get corrections by corrector ID",
				description: "Returns all corrections made by a specific corrector",
				tags: ["Corrections"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: CorrectionArraySchema,
							},
						},
					},
					404: {
						description: "Corrector not found",
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
	.get(
		"/by_corrected/:user_id",
		async ({ params, status }) => {
			try {
				if (!(await studentService.getOne(Number(params.user_id)))) {
					return status(404, {
						message: `Not Found: corrected with id '${params.user_id}'`,
					});
				}
				return await correctionService.getByCorrected(Number(params.user_id));
			} catch (err) {
				loggerService.logError("CorrectionController", "getByCorrected", err);
				return status(500, { message: "Failed to get corrections by corrected" });
			}
		},
		{
			params: t.Object({
				user_id: t.String(),
			}),
			detail: {
				summary: "Get corrections by corrected user ID",
				description: "Returns all corrections where a specific user was corrected",
				tags: ["Corrections"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: CorrectionArraySchema,
							},
						},
					},
					404: {
						description: "User not found",
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
	.get(
		"/by_user/:user_id",
		async ({ params, status }) => {
			try {
				if (!(await studentService.getOne(Number(params.user_id)))) {
					return status(404, {
						message: `Not Found: user with id '${params.user_id}'`,
					});
				}
				const by_corrected =
					await correctionService.getByCorrected(Number(params.user_id));
				const by_corrector =
					await correctionService.getByCorrector(Number(params.user_id));
				return by_corrected.concat(by_corrector);
			} catch (err) {
				loggerService.logError("CorrectionController", "getByUser", err);
				return status(500, { message: "Failed to get corrections by user" });
			}
		},
		{
			params: t.Object({
				user_id: t.String(),
			}),
			detail: {
				summary: "Get corrections by user ID",
				description: "Returns all corrections where the user was either corrector or corrected",
				tags: ["Corrections"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: CorrectionArraySchema,
							},
						},
					},
					404: {
						description: "User not found",
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
	.post(
		"/",
		async ({ body, status }) => {
			try {
				if (
					body.corrector_id &&
					!(await studentService.getOne(body.corrector_id))
				) {
					return status(404, {
						message: `Not Found: corrector with id '${body.corrector_id}'`,
					});
				}
				if (!(await pushesService.getOne(body.push_id))) {
					return status(404, {
						message: `Not Found: push with id '${body.push_id}'`,
					});
				}

				return await correctionService.create({
					id: body.id,
					comment: body.comment,
					feedback: body.feedback,
					mark: body.mark,
					status: body.status,
					beginAt: parseDate(body.begin_at),
					filledAt: parseDate(body.filled_at),
					correctorId: body.corrector_id,
					pushId: body.push_id,
				});
			} catch (err) {
				loggerService.logError("CorrectionController", "create", err);
				if (err instanceof Error && err.message.includes("Duplicate entry")) {
					return status(409, { message: err.message });
				}
				return status(500, { message: "Failed to create correction" });
			}
		},
		{
			body: t.Object({
				id: t.Number(),
				comment: t.Optional(t.String()),
				feedback: t.Optional(t.String()),
				mark: t.Optional(t.Number()),
				status: t.String(),
				begin_at: t.Optional(t.Union([t.String(), t.Null()])),
				filled_at: t.Optional(t.Union([t.String(), t.Null()])),
				corrector_id: t.Optional(t.Union([t.Number(), t.Null()])),
				push_id: t.Number(),
			}),
			detail: {
				summary: "Create a new correction",
				description: "Creates a new correction and returns it with populated data",
				tags: ["Corrections"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: CorrectionSchema,
							},
						},
					},
					404: {
						description: "Corrector or push not found",
						content: {
							"application/json": {
								schema: ErrorSchema,
							},
						},
					},
					409: {
						description: "Duplicate entry",
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
				if (
					body.corrector_id &&
					!(await studentService.getOne(body.corrector_id))
				) {
					return status(404, {
						message: `Not Found: corrector with id '${body.corrector_id}'`,
					});
				}
				if (!(await pushesService.getOne(body.push_id))) {
					return status(404, {
						message: `Not Found: push with id '${body.push_id}'`,
					});
				}
				const correction = await correctionService.getOne(Number(params.id));
				if (!correction) {
				// Filter out null values and convert to undefined for Mongoose
				const createData: {
					id: number;
					comment?: string;
					feedback?: string;
					mark?: number;
					status: string;
					beginAt?: Date;
					filledAt?: Date;
					correctorId?: number;
					pushId: number;
				} = {
						id: Number(params.id),
						comment: body.comment ?? undefined,
						feedback: body.feedback ?? undefined,
						mark: body.mark ?? undefined,
						status: body.status,
						beginAt: parseDate(body.begin_at),
						filledAt: parseDate(body.filled_at),
						correctorId: body.corrector_id ?? undefined,
						pushId: body.push_id,
					};
					return await correctionService.create(createData);
				}
				// Filter out null values and convert to undefined for Mongoose
				const updateData: {
					comment?: string;
					feedback?: string;
					mark?: number;
					status: string;
					beginAt?: Date;
					filledAt?: Date;
					correctorId?: number;
					pushId: number;
				} = {
					comment: body.comment ?? undefined,
					feedback: body.feedback ?? undefined,
					mark: body.mark ?? undefined,
					status: body.status,
					beginAt: parseDate(body.begin_at),
					filledAt: parseDate(body.filled_at),
					correctorId: body.corrector_id ?? undefined,
					pushId: body.push_id,
				};
				await correctionService.update(Number(params.id), updateData);
				const updatedCorrection = await correctionService.getOne(Number(params.id));
				return updatedCorrection;
			} catch (err) {
				loggerService.logError("CorrectionController", "update", err);
				return status(500, { message: "Failed to sync correction" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			body: t.Object({
				comment: t.Optional(t.Union([t.String(), t.Null()])),
				feedback: t.Optional(t.Union([t.String(), t.Null()])),
				mark: t.Optional(t.Union([t.Number(), t.Null()])),
				status: t.String(),
				begin_at: t.Optional(t.Union([t.String(), t.Null()])),
				filled_at: t.Optional(t.Union([t.String(), t.Null()])),
				corrector_id: t.Optional(t.Union([t.Number(), t.Null()])),
				push_id: t.Number(),
			}),
			detail: {
				summary: "Create or update a correction",
				description: "Creates a new correction if it doesn't exist, or updates an existing one",
				tags: ["Corrections"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: CorrectionSchema,
							},
						},
					},
					404: {
						description: "Corrector or push not found",
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
	.patch(
		"/:id",
		async ({ params, body, status }) => {
			try {
				const correction = await correctionService.getOne(Number(params.id));
				if (!correction) {
					return status(404, {
						message: `Not Found: correction with id '${params.id}'`,
					});
				}
				// Filter out null values and convert to undefined for Mongoose
				const updateData: {
					comment?: string;
					feedback?: string;
					mark?: number;
					status?: string;
					beginAt?: Date;
					filledAt?: Date;
					correctorId?: number;
				} = {};
				if (body.comment !== undefined) updateData.comment = body.comment ?? undefined;
				if (body.feedback !== undefined) updateData.feedback = body.feedback ?? undefined;
				if (body.mark !== undefined) updateData.mark = body.mark ?? undefined;
				if (body.status !== undefined) updateData.status = body.status;
				if (body.begin_at !== undefined) updateData.beginAt = parseDate(body.begin_at);
				if (body.filled_at !== undefined) updateData.filledAt = parseDate(body.filled_at);
				if (body.corrector_id !== undefined) updateData.correctorId = body.corrector_id ?? undefined;
				await correctionService.update(Number(params.id), updateData);
				const updatedCorrection = await correctionService.getOne(Number(params.id));
				return updatedCorrection;
			} catch (err) {
				loggerService.logError("CorrectionController", "update", err);
				return status(500, { message: "Failed to update correction" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			body: t.Object({
				comment: t.Optional(t.Union([t.String(), t.Null()])),
				feedback: t.Optional(t.Union([t.String(), t.Null()])),
				mark: t.Optional(t.Union([t.Number(), t.Null()])),
				status: t.Optional(t.String()),
				begin_at: t.Optional(t.Union([t.String(), t.Null()])),
				filled_at: t.Optional(t.Union([t.String(), t.Null()])),
				corrector_id: t.Optional(t.Union([t.Number(), t.Null()])),
			}),
			detail: {
				summary: "Partially update a correction",
				description: "Updates specific fields of an existing correction",
				tags: ["Corrections"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: CorrectionSchema,
							},
						},
					},
					404: {
						description: "Correction not found",
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
