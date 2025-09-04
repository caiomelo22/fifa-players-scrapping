def get_asset_info(element, prefix=""):
    element_src = element.get_attribute("src")
    element_name = element.get_attribute("data-original-title")

    return element_name, element_src