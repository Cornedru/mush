import { Elysia, t } from "elysia";
import { ProjectService } from "./projects.service";
import { loggerService } from "../utils/logger";
import { ProjectSchema, ProjectArraySchema } from "../schemas/projects.schema";
import { ErrorSchema } from "../schemas/common.schema";

const projectService = new ProjectService();

export const projectsRoutes = new Elysia({ prefix: "/projects" })
	.get(
		"/",
		async ({ status }) => {
			try {
				return await projectService.getAll();
			} catch (err) {
				loggerService.logError("ProjectController", "getAll", err);
				return status(500, { message: "Failed to get projects" });
			}
		},
		{
			detail: {
				summary: "Get all projects",
				description: "Returns a list of all projects",
				tags: ["Projects"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: ProjectArraySchema,
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
				const project = await projectService.getOne(Number(params.id));
				if (!project) {
					return status(404, {
						message: `Not Found: project with id '${params.id}'`,
					});
				}
				return project;
			} catch (err) {
				loggerService.logError("ProjectController", "getOne", err);
				return status(500, { message: "Failed to get project" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			detail: {
				summary: "Get a project by ID",
				description: "Returns a single project",
				tags: ["Projects"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: ProjectSchema,
							},
						},
					},
					404: {
						description: "Project not found",
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
				return await projectService.create(body);
			} catch (err) {
				loggerService.logError("ProjectController", "create", err);
				if (err instanceof Error && err.message.includes("Duplicate entry")) {
					return status(409, { message: err.message });
				}
				return status(500, { message: "Failed to create project" });
			}
		},
		{
			body: t.Object({
				id: t.Number(),
				name: t.String(),
			}),
			detail: {
				summary: "Create a new project",
				description: "Creates a new project",
				tags: ["Projects"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: ProjectSchema,
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
				const project = await projectService.getOne(Number(params.id));
				if (!project) {
					return await projectService.create(body);
				}
				await projectService.update(Number(params.id), body);
				const updatedProject = await projectService.getOne(Number(params.id));
				return updatedProject;
			} catch (err) {
				loggerService.logError("ProjectController", "create", err);
				return status(500, { message: "Failed to sync project" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			body: t.Object({
				id: t.Number(),
				name: t.String(),
			}),
			detail: {
				summary: "Create or update a project",
				description: "Creates a new project if it doesn't exist, or updates an existing one",
				tags: ["Projects"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: ProjectSchema,
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
