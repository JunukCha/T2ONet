import os, os.path as osp
from PIL import Image
import numpy as np
import json
import tqdm
from io import BytesIO
import tempfile

import botocore
import boto3


class S3Data():
    def __init__(
        self, 
        json_path, 
        base_path, 
        bucket, 
        region_name="us-west-2", 
    ):
        
        self.json_path = json_path
        self.base_path = base_path
        self.bucket = bucket
        
        self.objClient = boto3.session.Session().client(
            service_name="s3",
            config=botocore.config.Config(
                region_name=region_name,
                connect_timeout=10,
                read_timeout=10,
                retries={"mode": "standard", "max_attempts": 10},
                signature_version=botocore.UNSIGNED,
            ),
        )
        
        self.data_list = []
        if osp.exists(json_path):
            with open(json_path, 'r') as f:
                self.data_list = json.load(f)
    
    def get_video(self, index, key):
        data = self.data_list[index]
        video_path = osp.join(self.base_path, data[key])
        temp_video_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        self.objClient.download_file(self.bucket, video_path, temp_video_file.name)
        return temp_video_file.name
    
    def get_image(self, index, key, return_path=False):
        data = self.data_list[index]
        print(data[key])
        real_image_path = osp.join(self.base_path, data[key])
        image_path = self.objClient.get_object(Bucket=self.bucket, Key=real_image_path)["Body"]
        if return_path:
            return image_path, real_image_path
        else:
            image = Image.open(image_path)
            return image
    
    def get_exr_file(self, index, key):
        data = self.data_list[index]
        exr_path = osp.join(self.base_path, data[key])
        temp_exr_file = tempfile.NamedTemporaryFile(delete=False, suffix='.exr')
        self.objClient.download_file(self.bucket, exr_path, temp_exr_file.name)
        return temp_exr_file.name
    
    def get_text(self, index, value="text", return_path=False, text_index=0, random=False, all_return=False):
        data = self.data_list[index]
        real_text_path = osp.join(self.base_path, data[value])
        text_path = self.objClient.get_object(Bucket=self.bucket, Key=real_text_path)["Body"]
        if return_path:
            return text_path, real_text_path
        else:
            texts = text_path.read().decode('utf-8').split("\n")
            if random:
                text = np.random.choice(texts)
                # while "Sure!" in text:
                #     texts = list(set(texts) - set([text]))
                #     text = np.random.choice(texts)
            elif all_return:
                text = texts
            else:
                text = texts[text_index]
            return text

    def get_opt_light(self, index, kind="opt_light"):
        """
            json
        """
        data = self.data_list[index]
        real_json_path = osp.join(self.base_path, data[kind])
        json_path = self.objClient.get_object(Bucket=self.bucket, Key=real_json_path)["Body"]
        opt_light = json_path.read().decode('utf-8')
        opt_light = json.loads(opt_light)
        return opt_light # point_end, shading_intensity_end, bg_suppress_end

    def get_path(self, index, key, with_base_path=False):
        data = self.data_list[index]
        try:
            if with_base_path:
                path = osp.join(self.base_path, data[key])
            else:
                path = data[key]
        except KeyError:
            path = None
        return path
        
    def upload_image(self, path, image):
        buffer = BytesIO()
        image.save(buffer, self.__get_safe_ext(path))
        buffer.seek(0)
        save_path = osp.join(self.base_path, path)
        content_type = self.__get_content_safe_ext(path)
        self.objClient.put_object(Bucket=self.bucket, Key=save_path, Body=buffer, ContentType=content_type)
    
    def upload_text(self, path, text):
        buffer = BytesIO()
        buffer.write(text.encode('utf-8'))
        buffer.seek(0)
        save_path = osp.join(self.base_path, path)
        self.objClient.put_object(Bucket=self.bucket, Key=save_path, Body=buffer, ContentType="text/plain")

    def upload_file(self, path, tmp_path):
        """
            json, mp4, exr
        """
        save_path = osp.join(self.base_path, path)
        content_type = self.__get_content_safe_ext(path)
        self.objClient.upload_file(
            tmp_path, 
            self.bucket, 
            save_path, 
            ExtraArgs={
                'ContentType': content_type, 
            }
        )
        
    def upload_file2(self, path, tmp_path):
        """
            big exr
        """
        save_path = osp.join(self.base_path, path)
        content_type = self.__get_content_safe_ext(path)
        with open(tmp_path, 'rb') as data:
            self.objClient.put_object(Bucket=self.bucket, Key=save_path, Body=data, ContentType=content_type)

    def __get_safe_ext(self, key):
        ext = os.path.splitext(key)[-1].strip('.').upper()
        if ext in ['JPG', 'JPEG']:
            return 'JPEG' 
        elif ext in ['PNG']:
            return 'PNG' 
        else:
            raise S3ImagesInvalidExtension('Extension is invalid') 
            
    def __get_content_safe_ext(self, key):
        ext = os.path.splitext(key)[-1].strip('.').upper()
        if ext in ['JPG', 'JPEG']:
            return 'image/jpeg'
        elif ext in ['PNG']:
            return 'image/png'
        elif ext in ['JSON']:
            return 'application/json'
        elif ext in ['MP4']:
            return 'video/mp4'
        else:
            return 'binary/octet-stream'
            
    def update_json(self, index, key, value):
        data = self.data_list[index]
        data[key] = value
    
    def append_json(self, key, value):
        self.data_list.append({
            key: value
        })
    
    def split(self, idx0, idx1):
        self.data_list = self.data_list[idx0:idx1]
    
    def save_json(self, path=None):
        if path is None:
            path = self.json_path
        os.makedirs(osp.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            json.dump(self.data_list, f)
    
    def __len__(self):
        return len(self.data_list)

if __name__ == "__main__":
    my_s3_data = S3Data("data/s3_json/general_set001_s3_data.json", "junuk", "jaeyoon-west2")
#     index = 5
#     gen_bg_image = my_s3_data.get_image(index, "bg_style")
#     text = my_s3_data.get_text(index)
#     print(gen_bg_image.shape, text)
    print(len(my_s3_data))
