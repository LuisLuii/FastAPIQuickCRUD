import inspect
import sys
from pathlib import Path
from textwrap import dedent
from typing import ClassVar

import importmagic
import jinja2
from importmagic import SymbolIndex, Scope
from sqlalchemy import Table

from fastapi_quickcrud_codegen.generator.model_template_generator import model_template_gen


class ModelCodeGen():
    def __init__(self, file_name, db_type):
        self.file_name = file_name
        self.table_list = {}
        self.code = ""
        self.model_code = ""
        self.index = SymbolIndex()
        lib_path: list[str] = [i for i in sys.path if "FastAPIQuickCRUD" not in i]
        self.index.build_index(lib_path)
        self.import_list = f"""
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, date, time
from decimal import Decimal
from typing import Optional, List, Union, NewType

from fastapi import Query, Body
from sqlalchemy import *
from sqlalchemy.dialects.{db_type} import *

from fastapi_quick_crud_template.common.utils import value_of_list_to_str, ExcludeUnsetBaseModel, filter_none
from fastapi_quick_crud_template.common.db import Base
from fastapi_quick_crud_template.common.typing import ItemComparisonOperators, PGSQLMatchingPatternInString, \
    ExtraFieldTypePrefix, RangeToComparisonOperators, MatchingPatternInStringBase, RangeFromComparisonOperators
"""

    def gen(self):
        # src = dedent(self.model_code + "\n\n" +self.code)
        # scope = Scope.from_source(src)
        #
        # unresolved, unreferenced = scope.find_unresolved_and_unreferenced_symbols()
        # python_source = importmagic.update_imports(src, self.index, unresolved, unreferenced)
        # model_template_gen.add_model(self.file_name, python_source)
        return model_template_gen.add_model(self.file_name, self.import_list + "\n\n" + self.model_code + "\n\n" + self.code)

    def gen_model(self, model):
        if isinstance(model, Table):
            raise TypeError("not support table yet")
        model_code = inspect.getsource(model)
        self.model_code += "\n\n\n" + model_code

    def build_base_model(self, *, class_name, fields, description=None, orm_mode=True,
                         value_of_list_to_str_columns=None, filter_none=None):
        TEMPLATE_FILE_PATH: ClassVar[str] = 'pydantic/BaseModel.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "BaseModel.jinja2"
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render(
            {"class_name": class_name, "fields": fields, "description": description, "orm_mode": orm_mode,
             "value_of_list_to_str_columns": value_of_list_to_str_columns, "filter_none": filter_none})
        self.table_list[class_name] = code
        self.code += "\n\n\n" + code

    def build_base_model_root(self, *, class_name, field, description=None, base_model="BaseModel",
                         value_of_list_to_str_columns=None, filter_none=None):

        if class_name in self.table_list:
            return self.table_list[class_name]
        TEMPLATE_FILE_PATH: ClassVar[str] = 'pydantic/BaseModel.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "BaseModel_root.jinja2"
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render(
            {"class_name": class_name, "field": field, "description": description, "base_model": base_model,"value_of_list_to_str_columns": value_of_list_to_str_columns, "filter_none": filter_none})
        self.table_list[class_name] = code
        self.code += "\n\n\n" + code

    def build_dataclass(self, *, class_name, fields, description=None, value_of_list_to_str_columns=None,
                        filter_none=None):
        if class_name in self.table_list:
            return self.table_list[class_name]
        TEMPLATE_FILE_PATH: ClassVar[str] = 'pydantic/BaseModel.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "dataclass.jinja2"
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render({"class_name": class_name, "fields": fields, "description": description,
                                "value_of_list_to_str_columns": value_of_list_to_str_columns,
                                "filter_none": filter_none})
        self.code += "\n\n\n" + code

    def build_enum(self, *, class_name, fields, description=None):
        if class_name in self.table_list:
            return self.table_list[class_name]
        TEMPLATE_FILE_PATH: ClassVar[str] = ''
        template_file_path = Path(TEMPLATE_FILE_PATH)
        BASE_CLASS: ClassVar[str] = 'pydantic.BaseModel'

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "Enum.jinja2"
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render({"class_name": class_name, "fields": fields, "description": description})
        self.table_list[class_name] = code
        self.code += "\n\n\n" + code

    def build_constant(self, *, constants):
        TEMPLATE_FILE_PATH: ClassVar[str] = ''
        template_file_path = Path(TEMPLATE_FILE_PATH)
        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = "Constant.jinja2"
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render({"constants": constants})
        self.code += "\n\n\n" + code

