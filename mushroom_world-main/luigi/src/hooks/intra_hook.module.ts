import { Context } from "elysia";
import { find_event_type } from "./find_event_type.module";

export const intra_hook = async ({ body, headers, set }: Context): Promise<string> => {
	const intra_token = headers["x-secret"] as string | undefined;

	if (!intra_token) {
		console.warn("Missing x-secret header in webhook request");
		set.status = 401;
		return "Unauthorized: Missing x-secret header";
	}

	const event = find_event_type(intra_token);

	// If no valid token matched, return unauthorized
	if (event.name === "noop") {
		console.warn("Invalid or missing webhook token");
		set.status = 401;
		return "Unauthorized: Invalid token";
	}

	console.log("Event:", event.name);
	try {
		if (!body || typeof body !== "object") {
			throw new Error("Invalid request body: expected object");
		}
		await event.handler(body as Record<string, unknown>);
		return "OK";
	} catch (err) {
		console.error("Error in event handler:", err);
		if (err instanceof Error) {
			console.error("Error stack:", err.stack);
		}
		throw err;
	}
};
