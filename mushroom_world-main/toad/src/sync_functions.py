from sync_students import sync_students, STUDENTS
from sync_projects import sync_projects, PROJECTS
from sync_pushes import sync_pushes, PUSHES
from sync_corrections import sync_corrections, CORRECTIONS
from sync_active_sessions import sync_active_sessions, ACTIVE_SESSIONS
from sync_slots import sync_slots, SLOTS

sync_functions = [
	{
		"name": STUDENTS,
		"f": sync_students,
	},
	{
		"name": PROJECTS,
		"f": sync_projects,
	},
	{
		"name": PUSHES,
		"f": sync_pushes,
	},
	{
		"name": CORRECTIONS,
		"f": sync_corrections,
	},
	{
		"name": ACTIVE_SESSIONS,
		"f": sync_active_sessions,
	},
	{
		"name": SLOTS,
		"f": sync_slots,
	},
]

slot_sync_functions = [
	{
		"name": SLOTS,
		"f": sync_slots,
	},
]
