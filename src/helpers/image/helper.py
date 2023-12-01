import requests
import os
import io
from selenium.webdriver.common.by import By


class ImageHelper:
    def __init__(self) -> None:
        self.dir_path = os.environ.get('IMAGE_DIR_PATH')
        if self.dir_path is None:
            raise Exception("Environment variable IMAGE_DIR_PATH is not set.")

    def save_image(self, img, directory, file_name):
        # Create the 'dist' folder within the specified path if it doesn't exist
        dist_folder = os.path.join(self.dir_path, directory)
        os.makedirs(dist_folder, exist_ok=True)

        # Prepare the image content from the URL
        image_content = requests.get(img).content
        image_file = io.BytesIO(image_content)

        # Save the image to the specified folder and filename
        file_path = os.path.join(dist_folder, file_name)
        with open(file_path, "wb") as f:
            f.write(image_file.getbuffer())
        
        return os.path.join(directory, file_name)

    def get_img_url(self, element):
        return element.get_attribute("src")

    def extract_save_img(
        self, element, element_name, obj_list, dir_name, dict_complement={}
    ):
        img = self.get_img_url(element)
        try:
            obj = next(filter(lambda x: x["name"] == element_name, obj_list))
        except StopIteration:
            file_path = self.save_image(
                img, dir_name, f"{element_name.replace(' ', '')}.png"
            )
            img = file_path

            obj_list.append(
                {
                    "id": len(obj_list) + 1,
                    "name": element_name,
                    "image_path": img,
                    **dict_complement,
                }
            )

            obj = obj_list[-1]

        return obj
