import { t } from "elysia";

export const StudentSchema = t.Object({
	id: t.Number(),
	login: t.String(),
	alumnized: t.Boolean(),
});

export const StudentArraySchema = t.Array(StudentSchema);
