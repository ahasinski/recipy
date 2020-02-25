import os
import yaml
import argparse
import numpy as np
from collections import OrderedDict
from bash.bash_utils import load_run_script
from blue_apron_ocr import BlueApronCoverOCR, BlueApronInstructOCR

class BlueApronManager(object):
    def __init__(self,
                 cover_image=None,
                 instruct_image=None,
                 print_recipe=0,
                 debug=0,
                 pngs_path=None,
                 pdf_directory=None,
                 yml_directory=None,
                 overwrite_mode="auto"):
        self._prep_manager(debug=debug,
                           print_recipe=print_recipe,
                           overwrite_mode=overwrite_mode)
        self.format_inputs(cover_image=cover_image,
                           instruct_image=instruct_image,
                           pngs_path=pngs_path)
        self.cover_ocr.ocr(self.cover_image)
        self.instruct_ocr.ocr(self.instruct_image)
        self.format_outputs(pdf_dir=pdf_directory,
                            yml_dir=yml_directory)
        self.collect_recipe()
        self.write_outputs()


    def _prep_manager(self, debug, print_recipe, overwrite_mode):
        # get paths to bash scripts
        class_path = os.path.dirname(os.path.abspath(__file__))
        self.pdf2png = os.path.join(class_path, "bash/pdf2png.sh")
        self.join_pdfs = os.path.join(class_path, "bash/join_pdfs.sh")
        # turn params into attributes
        self.debug = debug
        self.print_recipe = print_recipe
        self.overwrite_mode = overwrite_mode
        self.cover_ocr = BlueApronCoverOCR(debug=debug)
        self.instruct_ocr = BlueApronInstructOCR(debug=debug)

    def infer_other_image(self, image, increment=1):
        image_num_str = image.split("-")[-1].split(".")[0]
        digits = len(image_num_str)
        image_num = int(image_num_str)
        image_num2 = image_num + increment
        image_num_str2 = "%0{}d".format(digits) % (image_num2)
        image2 = image.replace("-{}.".format(image_num_str),
                               "-{}.".format(image_num_str2))
        return image2

    def convert_image(self, image, pngs_path=None):
        if image[-3:] == "pdf":
            if pngs_path is None:
                pngs_path = os.path.dirname(image).replace("pdf", "png").replace("/partials","")
            self.verify_dir(pngs_path)
            png = os.path.join(pngs_path, os.path.basename(image).replace(".pdf", ".png"))
            load_run_script(self.pdf2png, image, png)
            return png, image
        else:
            return image, None


    def format_inputs(self, cover_image, instruct_image, pngs_path):
        # if only cover or instruct image is provided,
        # use increment/decrement to infer the other
        if cover_image is None:
            cover_image = self.infer_other_image(instruct_image, increment=-1)
        elif instruct_image is None:
            instruct_image = self.infer_other_image(cover_image, increment=1)
        # convert to pngs
        self.cover_image, self.cover_pdf = self.convert_image(cover_image, pngs_path=pngs_path)
        self.instruct_image, self.instruct_pdf = self.convert_image(instruct_image, pngs_path=pngs_path)
        # get directory and extension
        self.input_dir = os.path.dirname(self.cover_image)
        self.extension = self.cover_image.split(".")[1]

    def verify_dir(self, dir):
        """
        Goes through a directory to see if each folder
        exists. Make if necessary.
        :param dir: string directory
        :return:
          Nothing, but will create directories.
        """
        dir_list = dir.split("/")
        dir2 = "/"
        for d in dir_list[1:]:
            dir2 = os.path.join(dir2, d)
            if not os.path.isdir(dir2):
                os.mkdir(dir2)

    # def change_dir_ext(self, dir, old_ext, new_ext):
    #     new_dir = dir.replace(old_ext, new_ext)
    #     self.verify_dir(new_dir)
    #     return new_dir


    def collect_recipe(self):
        recipe = self.cover_ocr.recipe
        recipe.update(self.instruct_ocr.recipe)
        recipe["source"] = "Blue Apron"
        recipe["pdf"] = self.pdf_path
        recipe["url"] = ""
        recipe["yml"] = self.yml_path
        self.recipe = recipe


    def format_outputs(self, pdf_dir=None, yml_dir=None):
        output_name = self.cover_ocr.recipe["name"]
        output_name = "_".join(output_name.split())
        self.output_name = output_name
        if pdf_dir is None:
            pdf_dir = self.input_dir.replace(self.extension, "pdf")
            self.verify_dir(pdf_dir)
        if (self.cover_pdf is not None) and (self.instruct_pdf is not None):
            self.pdf_path = os.path.join(pdf_dir, "{}.pdf".format(output_name))
        else:
            self.pdf_dir = None
        if yml_dir is None:
            yml_dir = self.input_dir.replace(self.extension, "yml")
            self.verify_dir(yml_dir)
        self.yml_path = os.path.join(yml_dir, "{}.yml".format(output_name))
        return self.output_name, self.pdf_path, self.yml_path

    def write_outputs(self):
        if self.print_recipe:
            self.recipe_printer(self.recipe)
        write_recipe(recipe=self.recipe,
                     write_path=self.yml_path,
                     overwrite_mode=self.overwrite_mode)
        if self.pdf_path is not None:
            load_run_script(self.join_pdfs,
                            self.cover_pdf,
                            self.instruct_pdf,
                            self.pdf_path)


def kv_printer(key, values):
    # print simple strings on single line
    # names, timing, servings
    if np.isscalar(values):
        print("{}: {}".format(key, values))
    else:
        print("{}:".format(key))
        for value in values:
            # print lists of strings
            # tags
            if np.isscalar(value):
                print("- {}".format(value))
            # print lists of dicts
            # measured_ingredients
            elif type(value) is dict:
                print("- {}: {}".format(value.keys()[0], value.values()[0]))
            # print lists of list of length 3+
            # instructions
            else:
                print(value[0])
                for n, val in enumerate(value[1:]):
                    print("  {}".format(val))

def recipe_printer(recipe):
    components = [
        "name",
        "source",
        "time",
        "servings",
        "tags",
        "ingredients",
        "instructions",
        "pdf",
        "url",
        "yml",
    ]
    for component in components:
        try:
            kv_printer(component, recipe[component])
        except:
            print("No {} found.".format(component))


def recipe_difference(recipe1, recipe2):
    # get set of all keys
    keys = set(recipe1.keys() + recipe2.keys())
    for key in keys:
        # if key does not exist in a recipe, note this & move on
        try:
            value1 = recipe1[key]
        except KeyError:
            print("{} not in first recipe.".format(key))
            continue
        try:
            value2 = recipe2[key]
        except KeyError:
            print("{} not in second recipe.".format(key))
            continue
        # if keys exist in both recipes and values are identical, ignore
        if value1 == value2:
            continue
        # otherwise note that they differ and print them
        else:
            print("{} differs between recipes: ".format(key))
            print(value1)
            print("-----")
            print(value2)
            print("\n\n")
    return None


def ordered_dict_representer(self, value):
    return self.represent_mapping('tag:yaml.org,2002:map', value.items())
yaml.add_representer(OrderedDict, ordered_dict_representer)


def _write_recipe(recipe, write_path):
    components = [
        "name",
        "source",
        "time",
        "servings",
        "tags",
        "ingredients",
        "instructions",
        "pdf",
        "url",
    ]
    with open(write_path, "w") as output:
        ordered_recipe = OrderedDict([
            (k,recipe[k]) for k in components if k in recipe.keys()])
        yaml.dump(ordered_recipe, output, default_flow_style=False)

def write_recipe(recipe, write_path, overwrite_mode="manual"):
    # check if recipe already exists at path
    if os.path.exists(write_path):
        # if recipe exists, load it and see if it matches current recipe
        orig_recipe = yaml.load(open(write_path,"r"))
        if recipe == orig_recipe:
            # if recipes match, not existence and move on
            print("Identical recipe exists, will not overwrite.")
        else:
            # if recipes do not match, warn user
            print("Non-identical recipe already exists. Here are the differences:")
            recipe_difference(orig_recipe, recipe)
            if overwrite_mode == "auto":
                # if auto overwrite, overwrite recipe and warn user
                print("Automatically overwriting recipe...")
                _write_recipe(recipe, write_path)
            elif overwrite_mode == "manual":
                # otherwise just warn user
                resp = input("Would you like to overwrite existing recipe (y/n)")
                if resp.lower()[0] == "y":
                    print("Overwriting recipe...")
                    _write_recipe(recipe, write_path)
            else:
                print("Will not overwrite.")
    else:
        print("writing recipe...")
        _write_recipe(recipe, write_path)



if __name__ == "__main__":
    # construct the argument parse and parse the arguments
    ap = argparse.ArgumentParser()
    ap.add_argument("-c", "--cover_image", required=False,
        help="path to input cover image to be OCR'd")
    ap.add_argument("-i", "--instruct_image", required=False,
        help="path to input instruction image to be OCR'd")
    ap.add_argument("-p", "--pdf_directory", required=False,
                    help="path to 2-page pdf to create and add as link")
    ap.add_argument("-y", "--yml_directory", required=False,
                    help="path to yml directory to create")
    ap.add_argument("-o", "--overwrite_mode", required=False,
                    help="how to overwrite existing recipes: auto/manual/none")
    ap.add_argument("-d", "--debug", required=False, default=0,
                    help="1: debug mode. 2: extreme debug mode.")
    ap.add_argument("-P", "--print_recipe", required=False, action='store_true',
                    help="if argument is provided, activate debug mode.")
    #ap.add_argument("-p", "--preprocess", type=str, default="thresh",
    #    help="type of preprocessing to be done")

    args = vars(ap.parse_args())


    blue_apron_manager = BlueApronManager(
        cover_image   =args["cover_image"],
        instruct_image=args["instruct_image"],
        pdf_directory =args["pdf_directory"],
        yml_directory =args["yml_directory"],
        overwrite_mode=args["overwrite_mode"],
        debug     =int(args["debug"]),
        print_recipe  =args["print_recipe"])