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

import sys
import os
import getpass
import re
import argparse

try:
	os.environ['PYTHONPATH'] = '/software/ddd/python2/lib/python2.7/site-packages:'
	if getpass.getuser() == 'na10':
		sys.path.insert(0, '/nfs/users/nfs_n/na10/.local/lib/python2.7/site-packages/')
	sys.path.append('/software/ddd/python2/lib/python2.7/site-packages')
	module_dump = '/lustre/scratch113/projects/ddd/users/ja16/variant_parser/py_module_dump/'
	for i in os.listdir(module_dump):
		sys.path.append(module_dump+i)
	#sys.path.append('/nfs/users/nfs_j/ja16/.local/')
	#sys.path.append('/nfs/users/nfs_j/ja16/.local/lib/python3.3/site-packages/pyhgvs-0.9.4-py3.3.egg')
	#sys.path.append('/nfs/users/nfs_j/ja16/pygr-0.8.2-py2.6-linux-x86_64.egg')
	#sys.path.append('/nfs/users/nfs_j/ja16/.local/lib/python2.7/site-packages/pytabix-0.0.2-py2.7-linux-x86_64.egg')
	import psycopg2
	import requests
	import tabix
	from pyhgvs import parse_hgvs_name
	from pyhgvs import utils
	from pygr import seqdb
	from pygr.seqdb import SequenceFileDB
except:
	pass

#---------------------------------
## Function and Class Definitions 
#--------------------------------
def ddd_prod_connect_and_fetch(sql_statement, usr_settings_dict):
	"""Connects to ddd_prod and executes sql statement.If this fails, the script will exit."""
	try:
		conxn = psycopg2.connect(dbname=usr_settings_dict['ddd_prod_dbname'], user=usr_settings_dict['ddd_prod_username'], host=usr_settings_dict['ddd_prod_host'], port=usr_settings_dict['ddd_prod_port'], password=usr_settings_dict['ddd_prod_user_password'])
		cursr = conxn.cursor()
		cursr.execute(sql_statement)
		db_out = cursr.fetchall()
		conxn.close()
		return db_out
	except:
		sys.exit('Problem retrieving data from ddd_prod database.')


def generate_sql_II_statement(ID):
	"""Generate an sql statement for a given id."""
	return "select tmp_path from dataset where person_stable_id = '{}';".format(ID)


def calculator_gene_name(gene_notation, user_settings_dict):
	"""This function is executed if a gene name is given."""
	sql_III_statement = "select chr, chr_start, chr_end from dd_gene_detail where name = '{}';".format(gene_notation)
	db_result = ddd_prod_connect_and_fetch(sql_III_statement, user_settings_dict)
	if (db_result):
		chrom, start, stop = db_result[0]
		return ('chr:{}\tstart:{}\tstop:{}'.format(chrom, start, stop))
	else:
		return ('chr:NA\tstart:NA\tstop:NA')

"""
def calculator_hgvs_notation(user_hgvs, human_reference):
	## The old HGVS function.
	try:
		genome = seqdb.SequenceFileDB(human_reference)
		with open(gui_backend_path + 'genes.refGene') as infile:
			transcripts = utils.read_transcripts(infile)
		def get_transcript(name):
			return transcripts.get(name)
		chrom, offset, ref, alt = parse_hgvs_name(user_hgvs, genome, get_transcript=get_transcript)
		get_chr = re.search('(\d+)', chrom)
		return ('chr:{}\tstart:{}\tstop:{}'.format(get_chr.group(1), offset, offset))
	except:
		return ('chr:Error\tstart:Error\tstop:Error')
"""

def get_newest_vcf(db_dir_content):
	"""From the database fetch output, get newest VCF according to time of creation."""
	db_out = []; result = []
	for i in db_dir_content:
		db_out.append(i[0]) ## tuple-form result
	for x in db_out:
		if re.search('./vcfs/.', x):
			try:
				result.append((os.path.getctime(x), x)) ## tuple of VCF and its time
			except:
				pass
	result.sort(key=lambda y: y[0]) ## sort according to time
	return result[0][1] ## take the VCF of the latest time



def tabix_vcf(vcf_file, in_chr, in_start, in_stop):
	"""A generator to get records in a VCF given a location."""
	chrom = str(in_chr); start = int(in_start); stop = int(in_stop)
	try:
		vcf_tb = tabix.open(vcf_file)
		for rec in vcf_tb.query(chrom, start, stop):
			yield rec
	except:
		return


class Record:
	"""A class for VCF data."""
	def __init__(self, record, cq_validation_list, max_af_cutoff, max_af_value):
		self.variant_line = record
		self.info = record[7] ## The INFO field.
		self.vcf_info_field_dict()
		self.cq_validation_list = cq_validation_list
		self.max_af_value = max_af_value
		try:
			self.max_af_cutoff = float(max_af_cutoff)
		except:
			self.max_af_cutoff = 'ignore'
	def get_variant_line(self):
		"""Return the variant line as a tab-separated string."""
		return '\t'.join(self.variant_line)
	def vcf_info_field_dict(self):
		"""Parsing the INFO field."""
		self.info_field_dict = {}
		## Assumes INFO field line is sepqrated by ';'
		info_field_items = re.split(';', self.info)
		for item in info_field_items:
			try:
				m = re.search('(\S+)=(\S+)', item)
				self.info_field_dict[m.group(1)] = m.group(2)
			except:
				pass ## no variable=value
		return None
	def validate_cq(self):
		"""Returns True if any CQ element in the VCF line is found in the user-defined CQ input."""
		try:
			my_cq = self.info_field_dict['CQ']
		except:
			my_cq = None
		if (my_cq):
			## Assumes CQ are separated by ',' or '|'
			cq = re.split('[,|]', my_cq)
			if (any(map(lambda x: x in self.cq_validation_list, cq))):
				return True
		return False
	def validate_max_af_cutoff(self):
		"""Checks that MAX_AF values in the VCF line are all less than a user-defined cutoff if provided."""
		if self.max_af_cutoff == 'ignore': ## no user-defined max_af
			return True
		elif ('MAX_AF' not in self.info_field_dict.keys()): ## no MAX_AF in the INFO field
			return True
		else:
			try:
				my_max_af = self.info_field_dict['MAX_AF']
				if (my_max_af):
					## Assumes max_af is separated by a ',' or '|'
					max_af = list(map(lambda x: float(x), re.split('[,|]', my_max_af))) ## works if all are floats
					if (all([val < self.max_af_cutoff for val in max_af])):
						return True ## all are less than cutoff
					else:
						return False ## not all are less than cutoff
				else:
					return True ## MAX_AF is empty
			except:
				return False ## a charactare is found in the MAX_AF list
	def validate_max_af_value(self):
		"""Checks that MAX_AF value in the VCF line is equal a user-defined value if provided."""
		if self.max_af_value == 'ignore': ## no user-defined max_af
			return True
		elif ('MAX_AF' not in self.info_field_dict.keys()): ## no MAX_AF in the INFO field
			return False
		else:
			try:
				my_max_af = self.info_field_dict['MAX_AF']
				if (my_max_af):
					## Assumes max_af is separated by a ',' or '|'
					max_af = re.split('[,|]', my_max_af)
					if (all([val == self.max_af_value for val in max_af])): ## if elements MAX_AF in the VCF line are equal to the user-defined value
						return True ## all MAX_AF elements in the VCF line are equal to the user-defined value
					else:
						return False ## not all MAX_AF elements in the VCF line are equal to the user-defined value
				else:
					return False ## MAX_AF is empty
			except:
				return False ## any error



def prepare_cq(cq_in=None):
	if (cq_in):
		vep_cq_list = re.split(',', cq_in)
		return vep_cq_list
	else:
		internal_cq_list = 'transcript_ablation,splice_donor_variant,splice_acceptor_variant,stop_gained,frameshift_variant,stop_lost,inframe_insertion,inframe_deletion,missense_variant,transcript_amplification,splice_region_variant,incomplete_terminal_codon_variant,synonymous_variant,stop_retained_variant,mature_miRNA_variant,5_prime_UTR_variant,3_prime_UTR_variant,intron_variant,NMD_transcript_variant,non_coding_exon_variant,nc_transcript_variant,upstream_gene_variant,downstream_gene_variant,TFBS_ablation,TFBS_amplification,TF_binding_site_variant,regulatory_region_variant,regulatory_region_ablation,regulatory_region_amplification,feature_elongation,feature_truncation,intergenic_variant'
		vep_cq_list = re.split(',', internal_cq_list)
		return vep_cq_list


def id_checker(id_in):
	if re.search('^\d+', id_in):
		return 'decipher'
	elif re.search('^DDDP', id_in):
		return 'person'
	else:
		return 'unknown'


def id_in_ddd_prod(id_in, usr_settings_dict):
	"""Get the individual IDs by trying 2 relations in ddd_prod."""
	if (id_checker(id_in) == 'decipher'): ## if the user-defined ID is a decipher ID
		sql_I_statement = "select proband_stable_id,mother_stable_id,father_stable_id from trio where decipher_id = '{}';".format(id_in)
		sql_II_statement = "select proband_stable_id, mother_stable_id, father_stable_id from families where decipher_id = '{}';".format(id_in)
		child_person_id = '';mum_person_id = ''; dad_person_id = ''
		try: ## trying SQL statement 1
			ids = ddd_prod_connect_and_fetch(sql_I_statement, usr_settings_dict)
			child_person_id = ids[0][0]
			mum_person_id = ids[0][1]
			dad_person_id = ids[0][2]
		except:
			print 'trio table didn\'t work for this decipher id.'
		if (all(list(map(lambda x: not x, [child_person_id, mum_person_id, dad_person_id])))): ## all variables are still empty
			try: ## trying SQL statement 2
				ids = ddd_prod_connect_and_fetch(sql_II_statement, usr_settings_dict)
				child_person_id = ids[0][0]
				mum_person_id = ids[0][1]
				dad_person_id = ids[0][2]
			except:
				print 'families table didn\'t work for this decipher id.'
		return (child_person_id, mum_person_id, dad_person_id)
	elif (id_checker(id_in) == 'person'): ## if the user-defined ID is a person stable ID
		sql_I_statement = "select proband_stable_id,mother_stable_id,father_stable_id from trio where proband_stable_id = '{}';".format(id_in)
		sql_II_statement = "select proband_stable_id, mother_stable_id, father_stable_id from families where proband_stable_id = '{}';".format(id_in)
		child_person_id = '';mum_person_id = ''; dad_person_id = ''
		try: ## trying SQL statement 1
			ids = ddd_prod_connect_and_fetch(sql_I_statement, usr_settings_dict)
			child_person_id = ids[0][0]
			mum_person_id = ids[0][1]
			dad_person_id = ids[0][2]
		except:
			print 'trio table didn\'t work for this person stable id.'
		if (all(list(map(lambda x: not x, [child_person_id, mum_person_id, dad_person_id])))): ## all variables are still empty
			try: ## trying SQL statement 2
				ids = ddd_prod_connect_and_fetch(sql_II_statement, usr_settings_dict)
				child_person_id = ids[0][0]
				mum_person_id = ids[0][1]
				dad_person_id = ids[0][2]
			except:
				print 'families table didn\'t work for this person stable id.'
		return (child_person_id, mum_person_id, dad_person_id)
	

def get_indiv_vcf_path(indiv_person_stable_id, params=''):
	"""Get the newest VCF path of a person stable ID."""
	indiv_vcf_path = ''
	try:
		indiv_vcf_path = get_newest_vcf(ddd_prod_connect_and_fetch(generate_sql_II_statement(indiv_person_stable_id), params))
		return indiv_vcf_path
	except:
		return indiv_vcf_path



def get_indiv_variants(person_id, person_vcf_path, CHR, START, STOP, cq_definitions, max_af_cutoff, max_af_value):
	"""Extracting the variants with tabix."""
	res = []
	if (os.access(person_vcf_path, os.F_OK) and os.access(person_vcf_path, os.R_OK)):
		vcf_generator = tabix_vcf(person_vcf_path, CHR, START, STOP)
		condition = True
		while (condition):
			my_rec = next(vcf_generator, False)
			if (my_rec):
				obj = Record(my_rec, cq_definitions, max_af_cutoff, max_af_value)
				if (obj.validate_cq() and obj.validate_max_af_cutoff() and obj.validate_max_af_value()):
					res.append('{}\t{}\n'.format(person_id, obj.get_variant_line()))
			else:
				condition = my_rec
		return res
	else:
		return res


