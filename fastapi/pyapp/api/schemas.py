from pydantic import BaseModel

class Tier1Batch(BaseModel):
    batch_id: int
    validators: list[str]
    model_indexes: list[int]
    finalized: bool
    final_cid: str

class Tier2Batch(BaseModel):
    batch_id: int
    validators: list[str]
    finalized: bool
    final_cid: str