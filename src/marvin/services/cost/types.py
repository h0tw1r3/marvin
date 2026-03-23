from typing import Protocol

from marvin.services.cost.schema import CostReportSchema, CalculateCostSchema


class CostServiceProtocol(Protocol):
    def calculate(self, result: CalculateCostSchema) -> CostReportSchema | None:
        ...

    def aggregate(self) -> CostReportSchema | None:
        ...
