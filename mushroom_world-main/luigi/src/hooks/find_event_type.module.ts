import {
	scale_team_create,
	scale_team_destroy,
	scale_team_update,
} from "./scale_team.module";
import { team_create } from "./team.module";
import {
	user_alumnize,
	user_create,
	user_update,
} from "./user.module";
import { location_create, location_close } from "./location.module";
import { isValidToken } from "../utils/validation";

type EventHandler = (body: Record<string, unknown>) => Promise<void>;

interface Event {
	name: string;
	handler: EventHandler;
}

const noop = async (_body: Record<string, unknown>): Promise<void> => {};

const noopEvent: Event = { name: "noop", handler: noop };

export const find_event_type = (secret: string | undefined): Event => {
	if (!secret) return noopEvent;

	const env = Bun.env;

	// User hooks
	if (isValidToken(env.USER_CREATE_TOKEN) && secret === env.USER_CREATE_TOKEN)
		return { name: "user_create", handler: user_create };
	if (isValidToken(env.USER_UPDATE_TOKEN) && secret === env.USER_UPDATE_TOKEN)
		return { name: "user_update", handler: user_update };
	if (isValidToken(env.USER_ALUMNIZE_TOKEN) && secret === env.USER_ALUMNIZE_TOKEN)
		return { name: "user_alumnize", handler: user_alumnize };

	// Team hooks
	if (isValidToken(env.TEAM_CREATE_TOKEN) && secret === env.TEAM_CREATE_TOKEN)
		return { name: "team_create", handler: team_create };

	// Scale team hooks
	if (isValidToken(env.SCALE_TEAM_CREATE_TOKEN) && secret === env.SCALE_TEAM_CREATE_TOKEN)
		return { name: "scale_team_create", handler: scale_team_create };
	if (isValidToken(env.SCALE_TEAM_UPDATE_TOKEN) && secret === env.SCALE_TEAM_UPDATE_TOKEN)
		return { name: "scale_team_update", handler: scale_team_update };
	if (isValidToken(env.SCALE_TEAM_DESTROY_TOKEN) && secret === env.SCALE_TEAM_DESTROY_TOKEN)
		return { name: "scale_team_destroy", handler: scale_team_destroy };

	// Location hooks
	if (isValidToken(env.LOCATION_CREATE_TOKEN) && secret === env.LOCATION_CREATE_TOKEN)
		return { name: "location_create", handler: location_create };
	if (isValidToken(env.LOCATION_CLOSE_TOKEN) && secret === env.LOCATION_CLOSE_TOKEN)
		return { name: "location_close", handler: location_close };

	return noopEvent;
};
