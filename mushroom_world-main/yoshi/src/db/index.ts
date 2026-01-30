import mongoose from "mongoose";
import { DB_HOST } from "../utils/config";

const connectionString = `mongodb://${Bun.env.DB_USER}:${Bun.env.DB_PASS}@${DB_HOST}:27017/${Bun.env.DB_NAME}?authSource=admin`;

// Setup connection event handlers
mongoose.connection.on("connected", () => {
	console.log("MongoDB connection established");
});

mongoose.connection.on("error", (err) => {
	console.error("MongoDB connection error:", err);
});

mongoose.connection.on("disconnected", () => {
	console.warn("MongoDB disconnected");
});

export async function connectDatabase(): Promise<void> {
	try {
		await mongoose.connect(connectionString, {
			maxPoolSize: 10,
			serverSelectionTimeoutMS: 5000,
			socketTimeoutMS: 45000,
			connectTimeoutMS: 10000,
		});
		console.log("Connected to MongoDB");
	} catch (error) {
		console.error("MongoDB connection error:", error);
		throw error;
	}
}

export async function disconnectDatabase(): Promise<void> {
	try {
		await mongoose.disconnect();
		console.log("Disconnected from MongoDB");
	} catch (error) {
		console.error("MongoDB disconnection error:", error);
		// Don't throw on disconnect - allow graceful shutdown even if disconnect fails
	}
}

export function isDatabaseConnected(): boolean {
	return mongoose.connection.readyState === 1;
}
