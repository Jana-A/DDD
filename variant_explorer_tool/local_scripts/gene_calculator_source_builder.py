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
parser.add_argument('--gene', type=str, default=None, help='The gene name.')
parser.add_argument('--string_user_settings_dict', type=str, default=None, help='User credentials.')

## prepare argument variables
args = parser.parse_args()
gui_path = args.gui_path
out = args.o
backend_dir = args.remote_dir
gene = args.gene
string_user_settings_dict = args.string_user_settings_dict

## the template of current_run.py in the form of a string
template = r"""
remote_dir = '{builder_backend_dir}'
gene = '{builder_gene}'
string_user_settings_dict = '{builder_string_user_settings_dict}'

user_settings_dict = {{}}

for i in string_user_settings_dict.split(';'):
	temp = i.split(':')
	user_settings_dict[temp[0]] = temp[1]


import json
json_dict = dict()

json_dict['error_msgs'] = ''

try:
	json_dict['error_msgs'] = 'No_error'
	json_dict['gene_calculator'] = calculator_gene_name(gene, user_settings_dict)
	with open(remote_dir+'gene_calculator_out.json', 'w') as out:
		json.dump(json_dict, out)
except:
	json_dict['error_msgs'] = 'Error'
	with open(remote_dir+'gene_calculator_out.json', 'w') as out:
		json.dump(json_dict, out)


""".format(builder_backend_dir=backend_dir, builder_gene=gene, builder_string_user_settings_dict=string_user_settings_dict)

## add the function and class definitions
with open('{}local_scripts/parsing_setups.py'.format(gui_path), 'r') as defins:
	defins = defins.read()

## write current_run.py
with open(out, 'w') as outfile:
	outfile.write('\n'.join([defins, template]))

