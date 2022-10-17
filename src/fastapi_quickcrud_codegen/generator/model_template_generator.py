import os
import sys

from fastapi_quickcrud_codegen.misc.constant import GENERATION_FOLDER, MODEL


class ModelTemplateGenerator:
    def __init__(self):
        dirname, filename = os.path.split(os.path.abspath(sys.argv[0]))
        self.current_directory = dirname
        self.template_root_directory = os.path.join(self.current_directory, GENERATION_FOLDER)
        self.module_path_map = {}

    def __create_root_template_folder(self):
        if not os.path.exists(self.template_root_directory):
            os.makedirs(self.template_root_directory)

    def __create_model_folder(self, path):
        if not os.path.exists(path):
            os.makedirs(path)

    def __create_module_folder(self):
        if not os.path.exists(self.template_model_directory):
            os.makedirs(self.template_model_directory)

    def add_model(self, model_name, code):
        template_model_directory = os.path.join(self.template_root_directory, MODEL)
        self.__create_model_folder(template_model_directory)

        path = f'{template_model_directory}/__init__.py'
        self.add_code_to_file(path, "")

        path = f'{template_model_directory}/{model_name}.py'
        self.add_code_to_file(path, code)
        self.module_path_map[model_name] = {'model': path}

    @staticmethod
    def add_code_to_file(path, code):
        with open(path, 'a') as model_file:
            model_file.write(code)

    @staticmethod
    def add_to_controller_file(path, code):
        with open(path, 'a') as model_file:
            model_file.write(code)


model_template_gen = ModelTemplateGenerator()


