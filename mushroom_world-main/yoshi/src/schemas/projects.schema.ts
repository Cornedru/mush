import { t } from "elysia";

export const ProjectSchema = t.Object({
	id: t.Number(),
	name: t.String(),
});

export const ProjectArraySchema = t.Array(ProjectSchema);
