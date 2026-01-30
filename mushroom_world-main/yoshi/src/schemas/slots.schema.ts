import { t } from "elysia";

export const SlotSchema = t.Object({
	id: t.Number(),
	student_id: t.Number(),
	begin_at: t.String(),
	end_at: t.String(),
	created_at: t.Optional(t.String()),
	updated_at: t.Optional(t.String()),
});

export const SlotArraySchema = t.Array(SlotSchema);

export const SlotCleanupSchema = t.Object({
	slotIds: t.Array(t.Number()),
});
