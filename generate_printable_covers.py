#!/usr/bin/python3

# MIT License
# 
# Copyright (c) 2024- Elisabeth Oertel
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

# USAGE: generate_printable_covers.py [-h] [-p PATH] [-f [FILE ...]] [-s SIZE] [-q] [-y]
# 
# Skript to generate a PDF containing miniature bookcovers to print out. Bookcover images must be in JPG or PNG format.
# 
# options:
#   -h, --help            show this help message and exit
#   -p PATH, --path PATH  directory path that contains the cover images to create printable pages for. ignored when --file is used. output files will be placed here as well. (default: .)
#   -f [FILE ...], --file [FILE ...]
#                         filenames to create printable for, or .csv/.txt file containing filenames, one per line (default: None)
#   -s SIZE, --size SIZE  sizes to create printables for, can be used multiple time. syntax: <x-mm>:<y-mm>[:<num-copies-per-cover>]. (default: 30:48)
#   -q, --quiet           less verbose output (default: False)
#   -y, --answer-yes      answer yes to all interactive questions (default: False)

# EXAMPLES:
# - Generate PDF containing 25mm x 40mm sized versions of image files in the working directory
#       generate_printable_covers.py --size "25:40"
#
# - Generate PDF containing default sized (30x48) versions of image files listed in covers.csv. The output file will be placed in the current working directory
#       generate_printable_covers.py -f covers.csv
#
# - Generate two PDF files, one for size 25x40 with each cover appearing 2 times, and one for size 30x48, for the image files in directory cover_images/
#   The output files will be placed in directory cover_images/ as well.
#       generate_printable_covers.py --path cover_images/ -s "25:40:2" -s "30:48:1"

# WARNING: I only tried running this on Linux. The generated .tex files should run fine with xelatex on Windows (e.g. through TexWorks) since they use relative paths for the image includes.

import os
import sys
import argparse
import datetime
import subprocess

INCLUDEGRAPHICS_TEMPLATE = "\\includegraphics[width={width}mm, height={height}mm, keepaspectratio=false]{{{filename}}}"
def get_includegraphics(filename, width, height):
    return INCLUDEGRAPHICS_TEMPLATE.format(width=width, height=height, filename=filename)

def get_line(filenames, size):
    igraphics = [ get_includegraphics(f, size["x"], size["y"]) for f in filenames ]
    line = "\\noindent\\vspace{0.1mm}" + "\\hspace{0.5mm}".join(igraphics)
    return line

def get_latex_bodies(filenames, sizes):
    bodies = {}
    for sizename, size in sizes.items():
        body = []
        loc_filenames = filenames.copy()
        num_per_line = size["num_per_line"]
        while len(loc_filenames) > num_per_line:
            line_filenames = loc_filenames[:num_per_line]
            loc_filenames = loc_filenames[num_per_line:]
            for _ in range(size["num"]):
                body.append(get_line(line_filenames, size))
        # append possibly underfull last line
        for _ in range(size["num"]):
            body.append(get_line(loc_filenames, size))
        bodies[sizename] = body
    return bodies

def _get_datestring():
    now = datetime.datetime.now()
    nowstring = now.strftime("%Y%m%d-%H%M%S")
    return nowstring

OUT_FILENAME_TEMPLATE = "covers_{sizename}_{datestring}.tex"
def make_output_data(filenames, sizes):
    bodies = get_latex_bodies(filenames, sizes)
    output_data = {}
    for sizename, body in bodies.items():
        out_filename = OUT_FILENAME_TEMPLATE.format(sizename=sizename, datestring=_get_datestring())
        bodystring = "\n\n".join(body)
        output_data[out_filename] = bodystring
    return output_data

TEX_TEMPLATE = """\\documentclass[a4]{{article}}
\\usepackage{{geometry}}
\\geometry{{a4paper,margin=1cm}}
\\usepackage{{graphicx}}
\\begin{{document}}
{body}
\\end{{document}}
"""
def print_tex_files(output_path, output_data):
    out_filepaths = []
    os.makedirs(output_path, exist_ok=True)
    for out_filename, bodystring in output_data.items():
        out_filepath = os.path.join(output_path, out_filename)
        out_string = TEX_TEMPLATE.format(body=bodystring)
        with open(out_filepath, "w") as ofh:
            ofh.write(out_string)
        out_filepaths.append(out_filepath)
    return out_filepaths

def parse_sizes(size_list):
    # remove default size if any sizes were explicitely given
    if len(size_list) > 1:
        size_list.pop(0)

    my_sizes = {}
    for size in size_list:
        size = str(size).strip()
        size_parts = size.split(":")
        if len(size_parts) < 2 or len(size_parts) > 3:
            raise ValueError(f"invalid size '{size}'")
        num = int(size_parts[2]) if len(size_parts) == 3 else 1
        x = int(size_parts[0])
        y = int(size_parts[1])
        size_name = "x".join(size_parts[:2])
        num_per_line = int((210-20)/(x+1))
        my_sizes[size_name] = { "x": x, "y": y, "num": num, "num_per_line": num_per_line }
    return my_sizes


def is_img_format(f):
    ext = f.split(".")[-1]
    if ext in ["jpg", "jpeg", "png"]: return True
    else: return False

def _prepend_cwd(f):
    if not f.startswith("/"):
        return os.path.join(os.path.abspath(os.getcwd()), f)
    else:
        return f

def get_files(args):
    if args.file:
        filenames = args.file
        # read filenames from file
        if filenames[0].endswith(".csv") or filenames[0].endswith(".txt"):
            with open(filenames[0], "r") as infh:
                filenames = infh.readlines()
        # filter files that don't exist
        filenames = list(filter(lambda f: os.path.isfile(f), filenames))
    elif args.path:
        filenames = os.listdir(args.path)
    # filter list for image files
    filenames = list(filter(lambda f: f.strip(), filenames))
    filenames = list(filter(is_img_format, filenames ))
    return filenames

def rm_file(filename):
    try:
        os.remove(filename)
    except OSError as e:
        print(f">>> ERROR: {e.filename} - {e.strerror}")

def run_xelatex(args, out_filepaths):
    # check if xelatex is installed
    try:
        subprocess.run(args=["which", "xelatex"], capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError:
        print(f">>> xelatex is not installed.")
        return

    for filepath in out_filepaths:
        try:
            subprocess.run( args=["xelatex", filepath], check=True, capture_output=True, text=True )
            if not args.quiet: print(f">>> xelatex {filepath} success")
        except subprocess.CalledProcessError as e:
            print(f">>> ERROR: failed running xelatex on {filepath}: {str(e.stderr)}")
    if args.answer_yes or ask_continue("remove .aux .log files [y/n]? > "):
        for filepath in out_filepaths:
            basename = ".".join(filepath.split(".")[:-1])
            rm_file(basename + ".aux")
            rm_file(basename + ".log")

def ask_continue(question="continue [y/n]? > "):
    res = input(question).strip().lower()
    if res == "y":
        return True
    else:
        return False

def run(args):
    filenames = get_files(args)
    if not args.quiet: print(">>> filenames: {}".format(", ".join([os.path.basename(f) for f in filenames])))
    else: print(f">>> {len(filenames)} files found.")

    if not args.answer_yes and not ask_continue(): sys.exit(0)

    output_data = make_output_data(filenames, parse_sizes(args.size))
    if not args.quiet: print(f">>> generated data for {len(output_data)} output files")
    out_filepaths = print_tex_files(args.path, output_data)
    if not args.quiet: print(f">>> printed {len(out_filepaths)} .tex files: {', '.join(out_filepaths)}")

    if not args.answer_yes and not ask_continue("run xetex on .tex files [y/n]? > "): sys.exit(0)
    run_xelatex(args, out_filepaths)

parser = argparse.ArgumentParser(description="Skript to generate a PDF containing miniature bookcovers to print out. Bookcover images must be in JPG or PNG format.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-p", "--path", help="directory path that contains the cover images to create printable pages for. ignored when --file is used. output files will be placed here as well.", default=".")
parser.add_argument("-f", "--file", help="filenames to create printable for, or .csv/.txt file containing filenames, one per line", nargs="*")
parser.add_argument("-s", "--size", help="sizes to create printables for, can be used multiple time. syntax: <x-mm>:<y-mm>[:<num-copies-per-cover>].", action="append", default=["30:48"])
parser.add_argument("-q", "--quiet", help="less verbose output", action="store_true")
parser.add_argument("-y", "--answer-yes", help="answer yes to all interactive questions", action="store_true")

if __name__ == "__main__":
    args = parser.parse_args()
    run(args)
