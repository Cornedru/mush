import { t } from "elysia";

export const StatsSchema = t.Object({
	students: t.Number(),
	activeSessions: t.Number(),
	projects: t.Number(),
	pushes: t.Number(),
	corrections: t.Number(),
	slots: t.Number(),
	flags: t.Number(),
});
