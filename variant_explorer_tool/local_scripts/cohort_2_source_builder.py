#!/usr/bin/env python

"""
-------------
Copyright (c) 2015. Genome Research Ltd.
Author: Deciphering Development Disorders Project Team.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.

See the License for the specific language governing permissions and
limitations under the License.
---------------
"""

## Description = This script is not meant to be used directly by the user, it is however used inside the GUI.
##				 This script creates another python script called current_run.py that is executed on the server.
##				 It takes the user-defined parameters and puts them in the current_run.py template.
##				 This script embeds some function and class definitions found in parsing_setups.py


import argparse

## the command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--o', type=str, default=None, help='The output path of current_run.py.')
parser.add_argument('--remote_dir', type=str, default=None, help='The name of the remote temporary directory.')

## prepare argument variables
args = parser.parse_args()
out = args.o
backend_dir = args.remote_dir

## the template of current_run.py in the form of a string
template = r"""
import os
import re

remote_dir = '{builder_backend_dir}'

## put the file results of the multiprocessing function into a single file
current_dir_files = os.listdir(remote_dir)
process_files = [fl for fl in current_dir_files if re.search('^f_\d+_\d+[\.]tsv[\.]gz', fl)]
with open(remote_dir+'selected_cohort_variants.tsv.gz', 'wb') as cohort:
	for infile in process_files:
		with open(remote_dir+infile, 'rb') as redirect_this:
			cohort.write(redirect_this.read())

[os.remove(remote_dir+x) for x in process_files]

""".format(builder_backend_dir=backend_dir)

## write current_run.py
with open(out, 'w') as outfile:
	outfile.write(template+'\n')



