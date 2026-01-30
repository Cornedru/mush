export const REQUIRED_ENV_VARS = [
	"DB_USER",
	"DB_PASS",
	"DB_NAME",
] as const;

export const DB_HOST = Bun.env.DB_HOST || "peach";
