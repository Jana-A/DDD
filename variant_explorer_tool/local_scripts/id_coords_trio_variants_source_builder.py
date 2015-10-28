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
parser.add_argument('--id', type=str, default=None, help='User-defined person stable ID or decipher ID.')
parser.add_argument('--chrom', type=str, default=None, help='User-defined chromosome.')
parser.add_argument('--start', type=str, default=None, help='User-defined start.')
parser.add_argument('--stop', type=str, default=None, help='User-defined stop.')
parser.add_argument('--cq', type=str, default=None, help='User-defined comma-separated consequence.')
parser.add_argument('--max_af_cutoff', type=str, default=None, help='User-defined MAX AF cutoff.')
parser.add_argument('--max_af_value', type=str, default=None, help='User-defined MAX AF value.')
parser.add_argument('--string_user_settings_dict', type=str, default=None, help='User credentials.')

## prepare argument variables
args = parser.parse_args()
gui_path = args.gui_path
out = args.o
backend_dir = args.remote_dir
ID = args.id
chrom = args.chrom
start = args.start
stop = args.stop
cq = args.cq
max_af_cutoff = args.max_af_cutoff
max_af_value = args.max_af_value
string_user_settings_dict = args.string_user_settings_dict

## the template of current_run.py in the form of a string
template = r"""
remote_dir = '{builder_backend_dir}'
ID = '{builder_id}'
chrom = '{builder_chrom}'
start = '{builder_start}'
stop = '{builder_stop}'
cq = '{builder_cq}'
max_af_cutoff = '{builder_max_af_cutoff}'
max_af_value = '{builder_max_af_value}'
string_user_settings_dict = '{builder_string_user_settings_dict}'


user_settings_dict = {{}}

for i in string_user_settings_dict.split(';'):
	temp = i.split(':')
	user_settings_dict[temp[0]] = temp[1]


import json
json_dict = dict()

json_dict['error_msgs'] = 'No_error'
json_dict['trio_ids'] = ''
json_dict['variants'] = ''

## to do: get IDs, get VCF paths, get variants
try:
	cq_list = prepare_cq(cq)
	trio = id_in_ddd_prod(ID, user_settings_dict)
	child_id = trio[0]; mum_id = trio[1]; dad_id = trio[2]
	json_id_identifier_line = ''
	if (child_id):
		json_id_identifier_line = json_id_identifier_line + child_id + '\t'
	else:
		json_id_identifier_line = json_id_identifier_line + 'child_id_missing\t'
	if (mum_id):
		json_id_identifier_line = json_id_identifier_line + mum_id + '\t'
	else:
		json_id_identifier_line = json_id_identifier_line + 'mum_id_missing\t'
	if (dad_id):
		json_id_identifier_line = json_id_identifier_line + dad_id + '\t'
	else:
		json_id_identifier_line = json_id_identifier_line + 'dad_id_missing'
	json_dict['trio_ids'] = json_id_identifier_line
	json_dict['variants'] = ''
	child_vcf = get_indiv_vcf_path(child_id, params=user_settings_dict)
	mum_vcf = get_indiv_vcf_path(mum_id, params=user_settings_dict)
	dad_vcf = get_indiv_vcf_path(dad_id, params=user_settings_dict)
	try:
		json_dict['variants'] = json_dict['variants'] + ''.join(get_indiv_variants(child_id, child_vcf, chrom, start, stop, cq_list, max_af_cutoff, max_af_value))
	except:
		pass
	try:
		json_dict['variants'] = json_dict['variants'] + ''.join(get_indiv_variants(mum_id, mum_vcf, chrom, start, stop, cq_list, max_af_cutoff, max_af_value))
	except:
		pass
	try:
		json_dict['variants'] = json_dict['variants'] + ''.join(get_indiv_variants(dad_id, dad_vcf, chrom, start, stop, cq_list, max_af_cutoff, max_af_value))
	except:
		pass
	with open(remote_dir+'trio_variants.json', 'w') as out:
		json.dump(json_dict, out)
except:
	json_dict['error_msgs'] = 'Error'
	with open(remote_dir+'trio_variants.json', 'w') as out:
		json.dump(json_dict, out)


""".format(builder_backend_dir=backend_dir, builder_id=ID, builder_chrom=chrom, builder_start=start, builder_stop=stop, builder_cq=cq, builder_max_af_cutoff=max_af_cutoff, builder_max_af_value=max_af_value, builder_string_user_settings_dict=string_user_settings_dict)

## add the function and class definitions
with open('{}local_scripts/parsing_setups.py'.format(gui_path), 'r') as defins:
	defins = defins.read()

## write current_run.py
with open(out, 'w') as outfile:
	outfile.write('\n'.join([defins, template]))



