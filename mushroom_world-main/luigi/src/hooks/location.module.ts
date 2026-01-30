import { yoshiClient, handleApiError } from "../utils/http";
import { assertHasProperty, assertIsNumber, assertIsString } from "../utils/validation";

interface LocationBody {
	id: number;
	begin_at: string;
	end_at: string | null;
	primary: boolean;
	host: string;
	campus_id: number;
	user: {
		id: number;
		login: string;
		url: string;
	};
}

function validateLocationBody(body: Record<string, unknown>): LocationBody {
	assertHasProperty(body, "id");
	assertHasProperty(body, "begin_at");
	assertHasProperty(body, "host");
	assertHasProperty(body, "user");
	assertIsNumber(body.id, "id");
	assertIsString(body.host, "host");
	assertIsString(body.begin_at, "begin_at");

	if (!body.user || typeof body.user !== "object" || !("id" in body.user) || !("login" in body.user)) {
		throw new Error("Invalid body: user must have id and login");
	}
	assertIsNumber((body.user as { id: unknown }).id, "user.id");
	assertIsString((body.user as { login: unknown }).login, "user.login");

	return body as LocationBody;
}

export const location_create = async (body: Record<string, unknown>): Promise<void> => {
	const locationData = validateLocationBody(body);

	try {
		await yoshiClient.put(`/active-sessions/${locationData.user.id}`, {
			login: locationData.user.login,
			host: locationData.host,
			begin_at: locationData.begin_at,
		});
	} catch (error) {
		handleApiError(error, "upsert active session", {
			student_id: locationData.user.id,
			login: locationData.user.login,
			host: locationData.host,
		});
	}
};

export const location_close = async (body: Record<string, unknown>): Promise<void> => {
	const locationData = validateLocationBody(body);

	try {
		await yoshiClient.delete(`/active-sessions/${locationData.user.id}`);
	} catch (error) {
		// Silently ignore if session doesn't exist (may have been cleaned by sync)
		console.log(`Active session for student ${locationData.user.id} (${locationData.user.login}) not found or already removed`);
	}
};
