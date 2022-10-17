import inspect
import sys
from pathlib import Path
from textwrap import dedent
from typing import ClassVar

import importmagic
import jinja2
from importmagic import SymbolIndex, Scope
from sqlalchemy import Table

from fastapi_quickcrud_codegen.generator.crud_template_generator import CrudTemplateGenerator


class CrudCodeGen():
    def __init__(self, file_name, model_name, tags, prefix):
        self.file_name = file_name
        self.code = "\n\n\n" + "api = APIRouter(tags=" + str(tags) + ',' + "prefix=" + '"' + prefix + '")' + "\n\n"
        # self.index = SymbolIndex()
        # lib_path: list[str] = [i for i in sys.path if "FastAPIQuickCRUD" not in i]
        # self.index.build_index(lib_path)
        self.model_name = model_name
        self.import_list = f"""

import copy
from http import HTTPStatus
from typing import List
from os import path

from sqlalchemy import and_, select
from fastapi import Depends, Response, APIRouter
from sqlalchemy.sql.elements import BinaryExpression

from fastapi_quick_crud_template.common.utils import find_query_builder
from fastapi_quick_crud_template.common.sql_session import db_session
from fastapi_quick_crud_template.model.{file_name} import ({model_name}FindOneResponseModel, 
                                                           {model_name}PrimaryKeyModel, 
                                                           {model_name}FindOneRequestBody, 
                                                           {model_name})
        """

    def gen(self, template_generator: CrudTemplateGenerator):
        # src = dedent(self.model_code + "\n\n" +self.code)
        # scope = Scope.from_source(src)
        #
        # unresolved, unreferenced = scope.find_unresolved_and_unreferenced_symbols()
        # a = importmagic.get_update(src, self.index, unresolved, unreferenced)
        # python_source = importmagic.update_imports(src, self.index, unresolved, unreferenced)
        # template_generator.add_route(self.file_name, python_source)
        template_generator.add_route(self.file_name, self.import_list + "\n\n" + self.code)

    def build_find_one_route(self, *, async_mode, path):
        mode = "async" if async_mode else "sync"
        TEMPLATE_FILE_PATH: ClassVar[str] = f'route/{mode}_find_one.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = f'{mode}_find_one.jinja2'
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render(
            {"model_name": self.model_name, "path": path})
        self.code += "\n\n\n" + code

