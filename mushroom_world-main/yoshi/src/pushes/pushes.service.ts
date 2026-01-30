import {
	Push,
	StudentPush,
	NewPush,
	Student,
	Project,
} from "../db/schema";
import type { Push as IPush } from "../db/schema";
import { handleDatabaseError } from "../utils/errors";

export class PushesService {
	private async formatPush(push: IPush | null): Promise<any> {
		if (!push) return null;

		// Fetch related data
		const [project, studentPushes] = await Promise.all([
			Project.findOne({ id: push.projectId }).lean().exec(),
			StudentPush.find({ pushId: push.id }).lean().exec(),
		]);

		// Fetch correcteds (students in the push)
		const correctedIds = studentPushes.map((sp) => sp.correctedId);
		const correcteds = await Student.find({ id: { $in: correctedIds } })
			.lean()
			.exec();

		// Return in snake_case format matching 42 API
		return {
			id: push.id,
			nb_correction_needed: push.nbCorrectionNeeded,
			status: push.status,
			project: project
				? {
						id: project.id,
						name: project.name,
				  }
				: null,
			correcteds: correcteds.map((s) => ({
				id: s.id,
				login: s.login,
			})),
		};
	}

	async getAll(): Promise<any[]> {
		try {
			const pushes = await Push.find({}).lean().exec();
			if (pushes.length === 0) return [];

			// Batch fetch all related data
			const pushIds = pushes.map((p) => p.id);
			const projectIds = [...new Set(pushes.map((p) => p.projectId))];

			const [projects, studentPushes] = await Promise.all([
				Project.find({ id: { $in: projectIds } }).lean().exec(),
				StudentPush.find({ pushId: { $in: pushIds } }).lean().exec(),
			]);

			// Get unique corrected IDs
			const correctedIds = [
				...new Set(studentPushes.map((sp) => sp.correctedId)),
			];

			// Batch fetch all students
			const students =
				correctedIds.length > 0
					? await Student.find({ id: { $in: correctedIds } })
							.lean()
							.exec()
					: [];

			// Create lookup maps for O(1) access
			const projectMap = new Map(
				projects.map((p) => [p.id, { id: p.id, name: p.name }]),
			);
			const studentMap = new Map(
				students.map((s) => [s.id, { id: s.id, login: s.login }]),
			);
			const studentPushesByPushId = new Map<number, typeof studentPushes>();
			for (const sp of studentPushes) {
				if (!studentPushesByPushId.has(sp.pushId)) {
					studentPushesByPushId.set(sp.pushId, []);
				}
				studentPushesByPushId.get(sp.pushId)!.push(sp);
			}

			// Format all pushes using the pre-fetched data
			return pushes.map((push) => {
				const pushStudentPushes = studentPushesByPushId.get(push.id) || [];
				const correcteds = pushStudentPushes
					.map((sp) => studentMap.get(sp.correctedId))
					.filter((s) => s !== undefined);

				return {
					id: push.id,
					nb_correction_needed: push.nbCorrectionNeeded,
					status: push.status,
					project: projectMap.get(push.projectId) || null,
					correcteds: correcteds,
				};
			});
		} catch (error) {
			handleDatabaseError(error, "getAll pushes");
		}
	}

	async getOne(push_id: number): Promise<any | null> {
		try {
			const push = await Push.findOne({ id: push_id }).lean().exec();
			return this.formatPush(push as IPush | null);
		} catch (error) {
			handleDatabaseError(error, "getOne push");
		}
	}

	async create(push: NewPush & { correcteds: { id: number }[] }): Promise<IPush> {
		try {
			const createdPush = await Push.create(push);

			// Insert student-push relations
			if (push.correcteds && push.correcteds.length > 0) {
				await StudentPush.insertMany(
					push.correcteds.map((student) => ({
						correctedId: student.id,
						pushId: createdPush.id,
					})),
				);
			}

			return createdPush.toObject();
		} catch (error) {
			handleDatabaseError(error, "create push");
		}
	}

	async update(
		id: number,
		push_data: Partial<NewPush> & { correcteds?: { id: number }[] },
	): Promise<number> {
		try {
			const { correcteds, ...updateData } = push_data;

			const result = await Push.updateOne(
				{ id },
				{ ...updateData, updatedAt: new Date() },
			).exec();

			if (result.matchedCount === 0) return 0;

			// Update student-push relations if provided
			if (correcteds !== undefined) {
				// Delete existing relations
				await StudentPush.deleteMany({ pushId: id }).exec();

				// Insert new relations
				if (correcteds.length > 0) {
					await StudentPush.insertMany(
						correcteds.map((student) => ({
							correctedId: student.id,
							pushId: id,
						})),
					);
				}
			}

			return result.modifiedCount;
		} catch (error) {
			handleDatabaseError(error, "update push");
		}
	}
}
