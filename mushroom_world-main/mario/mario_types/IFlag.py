"""
Interface-based flag architecture for Mario.

This module defines the abstract base class (ABC) for all flags in the system,
providing a consistent interface, type safety, and built-in validation.
"""

from abc import ABC, abstractmethod
from typing import Optional


class IFlag(ABC):
	"""
	Abstract base class for all flags.

	Each flag implementation fetches its own data via Yoshi API and
	performs its calculation logic independently.
	"""

	result: Optional[float] = None
	details: Optional[str] = None

	@property
	@abstractmethod
	def name(self) -> str:
		"""
		Return the unique identifier for this flag.

		Returns:
			Uppercase snake_case name (e.g., 'CLUSTERING', 'FAVORITISM')
		"""
		pass

	@property
	@abstractmethod
	def threshold(self) -> float:
		"""
		Return the threshold for this flag.

		Each flag class should implement this to return its specific threshold value.
		"""
		pass

	@property
	@abstractmethod
	def sufficient(self) -> bool:
		"""
		Return the sufficient variable for this flag. If set to true, when the flag is triggered, it will be sufficient to flag the correction as suspicious.

		Returns:
			False, True
		"""
		pass

	@property
	@abstractmethod
	def description(self) -> str:
		"""
		Return the description of this flag.

		Each flag class should implement this to return its specific description.
		"""
		pass

	@abstractmethod
	def calculate(self, correction_id: str) -> Optional[float]:
		"""
		Calculate the flag value for the given correction.

		Each flag fetches the data it needs from Yoshi API and performs
		its calculation logic.

		Args:
			correction_id: The MongoDB ID of the correction to analyze

		Returns:
			Float in [0, 1] representing the flag value, or None if
			insufficient data to calculate or if the flag is not applicable

		Note:
			- Return value MUST be in [0, 1] range if not None
			- Return None when there's insufficient data to make a determination
			- Flags should fetch only the data they need for their calculation
		"""
		pass

	def validate_result(self, value: float) -> None:
		"""
		Validate that a flag result is within the valid range [0, 1].

		Args:
			value: The flag result to validate

		Raises:
			ValueError: If value is not in [0, 1]
		"""
		if value < 0 or value > 1:
			raise ValueError(f"Flag {self.name} returned {value}, must be in [0, 1]")

	def is_triggered(self) -> bool:
		"""
		Determine if the flag is triggered based on its own result.

		Returns:
			True if result is not None and exceeds or is equal to threshold, False otherwise
		"""
		if self.result is None:
			return False
		return self.result >= self.threshold
