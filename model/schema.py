from pydantic import BaseModel
from typing import List, Union, Optional
from datetime import datetime


class CreateCourierModel(BaseModel):
    name: str
    district: List[str]

class CourierResponseModel(BaseModel):
    id: int
    name: str

class CoruierDetailResponseModel(BaseModel):
    id: int
    name: str
    active_order: Optional[dict[str, Union[str, int]]]
    avg_order_complete_time: Optional[datetime]
    avg_order_day: int

class OrderResponseModel(BaseModel):
    courier_id: int
    status: int

class CreateOrderModel(BaseModel):
    name: str
    district: str
