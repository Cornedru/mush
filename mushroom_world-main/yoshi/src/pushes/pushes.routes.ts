import { Elysia, t } from "elysia";
import { PushesService } from "./pushes.service";
import { ProjectService } from "../projects/projects.service";
import { StudentService } from "../students/students.service";
import { loggerService } from "../utils/logger";
import { PushSchema, PushArraySchema } from "../schemas/pushes.schema";
import { ErrorSchema } from "../schemas/common.schema";

const pushesService = new PushesService();
const projectService = new ProjectService();
const studentService = new StudentService();

export const pushesRoutes = new Elysia({ prefix: "/pushes" })
	.get(
		"/",
		async ({ status }) => {
			try {
				return await pushesService.getAll();
			} catch (err) {
				loggerService.logError("PushController", "getAll", err);
				return status(500, { message: "Failed to get pushes" });
			}
		},
		{
			detail: {
				summary: "Get all pushes",
				description: "Returns a list of all pushes with populated project and correcteds data",
				tags: ["Pushes"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: PushArraySchema,
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
				const ret = await pushesService.getOne(Number(params.id));
				if (!ret) {
					return status(404, {
						message: `Not Found: push with id '${params.id}'`,
					});
				}
				return ret;
			} catch (err) {
				loggerService.logError("PushController", "getById", err);
				return status(500, { message: "Failed to get push" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			detail: {
				summary: "Get a push by ID",
				description: "Returns a single push with populated project and correcteds data",
				tags: ["Pushes"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: PushSchema,
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
	.post(
		"/",
		async ({ body, status }) => {
			try {
				if (!body.correcteds_logins || body.correcteds_logins.length === 0) {
					return status(422, {
						message: "correcteds_logins cannot be empty",
					});
				}

				const project = await projectService.getOne(body.project_id);
				if (!project) {
					return status(404, {
						message: `Not Found: project with id '${body.project_id}'`,
					});
				}

				const correcteds = [];
				for (const login of body.correcteds_logins) {
					const corrected = await studentService.getByLogin(login);
					if (!corrected) {
						return status(404, {
							message: `Not Found: corrected with login '${login}'`,
						});
					}
					correcteds.push(corrected);
				}

				return await pushesService.create({
					id: body.id,
					nbCorrectionNeeded: body.nb_correction_needed || 3,
					projectId: body.project_id,
					correcteds: correcteds.map((s) => ({ id: s.id })),
					status: body.status,
				});
			} catch (err) {
				loggerService.logError("PushController", "create", err);
				return status(500, { message: "Failed to create push" });
			}
		},
		{
			body: t.Object({
				id: t.Number(),
				nb_correction_needed: t.Optional(t.Number()),
				project_id: t.Number(),
				correcteds_logins: t.Array(t.String()),
				status: t.String(),
			}),
			detail: {
				summary: "Create a new push",
				description: "Creates a new push and returns it with populated data",
				tags: ["Pushes"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: PushSchema,
							},
						},
					},
					404: {
						description: "Project or corrected not found",
						content: {
							"application/json": {
								schema: ErrorSchema,
							},
						},
					},
					422: {
						description: "Validation error",
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
				if (!body.correcteds_logins || body.correcteds_logins.length === 0) {
					return status(422, {
						message: "correcteds_logins cannot be empty",
					});
				}

				const project = await projectService.getOne(body.project_id);
				if (!project) {
					return status(404, {
						message: `Not Found: project with id '${body.project_id}'`,
					});
				}

				const correcteds = [];
				for (const login of body.correcteds_logins) {
					const corrected = await studentService.getByLogin(login);
					if (!corrected) {
						return status(404, {
							message: `Not Found: corrected with login '${login}'`,
						});
					}
					correcteds.push(corrected);
				}

				const push = await pushesService.getOne(Number(params.id));
				if (!push) {
					return await pushesService.create({
						id: Number(params.id),
						nbCorrectionNeeded: body.nb_correction_needed || 3,
						projectId: body.project_id,
						correcteds: correcteds.map((s) => ({ id: s.id })),
						status: body.status,
					});
				}

				await pushesService.update(Number(params.id), {
					nbCorrectionNeeded: body.nb_correction_needed || 3,
					projectId: body.project_id,
					correcteds: correcteds,
					status: body.status,
				});

				const updatedPush = await pushesService.getOne(Number(params.id));
				return updatedPush;
			} catch (err) {
				loggerService.logError("PushController", "sync", err);
				return status(500, { message: "Failed to sync push" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			body: t.Object({
				id: t.Optional(t.Number()),
				nb_correction_needed: t.Optional(t.Number()),
				project_id: t.Number(),
				correcteds_logins: t.Array(t.String()),
				status: t.String(),
			}),
			detail: {
				summary: "Create or update a push",
				description: "Creates a new push if it doesn't exist, or updates an existing one",
				tags: ["Pushes"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: PushSchema,
							},
						},
					},
					404: {
						description: "Project or corrected not found",
						content: {
							"application/json": {
								schema: ErrorSchema,
							},
						},
					},
					422: {
						description: "Validation error",
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
				const push = await pushesService.getOne(Number(params.id));
				if (!push) {
					return status(404, {
						message: `Not Found: push with id '${params.id}'`,
					});
				}

				const updateData: {
					nbCorrectionNeeded?: number;
					status?: string;
					correcteds?: { id: number }[];
					projectId?: number;
				} = {};

				if (body.nb_correction_needed !== undefined) {
					updateData.nbCorrectionNeeded = body.nb_correction_needed;
				}
				if (body.status !== undefined) {
					updateData.status = body.status;
				}

				if (body.correcteds_logins !== undefined) {
					if (body.correcteds_logins.length === 0) {
						return status(422, {
							message: "correcteds_logins cannot be empty",
						});
					}
					const correcteds = [];
					for (const login of body.correcteds_logins) {
						const corrected = await studentService.getByLogin(login);
						if (!corrected) {
							return status(404, {
								message: `Not Found: corrected with login '${login}'`,
							});
						}
						correcteds.push(corrected);
					}
					updateData.correcteds = correcteds.map((s) => ({ id: s.id }));
				}

				if (body.project_id !== undefined) {
					const project = await projectService.getOne(body.project_id);
					if (!project) {
						return status(404, {
							message: `Not Found: project with id '${body.project_id}'`,
						});
					}
					updateData.projectId = body.project_id;
				}

				await pushesService.update(Number(params.id), updateData);
				const updatedPush = await pushesService.getOne(Number(params.id));
				return updatedPush;
			} catch (err) {
				loggerService.logError("PushController", "edit", err);
				return status(500, { message: "Failed to update push" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			body: t.Object({
				nb_correction_needed: t.Optional(t.Number()),
				project_id: t.Optional(t.Number()),
				correcteds_logins: t.Optional(t.Array(t.String())),
				status: t.Optional(t.String()),
			}),
			detail: {
				summary: "Partially update a push",
				description: "Updates specific fields of an existing push",
				tags: ["Pushes"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: PushSchema,
							},
						},
					},
					404: {
						description: "Push, project, or corrected not found",
						content: {
							"application/json": {
								schema: ErrorSchema,
							},
						},
					},
					422: {
						description: "Validation error",
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
