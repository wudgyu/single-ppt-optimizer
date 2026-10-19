"""Source document and fact contracts used by parsing and planning."""

from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator


class SourceFileType(StrEnum):
    PPTX = "pptx"
    DOCX = "docx"
    PDF = "pdf"


class ShapeType(StrEnum):
    TEXT_BOX = "text_box"
    AUTO_SHAPE = "auto_shape"
    TABLE = "table"
    CHART = "chart"
    GROUP = "group"
    PICTURE = "picture"
    UNKNOWN = "unknown"


class FactType(StrEnum):
    SOURCE_FACT = "source_fact"
    DERIVED_FACT = "derived_fact"
    INFERENCE = "inference"
    RECOMMENDATION = "recommendation"


class FactStatus(StrEnum):
    VERIFIED = "verified"
    CONFLICT = "conflict"
    LOW_CONFIDENCE = "low_confidence"
    REJECTED = "rejected"


class SourceAnchor(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    filename: str
    page: int | None = Field(default=None, ge=1)
    paragraph_index: int | None = Field(default=None, ge=0)
    shape_id: str | None = None
    table_id: str | None = None
    chart_id: str | None = None
    text_quote: str


class TextStyle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    font_size_pt: float | None = Field(default=None, gt=0)
    font_name: str | None = None
    bold: bool | None = None
    color: str | None = None
    alignment: str | None = None


class ParsedTableCell(BaseModel):
    model_config = ConfigDict(extra="forbid")

    row: int = Field(ge=0)
    column: int = Field(ge=0)
    text: str


class ParsedTable(BaseModel):
    model_config = ConfigDict(extra="forbid")

    table_id: str
    row_count: int = Field(gt=0)
    column_count: int = Field(gt=0)
    cells: list[ParsedTableCell]
    source_anchor: SourceAnchor


class ParsedChartSeries(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    values: list[float | None]


class ParsedChart(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chart_id: str
    categories: list[str]
    series: list[ParsedChartSeries]
    accessible: bool
    source_anchor: SourceAnchor


class ParsedShape(BaseModel):
    model_config = ConfigDict(extra="forbid")

    shape_id: str
    shape_type: ShapeType
    text: str
    x: float | None = Field(default=None, ge=0)
    y: float | None = Field(default=None, ge=0)
    w: float | None = Field(default=None, ge=0)
    h: float | None = Field(default=None, ge=0)
    rotation_degrees: float = 0
    text_style: TextStyle | None = None
    tables: list[ParsedTable] = Field(default_factory=list)
    charts: list[ParsedChart] = Field(default_factory=list)
    source_anchor: SourceAnchor
    limitations: list[str] = Field(default_factory=list)


class ParsedSlide(BaseModel):
    model_config = ConfigDict(extra="forbid")

    slide_number: int = Field(ge=1)
    canvas_width_inches: float = Field(gt=0)
    canvas_height_inches: float = Field(gt=0)
    background: str
    shapes: list[ParsedShape] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)


class ParsedBlock(BaseModel):
    model_config = ConfigDict(extra="forbid")

    block_id: str
    block_type: str
    text: str
    page: int | None = Field(default=None, ge=1)
    heading_level: int | None = Field(default=None, ge=1)
    paragraph_index: int | None = Field(default=None, ge=0)
    table: ParsedTable | None = None
    source_anchor: SourceAnchor
    limitations: list[str] = Field(default_factory=list)


class SourceDocument(BaseModel):
    model_config = ConfigDict(extra="forbid")

    document_id: str
    filename: str
    file_type: SourceFileType
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    page_count: int = Field(gt=0)
    extracted_text_path: str
    rendered_pages: list[dict[str, str | int]] = Field(default_factory=list)
    parsed_slides: list[ParsedSlide] = Field(default_factory=list)
    parsed_blocks: list[ParsedBlock] = Field(default_factory=list)
    image_only_pages: list[int] = Field(default_factory=list)

    @field_validator("rendered_pages")
    @classmethod
    def validate_rendered_pages(
        cls, value: list[dict[str, str | int]]
    ) -> list[dict[str, str | int]]:
        for item in value:
            if "page" not in item or not isinstance(item["page"], int) or item["page"] < 1:
                raise ValueError("rendered_pages entries require a positive integer page")
            if "image_artifact_id" not in item or not isinstance(item["image_artifact_id"], str):
                raise ValueError("rendered_pages entries require image_artifact_id")
        return value


class SourceFact(BaseModel):
    model_config = ConfigDict(extra="forbid")

    fact_id: str = Field(pattern=r"^F\d{3,}$")
    statement: str
    value_raw: str | None = None
    value_normalized: float | None = None
    unit: str | None = None
    entity: str | None = None
    time_scope: str | None = None
    qualifier: str | None = None
    source: SourceAnchor
    confidence: float = Field(ge=0, le=1)
    fact_type: FactType
    status: FactStatus
    conflict_group_id: str | None = None
    formula: str | None = None
    input_fact_ids: list[str] = Field(default_factory=list)

    @field_validator("input_fact_ids")
    @classmethod
    def validate_derived_inputs(cls, value: list[str], info: ValidationInfo) -> list[str]:
        data = info.data
        if data.get("fact_type") == FactType.DERIVED_FACT:
            if not data.get("formula"):
                raise ValueError("derived facts require a formula")
            if not value:
                raise ValueError("derived facts require input fact IDs")
        return value


class FactLedger(BaseModel):
    model_config = ConfigDict(extra="forbid")

    facts: list[SourceFact] = Field(default_factory=list)
    conflicts: list["ConflictGroup"] = Field(default_factory=list)


class ConflictGroup(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_id: str
    fact_ids: list[str] = Field(min_length=2)
