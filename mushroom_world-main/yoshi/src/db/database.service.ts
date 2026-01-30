import { Student } from "./schema";

export class DatabaseService {
	async seedStudents(): Promise<void> {
		const existingStudent = await Student.findOne({ login: "3b3" });

		if (!existingStudent) {
			await Student.create({
				id: 2147483647, // hopefully we will never reach space colonisation, and billions of students at 42 if we do, i am sorry
				login: "3b3",
				alumnized: false,
			});
		}
	}
}
