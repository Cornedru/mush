export class LoggerService {
	logError(context: string, methodName: string, error: unknown): void {
		if (error && typeof error === "object" && "status" in error) {
			console.error(
				`[${context}] [${methodName.toUpperCase()}] HTTP Exception: ${(error as any).message}`,
			);
		} else if (error instanceof Error) {
			console.error(
				`[${context}] [${methodName.toUpperCase()}] Internal Server Error: ${error.message}`,
				error.stack,
			);
		} else {
			console.error(
				`[${context}] [${methodName.toUpperCase()}] Unknown error:`,
				error,
			);
		}
	}
}

export const loggerService = new LoggerService();
