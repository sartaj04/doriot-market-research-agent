# models/auth_models.py
from pydantic import BaseModel
from typing import List, Optional

class Token(BaseModel):
    access_token: str
    token_type: str

class User(BaseModel):
    uuid: str
    org_name: str
    org_country_code: str
    org_region: str
    investment_round: str
    category_list: List[str]
    category_groups_list: List[str]
    description: str
    full_name: str
    email: str
    phone: str
    is_verified: bool
    is_payment_done: bool
    investors_simple_list: Optional[List[dict]]