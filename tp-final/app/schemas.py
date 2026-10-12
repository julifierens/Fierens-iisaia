"""Modelos Pydantic: reflejan los schemas de openapi.yaml v1.1."""
from typing import Literal

from pydantic import BaseModel, Field


class ProcessingParameters(BaseModel):
    apply_compliance_correction: bool
    compliance_mm_per_n: float | None
    beta: float


class Result(BaseModel):
    pm_n: float
    dm_mm: float
    rm_mpa: float
    py_t10_n: float | None
    py_t10_displacement_mm: float | None
    sigma_y_t10_mpa: float | None
    parameters: ProcessingParameters
    processed_at: str


class Test(BaseModel):
    id: int
    filename: str
    material: str
    thickness_mm: float
    uploaded_at: str
    point_count: int
    result: Result | None


class TestUpdate(BaseModel):
    thickness_mm: float = Field(gt=0, allow_inf_nan=False)


class ProcessingRequest(BaseModel):
    apply_compliance_correction: bool = False
    compliance_mm_per_n: float = Field(default=2.281e-4, gt=0, allow_inf_nan=False)
    beta: float = Field(default=0.277, gt=0, allow_inf_nan=False)


class Curve(BaseModel):
    test_id: int
    source: Literal["raw", "processed"]
    displacement_mm: list[float]
    load_n: list[float]


class Error(BaseModel):
    code: Literal["TEST_NOT_FOUND", "RESULT_NOT_FOUND", "INVALID_FILE", "INVALID_PARAMETERS", "PROCESSING_FAILED"]
    message: str
