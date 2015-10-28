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
##				 This script creates a perl script called current_run.pl that is executed on the server.
##				 It takes the user-defined parameters and puts them in the current_run.pl template.

import os
import argparse

## the command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('--o', type=str, default=None, help='The output path of current_run.pl.')
parser.add_argument('--remote_dir', type=str, default=None, help='The absolute path of the GUI.')
parser.add_argument('--hgvs_transcript', type=str, default=None, help='The HGVS transcript name.')
parser.add_argument('--hgvs_term', type=str, default=None, help='The complete HGVS term.')

## prepare argument variables
args = parser.parse_args()
out = args.o
backend_dir = args.remote_dir
hgvs_transcript = args.hgvs_transcript
hgvs_term = args.hgvs_term

## the template of current_run.pl in the form of a string
template = r"""

use strict;
use warnings;
use Getopt::Long;
use Vcf;
use Data::Dumper;
use HTTP::Tiny;
use JSON; 


my $remote_dir = '{builder_backend_dir}';

my $http = HTTP::Tiny->new();

my $user_transcript = '{builder_hgvs_transcript}';
my $user_hgvs_term = '{builder_hgvs_term}';

my $server = 'http://grch37.rest.ensembl.org';
my $ext = '/map/cdna/'.$user_transcript.'/100..300?';
my $response = $http->get($server.$ext, {{
  headers => {{ 'Content-type' => 'application/json' }}
}});

my $chr = '';
my @result;

if(length $response->{{content}}) {{
  my $hash = decode_json($response->{{content}});
  $chr = $hash->{{mappings}}[0]->{{'seq_region_name'}};
}}


my $vcf_file = '/lustre/scratch113/projects/ddd/resources/ddd_data_releases/2015-04-13/ANNOTATE_VEP/vep_out.'.$chr.'.vcf.gz';

open OUT, '>', $remote_dir . 'hgvs_coords.tsv';

my $vcf = Vcf->new( file => $vcf_file );
$vcf->parse_header();


while (my $var = $vcf->next_data_hash()) {{
	my $res = '';
	$res .= $var->{{CHROM}} . "\t";
	$res .= $var->{{POS}};
	
	my @vcf_transcripts;

	my @CSQ = split('\|', $var->{{INFO}}{{CSQ}});
	foreach (@CSQ) {{
				chomp;
				if (m/^ENST/ and index($_, '>') != -1 and index($_ , ':') != -1) {{
												push @vcf_transcripts, $_;
											}}
			}}
	my @catch_hgvs = grep {{$_ eq $user_hgvs_term}} @vcf_transcripts;
	if (scalar @catch_hgvs > 0) {{
				print OUT "$res\n";
			}}
}}

close OUT;


""".format(builder_backend_dir=backend_dir, builder_hgvs_transcript=hgvs_transcript, builder_hgvs_term=hgvs_term)

## write current_run.pl
with open(out, 'w') as outfile:
	outfile.write(template)

