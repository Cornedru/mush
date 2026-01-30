import { yoshiClient, handleApiError } from "../utils/http";
import { assertHasProperty, assertIsNumber, assertIsString } from "../utils/validation";

interface UserBody {
	id: number;
	login: string;
}

function validateUserBody(body: Record<string, unknown>): UserBody {
	assertHasProperty(body, "id");
	assertHasProperty(body, "login");
	assertIsNumber(body.id, "id");
	assertIsString(body.login, "login");
	return body as UserBody;
}

export const user_create = async (body: Record<string, unknown>): Promise<void> => {
	const { id, login } = validateUserBody(body);

	try {
		await yoshiClient.put(`/students/${id}`, {
			login,
			id,
		});
	} catch (error) {
		handleApiError(error, "create user", { user_id: id, login });
	}
};

export const user_update = async (body: Record<string, unknown>): Promise<void> => {
	const { id, login } = validateUserBody(body);

	try {
		await yoshiClient.put(`/students/${id}`, {
			login,
			id,
		});
	} catch (error) {
		handleApiError(error, "update user", { user_id: id, login });
	}
};

export const user_alumnize = async (body: Record<string, unknown>): Promise<void> => {
	assertHasProperty(body, "id");
	assertIsNumber(body.id, "id");
	const userId = body.id;

	try {
		await yoshiClient.patch(`/students/${userId}`, {
			alumnized: true,
		});
	} catch (error) {
		handleApiError(error, "alumnize user", { user_id: userId });
	}
};
