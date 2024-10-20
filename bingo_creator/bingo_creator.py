#!/usr/bin/python3
# -*- coding: UTF-8 -*-

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

import os
import sys
import pprint
import random
import argparse

def random_subset(num, datalist):
    # turn datalist to set and back to list to remove duplicates
    _dlist = list(set(datalist))
    return random.sample(_dlist, num)

def make_2d_array(some_list, xsize, ysize=None):
    xsize = int(xsize)
    ysize = int(ysize) if ysize is not None else xsize
    if xsize <= 0: raise ValueError("xsize must be > 0")
    if ysize <= 0: raise ValueError("ysize must be > 0")

    arr = []
    _list = some_list.copy()
    for y_idx in range(ysize):
        this_row = []
        for x_idx in range(xsize):
            if not _list: break
            item = _list.pop(0)
            this_row.append(item)
        arr.append(this_row)
    return arr

def make_bingo(datalist, size, joker):
    num_entries = size*size
    # for uneven square size, middle field is "joker"
    if size%2 == 1:
        num_entries -= 1
    if num_entries > len(datalist):
        raise ValueError(f"not enough values in data list to generate {num_entries} entries")
    bingo_entries = random_subset(num_entries, datalist)
    # insert middle "joker" field
    if size%2 == 1:
        bingo_entries.insert(int(len(bingo_entries)/2), joker)
    bingo_array = make_2d_array(bingo_entries, size)
    return bingo_array

def read_bingodata_file(filepath):
    with open(args.file, "r") as infh:
        bingodata = infh.readlines()
    # ignore comments
    bingodata = list(filter(lambda b: not b.startswith("#"), bingodata))
    # strip whitespace and empty lines
    bingodata = [ b.strip() for b in bingodata if b.strip() ]
    return bingodata

def run(args):
    bingodata = read_bingodata_file(args.file)
    bingo = make_bingo(bingodata, args.size, args.joker)
    pprint.pprint(bingo)


parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("file", help="path to file containing bingo entries (one entry per line). lines prefixed with # (comments) and empty lines are ignored.")
parser.add_argument("-s", "--size", type=int, default=5, help="size of the bingo square (only uneven sizes get a center joker field)")
parser.add_argument("-j", "--joker", type=str, default="JOKER", help="text for the center joker field")

if __name__ == "__main__":
    args = parser.parse_args()
    try:
        run(args)
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {str(e)}")
        sys.exit(1)
