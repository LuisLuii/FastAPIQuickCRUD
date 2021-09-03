from typing import Optional

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
import pydantic

app = FastAPI()
class AppModel(BaseModel):
  def dict(self, *args, **kwargs):
    if kwargs and kwargs.get("exclude_none") is not None:
      kwargs["exclude_unset"] = True
      return BaseModel.dict(self, *args, **kwargs)
class Item(AppModel):
    name: str
    description: str
    price: Optional[float]
    tax: Optional[float]


class AllOptional(pydantic.main.ModelMetaclass):
    def __new__(self, name, bases, namespaces, **kwargs):
        annotations = namespaces.get('__annotations__', {})
        print(bases)
        print(bases[0].__annotations__)
        for base in bases:
            annotations = {**annotations, **base.__annotations__}
        for field in annotations:
            if not field.startswith('__'):
                annotations[field] = Optional[annotations[field]]
        namespaces['__annotations__'] = annotations
        return super().__new__(self, name, bases, namespaces, **kwargs)


class UpdatedItem(Item, metaclass=AllOptional):
    pass

# This continues to work correctly
@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    return {
        'name': 'Uzbek Palov',
        'description': 'Palov is my traditional meal',
        'price': 15.0,
    }

@app.patch("/items/{item_id}") # not using response_model=Item
async def update_item(item_id: str, item: UpdatedItem):
    return item

uvicorn.run(app, host="0.0.0.0", port=8000, debug=False)
