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

import os
import argparse

## the command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--o', type=str, default=None, help='The output path of current_run.py.')
parser.add_argument('--gui_path', type=str, default=None, help='The absolute path of the GUI.')
parser.add_argument('--remote_dir', type=str, default=None, help='The name of the remote temporary directory.')
parser.add_argument('--gene', type=str, default=None, help='The gene name.')
parser.add_argument('--cq', type=str, default=None, help='User-defined comma-separated consequence.')
parser.add_argument('--max_af_cutoff', type=str, default=None, help='User-defined MAX AF cutoff.')
parser.add_argument('--max_af_value', type=str, default=None, help='User-defined MAX AF value.')
parser.add_argument('--string_user_settings_dict', type=str, default=None, help='User credentials.')

## prepare argument variables
args = parser.parse_args()
gui_path = args.gui_path
out = args.o
backend_dir = args.remote_dir
gene = args.gene
cq = args.cq
max_af_cutoff = args.max_af_cutoff
max_af_value = args.max_af_value
string_user_settings_dict = args.string_user_settings_dict

## the template of current_run.py in the form of a string
template = r"""
remote_dir = '{builder_backend_dir}'
import multiprocessing
import gzip

gene = '{builder_gene}'
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
json_dict['error_msgs'] = ''


try:
	gene_coords = calculator_gene_name(gene, user_settings_dict)
	coord_match = re.search('chr:(\S+)\tstart:(\S+)\tstop:(\S+)', gene_coords)
	chrom = coord_match.group(1)
	start = coord_match.group(2)
	stop = coord_match.group(3)
	cq_list = prepare_cq(cq)
	## The multiprocessing function.
	def mp_func(a, b, chrom=chrom, start=start, stop=stop, cq_definitions=cq, max_af_cutoff=max_af_cutoff, max_af_value=max_af_value):
		output_file_name = remote_dir + 'f_'+str(a)+'_'+str(b)+'.tsv.gz'
		out = gzip.open(output_file_name, 'wb') ## open a compressed file used to write to
		for tup in vcf_paths[a:b]:
			person_id, person_vcf = tup
			if (os.access(person_vcf, os.F_OK) and os.access(person_vcf, os.R_OK)):
				vcf_generator = tabix_vcf(person_vcf, chrom, start, stop)
				condition = True
				while (condition):
					my_rec = next(vcf_generator, False)
					if (my_rec):
						obj = Record(my_rec, cq_definitions, max_af_cutoff, max_af_value)
						if (obj.validate_cq() and obj.validate_max_af_cutoff() and obj.validate_max_af_value()):
							out.write('{{}}\t{{}}\n'.format(person_id, obj.get_variant_line()))
					else:
						condition = my_rec
		out.close()
	get_all_current_vcfs_sql_statement = r"select person_stable_id,tmp_path from dataset where tmp_path like '%/vcfs/%uber%' and data_freeze_id = (select data_freeze_id from data_freeze where is_current = 't');"
	vcf_paths = ddd_prod_connect_and_fetch(get_all_current_vcfs_sql_statement, user_settings_dict)
	ind = list(range(0,len(vcf_paths),500))
	ind[-1] = len(vcf_paths) ## replace last index by length of list
	for i in range(0, len(ind)-1):
		multiprocessing.Process(target=mp_func, args=(ind[i], ind[i+1])).start()
	json_dict['error_msgs'] = 'No_error'
	with open(remote_dir + 'cohort_variants.json', 'w') as out:
		json.dump(json_dict, out)
except:
	json_dict['error_msgs'] = 'Error'
	with open(remote_dir + 'cohort_variants.json', 'w') as out:
		json.dump(json_dict, out)


""".format(builder_backend_dir=backend_dir, builder_gene=gene, builder_cq=cq, builder_max_af_cutoff=max_af_cutoff, builder_max_af_value=max_af_value, builder_string_user_settings_dict=string_user_settings_dict)

## add the function and class definitions
with open('{}local_scripts/parsing_setups.py'.format(gui_path), 'r') as defins:
	defins = defins.read()

## write current_run.py
with open(out, 'w') as outfile:
	outfile.write('\n'.join([defins, template]))




