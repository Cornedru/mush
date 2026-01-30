import { yoshiClient, handleApiError } from "../utils/http";
import { assertHasProperty, assertIsNumber } from "../utils/validation";
import axios from "axios";

interface ScaleTeamBody {
	id: number;
	team: { id: number };
	user?: { id: number };
	corrector?: { id: number };
	scale: { correction_number: number };
	comment: string;
	feedback: string;
	final_mark: number | null;
	flag?: { name: string };
	begin_at: string | null;
	filled_at: string | null;
}

function validateScaleTeamBody(body: Record<string, unknown>): ScaleTeamBody {
	assertHasProperty(body, "id");
	assertHasProperty(body, "team");
	assertHasProperty(body, "scale");
	assertIsNumber(body.id, "id");

	if (!body.team || typeof body.team !== "object" || !("id" in body.team)) {
		throw new Error("Invalid body: team must have an id");
	}
	assertIsNumber((body.team as { id: unknown }).id, "team.id");

	if (!body.scale || typeof body.scale !== "object" || !("correction_number" in body.scale)) {
		throw new Error("Invalid body: scale must have correction_number");
	}
	assertIsNumber((body.scale as { correction_number: unknown }).correction_number, "scale.correction_number");

	return body as ScaleTeamBody;
}

function parseDate(dateString: string | null | undefined): string | undefined {
	if (!dateString) return undefined;
	const parsed = Date.parse(dateString);
	if (isNaN(parsed)) {
		console.warn(`Invalid date string: ${dateString}`);
		return undefined;
	}
	return new Date(parsed).toISOString();
}

function getCorrectionStatus(filledAt: string | null | undefined): string {
	if (filledAt === null || filledAt === undefined || filledAt === "") {
		return "scheduled";
	}
	return "done";
}

export const scale_team_create = async (body: Record<string, unknown>): Promise<void> => {
	console.log("scale_team_create body", JSON.stringify(body, null, 2));
	const scaleTeamData = validateScaleTeamBody(body);

	// Check if push exists
	try {
		await yoshiClient.get(`/pushes/${scaleTeamData.team.id}`);
	} catch (error) {
		// Push doesn't exist, skip processing
		return;
	}

	// Update push correction number if needed
	if (scaleTeamData.scale.correction_number !== 3) {
		try {
			await yoshiClient.patch(`/pushes/${scaleTeamData.team.id}`, {
				nb_correction_needed: scaleTeamData.scale.correction_number,
			});
		} catch (error) {
			handleApiError(error, "update push correction number", {
				team_id: scaleTeamData.team.id,
				correction_id: scaleTeamData.id,
				nb_needed: scaleTeamData.scale.correction_number,
			});
		}
	}

	const status = getCorrectionStatus(scaleTeamData.filled_at);
	const correctorId = scaleTeamData.corrector
		? scaleTeamData.corrector.id
		: scaleTeamData.user?.id;

	try {
		await yoshiClient.put(`/corrections/${scaleTeamData.id}`, {
			id: scaleTeamData.id,
			comment: scaleTeamData.comment,
			feedback: scaleTeamData.feedback,
			mark: scaleTeamData.final_mark,
			flag: scaleTeamData.flag?.name,
			begin_at: parseDate(scaleTeamData.begin_at),
			filled_at: parseDate(scaleTeamData.filled_at),
			corrector_id: correctorId,
			push_id: scaleTeamData.team.id,
			status: status,
		});
	} catch (error) {
		handleApiError(error, "create correction", {
			correction_id: scaleTeamData.id,
			team_id: scaleTeamData.team.id,
			corrector_id: correctorId || "none",
		});
	}

	await axios.get(`http://mario:3002/trigger/${scaleTeamData.id}`);
};

export const scale_team_update = async (body: Record<string, unknown>): Promise<void> => {
	console.log("scale_team_update body", JSON.stringify(body, null, 2));
	const scaleTeamData = validateScaleTeamBody(body);

	// Check if push exists
	try {
		await yoshiClient.get(`/pushes/${scaleTeamData.team.id}`);
	} catch (error) {
		// Push doesn't exist, skip processing
		return;
	}

	// Update push correction number if needed
	if (scaleTeamData.scale.correction_number !== 3) {
		try {
			await yoshiClient.patch(`/pushes/${scaleTeamData.team.id}`, {
				nb_correction_needed: scaleTeamData.scale.correction_number,
			});
		} catch (error) {
			handleApiError(error, "update push correction number", {
				team_id: scaleTeamData.team.id,
				correction_id: scaleTeamData.id,
				nb_needed: scaleTeamData.scale.correction_number,
			});
		}
	}

	const status = getCorrectionStatus(scaleTeamData.filled_at);
	const correctorId = scaleTeamData.corrector
		? scaleTeamData.corrector.id
		: scaleTeamData.user?.id;

	try {
		await yoshiClient.put(`/corrections/${scaleTeamData.id}`, {
			id: scaleTeamData.id,
			comment: scaleTeamData.comment,
			feedback: scaleTeamData.feedback,
			mark: scaleTeamData.final_mark,
			flag: scaleTeamData.flag?.name,
			begin_at: parseDate(scaleTeamData.begin_at),
			filled_at: parseDate(scaleTeamData.filled_at),
			corrector_id: correctorId,
			push_id: scaleTeamData.team.id,
			status: status,
		});
	} catch (error) {
		handleApiError(error, "update correction", {
			correction_id: scaleTeamData.id,
			team_id: scaleTeamData.team.id,
			corrector_id: correctorId || "none",
		});
	}
};

export const scale_team_destroy = async (body: Record<string, unknown>): Promise<void> => {
	console.log("scale_team_destroy body", JSON.stringify(body, null, 2));
	const scaleTeamData = validateScaleTeamBody(body);

	// Check if push exists
	try {
		await yoshiClient.get(`/pushes/${scaleTeamData.team.id}`);
	} catch (error) {
		// Push doesn't exist, skip processing
		return;
	}

	try {
		await yoshiClient.patch(`/corrections/${scaleTeamData.id}`, {
			status: "canceled",
		});
	} catch (error) {
		handleApiError(error, "cancel correction", {
			correction_id: scaleTeamData.id,
			team_id: scaleTeamData.team.id,
		});
	}
};
