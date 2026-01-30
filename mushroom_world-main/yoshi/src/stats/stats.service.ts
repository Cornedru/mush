import {
	Student,
	ActiveSession,
	Project,
	Correction,
	Push,
	Slot,
	CorrectionFlag,
} from "../db/schema";
import { handleDatabaseError } from "../utils/errors";

export interface Stats {
	students: number;
	activeSessions: number;
	projects: number;
	corrections: number;
	pushes: number;
	slots: number;
	flags: number;
}

export class StatsService {
	async getStats(): Promise<Stats> {
		try {
			const [
				students,
				activeSessions,
				projects,
				corrections,
				pushes,
				slots,
				flags,
			] = await Promise.all([
				Student.countDocuments().exec(),
				ActiveSession.countDocuments().exec(),
				Project.countDocuments().exec(),
				Correction.countDocuments().exec(),
				Push.countDocuments().exec(),
				Slot.countDocuments().exec(),
				CorrectionFlag.countDocuments().exec(),
			]);

			return {
				students,
				activeSessions,
				projects,
				corrections,
				pushes,
				slots,
				flags,
			};
		} catch (error) {
			handleDatabaseError(error, "getStats");
		}
	}
}
