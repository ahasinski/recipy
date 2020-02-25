# import the necessary packages

from PIL import Image
import pytesseract
import argparse
import cv2
import os
import numpy as np
import yaml
from collections import OrderedDict
#from blue_apron_manager import BlueApronManager

class BlueApronBaseOCR(object):

    def __init__(self,):
        pass

    def load_image(self, image):
        # load the example image and convert it to grayscale
        image = cv2.imread(image)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        image = cv2.threshold(image, 0, 255,
                             cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
        return image

    def crop_image(self, image=None, y0=None, y1=None, x0=None, x1=None):
        if image is None:
            image = self.image.copy()
        cropped_image = image[y0:y1, x0:x1]
        return cropped_image




class BlueApronCoverOCR(BlueApronBaseOCR):

    def __init__(self, debug=0):
        self.recipe = {
            "name": None,
            "ingredients": [],
            }

        self.segments = {
            "name":
                {"y0": 50,
                 "y1": 325,
                 "x0": 50,
                 "x1": 440},
            "time":
                {"y0": 350,
                 "y1": 425,
                 "x0": 50,
                 "x1": 440}}

        ingredient_segments = self._ingredient_segments()
        self.segments.update(ingredient_segments)
        self.debug=debug


    def _ingredient_segments(self):
        # ('SHAPE: ', (1650, 1275, 3))
        x0 = 30
        x1 = 225
        x_inc = 170
        y0 = 1200
        y1 = 1295
        y_inc = 200
        dct = {}
        counter = 1
        for c in range(7):
            for r in range(2):
                dct["ingredient_%02d" % counter] = {
                    "y0": y0 + y_inc*r,
                    "y1": y1 + y_inc*r,
                    "x0": x0 + x_inc*c,
                    "x1": x1 + x_inc*c,
                }
                counter+=1
        return dct

    def ocr(self, image):
        image = self.load_image(image)
        for segment, bounds in self.segments.items():
            image_segment = self.crop_image(image, **bounds)
            if "name" in segment:
                image_segment = cv2.bitwise_not(image_segment)

            #kernel = np.ones((2,2))
            #kernel = np.array([[0., 1., 0.], [1., 1., 1.],[0., 1., 0.]])
            #kernel = np.array([[0.,0.,1.,0.,0.],[0.,1.,1.,1.,0.],[1.,1.,1.,1.,1.],[0.,1.,1.,1.,0.],[0.,0.,1.,0.,0.]])
            #image_segment = cv2.erode(image_segment, kernel, iterations=1)
            #image_segment = cv2.morphologyEx(image_segment, cv2.MORPH_OPEN, kernel)
            #image_segment = cv2.morphologyEx(image_segment, cv2.MORPH_GRADIENT, kernel)

            # write the grayscale image to disk as a temporary file so we can
            # apply OCR to it
            filename = "{}.png".format(os.getpid())
            cv2.imwrite(filename, image_segment)
            # load the image as a PIL/Pillow image, apply OCR, and then delete
            # the temporary file
            text = pytesseract.image_to_string(Image.open(filename), config="--psm 6 --oem 2")
            text = text.encode("ascii", "replace")
            if text=="":
                continue
            if "Did You Know?" in text:
                continue
            os.remove(filename)
            # reformat
            if "ingredient" in segment:
                ingredient = self.fix_ingredient(text)
                self.recipe["ingredients"].append(ingredient)
            elif "name" in segment:
                self.recipe["name"] = self.fix_name(text)
            else:
                time,servings = self.fix_time_serving(text)
                self.recipe["time"] = time
                self.recipe["servings"] = servings

            if self.debug:
                # show the output images
                cv2.imshow("Image", image_segment)
                cv2.waitKey(0)


    def fix_ingredient(self, text):
        if np.isscalar(text):
            text = text.split("\n")
        if len(text) > 1:
            amount = text[0]
            ingredient = " ".join(text[1:])
        else:
            amount = ""
            ingredient = text[0]
        ingredient = {ingredient: amount}
        return ingredient

    def fix_name(self, text):
        if np.isscalar(text):
            text = text.split("\n")
        text = " ".join(text)
        text = text.replace("&", "and").replace(",","").replace("?","")
        return text

    def fix_time_serving(self, text):
        if np.isscalar(text):
            text = text.split("\n")
        time, servings = None, None
        for line in text:
            if "TIME" in line:
                time = line.replace("TIME:","").strip()
            elif "SERVINGS" in line:
                servings = line.replace("SERVINGS:", "").strip()
            else:
                continue
        return time, servings

    def print_name(self, name=None):
        if name is None:
            name = self.recipe["name"]
        print(name)

    def print_ingredients(self, ingredients=None):
        if ingredients is None:
            ingredients = self.recipe["ingredients"]
            ingredients = ["{}: {}".format(
                k, v) for k,v in ingredients.items()]
        print(", \n".join(ingredients))

    def print_attribute(self, attribute, value=None):
        if value is None:
            value = self.recipe[attribute]
        print("{}: {}".format(attribute, value))





class BlueApronInstructOCR(BlueApronBaseOCR):

    def __init__(self, debug=0):
        self.recipe = {
            "instructions": None,
            "tags": None
        }
        self.segments = {
            "instructions":
                {"y0": None,
                 "y1": -60,
                 "x0": 545,
                 "x1": None},
        }
        self.debug=debug

    def ocr(self, image):
        self.output_segments = []
        image = self.load_image(image)
        for segment, bounds in self.segments.items():
            image_segment = self.crop_image(image, **bounds)
            # write the grayscale image to disk as a temporary file so we can
            # apply OCR to it
            filename = "{}.png".format(os.getpid())
            cv2.imwrite(filename, image_segment)
            # load the image as a PIL/Pillow image, apply OCR, and then delete
            # the temporary file
            text = pytesseract.image_to_string(Image.open(filename), config="--psm 6 --oem 2")
            text = text.encode("ascii", "replace")
            os.remove(filename)
            # reformat
            self.fix(text)
            if self.debug:
                # show the output images
                cv2.imshow("Image", image_segment)
                cv2.waitKey(0)

    def fix(self, text):
        if np.isscalar(text):
            text = text.split("\n")
        #text = self.paragrapher(text)
        steps = self.stepper(text)
        self.recipe["instructions"] = steps
        self.recipe["tags"] = self.auto_tagger(steps)

    def print_instruction(self, instruction=None):
        if instruction is None:
            instruction = self.recipe["instructions"]
        for step, substeps in instruction:
            for substep in substeps:
                print(" - {}".format(substep))
        #print("\n".join(instruction))

    def print_auto_tags(self, auto_tags=None):
        if auto_tags is None:
            auto_tags = self.recipe["auto_tags"]
        print(", ".join(auto_tags))

    def new_step(self, line, step=1):
        step_title =  "{count}. {line}".format(count=step, line=line)
        return [step_title, ]

    def new_substep(self, substep_count):
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        substep = "{}. ".format(alphabet[substep_count])
        substep_count += 1
        return substep, substep_count

    def stepper(self, text):
        text.append("")
        steps = [] #[self.new_step(text[0], 1)]
        step_count = 1
        substep_count = 0
        substep = "a. "
        for line in text:
            if self.debug >= 2:
                print("|{}|".format(line))
                # print(step_count, substep_count)
                print(substep)
                print("-----")
            # detect empty line
            if len(set(line))<=1:
                # append substep and start new substep
                if (len(substep)>3) and (substep[-1] in [".", "!",]):
                    steps[-1].append(substep.strip())
                    substep, substep_count = self.new_substep(substep_count)
                # otherwise just skip over it
            # detect new step
            elif (line.strip()[-1] == ":") or \
                ("Make Ahead Modifications" in line):
                # if exists, append last substep
                if (len(substep)>3):
                    steps[-1].append(substep.strip())
                # reset substep
                substep, substep_count = self.new_substep(0)
                # append new step
                steps.append(self.new_step(line, step_count))
                step_count += 1
            # otherwise increase substep with current line
            else:
                substep = "{} {}".format(substep, line)
        return steps


    def auto_tagger(self, steps):
        auto_tags = []
        for step in steps:
            step_title = step[0]
            step_title = step_title[:-1]
            step_title = step_title.replace("Prepare the ingredients & ", "")
            step_title = step_title.replace(" & serve your dish", "")
            step_title = step_title.replace("Make Ahead Modifications.", "make_ahead")
            step_title = step_title.split(" the ")[-1]
            step_title = step_title.replace(" ", "_")
            auto_tags.append(step_title)
        auto_tags = list(set(auto_tags))
        return auto_tags



# def blue_apron_ocr(cover_image,
#                    instruct_image,
#                    overwrite_mode="manual",
#                    debug=False,
#                    print_recipe=False,
#                    pdf_directory=None,
#                    yml_directory=None):
#     debug=int(debug)
#     manager = BlueApronManager(cover_image=cover_image,
#                                instruct_image=instruct_image)
#     cover_ocr = BlueApronCoverOCR(debug=debug)
#     cover_ocr.ocr(manager.cover_image)
#
#     instruct_ocr = BlueApronInstructOCR(debug=debug)
#     instruct_ocr.ocr(manager.instruct_image)
#
#     recipe = cover_ocr.recipe
#     recipe.update(instruct_ocr.recipe)
#     recipe["source"] = "Blue Apron"
#     recipe["url"] = ""
#
#     outputs = manager.format_outputs(output_name=recipe["name"],
#                                      pdf_dir=pdf_directory,
#                                      yml_dir=yml_directory)
#     recipe_name, pdf_dir, yml_dir = outputs
#
#     if pdf_directory is not None:
#         recipe["pdf"] = pdf_dir
#         # func_path = os.path.dirname(os.path.abspath(__file__))
#         # join_pdfs = os.path.join(func_path, "bash/join_pdfs.sh")
#         # load_run_script(join_pdfs, image)
#     if print_recipe:
#         recipe_printer(recipe)
#     if yml_directory != -1:
#         write_recipe(recipe, yml_dir, overwrite_mode=overwrite_mode)






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


    blue_apron_ocr(
        cover_image   =args["cover_image"],
        instruct_image=args["instruct_image"],
        pdf_directory =args["pdf_directory"],
        yml_directory =args["yml_directory"],
        overwrite_mode=args["overwrite_mode"],
        debug     =int(args["debug"]),
        print_recipe  =args["print_recipe"])


#('SHAPE: ', (1650, 1275, 3))


# #gray = gray[y:y+h, x:x+w]
# gray = gray[:-60, 540:]
#
#
# # check to see if we should apply thresholding to preprocess the
# # image
# if args["preprocess"] == "thresh":
#     #gray = cv2.GaussianBlur(gray, (1, 1), 0)
#     gray = cv2.threshold(gray, 0, 255,
#                          cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
#
# elif args["preprocess"] == "adapt_thresh":
#     gray = cv2.adaptiveThreshold(gray,255,cv2.ADAPTIVE_THRESH_MEAN_C,\
#             cv2.THRESH_BINARY,11,2)
#
# # make a check to see if median blurring should be done to remove
# # noise
# elif args["preprocess"] == "blur":
#     gray = cv2.medianBlur(gray, 3)
#
# # write the grayscale image to disk as a temporary file so we can
# # apply OCR to it
# filename = "{}.png".format(os.getpid())
# cv2.imwrite(filename, gray)
#
# # load the image as a PIL/Pillow image, apply OCR, and then delete
# # the temporary file
# text = pytesseract.image_to_string(Image.open(filename))
# os.remove(filename)
#
# fixer = BlueApronInstructFixer()
# text = fixer.fix(text)
#
# print(text)
#
# # show the output images
# cv2.imshow("Cover_Image", image)
# cv2.imshow("Cover_Output", self.)
# cv2.waitKey(0)