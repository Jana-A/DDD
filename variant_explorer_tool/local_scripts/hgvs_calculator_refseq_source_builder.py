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
import os

## the command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--o', type=str, default=None, help='The output path of current_run.py.')
parser.add_argument('--gui_path', type=str, default=None, help='The absolute path of the GUI.')
parser.add_argument('--remote_dir', type=str, default=None, help='The name of the remote temporary directory.')
parser.add_argument('--hgvs', type=str, default=None, help='The complete HGVS term.')

## prepare argument variables
args = parser.parse_args()
gui_path = args.gui_path
backend_dir = args.remote_dir
out = args.o
hgvs = args.hgvs

## the template of current_run.py in the form of a string
template = r"""
import re

remote_dir = '{builder_backend_dir}'
hgvs_term = '{builder_hgvs}'

chrom = 'NA'
## use regex to get the chromosome
chrom_match = re.search('[\D+\d+][\.](\d+):\S+', hgvs_term)
if chrom_match:
	chrom = str(chrom_match.group(1))

try:
	import hgvs.parser
	hgvsparser = hgvs.parser.Parser()
	variant_term = hgvsparser.parse_hgvs_variant(hgvs_term)
	import hgvs.dataproviders.uta
	hdp = hgvs.dataproviders.uta.connect()
	import hgvs.variantmapper
	variantmapper = hgvs.variantmapper.EasyVariantMapper(hdp)
	variant_location = variantmapper.c_to_g(variant_term)
	starts = str(variant_location.posedit.pos.start.base)
	stops = str(variant_location.posedit.pos.end.base)
	with open(remote_dir+'hgvs_coords.tsv', 'w') as out:
		out.write(chrom+'\t'+starts+'\t'+stops+'\n')
except:
	with open(remote_dir+'hgvs_coords.tsv', 'w') as out:
		out.write(chrom+'\tNA\tNA\n')


""".format(builder_backend_dir=backend_dir, builder_hgvs=hgvs)

## add the function and class definitions
with open('{}local_scripts/parsing_setups.py'.format(gui_path), 'r') as defins:
	defins = defins.read()

## write current_run.py
with open(out, 'w') as outfile:
	outfile.write('\n'.join([defins, template]))

