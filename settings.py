import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())

url = os.environ.get('URL')
default_output_directory = os.environ.get('DEFAULT_OUTPUT_DIRECTORY')
default_file_type = os.environ.get('DEFAULT_FILE_TYPE')