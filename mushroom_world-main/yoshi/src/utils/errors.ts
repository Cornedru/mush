import mongoose from "mongoose";

export function isMongoError(error: unknown): error is mongoose.Error {
	return error instanceof mongoose.Error;
}

export function isDuplicateKeyError(error: unknown): boolean {
	if (!isMongoError(error)) return false;
	return (error as any).code === 11000 || (error as any).code === 11001;
}

export function getDuplicateKeyField(error: unknown): string | null {
	if (!isDuplicateKeyError(error)) return null;
	const mongoError = error as any;
	if (mongoError.keyPattern) {
		return Object.keys(mongoError.keyPattern)[0] || null;
	}
	return null;
}

export function handleDatabaseError(error: unknown, context: string): never {
	if (isDuplicateKeyError(error)) {
		const field = getDuplicateKeyField(error);
		const message = field
			? `Duplicate entry: ${field} already exists`
			: "Duplicate entry: resource already exists";
		throw new Error(message);
	}

	if (isMongoError(error)) {
		throw new Error(`Database error in ${context}: ${error.message}`);
	}

	if (error instanceof Error) {
		throw error;
	}

	throw new Error(`Unexpected error in ${context}`);
}
