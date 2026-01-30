import {
	Correction,
	StudentPush,
	NewCorrection,
	Student,
	Push,
	Project,
} from "../db/schema";
import type { Correction as ICorrection } from "../db/schema";
import { handleDatabaseError } from "../utils/errors";

export class CorrectionService {
	private async formatCorrection(correction: ICorrection | null): Promise<any> {
		if (!correction) return null;

		// Fetch related data
		const [push, corrector, studentPushes] = await Promise.all([
			Push.findOne({ id: correction.pushId }).lean().exec(),
			correction.correctorId
				? Student.findOne({ id: correction.correctorId }).lean().exec()
				: null,
			StudentPush.find({ pushId: correction.pushId }).lean().exec(),
		]);

		// Fetch correcteds (students in the push)
		const correctedIds = studentPushes.map((sp) => sp.correctedId);
		const correcteds = await Student.find({ id: { $in: correctedIds } })
			.lean()
			.exec();

		// Fetch project if push exists
		const project = push
			? await Project.findOne({ id: push.projectId }).lean().exec()
			: null;

		// Format push with correcteds and project
		const formattedPush = push
			? {
					id: push.id,
					project_id: push.projectId,
					correcteds: correcteds.map((s) => ({
						id: s.id,
						login: s.login,
					})),
			  }
			: null;

		// Format corrector
		const formattedCorrector = corrector
			? {
					id: corrector.id,
					login: corrector.login,
			  }
			: null;

		// Return in snake_case format matching 42 API
		return {
			id: correction.id,
			comment: correction.comment,
			feedback: correction.feedback,
			mark: correction.mark,
			status: correction.status,
			begin_at: correction.beginAt
				? correction.beginAt.toISOString()
				: null,
			filled_at: correction.filledAt
				? correction.filledAt.toISOString()
				: null,
			corrector: formattedCorrector,
			push: formattedPush,
			project: project
				? {
						id: project.id,
						name: project.name,
				  }
				: null,
		};
	}

	async getAll(): Promise<any[]> {
		try {
			const corrections = await Correction.find({}).lean().exec();
			if (corrections.length === 0) return [];

			// Batch fetch all related data
			const pushIds = [...new Set(corrections.map((c) => c.pushId))];
			const correctorIds = [
				...new Set(
					corrections
						.map((c) => c.correctorId)
						.filter((id): id is number => id !== undefined),
				),
			];

			const [pushes, correctors, studentPushes] = await Promise.all([
				Push.find({ id: { $in: pushIds } }).lean().exec(),
				correctorIds.length > 0
					? Student.find({ id: { $in: correctorIds } }).lean().exec()
					: [],
				StudentPush.find({ pushId: { $in: pushIds } }).lean().exec(),
			]);

			// Batch fetch all projects
			const projectIds = [...new Set(pushes.map((p) => p.projectId))];
			const projects =
				projectIds.length > 0
					? await Project.find({ id: { $in: projectIds } })
							.lean()
							.exec()
					: [];
			const projectMap = new Map(
				projects.map((p) => [p.id, { id: p.id, name: p.name }]),
			);

			// Get unique corrected IDs
			const correctedIds = [
				...new Set(studentPushes.map((sp) => sp.correctedId)),
			];

			// Batch fetch all students (correcteds)
			const correcteds =
				correctedIds.length > 0
					? await Student.find({ id: { $in: correctedIds } })
							.lean()
							.exec()
					: [];

			// Create lookup maps for O(1) access
			const pushMap = new Map(pushes.map((p) => [p.id, p]));
			const correctorMap = new Map(
				correctors.map((c) => [c.id, { id: c.id, login: c.login }]),
			);
			const studentMap = new Map(
				correcteds.map((s) => [s.id, { id: s.id, login: s.login }]),
			);
			const studentPushesByPushId = new Map<number, typeof studentPushes>();
			for (const sp of studentPushes) {
				if (!studentPushesByPushId.has(sp.pushId)) {
					studentPushesByPushId.set(sp.pushId, []);
				}
				studentPushesByPushId.get(sp.pushId)!.push(sp);
			}

			// Format all corrections using the pre-fetched data
			return corrections.map((correction) => {
				const push = pushMap.get(correction.pushId);
				const pushStudentPushes =
					studentPushesByPushId.get(correction.pushId) || [];
				const formattedCorrecteds = pushStudentPushes
					.map((sp) => studentMap.get(sp.correctedId))
					.filter((s) => s !== undefined);

				const formattedPush = push
					? {
							id: push.id,
							project_id: push.projectId,
							correcteds: formattedCorrecteds,
					  }
					: null;

				const formattedCorrector = correction.correctorId
					? correctorMap.get(correction.correctorId) || null
					: null;

				const formattedProject = push
					? projectMap.get(push.projectId) || null
					: null;

				return {
					id: correction.id,
					comment: correction.comment,
					feedback: correction.feedback,
					mark: correction.mark,
					status: correction.status,
					begin_at: correction.beginAt
						? correction.beginAt.toISOString()
						: null,
					filled_at: correction.filledAt
						? correction.filledAt.toISOString()
						: null,
					corrector: formattedCorrector,
					push: formattedPush,
					project: formattedProject,
				};
			});
		} catch (error) {
			handleDatabaseError(error, "getAll corrections");
		}
	}

	async getOne(id: number): Promise<any | null> {
		try {
			const correction = await Correction.findOne({ id }).lean().exec();
			return this.formatCorrection(correction as ICorrection | null);
		} catch (error) {
			handleDatabaseError(error, "getOne correction");
		}
	}

	async getByPush(push_id: number): Promise<any[]> {
		try {
			const corrections = await Correction.find({ pushId: push_id })
				.lean()
				.exec();
			return Promise.all(
				corrections.map((corr) => this.formatCorrection(corr as ICorrection)),
			);
		} catch (error) {
			handleDatabaseError(error, "getByPush corrections");
		}
	}

	async getByCorrector(corrector_id: number): Promise<any[]> {
		try {
			const corrections = await Correction.find({ correctorId: corrector_id })
				.lean()
				.exec();
			return Promise.all(
				corrections.map((corr) => this.formatCorrection(corr as ICorrection)),
			);
		} catch (error) {
			handleDatabaseError(error, "getByCorrector corrections");
		}
	}

	async getByCorrected(user_id: number): Promise<any[]> {
		try {
			// Get all pushes where the user is corrected
			const userPushes = await StudentPush.find({ correctedId: user_id })
				.select("pushId")
				.lean()
				.exec();

			const pushIds = userPushes.map((up) => up.pushId);

			if (pushIds.length === 0) return [];

			const corrections = await Correction.find({
				pushId: { $in: pushIds },
			})
				.lean()
				.exec();
			return Promise.all(
				corrections.map((corr) => this.formatCorrection(corr as ICorrection)),
			);
		} catch (error) {
			handleDatabaseError(error, "getByCorrected corrections");
		}
	}

	async create(correction: NewCorrection): Promise<ICorrection> {
		try {
			const created = await Correction.create(correction);
			return created.toObject();
		} catch (error) {
			handleDatabaseError(error, "create correction");
		}
	}

	async update(
		id: number,
		correction_data: Partial<NewCorrection>,
	): Promise<number> {
		try {
			const result = await Correction.updateOne(
				{ id },
				{ ...correction_data, updatedAt: new Date() },
			).exec();
			return result.modifiedCount;
		} catch (error) {
			handleDatabaseError(error, "update correction");
		}
	}
}
