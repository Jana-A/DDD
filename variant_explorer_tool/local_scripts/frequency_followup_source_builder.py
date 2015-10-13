#!/usr/bin/env python

## Description = This script is not meant to be used directly by the user, it is however used inside the GUI.
##				 This script creates another python script called current_run.py that is executed on the server.
##				 It takes the user-defined parameters and puts them in the current_run.py template.
##				 This script embeds some function and class definitions found in parsing_setups.py

import os
import argparse

## the command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--o', type=str, default=None, help='The output path of current_run.py.')
parser.add_argument('--gui_path', type=str, default=None, help='The absolute path of the GUI.')
parser.add_argument('--remote_dir', type=str, default=None, help='The name of the remote temporary directory.')

## prepare argument variables
args = parser.parse_args()
gui_path = args.gui_path
out = args.o
backend_dir = args.remote_dir

## the template of current_run.py in the form of a string
template = r"""
import os
import glob
import re

remote_dir = '{builder_backend_dir}'
count = 0
freq_files = glob.glob(remote_dir+'*_freq.txt')

if (freq_files):
	for fl in freq_files:
		with open(fl, 'r') as infile:
			count = count + int(re.sub('\n', '', infile.read()))
		os.remove(fl)
	with open(remote_dir+'final_freq', 'w') as outfile:
		outfile.write(str(count)+'\n')
else:
	with open(remote_dir+'final_freq', 'w') as outfile:
		outfile.write('NA\n')


""".format(builder_backend_dir=backend_dir)

## add the function and class definitions
with open('{}local_scripts/parsing_setups.py'.format(gui_path), 'r') as defins:
	defins = defins.read()

## write current_run.py
with open(out, 'w') as outfile:
	outfile.write('\n'.join([defins, template]))










