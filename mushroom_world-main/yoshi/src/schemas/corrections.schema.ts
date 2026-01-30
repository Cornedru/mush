import { t } from "elysia";
import { StudentSchema, ProjectSchema } from "./common.schema";

const CorrectedSchema = t.Object({
	id: t.Number(),
	login: t.String(),
});

const PushInCorrectionSchema = t.Object({
	id: t.Number(),
	project_id: t.Number(),
	correcteds: t.Array(CorrectedSchema),
});

const CorrectorSchema = t.Nullable(
	t.Object({
		id: t.Number(),
		login: t.String(),
	}),
);

const ProjectInCorrectionSchema = t.Nullable(
	t.Object({
		id: t.Number(),
		name: t.String(),
	}),
);

export const CorrectionSchema = t.Object({
	id: t.Number(),
	comment: t.Nullable(t.String()),
	feedback: t.Nullable(t.String()),
	mark: t.Nullable(t.Number()),
	flag: t.Nullable(t.String()),
	status: t.String(),
	begin_at: t.Nullable(t.String()),
	filled_at: t.Nullable(t.String()),
	corrector: CorrectorSchema,
	push: t.Nullable(PushInCorrectionSchema),
	project: ProjectInCorrectionSchema,
});

export const CorrectionArraySchema = t.Array(CorrectionSchema);
