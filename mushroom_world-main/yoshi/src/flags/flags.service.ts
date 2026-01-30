import { CorrectionFlag } from "../db/schema";
import type { CorrectionFlagType as ICorrectionFlag } from "../db/schema";
import { handleDatabaseError } from "../utils/errors";

interface FlagInput {
	correction_id: number;
	flag_name: string;
	value: number;
	is_triggered: boolean;
	sufficient: boolean;
	description: string;
	details?: string;
}

interface FormattedFlag {
	correction_id: number;
	flag_name: string;
	value: number;
	is_triggered: boolean;
	sufficient: boolean;
	description: string;
	details: string | null;
	created_at: string | null;
	updated_at: string | null;
}

export class FlagService {
	private formatFlag(flag: ICorrectionFlag | null): FormattedFlag | null {
		if (!flag) return null;
		return {
			correction_id: flag.correctionId,
			flag_name: flag.flagName,
			value: flag.value,
			is_triggered: flag.isTriggered,
			sufficient: flag.sufficient,
			description: flag.description,
			details: flag.details || null,
			created_at: flag.createdAt ? flag.createdAt.toISOString() : null,
			updated_at: flag.updatedAt ? flag.updatedAt.toISOString() : null,
		};
	}

	async getByCorrection(correctionId: number): Promise<FormattedFlag[]> {
		try {
			const flags = await CorrectionFlag.find({ correctionId }).lean().exec();
			return flags.map((flag) => this.formatFlag(flag)!);
		} catch (error) {
			handleDatabaseError(error, "getByCorrection flags");
		}
	}

	async upsert(flag: FlagInput): Promise<FormattedFlag> {
		try {
			const result = await CorrectionFlag.findOneAndUpdate(
				{ correctionId: flag.correction_id, flagName: flag.flag_name },
				{
					$set: {
						value: flag.value,
						isTriggered: flag.is_triggered,
						sufficient: flag.sufficient,
						description: flag.description,
						details: flag.details,
					},
					$setOnInsert: {
						correctionId: flag.correction_id,
						flagName: flag.flag_name,
					},
				},
				{ upsert: true, new: true }
			)
				.lean()
				.exec();
			return this.formatFlag(result)!;
		} catch (error) {
			handleDatabaseError(error, "upsert flag");
		}
	}

	async upsertMany(flags: FlagInput[]): Promise<FormattedFlag[]> {
		try {
			const results: FormattedFlag[] = [];
			for (const flag of flags) {
				const result = await this.upsert(flag);
				results.push(result);
			}
			return results;
		} catch (error) {
			handleDatabaseError(error, "upsertMany flags");
		}
	}

	async deleteByCorrection(correctionId: number): Promise<number> {
		try {
			const result = await CorrectionFlag.deleteMany({ correctionId }).exec();
			return result.deletedCount || 0;
		} catch (error) {
			handleDatabaseError(error, "deleteByCorrection flags");
		}
	}
}
