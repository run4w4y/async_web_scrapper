from abc import ABC, abstractmethod


class GenericItem(ABC):
    @abstractmethod
    def to_csv_row(self) -> list:
        pass