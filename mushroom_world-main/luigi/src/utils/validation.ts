export function isValidToken(token: string | undefined): token is string {
	return typeof token === "string" && token.length > 0;
}

export function assertHasProperty<T extends Record<string, unknown>>(
	obj: unknown,
	property: keyof T
): asserts obj is T {
	if (!obj || typeof obj !== "object") {
		throw new Error(`Invalid body: expected object`);
	}
	if (!(property in obj)) {
		throw new Error(`Invalid body: missing required property '${String(property)}'`);
	}
}

export function assertIsNumber(value: unknown, fieldName: string): asserts value is number {
	if (typeof value !== "number" || isNaN(value)) {
		throw new Error(`Invalid ${fieldName}: expected number`);
	}
}

export function assertIsString(value: unknown, fieldName: string): asserts value is string {
	if (typeof value !== "string") {
		throw new Error(`Invalid ${fieldName}: expected string`);
	}
}
