import { yoshiClient, handleApiError, isAxiosError } from "../utils/http";
import { assertHasProperty, assertIsNumber } from "../utils/validation";

interface TeamBody {
	id: number;
	project: { id: number };
	users: Array<{ id: number; login: string }>;
	final_mark: number | null;
}

function validateTeamBody(body: Record<string, unknown>): TeamBody {
	assertHasProperty(body, "id");
	assertHasProperty(body, "project");
	assertHasProperty(body, "users");
	assertIsNumber(body.id, "id");

	if (!body.project || typeof body.project !== "object" || !("id" in body.project)) {
		throw new Error("Invalid body: project must have an id");
	}
	assertIsNumber(body.project.id, "project.id");

	if (!Array.isArray(body.users)) {
		throw new Error("Invalid body: users must be an array");
	}

	return body as TeamBody;
}

export const team_create = async (body: Record<string, unknown>): Promise<void> => {
	const teamData = validateTeamBody(body);

	// Check if project exists
	try {
		const projectResp = await yoshiClient.get(`/projects/${teamData.project.id}`);
		if (projectResp.status !== 200) {
			return;
		}
	} catch (error) {
		// Project doesn't exist, skip processing
		return;
	}

	// Ensure all students exist
	for (const student of teamData.users) {
		try {
			await yoshiClient.get(`/students/${student.id}`);
		} catch (error) {
			// Student doesn't exist, create it
			try {
				await yoshiClient.put(`/students/${student.id}`, {
					login: student.login,
					id: student.id,
				});
			} catch (createError) {
				// Handle race condition: if student was created by another request, that's okay
				if (isAxiosError(createError) && createError.response?.status === 409) {
					console.warn(
						`Student ${student.id} already exists (race condition), continuing...`
					);
					continue;
				}
				handleApiError(createError, "create student", {
					student_id: student.id,
					login: student.login,
					team_id: teamData.id,
				});
			}
		}
	}

	// Create or update push
	try {
		await yoshiClient.put(`/pushes/${teamData.id}`, {
			id: teamData.id,
			project_id: teamData.project.id,
			correcteds_logins: teamData.users.map((user) => user.login),
			status:
				teamData.final_mark !== null
					? "finished"
					: "waiting_for_correction",
		});
	} catch (error) {
		handleApiError(error, "create push", {
			push_id: teamData.id,
			project_id: teamData.project.id,
			users: teamData.users.map((u) => u.login).join(", "),
		});
	}
};
