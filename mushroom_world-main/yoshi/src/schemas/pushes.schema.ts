import { t } from "elysia";
import { ProjectSchema } from "./common.schema";

const CorrectedInPushSchema = t.Object({
	id: t.Number(),
	login: t.String(),
});

export const PushSchema = t.Object({
	id: t.Number(),
	nb_correction_needed: t.Number(),
	status: t.String(),
	project: t.Nullable(ProjectSchema),
	correcteds: t.Array(CorrectedInPushSchema),
});

export const PushArraySchema = t.Array(PushSchema);
