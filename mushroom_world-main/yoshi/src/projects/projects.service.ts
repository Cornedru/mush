import { Project, NewProject } from "../db/schema";
import type { Project as IProject } from "../db/schema";
import { handleDatabaseError } from "../utils/errors";

export class ProjectService {
	async getAll(): Promise<IProject[]> {
		try {
			return await Project.find({}).lean().exec();
		} catch (error) {
			handleDatabaseError(error, "getAll projects");
		}
	}

	async getOne(project_id: number): Promise<IProject | null> {
		try {
			return await Project.findOne({ id: project_id }).lean().exec();
		} catch (error) {
			handleDatabaseError(error, "getOne project");
		}
	}

	async create(project: NewProject): Promise<IProject> {
		try {
			const created = await Project.create(project);
			return created.toObject();
		} catch (error) {
			handleDatabaseError(error, "create project");
		}
	}

	async update(id: number, project_data: Partial<NewProject>): Promise<number> {
		try {
			const result = await Project.updateOne(
				{ id },
				{ ...project_data, updatedAt: new Date() },
			).exec();
			return result.modifiedCount;
		} catch (error) {
			handleDatabaseError(error, "update project");
		}
	}
}
