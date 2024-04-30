import os, os.path as osp
import zipfile
import glob

zip_path = 'lgie.zip'

files_to_zip = glob.glob(osp.join("results", "*", "concatenated_image.jpg"))
files_to_zip.sort()

with zipfile.ZipFile(zip_path, 'w') as zipf:
    for file in files_to_zip[75:100]:
        zipf.write(file, arcname=file)
        
print("ZIP file created successfully!")