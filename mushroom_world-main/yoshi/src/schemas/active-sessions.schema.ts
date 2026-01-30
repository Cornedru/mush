import { t } from "elysia";

export const ActiveSessionSchema = t.Object({
	student_id: t.Number(),
	login: t.String(),
	host: t.String(),
	begin_at: t.String(),
});

export const ActiveSessionArraySchema = t.Array(ActiveSessionSchema);
