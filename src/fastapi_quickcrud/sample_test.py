from fastapi import FastAPI
from fastapi_quickcrud import crud_router_builder
from sqlalchemy import *
from sqlalchemy.orm import *
from fastapi_quickcrud.crud_router import generic_sql_crud_router_builder

Base = declarative_base()


class Account(Base):
    __tablename__ = "account"
    id = Column(Integer, primary_key=True, autoincrement=True)
    post = relationship("BlogPost", back_populates="account_f")


class BlogPost(Base):
    __tablename__ = "blog_post"
    id = Column(Integer, primary_key=True, autoincrement=True)
    account_id = Column(Integer, ForeignKey("account.id"), nullable=False)
    account_f = relationship("Account", back_populates="post")
    blog = relationship("BlogComment", back_populates="post")


class BlogComment(Base):
    __tablename__ = "blog_comment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    blog_id = Column(Integer, ForeignKey("blog_post.id"), nullable=False)
    post = relationship("BlogPost", back_populates="blog")


crud_route_parent = crud_router_builder(
    db_model=Account,
    prefix="/account",
    tags=["account"],
    foreign_include=[BlogComment, BlogPost]

)
print("BlogPost222")

crud_route_child1 = generic_sql_crud_router_builder(
    db_model=BlogPost,
    prefix="/blog_post",
    tags=["blog_post"],
    foreign_include=[BlogComment, Account]

)
print("BlogComment111")

crud_route_child2 = generic_sql_crud_router_builder(
    db_model=BlogComment,
    prefix="/blog_comment",
    tags=["blog_comment"],
    foreign_include=[BlogPost]

)

app = FastAPI()
[app.include_router(i) for i in [crud_route_parent, crud_route_child1, crud_route_child2]]


@app.get("/", tags=["child"])
async def root():
    return {"message": "Hello World"}


import uvicorn

uvicorn.run(app, host="0.0.0.0", port=8002, debug=False)
