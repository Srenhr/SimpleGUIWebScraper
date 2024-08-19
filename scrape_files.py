import requests
from bs4 import BeautifulSoup
from settings import url, default_output_directory, default_file_type
import urllib.request
import os

response = requests.get(url)

soup = BeautifulSoup(response.content, 'html.parser')

links = soup.find_all('a', href=True)
files = [link['href'] for link in links if link['href'].endswith(default_file_type)]

output_directory = default_output_directory

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

for file in files:
    file_url = urllib.parse.urljoin(url, file)
    file_name = os.path.join(output_directory, file.split('/')[-1])

    if os.path.exists(file_name):
        print(f"File {file_name} already exists. Skipping download.")
        continue
    
    try:
        print(f"Downloading {file}...")
        urllib.request.urlretrieve(file_url, file_name)
    except:
        print("An exception occurred") 
    else:
        print(f"Saved to {file_name}")

print("All PDFs downloaded successfully!")
