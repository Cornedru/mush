import {
	ActiveSession,
} from "../db/schema";
import type { ActiveSession as IActiveSession } from "../db/schema";
import { handleDatabaseError } from "../utils/errors";

interface SessionInput {
	login: string;
	host: string;
	begin_at: string;
}

interface FormattedSession {
	student_id: number;
	login: string;
	host: string;
	begin_at: string | null;
}

export class ActiveSessionService {
	private formatSession(session: IActiveSession | null): FormattedSession | null {
		if (!session) return null;
		return {
			student_id: session.studentId,
			login: session.login,
			host: session.host,
			begin_at: session.beginAt ? session.beginAt.toISOString() : null,
		};
	}

	async getAll(): Promise<FormattedSession[]> {
		try {
			const sessions = await ActiveSession.find({}).lean().exec();
			return sessions.map(session => this.formatSession(session)!);
		} catch (error) {
			handleDatabaseError(error, "getAll active sessions");
		}
	}

	async getByStudentId(studentId: number): Promise<FormattedSession | null> {
		try {
			const session = await ActiveSession.findOne({ studentId }).lean().exec();
			return this.formatSession(session);
		} catch (error) {
			handleDatabaseError(error, "getByStudentId active session");
		}
	}

	async getByLogin(login: string): Promise<FormattedSession | null> {
		try {
			const session = await ActiveSession.findOne({ login }).lean().exec();
			return this.formatSession(session);
		} catch (error) {
			handleDatabaseError(error, "getByLogin active session");
		}
	}

	async create(studentId: number, session: SessionInput): Promise<FormattedSession> {
		try {
			const created = await ActiveSession.create({
				studentId,
				login: session.login,
				host: session.host,
				beginAt: session.begin_at,
			});
			return this.formatSession(created.toObject())!;
		} catch (error) {
			handleDatabaseError(error, "create active session");
		}
	}

	async upsert(studentId: number, session: SessionInput): Promise<FormattedSession> {
		try {
			const result = await ActiveSession.findOneAndUpdate(
				{ studentId },
				{
					studentId,
					login: session.login,
					host: session.host,
					beginAt: session.begin_at,
					updatedAt: new Date(),
				},
				{ upsert: true, new: true },
			).lean().exec();
			return this.formatSession(result as IActiveSession)!;
		} catch (error) {
			handleDatabaseError(error, "upsert active session");
		}
	}

	async deleteByStudentId(studentId: number): Promise<number> {
		try {
			const result = await ActiveSession.deleteOne({ studentId }).exec();
			return result.deletedCount;
		} catch (error) {
			handleDatabaseError(error, "delete active session by student id");
		}
	}

}
