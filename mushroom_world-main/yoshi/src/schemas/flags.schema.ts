import { t } from "elysia";

export const FlagSchema = t.Object({
	correction_id: t.Number(),
	flag_name: t.String(),
	value: t.Number(),
	is_triggered: t.Boolean(),
	sufficient: t.Boolean(),
	description: t.String(),
	details: t.Union([t.String(), t.Null()]),
	created_at: t.Union([t.String(), t.Null()]),
	updated_at: t.Union([t.String(), t.Null()]),
});

export const FlagArraySchema = t.Array(FlagSchema);

export const FlagInputSchema = t.Object({
	correction_id: t.Number(),
	flag_name: t.String(),
	value: t.Number(),
	is_triggered: t.Boolean(),
	sufficient: t.Boolean(),
	description: t.String(),
	details: t.Optional(t.String()),
});

export const FlagBatchInputSchema = t.Object({
	flags: t.Array(FlagInputSchema),
});
