import {
	Student,
	NewStudent,
} from "../db/schema";
import type { Student as IStudent } from "../db/schema";
import { handleDatabaseError } from "../utils/errors";

export class StudentService {
	async getAll(): Promise<IStudent[]> {
		try {
			return await Student.find({}).lean().exec();
		} catch (error) {
			handleDatabaseError(error, "getAll students");
		}
	}

	async getOne(id: number): Promise<IStudent | null> {
		try {
			return await Student.findOne({ id }).lean().exec();
		} catch (error) {
			handleDatabaseError(error, "getOne student");
		}
	}

	async getByLogin(login: string): Promise<IStudent | null> {
		try {
			let result = await Student.findOne({ login }).lean().exec();

			if (!result && login.startsWith("3b3")) {
				result = await Student.findOne({ login: "3b3" }).lean().exec();
			}

			return result;
		} catch (error) {
			handleDatabaseError(error, "getByLogin student");
		}
	}

	async create(student: NewStudent): Promise<IStudent> {
		try {
			const created = await Student.create(student);
			return created.toObject();
		} catch (error) {
			handleDatabaseError(error, "create student");
		}
	}

	async update(id: number, student_data: Partial<NewStudent>): Promise<number> {
		try {
			const result = await Student.updateOne(
				{ id },
				{ ...student_data, updatedAt: new Date() },
			).exec();
			return result.modifiedCount;
		} catch (error) {
			handleDatabaseError(error, "update student");
		}
	}
}
