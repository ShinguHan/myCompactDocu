from abc import ABC, abstractmethod
from sqlalchemy.orm import Session

class BaseImporter(ABC):
    @abstractmethod
    def parse(self, file_input) -> list:
        """Parse the file and return a list of raw data dictionaries."""
        pass

    @abstractmethod
    def validate(self, data: list) -> list:
        """Validate the parsed data."""
        pass

    @abstractmethod
    def save(self, data: list, db: Session, filename: str) -> int:
        """Save the data to the database."""
        pass
