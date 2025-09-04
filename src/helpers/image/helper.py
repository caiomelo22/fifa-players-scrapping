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
        self, element_src, element_name, position_element, dir_name, dict_complement={}
    ):
        try:
            obj = next(filter(lambda x: x["name"] == element_name, position_element[0]))
        except StopIteration:
            file_path = self.save_image(
                element_src, dir_name, f"{element_name.replace(' ', '')}.png"
            )

            position_element[0].append(
                {
                    "name": element_name,
                    "image_path": file_path,
                    **dict_complement,
                }
            )

            obj = position_element[0][-1]

        return obj
