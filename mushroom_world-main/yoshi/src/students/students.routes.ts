import { Elysia, t } from "elysia";
import { StudentService } from "./students.service";
import { loggerService } from "../utils/logger";
import { handleDatabaseError } from "../utils/errors";
import { StudentSchema, StudentArraySchema } from "../schemas/students.schema";
import { ErrorSchema } from "../schemas/common.schema";

const studentService = new StudentService();

export const studentsRoutes = new Elysia({ prefix: "/students" })
	.get(
		"/",
		async ({ status }) => {
			try {
				return await studentService.getAll();
			} catch (err) {
				loggerService.logError("StudentController", "getAll", err);
				return status(500, { message: "Failed to get students" });
			}
		},
		{
			detail: {
				summary: "Get all students",
				description: "Returns a list of all students",
				tags: ["Students"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: StudentArraySchema,
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
				return await studentService.create(body);
			} catch (err) {
				loggerService.logError("StudentController", "create", err);
				if (err instanceof Error && err.message.includes("Duplicate entry")) {
					return status(409, { message: err.message });
				}
				return status(500, { message: "Failed to create student" });
			}
		},
		{
			body: t.Object({
				id: t.Number(),
				login: t.String(),
				alumnized: t.Optional(t.Boolean()),
			}),
			detail: {
				summary: "Create a new student",
				description: "Creates a new student",
				tags: ["Students"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: StudentSchema,
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
				const student = await studentService.getOne(Number(params.id));
				if (!student) {
					return await studentService.create(body);
				}
				await studentService.update(Number(params.id), body);
				const updatedStudent = await studentService.getOne(Number(params.id));
				return updatedStudent;
			} catch (err) {
				loggerService.logError("StudentController", "sync", err);
				return status(500, { message: "Failed to sync student" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			body: t.Object({
				id: t.Number(),
				login: t.String(),
				alumnized: t.Optional(t.Boolean()),
			}),
			detail: {
				summary: "Create or update a student",
				description: "Creates a new student if it doesn't exist, or updates an existing one",
				tags: ["Students"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: StudentSchema,
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
		"/anonymize/:id",
		async ({ params, status }) => {
			try {
				const student = await studentService.getOne(Number(params.id));
				if (!student) {
					return status(404, {
						message: `Not Found: student with id '${params.id}'`,
					});
				}
				await studentService.update(Number(params.id), {
					id: Number(params.id),
					login: `3b3-${params.id}`,
				});
				const updatedStudent = await studentService.getOne(Number(params.id));
				return updatedStudent;
			} catch (err) {
				loggerService.logError("StudentController", "anonymize", err);
				return status(500, { message: "Failed to anonymize student" });
			}
		},
		{
			params: t.Object({
				id: t.String(),
			}),
			detail: {
				summary: "Anonymize a student",
				description: "Anonymizes a student by changing their login to 3b3-{id}",
				tags: ["Students"],
				responses: {
					200: {
						description: "Success",
						content: {
							"application/json": {
								schema: StudentSchema,
							},
						},
					},
					404: {
						description: "Student not found",
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
