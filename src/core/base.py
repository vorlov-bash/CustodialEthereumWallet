from datetime import datetime

from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    """
    This class is used to control all schemas in application to be
    configured in the same way for serialization.

    Also, this class have util serializable_dict() method for all client requests schemas to
    prevent serialization errors when using dict/pydantic models in http client methods.
    Example for http client method:

    # This will raise an error because datetime object is not serializable.
    json_data = {"start_date": datetime.now(), "some": "data", "k": 1}
    response = requests.post(url, json=json_data)

    But with this class it will be:

    # No errors, because non-serializable fields will
    # be converted to serializable format.
    class SomeRequestSchema(BaseClientRequestSchema):
        start_date: datetime
        some: str
        k: int

    json_data = SomeRequestSchema(start_date=datetime.now(), some="data", k=1).serializable_dict()
    response = requests.post(url, json=json_data)
    """

    model_config = ConfigDict(
        json_encoders={
            # Define custom json encoders here
            datetime: lambda v: v.isoformat(),
        },
    )

    def serializable_dict(self):
        default_dict = self.model_dump()
        return jsonable_encoder(default_dict)
