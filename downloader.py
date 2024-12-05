import os
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from utils import apply_random_delay

def download_file(base_url, file, output_directory):
    """Download a single file with a randomized delay."""
    file_name = os.path.basename(file)
    file_path = os.path.join(output_directory, file_name)

    # Check if the file already exists
    if os.path.exists(file_path):
        return f"{file_name} already exists in output folder. Skipping..."

    try:
        # Resolve relative URLs
        file_url = urllib.parse.urljoin(base_url, file)
        
        # Apply a randomized delay
        apply_random_delay()

        # Download the file
        urllib.request.urlretrieve(file_url, file_path)
        return f"Successfully downloaded {file_name}."
    except Exception as e:
        return f"Failed to download {file_name}: {e}"

def download_files_with_progress(base_url, files, output_directory, update_progress):
    """Download files while dynamically updating progress."""
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)

    results = []  # To store logs
    with ThreadPoolExecutor() as executor:
        future_to_file = {executor.submit(download_file, base_url, file, output_directory): file for file in files}
        for i, future in enumerate(future_to_file):
            result = future.result()
            results.append(result)
            update_progress(i + 1, "\n".join(results))

    return results
