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
parser.add_argument('--o', type=str, default=None, help='The output path of current_run.p')
parser.add_argument('--gui_path', type=str, default=None, help='The absolute path of the GUI.')
parser.add_argument('--remote_dir', type=str, default=None, help='The name of the remote temporary directory.')
parser.add_argument('--id', type=str, default=None, help='User-defined person stable ID or decipher ID.')
parser.add_argument('--chrom', type=str, default=None, help='User-defined chromosome.')
parser.add_argument('--start', type=str, default=None, help='User-defined start.')
parser.add_argument('--stop', type=str, default=None, help='User-defined stop.')
parser.add_argument('--string_user_settings_dict', type=str, default=None, help='User credentials.')

## prepare argument variables
args = parser.parse_args()
gui_path = args.gui_path
backend_dir = args.remote_dir
out = args.o
ID = args.id
chrom = args.chrom
start = args.start
stop = args.stop
string_user_settings_dict = args.string_user_settings_dict

## the template of current_run.py in the form of a string
template = r"""
remote_dir = '{builder_backend_dir}'
ID = '{builder_id}'
chrom = '{builder_chrom}'
start = '{builder_start}'
stop = '{builder_stop}'
string_user_settings_dict = '{builder_string_user_settings_dict}'

user_settings_dict = {{}}

for i in string_user_settings_dict.split(';'):
	temp = i.split(':')
	user_settings_dict[temp[0]] = temp[1]


## to do: send a request to the IGV API, read binary response
try:
	user_settings = {{
		'action': 'login',
		'username': user_settings_dict['igv_username'],
		'password': user_settings_dict['igv_user_password']
	}}
	trio = id_in_ddd_prod(ID, user_settings_dict)
	igv_plot_url = r'http://ddd-hpo.internal.sanger.ac.uk:8082/igv-driver/app/trio/person/' + trio[0] + r'/' + str(chrom) + r'/' + start + r'/' + stop
	with requests.session() as sesh:
		sesh.post(r'http://ddd-hpo.internal.sanger.ac.uk:8082/igv-driver/login', data=user_settings)
		response = sesh.get(igv_plot_url)
		igv_out = open(remote_dir+'trio_igv.png', 'wb')
		igv_out.write(response.content)
		igv_out.close()
except:
	pass


""".format(builder_backend_dir=backend_dir, builder_id=ID, builder_chrom=chrom, builder_start=start, builder_stop=stop, builder_string_user_settings_dict=string_user_settings_dict)

## add the function and class definitions
with open('{}local_scripts/parsing_setups.py'.format(gui_path), 'r') as defins:
	defins = defins.read()

## write current_run.py
with open(out, 'w') as outfile:
	outfile.write('\n'.join([defins, template]))

