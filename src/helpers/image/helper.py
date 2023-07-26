import requests
import os
import io
from selenium.webdriver.common.by import By


class ImageHelper:
    def __init__(self) -> None:
        pass

    def save_image(self, img, directory, file_name):
        image_content = requests.get(img).content
        image_file = io.BytesIO(image_content)
        directory = f"dist/{directory}"
        if not os.path.exists(directory):
            os.makedirs(directory)
        file_path = f"{directory}/{file_name}"

        open(file_path, "wb").write(image_file.getbuffer())
        return file_path

    def get_img_url(self, element):
        return element.find_element(By.TAG_NAME, "img").get_attribute("src")

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
