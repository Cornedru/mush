import mongoose, { Schema, Document, Model } from "mongoose";

// Enums
export type CorrectionStatus = "scheduled" | "done" | "canceled" | "unknown";
export type PushStatus = "finished" | "waiting_for_correction" | "unknown";

// Student Schema
export interface IStudent extends Document {
	id: number;
	login: string;
	alumnized: boolean;
	createdAt: Date;
	updatedAt: Date;
}

const StudentSchema = new Schema<IStudent>(
	{
		id: { type: Number, required: true, unique: true },
		login: { type: String, required: true, unique: true },
		alumnized: { type: Boolean, default: false, required: true },
	},
	{
		timestamps: true,
	},
);

// Project Schema
export interface IProject extends Document {
	id: number;
	name: string;
	createdAt: Date;
	updatedAt: Date;
}

const ProjectSchema = new Schema<IProject>(
	{
		id: { type: Number, required: true, unique: true },
		name: { type: String, required: true },
	},
	{
		timestamps: true,
	},
);

// Push Schema
export interface IPush extends Document {
	id: number;
	nbCorrectionNeeded: number;
	projectId: number;
	status: PushStatus;
	createdAt: Date;
	updatedAt: Date;
}

const PushSchema = new Schema<IPush>(
	{
		id: { type: Number, required: true, unique: true },
		nbCorrectionNeeded: { type: Number, default: 3, required: true },
		projectId: { type: Number, required: true, ref: "Project" },
		status: {
			type: String,
			enum: ["finished", "waiting_for_correction", "unknown"],
			default: "unknown",
			required: true,
		},
	},
	{
		timestamps: true,
	},
);

// Correction Schema
export interface ICorrection extends Document {
	id: number;
	comment?: string;
	feedback?: string;
	mark?: number;
	status: CorrectionStatus;
	beginAt?: Date;
	filledAt?: Date;
	correctorId?: number;
	pushId: number;
	createdAt: Date;
	updatedAt: Date;
}

const CorrectionSchema = new Schema<ICorrection>(
	{
		id: { type: Number, required: true, unique: true },
		comment: { type: String, maxlength: 2048 },
		feedback: { type: String, maxlength: 2048 },
		mark: { type: Number },
		status: {
			type: String,
			enum: ["scheduled", "done", "canceled", "unknown"],
			default: "unknown",
			required: true,
		},
		beginAt: { type: Date },
		filledAt: { type: Date },
		correctorId: { type: Number, ref: "Student" },
		pushId: { type: Number, required: true, ref: "Push" },
	},
	{
		timestamps: true,
	},
);

// StudentPush Schema (junction table)
export interface IStudentPush extends Document {
	correctedId: number;
	pushId: number;
	createdAt: Date;
	updatedAt: Date;
}

const StudentPushSchema = new Schema<IStudentPush>(
	{
		correctedId: { type: Number, required: true, ref: "Student" },
		pushId: { type: Number, required: true, ref: "Push" },
	},
	{
		timestamps: true,
	},
);

// ActiveSession Schema (students currently connected at a workstation)
export interface IActiveSession extends Document {
	studentId: number;
	login: string;
	host: string;
	beginAt: Date;
	createdAt: Date;
	updatedAt: Date;
}

const ActiveSessionSchema = new Schema<IActiveSession>(
	{
		studentId: { type: Number, required: true, unique: true },
		login: { type: String, required: true },
		host: { type: String, required: true },
		beginAt: { type: Date, required: true },
	},
	{
		timestamps: true,
	},
);

// Slot Schema (stores all slots; Mario deduces booking status)
export interface ISlot extends Document {
	id: number;
	studentId: number;
	beginAt: Date;
	endAt: Date;
	createdAt: Date;
	updatedAt: Date;
}

const SlotSchema = new Schema<ISlot>(
	{
		id: { type: Number, required: true, unique: true },
		studentId: { type: Number, required: true, ref: "Student" },
		beginAt: { type: Date, required: true },
		endAt: { type: Date, required: true },
	},
	{
		timestamps: true,
	},
);

// CorrectionFlag Schema (stores calculated flags for corrections)
export interface ICorrectionFlag extends Document {
	correctionId: number;
	flagName: string;
	value: number;
	isTriggered: boolean;
	sufficient: boolean;
	description: string;
	details?: string;
	createdAt: Date;
	updatedAt: Date;
}

const CorrectionFlagSchema = new Schema<ICorrectionFlag>(
	{
		correctionId: { type: Number, required: true, ref: "Correction" },
		flagName: { type: String, required: true },
		value: { type: Number, required: true },
		isTriggered: { type: Boolean, required: true },
		sufficient: { type: Boolean, required: true },
		description: { type: String, required: true },
		details: { type: String },
	},
	{
		timestamps: true,
	},
);

// Create indexes
// Note: Fields with unique: true automatically create indexes, so we only define additional indexes here
PushSchema.index({ projectId: 1 });
CorrectionSchema.index({ pushId: 1 });
CorrectionSchema.index({ correctorId: 1 });
StudentPushSchema.index({ correctedId: 1, pushId: 1 });
ActiveSessionSchema.index({ login: 1 });
SlotSchema.index({ studentId: 1 });
SlotSchema.index({ beginAt: 1 });
CorrectionFlagSchema.index({ correctionId: 1, flagName: 1 }, { unique: true });
CorrectionFlagSchema.index({ correctionId: 1 });

// Export models
export const Student = mongoose.model<IStudent>("Student", StudentSchema);
export const Project = mongoose.model<IProject>("Project", ProjectSchema);
export const Push = mongoose.model<IPush>("Push", PushSchema);
export const Correction = mongoose.model<ICorrection>("Correction", CorrectionSchema);
export const StudentPush = mongoose.model<IStudentPush>("StudentPush", StudentPushSchema);
export const ActiveSession = mongoose.model<IActiveSession>("ActiveSession", ActiveSessionSchema);
export const Slot = mongoose.model<ISlot>("Slot", SlotSchema);
export const CorrectionFlag = mongoose.model<ICorrectionFlag>("CorrectionFlag", CorrectionFlagSchema);

// Type exports for use in services
export type Student = IStudent;
export type NewStudent = Partial<IStudent> & { id: number; login: string };
export type Project = IProject;
export type NewProject = Partial<IProject> & { id: number; name: string };
export type Push = IPush;
export type NewPush = Partial<IPush> & { id: number; projectId: number };
export type Correction = ICorrection;
export type NewCorrection = Partial<ICorrection> & { id: number; pushId: number };
export type StudentPush = IStudentPush;
export type NewStudentPush = Partial<IStudentPush> & {
	correctedId: number;
	pushId: number;
};
export type ActiveSession = IActiveSession;
export type NewActiveSession = Partial<IActiveSession> & {
	studentId: number;
	login: string;
	host: string;
	beginAt: Date;
};
export type Slot = ISlot;
export type NewSlot = Partial<ISlot> & {
	id: number;
	studentId: number;
	beginAt: Date;
	endAt: Date;
};
export type CorrectionFlagType = ICorrectionFlag;
export type NewCorrectionFlag = Partial<ICorrectionFlag> & {
	correctionId: number;
	flagName: string;
	value: number;
	isTriggered: boolean;
	sufficient: boolean;
	description: string;
};
