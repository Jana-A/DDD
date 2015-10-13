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
parser.add_argument('--chrom', type=str, default=None, help='User-defined chromosome.')
parser.add_argument('--pos', type=str, default=None, help='The query position.')
parser.add_argument('--string_user_settings_dict', type=str, default=None, help='User credentials.')

## prepare argument variables
args = parser.parse_args()
gui_path = args.gui_path
out = args.o
backend_dir = args.remote_dir
chrom = args.chrom
pos = args.pos
string_user_settings_dict = args.string_user_settings_dict

## the template of current_run.py in the form of a string
template = r"""
import multiprocessing
import re

remote_dir = '{builder_backend_dir}'
chrom = '{builder_chrom}'
pos = '{builder_pos}'

chrom_numb = list(range(1,22))
chrom_numb = list(map(lambda x: str(x), chrom_numb))

chrom_numb.extend(['X', 'Y'])

validate_chrom = chrom in chrom_numb
validate_pos = re.search('^\d+$', pos)

def mp_freq_func(a, b, chrom=chrom, pos=pos):
	output_file_name = remote_dir+'f_'+str(a)+'_'+str(b)+'_freq.txt'
	out = open(output_file_name, 'w')
	count = 0
	for tup in vcf_paths[a:b]:
		person_id, person_vcf = tup
		if (os.access(person_vcf, os.F_OK) and os.access(person_vcf, os.R_OK)):
			vcf_generator = tabix_vcf(person_vcf, chrom, pos, pos)
			condition = True
			while (condition):
				my_rec = next(vcf_generator, False)
				if (my_rec):
					count = count + 1
				else:
					condition = my_rec
	out.write(str(count)+'\n')
	out.close()



if (validate_chrom and validate_pos):
	string_user_settings_dict = '{builder_string_user_settings_dict}'
	user_settings_dict = {{}}
	for i in string_user_settings_dict.split(';'):
		temp = i.split(':')
		user_settings_dict[temp[0]] = temp[1]

	get_all_current_vcfs_sql_statement = r"select person_stable_id,tmp_path from dataset where tmp_path like '%/vcfs/%uber%' and data_freeze_id = (select data_freeze_id from data_freeze where is_current = 't');"
	vcf_paths = ddd_prod_connect_and_fetch(get_all_current_vcfs_sql_statement, user_settings_dict)
	#
	with open(remote_dir+'total_vcfs', 'w') as ouffile:
		ouffile.write(str(len(vcf_paths))+'\n')
	#
	ind = list(range(0,len(vcf_paths),500))
	ind[-1] = len(vcf_paths) ## replace last index by length of list
	#
	for i in range(0, len(ind)-1):
		multiprocessing.Process(target=mp_freq_func, args=(ind[i], ind[i+1])).start()
else:
	with open(remote_dir+'total_vcfs', 'w') as ouffile:
		ouffile.write('NA\n')


""".format(builder_backend_dir=backend_dir, builder_chrom=chrom, builder_pos=pos, builder_string_user_settings_dict=string_user_settings_dict)

## add the function and class definitions
with open('{}local_scripts/parsing_setups.py'.format(gui_path), 'r') as defins:
	defins = defins.read()

## write current_run.py
with open(out, 'w') as outfile:
	outfile.write('\n'.join([defins, template]))


