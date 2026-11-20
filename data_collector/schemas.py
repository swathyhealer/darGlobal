
from typing import Any, Optional
from pydantic import BaseModel, Field


class ExtractedRecord(BaseModel):
    title: str = Field(
        description="Invented title which is suitable for representing the information block"
    )

    summarized_data: str = Field(
        description="Extracted relevant information from the HTML relevant to the information block"
    )

   


    source_url: Optional[str] = None

    additional_information: dict[str, Any] = Field(
        default_factory=dict
    )


class ExtractionResult(BaseModel):
    infomation_blocks: list[ExtractedRecord] = Field(
        default_factory=list
    )
