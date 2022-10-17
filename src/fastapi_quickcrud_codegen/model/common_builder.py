import inspect
import sys
from pathlib import Path
from textwrap import dedent
from typing import ClassVar

import importmagic
import jinja2
from importmagic import SymbolIndex, Scope
from sqlalchemy import Table


class CommonCodeGen():
    def __init__(self):
        self.code = ""
        self.model_code = ""
        self.index = SymbolIndex()
        lib_path: list[str] = [i for i in sys.path if "fastapi_quickcrud_codegen" not in i]
        self.index.build_index(lib_path)
        self.import_list = ""

    # todo add tpye for template_generator
    def gen(self, template_generator_method):
        template_generator_method( self.import_list + "\n\n" + self.code)

    def gen_model(self, model):
        if isinstance(model, Table):
            raise TypeError("not support table yet")
        model_code = inspect.getsource(model)
        self.model_code += "\n\n\n" + model_code

    def build_app(self, *, async_mode, model_name):
        mode = "async" if async_mode else "sync"
        TEMPLATE_FILE_PATH: ClassVar[str] = f'route/{mode}_find_one.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = f'{mode}_find_one.jinja2'
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render(
            {"model_name": model_name})
        self.code += "\n\n\n" + code

    def build_api_route(self):
        TEMPLATE_FILE_PATH: ClassVar[str] = f'common/api_route.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = f'api_route.jinja2'
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render()
        self.code += "\n\n\n" + code

    def build_type(self):
        TEMPLATE_FILE_PATH: ClassVar[str] = f'common/typing.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = f'typing.jinja2'
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render()
        self.code += "\n\n\n" + code

    def build_utils(self):
        TEMPLATE_FILE_PATH: ClassVar[str] = f'common/utils.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = f'utils.jinja2'
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render()
        self.import_list = """
from fastapi_quick_crud_template.common.http_exception import QueryOperatorNotFound
from fastapi_quick_crud_template.common.typing import ExtraFieldType, ExtraFieldTypePrefix, process_type_map, \
    process_map
    
"""
        self.code += "\n\n\n" + code

    def build_http_exception(self):
        TEMPLATE_FILE_PATH: ClassVar[str] = f'common/http_exception.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = f'http_exception.jinja2'
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render()
        self.code += "\n\n\n" + code

    def build_db(self):
        TEMPLATE_FILE_PATH: ClassVar[str] = f'common/db.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = f'db.jinja2'
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render()
        self.code += "\n\n\n" + code

    def build_db_session(self, model_list):
        TEMPLATE_FILE_PATH: ClassVar[str] = f'common/memory_sql_session.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = f'memory_sql_session.jinja2'
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render({"model_list": model_list})
        self.code += "\n\n\n" + code

    def build_app(self, model_list):
        TEMPLATE_FILE_PATH: ClassVar[str] = f'common/app.jinja2'
        template_file_path = Path(TEMPLATE_FILE_PATH)

        TEMPLATE_DIR: Path = Path(__file__).parents[0] / 'template'
        templateLoader = jinja2.FileSystemLoader(str(TEMPLATE_DIR / template_file_path.parent))
        templateEnv = jinja2.Environment(loader=templateLoader)
        TEMPLATE_FILE = f'app.jinja2'
        template = templateEnv.get_template(TEMPLATE_FILE)
        code = template.render({"model_list": model_list})
        self.code += "\n\n\n" + code
