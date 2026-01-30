import {
	Slot,
} from "../db/schema";
import type { Slot as ISlot } from "../db/schema";
import { handleDatabaseError } from "../utils/errors";

interface SlotInput {
	id: number;
	student_id: number;
	begin_at: string;
	end_at: string;
}

interface FormattedSlot {
	id: number;
	student_id: number;
	begin_at: string | null;
	end_at: string | null;
	created_at: string | null;
	updated_at: string | null;
}

export class SlotService {
	private formatSlot(slot: ISlot | null): FormattedSlot | null {
		if (!slot) return null;
		return {
			id: slot.id,
			student_id: slot.studentId,
			begin_at: slot.beginAt ? slot.beginAt.toISOString() : null,
			end_at: slot.endAt ? slot.endAt.toISOString() : null,
			created_at: slot.createdAt ? slot.createdAt.toISOString() : null,
			updated_at: slot.updatedAt ? slot.updatedAt.toISOString() : null,
		};
	}

	async getAll(): Promise<FormattedSlot[]> {
		try {
			const slots = await Slot.find({}).lean().exec();
			return slots.map(slot => this.formatSlot(slot)!);
		} catch (error) {
			handleDatabaseError(error, "getAll slots");
		}
	}

	async getById(id: number): Promise<FormattedSlot | null> {
		try {
			const slot = await Slot.findOne({ id }).lean().exec();
			return this.formatSlot(slot);
		} catch (error) {
			handleDatabaseError(error, "getById slot");
		}
	}

	async getByStudentId(studentId: number): Promise<FormattedSlot[]> {
		try {
			const slots = await Slot.find({ studentId }).lean().exec();
			return slots.map(slot => this.formatSlot(slot)!);
		} catch (error) {
			handleDatabaseError(error, "getByStudentId slots");
		}
	}

	async upsert(slot: SlotInput): Promise<FormattedSlot> {
		try {
			// Use $set to update fields, preserving createdAt on updates
			// Mongoose timestamps will handle createdAt on insert automatically
			const result = await Slot.findOneAndUpdate(
				{ id: slot.id },
				{
					$set: {
						studentId: slot.student_id,
						beginAt: slot.begin_at,
						endAt: slot.end_at,
					},
					$setOnInsert: {
						id: slot.id,
					},
				},
				{ upsert: true, new: true }
			).lean().exec();
			return this.formatSlot(result)!;
		} catch (error) {
			handleDatabaseError(error, "upsert slot");
		}
	}

	async delete(id: number): Promise<number> {
		try {
			const result = await Slot.deleteOne({ id }).exec();
			return result.deletedCount || 0;
		} catch (error) {
			handleDatabaseError(error, "delete slot");
		}
	}

	async deleteNotInList(ids: number[]): Promise<number> {
		try {
			const result = await Slot.deleteMany({
				id: { $nin: ids }
			}).exec();
			return result.deletedCount || 0;
		} catch (error) {
			handleDatabaseError(error, "deleteNotInList slots");
		}
	}
}
