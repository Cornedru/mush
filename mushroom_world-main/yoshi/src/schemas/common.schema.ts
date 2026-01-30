import { t } from "elysia";

export const ErrorSchema = t.Object({
	message: t.String(),
});

export const StudentSchema = t.Object({
	id: t.Number(),
	login: t.String(),
});

export const ProjectSchema = t.Object({
	id: t.Number(),
	name: t.String(),
});
