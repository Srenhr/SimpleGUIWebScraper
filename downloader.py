import os
import urllib.parse
import urllib.request
import logging
from concurrent.futures import ThreadPoolExecutor
from utils import apply_random_delay

def download_file(base_url, file, output_directory):
    file_name = os.path.basename(file)
    file_name = urllib.parse.unquote(file_name)
    file_path = os.path.join(output_directory, file_name)

    if os.path.exists(file_path):
        logging.info(f"{file_name} already exists in output folder. Skipping...")
        return f"{file_name} already exists in output folder. Skipping..."

    try:
        file_url = urllib.parse.urljoin(base_url, file)
        apply_random_delay()
        urllib.request.urlretrieve(file_url, file_path)
        logging.info(f"Successfully downloaded {file_name}.")
        return f"Successfully downloaded {file_name}."
    except Exception as e:
        logging.error(f"Failed to download {file_name}: {e}")
        return f"Failed to download {file_name}: {e}"

def download_files_with_progress(base_url, files, output_directory, update_progress):
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    results = []
    with ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(download_file, base_url, file, output_directory): file for file in files}
        for i, future in enumerate(future_to_file):
            result = future.result()
            results.append(result)
            update_progress(i + 1, "\n".join(results))

    logging.info(f"Completed downloading {len(files)} files.")
    return results
