import axios, { AxiosError } from "axios";
import { YOSHI_ENDPOINT } from "./config";

export const yoshiClient = axios.create({
	baseURL: YOSHI_ENDPOINT,
	headers: {
		"Content-Type": "application/json",
	},
	timeout: 10000,
});

export function isAxiosError(error: unknown): error is AxiosError {
	return axios.isAxiosError(error);
}

export function handleApiError(
	error: unknown,
	context: string,
	metadata?: Record<string, unknown>
): never {
	if (isAxiosError(error)) {
		const status = error.response?.status;
		const statusText = error.response?.statusText;
		const data = error.response?.data;

		const metaStr = metadata
			? Object.entries(metadata)
					.map(([k, v]) => `${k}=${v}`)
					.join(", ")
			: "";

		console.error(
			`Error ${context}: ${metaStr ? `${metaStr}, ` : ""}status=${status || "unknown"}, message=${error.message}`,
			{ error: data, stack: error.stack }
		);

		if (status === 409) {
			// Conflict - might be a race condition, allow caller to handle
			throw new Error(`Conflict: ${context}`);
		}
	}

	console.error(`Unexpected error ${context}:`, error);
	if (error instanceof Error) {
		console.error("Error stack:", error.stack);
	}

	throw new Error(`Failed to ${context}`);
}
