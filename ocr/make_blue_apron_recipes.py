from blue_apron_manager import BlueApronManager
import os
import glob
import yaml
import argparse

def make_blue_apron_recipes(config_path):
    with open(config_path, "rb") as file:
        config = yaml.load(file)

    source_root = config["paths"]["source"]
    source_paths = config["blue_apron_config"]["source_paths"]
    source_paths = [os.path.join(source_root, sp) for sp in source_paths]
    pdf_directory = config["paths"]["pdf"]
    yml_directory = config["paths"]["yml"]
    overwrite_mode = config["blue_apron_config"]["overwrite_mode"]
    debug = config["blue_apron_config"]["debug"]
    print_recipe = config["blue_apron_config"]["print_recipe"]

    cover_images = []
    for source_path in source_paths:
        source_path = os.path.join(source_path, "*-0001.pdf")
        images = sorted(glob.glob(source_path))
        cover_images.extend(images)
    print(cover_images)

    for cover_image in cover_images:
        blue_apron_manager = BlueApronManager(
            cover_image=cover_image,
            #instruct_image=instruct_image,
            pdf_directory=pdf_directory,
            yml_directory=yml_directory,
            overwrite_mode=overwrite_mode,
            debug=int(debug),
            print_recipe=print_recipe)


if __name__ == "__main__":
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--config", required=True,
        help="path to input config file")

    args = vars(ap.parse_args())

    make_blue_apron_recipes(args["config"])

