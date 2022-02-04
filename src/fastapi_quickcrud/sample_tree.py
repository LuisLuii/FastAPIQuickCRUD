from fastapi import FastAPI
from fastapi_quickcrud import crud_router_builder
from sqlalchemy import *
from sqlalchemy.orm import *
from fastapi_quickcrud.crud_router import generic_sql_crud_router_builder

Base = declarative_base()

class Account(Base):
    __tablename__ = "account"
    id = Column(Integer, primary_key=True, autoincrement=True)

class BlogPost(Base):
    __tablename__ = "blog_post"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)

class BlogComment(Base):
    __tablename__ = "blog_comment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    blog_id = Column(Integer, ForeignKey("blog_post.id"), nullable=False)

crud_route_parent = crud_router_builder(
    db_model=Account,
    prefix="/account",
    tags=["account"],
    foreign_include=[BlogPost,BlogComment]

)

crud_route_child1 = generic_sql_crud_router_builder(
    db_model=BlogPost,
    prefix="/blog_post",
    tags=["blog_post"]
)

crud_route_child2 = generic_sql_crud_router_builder(
    db_model=BlogComment,
    prefix="/blog_comment",
    tags=["blog_comment"]
)

app = FastAPI()
[app.include_router(i) for i in [crud_route_parent, crud_route_child1, crud_route_child2]]

@app.get("/", tags=["child"])
async def root():
    return {"message": "Hello World"}

import uvicorn
uvicorn.run(app, host="0.0.0.0", port=8002, debug=False)
