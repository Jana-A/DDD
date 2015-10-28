from Tkinter import *
import sys
import ttk
import os
import re
import time
import subprocess
from subprocess import PIPE
import json
import threading
import multiprocessing
import PIL
from PIL import Image, ImageTk
from tkFileDialog import askopenfilenames
import tkMessageBox
from result_widget_setups import *


def build_server_tester_expect_file(gui_path, temp_dump, user_info):
	"""This function is only used during the server connection step. It has timeout of 5 seconds."""
	expect_lines = r"""#!/usr/bin/expect
set timeout 5
spawn bash {dir_name}recent_runs/{local_dump}current_command
expect -re {{[Pp]assword}}
send "{passw}\n"
expect eof
""".format(dir_name=gui_path, local_dump=temp_dump, passw=user_info['server_user_password'])
	## save this as an expect script
	with open(gui_path+'recent_runs/'+temp_dump+'current_expect', 'w') as cmd:
		cmd.write(expect_lines)


def the_quiting_callback(direct_ssh_mode, server_connect_check, master, user_info, gui_path, backend_dir_name):
	"""This function will delete the backend and frontend directories created for the purpose of storing temporary files."""
	if tkMessageBox.askokcancel('Quit', 'Do you want to quit?'):
		if (server_connect_check):
			try:
				clear_backend_dir(direct_ssh_mode, user_info, gui_path, backend_dir_name)
			except:
				pass
		try:
			os.system('rm -r {}'.format(gui_path+'recent_runs/'+backend_dir_name))
		except:
			pass
		master.destroy()


def clear_backend_dir(direct_ssh_mode, var_user_settings, var_gui_abs_path, var_backend_dir):
	"""Removes the backend temporary directory if it exists."""
	try:
		if (not direct_ssh_mode):
			build_server_tester_expect_file(var_gui_abs_path, var_backend_dir, var_user_settings)
		with open(var_gui_abs_path+'recent_runs/'+var_backend_dir+'server_command', 'w') as cmd:
			cmd.write('rm -r {}'.format(var_backend_dir))
		with open(var_gui_abs_path+'recent_runs/'+var_backend_dir+'current_command', 'w') as cmd:
			cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=var_gui_abs_path+'recent_runs/'+var_backend_dir+'server_command', user=var_user_settings['server_username'], server=var_user_settings['server_name'])]))
		if (direct_ssh_mode):
			os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=var_gui_abs_path, local_dump=var_backend_dir))
		else:
			os.system('expect {a}recent_runs/{b}current_expect'.format(a=var_gui_abs_path, b=var_backend_dir))
	except:
		pass


def build_expect_file(gui_path, temp_dump, user_info):
	"""Creates the expect script that spawns the current_command file."""
	expect_lines = r"""#!/usr/bin/expect
set timeout -1
spawn bash {dir_name}recent_runs/{local_dump}current_command
expect -re {{[Pp]assword}}
send "{passw}\n"
expect "Permission denied, please try again."
exit 1
expect eof
""".format(dir_name=gui_path, local_dump=temp_dump, passw=user_info['server_user_password'])
	with open(gui_path+'recent_runs/'+temp_dump+'current_expect', 'w') as cmd:
		cmd.write(expect_lines)


def create_temp_backend_dir(direct_ssh_mode, gui_path, var_backend_dir, user_info):
	"""Creates the temporary backend directory."""
	if (not direct_ssh_mode):
		build_expect_file(gui_path, var_backend_dir, user_info)
	server_cmd = r"""#!/usr/bin/env bash
mkdir ~/{backend_dir_name}
""".format(backend_dir_name=var_backend_dir)
	with open(gui_path+'recent_runs/'+var_backend_dir+'server_command', 'w') as cmd:
		cmd.write(server_cmd)
	with open(gui_path+'recent_runs/'+var_backend_dir+'current_command', 'w') as cmd:
		cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=gui_path+'recent_runs/'+var_backend_dir+'server_command', user=user_info['server_username'], server=user_info['server_name'])]))
	if (direct_ssh_mode):
		os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=gui_path, local_dump=var_backend_dir))
	else:
		os.system('expect {a}recent_runs/{b}current_expect'.format(a=gui_path, b=var_backend_dir))
	time.sleep(1)



def read_server_user_file(server_path):
	"""Reads the dot server file according to a format described in the documentation pages."""
	temp_dict = {}
	if (os.access(server_path, os.R_OK) and os.access(server_path, os.F_OK)):
		with open(server_path, 'r') as server_user_file:
			server_user_file = server_user_file.readlines()
			try:
				server_user = list(map(lambda x: re.sub('(\r\n|\r|\n)','',x), server_user_file))
				server_user = list(map(lambda x: re.sub('\s+','',x), server_user))
				test_char = list(map(lambda x: not x, server_user))
				if (len(test_char) == 3 and True not in test_char):
					temp_dict['server_name'] = server_user[0]
					temp_dict['server_username'] = server_user[1]
					temp_dict['server_user_password'] = server_user[2]
					return temp_dict
				elif (len(test_char) == 2 and True not in test_char):
					temp_dict['server_name'] = server_user[0]
					temp_dict['server_username'] = server_user[1]
					return temp_dict
			except:
				return temp_dict


def read_igv_user_file(igv_path):
	"""Reads the dot igv file according to a format described in the documentation pages."""
	temp_dict = {}
	if (os.access(igv_path, os.R_OK) and os.access(igv_path, os.F_OK)):
		with open(igv_path, 'r') as igv_user_file:
			igv_user_file = igv_user_file.readlines()
			try:
				igv_user = list(map(lambda x: re.sub('(\r\n|\r|\n)','',x), igv_user_file))
				igv_user = list(map(lambda x: re.sub('\s+','',x), igv_user))
				temp_dict['igv_username'] = igv_user[0]
				temp_dict['igv_user_password'] = igv_user[1]
				return temp_dict
			except:
				return temp_dict

		
def read_ddd_prod_user_file(ddd_prod_path):
	"""Reads the dot ddd_prod file according to a format described in the documentation pages."""
	temp_dict = {}
	if (os.access(ddd_prod_path, os.R_OK) and os.access(ddd_prod_path, os.F_OK)):
		with open(ddd_prod_path, 'r') as ddd_prod_user_file:
			ddd_prod_user_file = ddd_prod_user_file.readlines()
			try:
				ddd_prod_user = list(map(lambda x: re.sub('(\r\n|\r|\n)','',x), ddd_prod_user_file))[0]
				for i in ddd_prod_user.split(';'):
					temp = i.split(':')
					temp_dict[temp[0]] = temp[1]
				return temp_dict
			except:
				return temp_dict


class prepare_result_tabs_igv_included:
	"""Create result tabs with an igv tab and populate."""
	def __init__(self, **kwargs):
		## extracting the arguments
		self.direct_ssh_mode = kwargs['direct_ssh_mode']
		self.previous_frame = kwargs['previous_frame']
		self.present_frame = kwargs['present_frame']
		self.past_frame = kwargs['past_frame']
		self.query_info = kwargs['query_info']
		self.var_backend_dir = kwargs['var_backend_dir']
		self.var_gui_abs_path = kwargs['gui_abs_path']
		self.var_user_settings = kwargs['user_settings_var']
		## hide previous and past frames, show present frame
		self.previous_frame.pack_forget()
		self.past_frame.pack_forget()
		self.present_frame.pack(fill=BOTH, expand=TRUE)
		## -----------------------------------------------------------------------
		## create the Back and Next buttons of this frame and bind them to methods
		## -----------------------------------------------------------------------
		self.window_navigation = Frame(self.present_frame, bg='#E0E0E0')
		self.window_navigation.pack(fill=X, expand=False, pady=5)
		self.window_navigation.columnconfigure(0, weight=1)
		self.window_navigation.columnconfigure(1, weight=1)
		self.window_navigation.rowconfigure(0, weight=1)
		##
		self.previous_window = Label(self.window_navigation, text='Back', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.previous_window.grid(row=0, column=0, sticky=E)
		self.previous_window.bind("<Button-1>", self.backward)
		self.previous_window.bind("<Leave>", lambda event: self.previous_window.configure(relief=GROOVE))
		self.previous_window.bind("<Enter>", lambda event: self.previous_window.configure(cursor='hand', relief=RAISED))
		##
		self.next_window = Label(self.window_navigation, text='Next', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.next_window.grid(row=0, column=1, sticky=W)
		self.next_window.configure(state='disabled')
		## -----------------------------------------------------------------------
		## create the notebook which displays data in tabs
		self.tabs = ttk.Notebook(self.present_frame)
		## initialize the frames of every tab
		self.query_info_tab = Frame(self.tabs, bg='#E0E0E0')
		self.trio_variants_tab = Frame(self.tabs, bg='#E0E0E0')
		self.igv_tab = Frame(self.tabs, bg='#E0E0E0')
		## add the tab titles
		self.tabs.add(self.query_info_tab, text='Query Info')
		self.tabs.add(self.trio_variants_tab, text='Variants')
		self.tabs.add(self.igv_tab, text='IGV')
		self.tabs.pack(fill=BOTH, expand=True)
		## populate the tabs with content/data
		self.query_info_obj = populate_query_info_tab(self.query_info_tab, self.query_info)
		self.igv_obj = populate_trio_igv_tab(direct_ssh_mode=self.direct_ssh_mode,query_info=self.query_info,frame=self.igv_tab, var_backend_dir=self.var_backend_dir,gui_abs_path=self.var_gui_abs_path,user_settings_var=self.var_user_settings)
		self.trio_var_obj = populate_trio_variants_tab(self.trio_variants_tab, self.var_gui_abs_path, self.var_backend_dir)
		self.trio_var_obj.prepare_varaints_for_display()
	def backward(self, event):
		## this method belongs to the Back label
		self.present_frame.pack_forget()
		self.previous_frame.pack(fill=BOTH, expand=TRUE)



class prepare_result_tabs_cohort:
	"""Create result tabs for the cohort variants and populate."""
	def __init__(self, **kwargs):
		## extracting the arguments
		self.previous_frame = kwargs['previous_frame']
		self.present_frame = kwargs['present_frame']
		self.past_frame = kwargs['past_frame']
		self.query_info = kwargs['query_info']
		self.var_gui_abs_path = kwargs['gui_abs_path']
		self.var_backend_dir = kwargs['backend_dir']
		## hide previous and past frames, show present frame
		self.previous_frame.pack_forget()
		self.past_frame.pack_forget()
		self.present_frame.pack(fill=BOTH, expand=TRUE)
		## -----------------------------------------------------------------------
		## create the Back and Next buttons of this frame and bind them to methods
		## -----------------------------------------------------------------------
		self.window_navigation = Frame(self.present_frame, bg='#E0E0E0')
		self.window_navigation.pack(fill=X, expand=False, pady=5)
		self.window_navigation.columnconfigure(0, weight=1)
		self.window_navigation.columnconfigure(1, weight=1)
		self.window_navigation.rowconfigure(0, weight=1)
		##
		self.previous_window = Label(self.window_navigation, text='Back', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.previous_window.grid(row=0, column=0, sticky=E)
		self.previous_window.bind("<Button-1>", self.backward)
		self.previous_window.bind("<Leave>", lambda event: self.previous_window.configure(relief=GROOVE))
		self.previous_window.bind("<Enter>", lambda event: self.previous_window.configure(cursor='hand', relief=RAISED))
		##
		self.next_window = Label(self.window_navigation, text='Next', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.next_window.grid(row=0, column=1, sticky=W)
		self.next_window.configure(state='disabled')
		## -----------------------------------------------------------------------
		## create the notebook which displays data in tabs
		self.tabs = ttk.Notebook(self.present_frame)
		## initialize the frames of every tab
		self.query_info_tab = Frame(self.tabs, bg='#E0E0E0')
		self.cohort_variants_tab = Frame(self.tabs, bg='#E0E0E0')
		## add the tab titles
		self.tabs.add(self.query_info_tab, text='Query Info')
		self.tabs.add(self.cohort_variants_tab, text='Variants')
		self.tabs.pack(fill=BOTH, expand=True)
		## populate the tabs with content/data
		self.query_info_obj = populate_query_info_tab(self.query_info_tab, self.query_info)
		self.cohort_obj = populate_cohort_tab(self.cohort_variants_tab, self.var_gui_abs_path, self.var_backend_dir)
		self.cohort_obj.prepare_varaints_for_display()
	def backward(self, event):
		## this method belongs to the Back label
		self.present_frame.pack_forget()
		self.previous_frame.pack(fill=BOTH, expand=TRUE)



class prepare_result_tabs_igv_excluded:
	"""Create result tabs without an igv tab and populate."""
	def __init__(self, **kwargs):
		## extracting the arguments
		self.previous_frame = kwargs['previous_frame']
		self.present_frame = kwargs['present_frame']
		self.past_frame = kwargs['past_frame']
		self.query_info = kwargs['query_info']
		self.var_gui_abs_path = kwargs['gui_abs_path']
		self.var_backend_dir = kwargs['backend_dir']
		## hide previous and past frames, show present frame
		self.previous_frame.pack_forget()
		self.past_frame.pack_forget()
		self.present_frame.pack(fill=BOTH, expand=TRUE)
		## -----------------------------------------------------------------------
		## create the Back and Next buttons of this frame and bind them to methods
		## -----------------------------------------------------------------------
		self.window_navigation = Frame(self.present_frame, bg='#E0E0E0')
		self.window_navigation.pack(fill=X, expand=False, pady=5)
		self.window_navigation.columnconfigure(0, weight=1)
		self.window_navigation.columnconfigure(1, weight=1)
		self.window_navigation.rowconfigure(0, weight=1)
		##
		self.previous_window = Label(self.window_navigation, text='Back', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.previous_window.grid(row=0, column=0, sticky=E)
		self.previous_window.bind("<Button-1>", self.backward)
		self.previous_window.bind("<Leave>", lambda event: self.previous_window.configure(relief=GROOVE))
		self.previous_window.bind("<Enter>", lambda event: self.previous_window.configure(cursor='hand', relief=RAISED))
		##
		self.next_window = Label(self.window_navigation, text='Next', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.next_window.grid(row=0, column=1, sticky=W)
		self.next_window.configure(state='disabled')
		## -----------------------------------------------------------------------
		## create the notebook which displays data in tabs
		self.tabs = ttk.Notebook(self.present_frame)
		## initialize the frames of every tab
		self.query_info_tab = Frame(self.tabs, bg='#E0E0E0')
		self.trio_variants_tab = Frame(self.tabs, bg='#E0E0E0')
		## add the tab titles
		self.tabs.add(self.query_info_tab, text='Query Info')
		self.tabs.add(self.trio_variants_tab, text='Variants')
		self.tabs.pack(fill=BOTH, expand=True)
		## populate the tabs with content/data
		self.query_info_obj = populate_query_info_tab(self.query_info_tab, self.query_info)
		self.trio_var_obj = populate_trio_variants_tab(self.trio_variants_tab, self.var_gui_abs_path, self.var_backend_dir)
		self.trio_var_obj.prepare_varaints_for_display()
	def backward(self, event):
		## this method belongs to the Back label
		self.present_frame.pack_forget()
		self.previous_frame.pack(fill=BOTH, expand=TRUE)



class startup_setup:
	"""Populate the startup frame."""
	def __init__(self, **kwargs):
		## extracting the arguments
		self.startup_frame_var = kwargs['startup_frame_var']
		self.next_frame = kwargs['next_frame']
		self.future_frame = kwargs['future_frame']
		self.var_backend_dir = kwargs['var_backend_dir']
		self.var_gui_abs_path = kwargs['var_gui_abs_path']
		self.server_file_check = kwargs['check_server']
		self.igv_file_check = kwargs['check_igv']
		self.ddd_prod_check = kwargs['check_ddd_prod']
		self.user_logins = kwargs['var_user_settings']
		self.notifications = kwargs['prepared_notifications']
		## show startup frame
		self.startup_frame_var.pack(fill=BOTH, expand=TRUE)
		## -----------------------------------------------------------------------
		## create the Back and Next buttons of this frame and bind them to methods
		## -----------------------------------------------------------------------
		self.window_navigation = Frame(self.startup_frame_var, bg='#E0E0E0')
		self.window_navigation.pack(fill=X, expand=False, pady=5)
		self.window_navigation.columnconfigure(0, weight=1)
		self.window_navigation.columnconfigure(1, weight=1)
		self.window_navigation.rowconfigure(0, weight=1)
		##
		self.previous_window = Label(self.window_navigation, text='Back', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.previous_window.grid(row=0, column=0, sticky=E)
		self.previous_window.configure(state='disabled')
		##
		self.next_window = Label(self.window_navigation, text='Next', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.next_window.grid(row=0, column=1, sticky=W)
		self.next_window.configure(state='disabled')
		## -----------------------------------------------------------------------
		## these 3 checks involve the dot files
		self.check1 = Label(self.startup_frame_var, text='{} Check 1: {}'.format(self.notifications[0][0], self.notifications[0][1]), anchor=NW, fg=self.notifications[0][2], relief=GROOVE, borderwidth=2, bg='#E0E0E0')
		self.check1.place(x=50, y=50)
		self.check2 = Label(self.startup_frame_var, text='{} Check 2: {}'.format(self.notifications[1][0], self.notifications[1][1]), anchor=NW, fg=self.notifications[1][2], relief=GROOVE, borderwidth=2, bg='#E0E0E0')
		self.check2.place(x=50, y=80)
		self.check3 = Label(self.startup_frame_var, text='{} Check 3: {}'.format(self.notifications[2][0], self.notifications[2][1]), anchor=NW, fg=self.notifications[2][2], relief=GROOVE, borderwidth=2, bg='#E0E0E0')
		self.check3.place(x=50, y=110)
		## create and place the Instructions paragraph
		self.instructions_frame = Frame(self.startup_frame_var, bg='#E0E0E0')
		self.instructions_frame.place(x=50, y=160)
		usage_line1 = 'To get started use the <Start> in the toolbar above. Choose to query by genomic coordinates, gene name or HGVS term. You can find variants of a child ID (decipher ID or person stable ID) or use VCFs from the entire cohort to find variants.\n\nThe sidebar to the left contains an option to find the frequency of a variant in the cohort VCFs. Also the ability to calculate a genomic coordinates given a gene name or an HGVS term.'
		self.title = Label(self.instructions_frame, text='\nInstructions:', font='Aerial 18 bold', anchor=NW, bg='#E0E0E0', wraplength=650)
		self.title.pack(anchor=W)
		self.line1 = Label(self.instructions_frame, text=usage_line1, anchor=NW, bg='#E0E0E0', wraplength=650, justify=LEFT)
		self.line1.pack(anchor=W) 
	def forward(self, event):
		## this method belongs to the Next label
		self.future_frame.pack_forget()
		self.startup_frame_var.pack_forget()
		self.next_frame.pack(fill=BOTH, expand=TRUE)



class options_sidebar_setup:
	"""Populate the options side bar."""
	def __init__(self, **kwargs):
		## extracting the arguments
		self.direct_ssh_mode = kwargs['direct_ssh_mode']
		self.master = kwargs['master']
		self.server_file_check = kwargs['check_server']
		self.ddd_prod_check = kwargs['check_ddd_prod']
		self.sidebar_frame_var = kwargs['side_frame_var']
		self.var_gui_abs_path = kwargs['var_gui_abs_path']
		self.var_backend_dir = kwargs['var_backend_dir']
		self.var_user_settings = kwargs['var_user_settings']
		## create the options box
		self.options_frame = Frame(self.sidebar_frame_var)
		self.options_title = Label(self.options_frame, text='More options', background='#C8C8C8', font='Aerial 14 bold', relief=GROOVE, borderwidth=2)
		self.options_title.grid(row=0, column=0, sticky=(N,W,E,S))
		## create the variant frequency option
		self.option1 = Label(self.options_frame, text='Find variant frequency', justify=LEFT)
		self.option1.grid(row=1, column=0, sticky=(N,W,E,S))
		self.option1.bind("<Button-1>", self.popup_coords)
		self.option1.bind("<Leave>", lambda event: self.option1.configure(relief=FLAT))
		self.option1.bind("<Enter>", lambda event: self.option1.configure(cursor='hand', relief=RAISED))
		## this commented option may be implemented in the future
		#self.option2 = Label(self.options_frame, text='Variant statistics', justify=LEFT)
		#self.option2.grid(row=, column=0, sticky=(N,W,E,S))
		#self.option2.bind("<Button-1>", self.pass_function)
		#self.option2.bind("<Leave>", lambda event: self.option2.configure(relief=FLAT))
		#self.option2.bind("<Enter>", lambda event: self.option2.configure(cursor='hand', relief=RAISED))
		## create the quit option
		self.option3 = Label(self.options_frame, text='Quit', justify=LEFT)
		self.option3.grid(row=2, column=0, sticky=(N,W,E,S))
		self.option3.bind("<Button-1>", self.quit)
		self.option3.bind("<Leave>", lambda event: self.option3.configure(relief=FLAT))
		self.option3.bind("<Enter>", lambda event: self.option3.configure(cursor='hand', relief=RAISED))
		## create the help label "?" found at the bottom right of the options box
		self.help = Label(self.options_frame, fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help.grid(row=3, column=0, sticky=E)
		self.help.bind("<Button-1>", self.help_popup)
		self.help.bind("<Leave>", lambda event: self.help.configure(relief=GROOVE))
		self.help.bind("<Enter>", lambda event: self.help.configure(cursor='hand', relief=RAISED))
	def popup_coords(self, event):
		## this is the input popup for the variant frequency option
		self.top = Toplevel(self.sidebar_frame_var)
		self.top.geometry("350x350+400+50") ## setting the dimension and location of the popup
		## create the popup content
		Label(self.top, text="Chromosome").pack()
		self.chrom_top = Entry(self.top)
		self.chrom_top.pack()
		Label(self.top, text="Position").pack()
		self.pos_top = Entry(self.top)
		self.pos_top.pack()
		top_btn = Button(self.top, text="Go", command=self.go)
		top_btn.pack()
		## if the global variables that check the dot server/ddd_prod files are false or None, the Go button of the popup is disabled.
		if (not self.server_file_check or not self.ddd_prod_check):
			top_btn.configure(state='disabled')
	def go(self):
		## first, remove any current scripts in the changeable directory
		try:
			local_path = self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir
			for file_found in os.listdir(local_path):
				os.remove(local_path + file_found)
		except:
			pass
		## get the entries of the user from the toplevel popup
		chrom_top = self.chrom_top.get()
		pos_top = self.pos_top.get()
		## prepare the expect file
		if (not self.direct_ssh_mode):
			build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
		string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
		## build the python script to be executed on the backend side
		os.system('python {a}local_scripts/cohort_frequency_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --chrom {f} --pos {g} --string_user_settings_dict \'{h}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=chrom_top, g=pos_top, h=string_user_settings))
		## populate the current_command file
		with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
			cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir=self.var_backend_dir)]))
		## execute the expect script
		if (self.direct_ssh_mode):
			os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
		else:
			os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
		## the bash commands to run on the server
		server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {file_name}
{command}
""".format(file_name=self.var_backend_dir+'current_run.py', command='python {file_name}'.format(file_name=self.var_backend_dir+'current_run.py'))
		## the server_command file
		with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
			cmd.write(server_cmd)
		##
		with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
			cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
		##
		if (self.direct_ssh_mode):
			os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
		else:
			os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
		## build the followup python script to be executed on the backend side
		os.system('python {a}local_scripts/frequency_followup_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e}'.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir))
		##
		with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
			cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir=self.var_backend_dir)]))
		##
		if (self.direct_ssh_mode):
			os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
		else:
			os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
		##
		server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {file_name}
{command}
""".format(file_name='{}current_run.py'.format(self.var_backend_dir), command='python {file_name}'.format(file_name='{}current_run.py'.format(self.var_backend_dir)))
		##
		with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
			cmd.write(server_cmd)
		##
		with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
			cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
		##
		if (self.direct_ssh_mode):
			os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
		else:
			os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
		##
		with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
			cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], file_name=self.var_backend_dir+'final_freq', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
		##
		if (self.direct_ssh_mode):
			os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
		else:
			os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
		##
		with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
			cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], file_name=self.var_backend_dir+'total_vcfs', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
		##
		if (self.direct_ssh_mode):
			os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
		else:
			os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
		## reading the server output files and displaying the variant frequency message
		try:
			frequency = {'variant_freq':'', 'cohort_vcfs':''}
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'final_freq', 'r') as freq:
				frequency['variant_freq'] = re.sub('\n', '', freq.read())
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'total_vcfs', 'r') as cohort:
				frequency['cohort_vcfs'] = re.sub('\n', '', cohort.read())
			frequency_msg = 'The variant appeared in the cohort :\n {} times in {} VCFs.'.format(frequency['variant_freq'], frequency['cohort_vcfs'])
			tkMessageBox.showinfo(title='Variant frequency in cohort', message=frequency_msg)
		except:
			frequency_msg = 'No Record.'
			tkMessageBox.showinfo(title='Variant frequency in cohort', message=frequency_msg)
		self.top.destroy()
	def quit(self, event):
		"""The quit option calls the global quit method."""
		the_quiting_callback(self.direct_ssh_mode, self.server_file_check, self.master, self.var_user_settings, self.var_gui_abs_path, self.var_backend_dir)
	def help_popup(self, event):
		"""Method to display the help content for this widget."""
		help_msg = '"Find variant frequency": find the number of times the variant occurs in the cohort VCFs. Using variant location, gene name or HGVS terminology.\n\n"Variant statistics": NA.\n'
		tkMessageBox.showinfo(title='Options', message=help_msg)
	def configure(self, event):
		"""This is triggered upon window resizing."""
		current_width, current_height = event.width, event.height
		options_frame_width = current_width*0.2*0.9 ## 20% of the window width and 90% of that (upper sidebar width)
		options_frame_height = current_height*0.9*0.2
		self.options_frame.place(x=0, y=0, width=int(options_frame_width), height=int(options_frame_height))
		self.options_frame.columnconfigure(0, weight=1)
		self.options_frame.rowconfigure(0, weight=1)
		self.options_frame.rowconfigure(1, weight=1)
		self.options_frame.rowconfigure(2, weight=1)
		self.options_frame.rowconfigure(3, weight=1)



class top_menu_setup:
	"""Create and position the top menu bar."""
	def __init__(self, **kwargs):
		## extracting the arguments
		self.direct_ssh_mode = kwargs['direct_ssh_mode']
		self.root_var = kwargs['root_var']
		self.container_frame_var = kwargs['container_frame_var']
		self.server_file_check = kwargs['check_server']
		self.igv_file_check = kwargs['check_igv']
		self.ddd_prod_check = kwargs['check_ddd_prod']
		self.startup_object_var = kwargs['startup_object_var']
		self.startup_frame_var = kwargs['startup_frame_var']
		self.user_input_frame_var = kwargs['user_input_frame_var']
		self.results_frame_var = kwargs['results_frame']
		self.backend_dir_var = kwargs['backend_dir']
		self.gui_abs_path_var = kwargs['gui_abs_path']
		self.user_settings_var = kwargs['user_info']
		## create and assign
		self.top_bar = Menu(self.root_var)
		self.root_var.config(menu=self.top_bar)
		##
		self.node_1 = Menu(self.top_bar)
		self.node_1.add_command(label='Child ID', command=lambda: genomic_coords_child_id(direct_ssh_mode=self.direct_ssh_mode, previous_frame_object=self.startup_object_var, previous_frame=self.startup_frame_var, present_frame=self.user_input_frame_var, next_frame=self.results_frame_var, var_backend_dir=self.backend_dir_var, check_server =self.server_file_check, check_igv=self.igv_file_check, check_ddd_prod = self.ddd_prod_check, var_gui_abs_path=self.gui_abs_path_var, var_user_settings=self.user_settings_var))
		self.node_1.add_separator()
		self.node_1.add_command(label='Cohort VCFs', command=lambda: genomic_coords_cohort(direct_ssh_mode=self.direct_ssh_mode, previous_frame_object=self.startup_object_var, previous_frame=self.startup_frame_var, present_frame=self.user_input_frame_var, next_frame=self.results_frame_var, var_backend_dir=self.backend_dir_var, check_server =self.server_file_check, check_ddd_prod = self.ddd_prod_check, var_gui_abs_path=self.gui_abs_path_var, var_user_settings=self.user_settings_var))
		self.node_1.add_separator()
		##
		self.node_2 = Menu(self.top_bar)
		self.node_2.add_command(label='Child ID', command=lambda: gene_name_child_id(direct_ssh_mode=self.direct_ssh_mode, previous_frame_object=self.startup_object_var, previous_frame=self.startup_frame_var, present_frame=self.user_input_frame_var, next_frame=self.results_frame_var, var_backend_dir=self.backend_dir_var, check_server =self.server_file_check, check_igv=self.igv_file_check, check_ddd_prod = self.ddd_prod_check, var_gui_abs_path=self.gui_abs_path_var, var_user_settings=self.user_settings_var))
		self.node_2.add_separator()
		self.node_2.add_command(label='Cohort VCFs', command=lambda: gene_name_cohort(direct_ssh_mode=self.direct_ssh_mode, previous_frame_object=self.startup_object_var, previous_frame=self.startup_frame_var, present_frame=self.user_input_frame_var, next_frame=self.results_frame_var, var_backend_dir=self.backend_dir_var, check_server =self.server_file_check, check_ddd_prod = self.ddd_prod_check, var_gui_abs_path=self.gui_abs_path_var, var_user_settings=self.user_settings_var))
		self.node_2.add_separator()
		##
		self.node_3 = Menu(self.top_bar)
		self.node_3.add_command(label='Child ID', command=lambda: hgvs_child_id(direct_ssh_mode=self.direct_ssh_mode, previous_frame_object=self.startup_object_var, previous_frame=self.startup_frame_var, present_frame=self.user_input_frame_var, next_frame=self.results_frame_var, var_backend_dir=self.backend_dir_var, check_server =self.server_file_check, check_igv=self.igv_file_check, check_ddd_prod = self.ddd_prod_check, var_gui_abs_path=self.gui_abs_path_var, var_user_settings=self.user_settings_var))
		self.node_3.add_separator()
		self.node_3.add_command(label='Cohort VCFs', command=lambda: hgvs_cohort(direct_ssh_mode=self.direct_ssh_mode, previous_frame_object=self.startup_object_var, previous_frame=self.startup_frame_var, present_frame=self.user_input_frame_var, next_frame=self.results_frame_var, var_backend_dir=self.backend_dir_var, var_gui_abs_path=self.gui_abs_path_var, check_server =self.server_file_check, check_ddd_prod = self.ddd_prod_check, var_user_settings=self.user_settings_var))
		self.node_3.add_separator()
		##
		self.submenu1 = Menu(self.top_bar)
		## nested menus
		self.top_bar.add_cascade(label='Start', menu=self.submenu1)
		self.submenu1.add_separator()
		self.submenu1.add_cascade(label='Genomic coordinates', menu=self.node_1)
		self.submenu1.add_separator()
		self.submenu1.add_cascade(label='Gene name', menu=self.node_2)
		self.submenu1.add_separator()
		self.submenu1.add_cascade(label='HGVS term', menu=self.node_3)
		self.submenu1.add_separator()
		##
		self.submenu2 = Menu(self.top_bar)
		self.top_bar.add_cascade(label='About', menu=self.submenu2)
		self.submenu2.add_separator()
		self.submenu2.add_command(label='Documentaion', command=lambda: self.documentation())
		self.submenu2.add_separator()
	def documentation(self):
		os.system('open {}documentation.pdf'.format(self.gui_abs_path_var))


class calculator_setup:
	"""Create and place calculator and its functionalities."""
	def __init__(self, **kwargs):
		## extracting the arguments
		self.direct_ssh_mode = kwargs['direct_ssh_mode']
		self.sidebar_frame_var = kwargs['side_frame_var']
		self.master = kwargs['master']
		self.server_file_check = kwargs['check_server']
		self.ddd_prod_check = kwargs['check_ddd_prod']
		self.var_backend_dir = kwargs['var_backend_dir']
		self.var_gui_abs_path = kwargs['var_gui_abs_path']
		self.var_user_settings = kwargs['var_user_settings']
		## create the calculator frame
		self.calculator_frame = Frame(self.sidebar_frame_var, relief=RIDGE, borderwidth=2)
		## the calculator widget title
		self.title = Label(self.calculator_frame, text='Genomic\ncoordinates\ncalculator', font='Aerial 14 bold', background='#C8C8C8')
		self.title.grid(row=0, columnspan=2, sticky=(N, W, E, S))
		## the labels and entries in the calculator
		self.gene_name_label = Label(self.calculator_frame, text='Gene name:')
		self.gene_name_label.grid(row=1, column=0, sticky=W, pady=10, padx=5)
		self.gene_name_entry = Entry(self.calculator_frame, width=8)
		self.gene_name_entry.grid(row=1, column=1, sticky=(N, W, E, S), pady=10, padx=5)
		self.or_label = Label(self.calculator_frame, text='or')
		self.or_label.grid(row=2, column=0, sticky=W, padx=2)
		self.hgvs_label = Label(self.calculator_frame, text='HGVS term:')
		self.hgvs_label.grid(row=3, column=0, sticky=W, pady=10, padx=5)
		self.hgvs_entry = Entry(self.calculator_frame, width=8)
		self.hgvs_entry.grid(row=3, column=1, sticky=(N, W, E, S), pady=10, padx=5)
		##
		self.human_ref_version_var = IntVar()
		self.human_ref_version_var.set('37')
		self.human_ref_version_37 = Radiobutton(self.calculator_frame, text='GRCh37', variable=self.human_ref_version_var, value = '37')
		self.human_ref_version_37.grid(row=4, column=0, sticky=W, pady=10, padx=5)
		## GRCh38 button reserved for future implementation
		self.human_ref_version_38 = Radiobutton(self.calculator_frame, text='GRCh38', state='disabled', variable='', value = '38')
		self.human_ref_version_38.grid(row=4, column=1, sticky=W, pady=10, padx=5)
		## create the refresh button that clears out the current calculator content
		self.refresh_button = Button(self.calculator_frame, text='Refresh', command=lambda: self.refresh(self.master))
		self.refresh_button.grid(row=5, column=0, sticky=E, pady=20)
		## create the Find button
		self.find_button = Button(self.calculator_frame, text='Find', command=self.calculate)
		self.find_button.grid(row=5, column=1, sticky=W, pady=20)
		## if the global variables that check the dot server/ddd_prod files are false or None, the Find button of the calculator is disabled.
		if (not self.server_file_check or not self.ddd_prod_check):
			self.find_button.configure(state='disabled')
		## create the labels and entries that will display the output of the Find button
		self.chr_var = StringVar()
		self.start_var = StringVar()
		self.stop_var = StringVar()
		self.chr_label = Label(self.calculator_frame, text='chromosome:')
		self.chr_label.grid(row=6, column=0, sticky=W, padx=5)
		self.chr_display = Label(self.calculator_frame, textvariable=self.chr_var)
		self.chr_display.grid(row=6, column=1, sticky=(N, W, E, S), padx=5)
		self.start_display = Label(self.calculator_frame, text='start:')
		self.start_display.grid(row=7, column=0, sticky=W, padx=5)
		self.start_display_output = Label(self.calculator_frame, textvariable=self.start_var)
		self.start_display_output.grid(row=7, column=1, sticky=(N, W, E, S), padx=5)
		self.stop_display = Label(self.calculator_frame, text='stop:')
		self.stop_display.grid(row=8, column=0, sticky=W, padx=5)
		self.stop_display_output = Label(self.calculator_frame, textvariable=self.stop_var)
		self.stop_display_output.grid(row=8, column=1, sticky=(N, W, E, S), padx=5)
		## create the help label "?" found at the bottom right of the calculator
		self.help = Label(self.calculator_frame, fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help.grid(row=9, column=1, sticky=E)
		self.help.bind("<Button-1>", self.help_popup)
		self.help.bind("<Leave>", lambda event: self.help.configure(relief=GROOVE))
		self.help.bind("<Enter>", lambda event: self.help.configure(cursor='hand', relief=RAISED))
		## give the columns equal weights upon expansion
		self.calculator_frame.columnconfigure(0, weight=1)
		self.calculator_frame.columnconfigure(1, weight=1)
	def configure(self, event):
		"""Is triggered upon window resizing."""
		current_width, current_height = event.width, event.height
		options_frame_width = current_width*0.2*0.9 ## 20% of the window width and 90% of that (upper sidebar width)
		options_frame_height = current_height*0.9*0.4
		self.calculator_frame.place(x=0, y=50+int(current_height*0.9*0.2), width=int(options_frame_width), height=380)
	def calculate(self):
		"""Is triggered when the Find button is clicked."""
		## remove current files in changeable directory
		try:
			local_path = self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir
			for file_found in os.listdir(local_path):
				os.remove(local_path+file_found)
		except:
			pass
		## build an expect file
		if (not self.direct_ssh_mode):
			build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
		## get the user input
		user_gene = re.sub('\n', '', self.gene_name_entry.get())
		user_hgvs = re.sub('\n', '', self.hgvs_entry.get())
		##
		if (user_gene):
			string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
			## build the source of the calculator script to be executed on the sever side
			os.system('python {a}local_scripts/gene_calculator_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --gene {f} --string_user_settings_dict \'{g}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=user_gene, g=string_user_settings))
			##
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
			##
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			##
			server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
			##
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
			##
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
			##
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			##
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='gene_calculator_out.json', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
			##
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			## reading the server output file
			gene_calculator_file_abs_path = self.var_gui_abs_path + 'recent_runs/'+self.var_backend_dir+'gene_calculator_out.json'
			gene_calculator_json = {}
			if (os.access(gene_calculator_file_abs_path, os.F_OK) and os.access(gene_calculator_file_abs_path, os.R_OK)):
				with open(gene_calculator_file_abs_path, 'r') as gene_calculator_json:
					gene_calculator_json = json.load(gene_calculator_json)
				## determine if there was an execution error on the server side
				if (gene_calculator_json['error_msgs'].encode('utf-8') == 'No_error'):
					try:
						regex_match = re.search('chr:(\S+)\tstart:(\S+)\tstop:(\S+)', gene_calculator_json['gene_calculator'].encode('utf-8'))
						chrom, start, stop = regex_match.group(1), regex_match.group(2), regex_match.group(3)
						self.chr_var.set(chrom)
						self.start_var.set(start)
						self.stop_var.set(stop)
					except:
						self.chr_var.set("NA")
						self.start_var.set("NA")
						self.stop_var.set("NA")
				else:						
					self.chr_var.set("NA")
					self.start_var.set("NA")
					self.stop_var.set("NA")
			else:
				self.chr_var.set("NA")
				self.start_var.set("NA")
				self.stop_var.set("NA")
		elif (user_hgvs):# in case there is an HGVS query
			is_an_ensemble_transcript = None
			is_a_refseq_transcript = None
			if (re.search('^(ENST\d+)', user_hgvs)):
				is_an_ensemble_transcript = True
				is_a_refseq_transcript = False
			elif (re.search('^[NX]', user_hgvs)):
				is_a_refseq_transcript = True
				is_an_ensemble_transcript = False
			## Ensemble case procedure:
			if (is_an_ensemble_transcript):
				## extract the transcript name
				regex_m = re.search('^(ENST\d+)', user_hgvs)
				user_transcript = regex_m.group(1)
				##
				if (not self.direct_ssh_mode):
					build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
				##
				os.system('python {a}local_scripts/hgvs_calculator_ensemble_source_builder.py --o {b}recent_runs/{c}current_run.pl --remote_dir {d} --hgvs_transcript \'{e}\' --hgvs_term \'{f}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_backend_dir, e=user_transcript, f=user_hgvs))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.pl', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.pl', command='perl {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.pl'))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='hgvs_coords.tsv', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				hgvs_calculator_file_abs_path = self.var_gui_abs_path + 'recent_runs/' + self.var_backend_dir + 'hgvs_coords.tsv'
				##
				if (os.access(hgvs_calculator_file_abs_path, os.F_OK) and os.access(hgvs_calculator_file_abs_path, os.R_OK)):
					with open(hgvs_calculator_file_abs_path, 'r') as hgvs_calculator_tsv:
						hgvs_calculator_tsv = hgvs_calculator_tsv.readlines()
					try:
						hgvs_calculator_tsv_line = re.sub('\n', '', hgvs_calculator_tsv[0])
						temp = hgvs_calculator_tsv_line.split('\t')
						chrom = temp[0]
						pos = temp[1]
						self.chr_var.set(str(chrom))
						self.start_var.set(str(pos))
						self.stop_var.set(str(pos))
					except:
						self.chr_var.set("NA")
						self.start_var.set("NA")
						self.stop_var.set("NA")
				else:
					self.chr_var.set("NA")
					self.start_var.set("NA")
					self.stop_var.set("NA")
			elif (is_a_refseq_transcript):# Refseq case procedure:
				## create expect file
				if (not self.direct_ssh_mode):
					build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
				##
				os.system('python {a}local_scripts/hgvs_calculator_refseq_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --hgvs \'{f}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=user_hgvs))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='hgvs_coords.tsv', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				hgvs_calculator_file_abs_path = self.var_gui_abs_path + 'recent_runs/' + self.var_backend_dir + 'hgvs_coords.tsv'
				##
				if (os.access(hgvs_calculator_file_abs_path, os.F_OK) and os.access(hgvs_calculator_file_abs_path, os.R_OK)):
					with open(hgvs_calculator_file_abs_path, 'r') as hgvs_calculator_tsv:
						hgvs_calculator_tsv = hgvs_calculator_tsv.readlines()
					try:
						hgvs_calculator_tsv_line = re.sub('\n', '', hgvs_calculator_tsv[0])
						temp = hgvs_calculator_tsv_line.split('\t')
						chrom = temp[0]
						pos = temp[1]
						self.chr_var.set(str(chrom))
						self.start_var.set(str(pos))
						self.stop_var.set(str(pos))
					except:
						self.chr_var.set("NA")
						self.start_var.set("NA")
						self.stop_var.set("NA")
				else:
					self.chr_var.set("NA")
					self.start_var.set("NA")
					self.stop_var.set("NA")
			else:
				self.chr_var.set('NA')
				self.start_var.set('NA')
				self.stop_var.set('NA')
	def refresh(self, master):
		"""Is triggered when the Refresh button is clicked."""
		self.gene_name_entry.delete(0, last='end')
		self.hgvs_entry.delete(0, last='end')
		self.human_ref_version_var.set('37')
		self.chr_var.set('')
		self.start_var.set('')
		self.stop_var.set('')
		master.focus()
	def help_popup(self, event):
		"""Method to display the help content for this widget."""
		help_msg = 'This is a calculator that finds the genomic coordinates of a gene or an HGVS term.\n\nFor the gene calculation, the coordinates (chromosome, start, stop) of the gene will be extracted from the ddd_gene_detail relation in the ddd_prod database.\n\nThe HGVS calculator can decipher Ensemble and Refseq transcripts. The Ensemble procedure is customized for the patients of the DDD project only.\nWhen an Ensemble term is entered, there will be a search conducted in the chromosome file of this term in the annotated VEP directory containing all variants per chromosome for all patients.\nThe Refseq HGVS calculator uses a module utilizing data found in a public repository.\n'
		tkMessageBox.showinfo(title='Coordinates calculator', message=help_msg)



class genomic_coords_child_id:
	"""Query by genomic coordinates and child ID."""
	LOF = ['transcript_ablation','splice_donor_variant','splice_acceptor_variant','stop_gained','frameshift_variant','stop_lost','start_lost','inframe_insertion','inframe_deletion','missense_variant','transcript_amplification','protein_altering_variant']
	def __init__(self, **kwargs):
		## extracting the arguments
		self.direct_ssh_mode = kwargs['direct_ssh_mode']
		self.previous_frame_object = kwargs['previous_frame_object']
		self.previous_frame = kwargs['previous_frame']
		self.present_frame = kwargs['present_frame']
		self.next_frame = kwargs['next_frame']
		self.var_backend_dir = kwargs['var_backend_dir']
		self.server_file_check = kwargs['check_server']
		self.igv_file_check = kwargs['check_igv']
		self.ddd_prod_check = kwargs['check_ddd_prod']
		self.var_gui_abs_path = kwargs['var_gui_abs_path']
		self.var_user_settings = kwargs['var_user_settings']
		## set up the title of the label frame
		self.present_frame['text'] = 'Query Input: Genomic Coordinates using a Child ID'
		## activate the Next button of the previous frame
		self.previous_frame_object.next_window.configure(state='active')
		self.previous_frame_object.next_window.bind("<Button-1>", self.previous_frame_object.forward)
		self.previous_frame_object.next_window.bind("<Leave>", lambda event: self.previous_frame_object.next_window.configure(relief=GROOVE))
		self.previous_frame_object.next_window.bind("<Enter>", lambda event: self.previous_frame_object.next_window.configure(cursor='hand', relief=RAISED))
		## hide the next and previous frames. Show the present frame
		self.next_frame.pack_forget()
		self.previous_frame.pack_forget()
		self.present_frame.pack(fill=BOTH, expand=TRUE)
		## destroy the current widgets occupying this frame (in case of a previous input layout)
		for widget in self.present_frame.winfo_children():
			widget.destroy()
		time.sleep(1)
		## the error collection variable
		self.error_collect = ''
		## setting up the scrollbars
		self.present_frame_y = Scrollbar(self.present_frame, orient=VERTICAL)
		self.present_frame_y.pack(fill=Y, side=RIGHT)
		self.present_frame_x = Scrollbar(self.present_frame, orient=HORIZONTAL)
		self.present_frame_x.pack(fill=X, side=BOTTOM)
		self.present_canvas = Canvas(self.present_frame, bg='#E0E0E0', highlightbackground='#E0E0E0', highlightcolor='#E0E0E0', yscrollcommand=self.present_frame_y.set, xscrollcommand=self.present_frame_x.set)
		self.present_canvas.pack(fill=BOTH, expand=True)
		self.present_canvas.configure(scrollregion=(0,0,1000,1000))
		self.present_frame_y.config(command=self.present_canvas.yview)
		self.present_frame_x.config(command=self.present_canvas.xview)
		self.widget_layer = Frame(self.present_canvas, bg='#E0E0E0')
		self.widget_layer.pack()
		self.present_canvas.create_window(0, 0, window=self.widget_layer, anchor='nw')
		## create the Back and Next buttons of this frame and bind them to methods
		self.window_navigation = Frame(self.widget_layer, bg='#E0E0E0')
		self.window_navigation.pack(fill=X, expand=False, pady=10, padx=100)
		self.window_navigation.columnconfigure(0, weight=1)
		self.window_navigation.columnconfigure(1, weight=1)
		self.window_navigation.rowconfigure(0, weight=1)
		#
		self.previous_window = Label(self.window_navigation, text='Back', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.previous_window.grid(row=0, column=0, sticky=E)
		self.previous_window.bind("<Button-1>", self.backward)
		self.previous_window.bind("<Leave>", lambda event: self.previous_window.configure(relief=GROOVE))
		self.previous_window.bind("<Enter>", lambda event: self.previous_window.configure(cursor='hand', relief=RAISED))
		#
		self.next_window = Label(self.window_navigation, text='Next', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.next_window.grid(row=0, column=1, sticky=W)
		self.next_window.configure(state='disabled')
		## creating the labels and entries in the input layout
		self.parameters = LabelFrame(self.widget_layer, text='Parameters', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.parameters.pack(fill=X, expand=False, pady=10, padx=100)
		self.parameters.columnconfigure(0, weight=1)
		self.parameters.columnconfigure(1, weight=1)
		self.parameters.columnconfigure(2, weight=1)
		self.parameters.columnconfigure(3, weight=1)
		self.parameters.rowconfigure(0, weight=1)
		self.parameters.rowconfigure(1, weight=1)
		self.parameters.rowconfigure(2, weight=1)
		self.parameters.rowconfigure(3, weight=1)
		self.child_id_label = Label(self.parameters, text='Child ID:', bg='#C8C8C8')
		self.child_id_entry = Entry(self.parameters, highlightbackground='#C8C8C8')
		self.child_id_label.grid(row=0, column=0, sticky=E)
		self.child_id_entry.grid(row=0, column=1, sticky=W)
		#
		self.chr_label = Label(self.parameters, text='Chromosome:', bg='#C8C8C8')
		self.chr_var = StringVar(self.parameters)
		self.chr_var.set('1')
		self.chrs = list(range(1,23))
		self.chrs.extend(['X', 'Y'])
		self.chr_menu = OptionMenu(self.parameters, self.chr_var, *self.chrs)
		self.chr_menu.config(bg='#C8C8C8')
		self.chr_label.grid(row=0, column=2, sticky=E)
		self.chr_menu.grid(row=0, column=3, sticky=W)
		#
		self.start_label = Label(self.parameters, text='Start:', bg='#C8C8C8')
		self.start_entry = Entry(self.parameters, highlightbackground='#C8C8C8')
		self.start_label.grid(row=1, column=0, sticky=E)
		self.start_entry.grid(row=1, column=1, sticky=W)
		#
		self.stop_label = Label(self.parameters, text='Stop:', bg='#C8C8C8')
		self.stop_entry = Entry(self.parameters, highlightbackground='#C8C8C8')
		self.stop_label.grid(row=2, column=0, sticky=E)
		self.stop_entry.grid(row=2, column=1, sticky=W)
		#
		self.igv_var = IntVar()
		self.igv_check = Checkbutton(self.parameters, text='Get IGV plot', onvalue=1, offvalue=0, variable=self.igv_var, bg='#C8C8C8')
		self.igv_check.grid(column=2, row=1, sticky=E)
		## if the dot igv file check is not, diable the igv checkbutton
		if (not self.igv_file_check):
			self.igv_check.configure(state='disabled')
		#
		self.help1 = Label(self.parameters, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help1.grid(row=3, column=3, sticky=E)
		self.help1.bind("<Button-1>", self.help1_popup)
		self.help1.bind("<Leave>", lambda event: self.help1.configure(relief=GROOVE))
		self.help1.bind("<Enter>", lambda event: self.help1.configure(cursor='hand', relief=RAISED))
		#
		self.max_af = LabelFrame(self.widget_layer, text='Maximum Allele Frequency', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.max_af.pack(fill=X, expand=False, pady=10, padx=100)
		self.max_af.columnconfigure(0, weight=1)
		self.max_af.columnconfigure(1, weight=1)
		self.max_af.columnconfigure(2, weight=1)
		self.max_af.columnconfigure(3, weight=1)
		self.max_af.rowconfigure(0, weight=1)
		self.max_af.rowconfigure(1, weight=1)
		self.max_af_cuttoff_label = Label(self.max_af, text='MAX_AF cutoff:', bg='#C8C8C8')
		self.max_af_cuttoff_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_cuttoff_label.grid(row=0, column=0, sticky=E)
		self.max_af_cuttoff_entry.grid(row=0, column=1, sticky=W)
		#
		self.max_af_value_label = Label(self.max_af, text='MAX_AF equal to:', bg='#C8C8C8')
		self.max_af_value_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_value_label.grid(row=0, column=2, sticky=E)
		self.max_af_value_entry.grid(row=0, column=3, sticky=W)
		#
		self.help2 = Label(self.max_af, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help2.grid(row=1, column=3, sticky=E)
		self.help2.bind("<Button-1>", self.help2_popup)
		self.help2.bind("<Leave>", lambda event: self.help2.configure(relief=GROOVE))
		self.help2.bind("<Enter>", lambda event: self.help2.configure(cursor='hand', relief=RAISED))
		#
		self.cq_frame = LabelFrame(self.widget_layer, text='Consequence', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.cq_frame.pack(fill=X, expand=False, pady=10, padx=100)
		self.cq_frame.columnconfigure(0, weight=1)
		self.cq_frame.columnconfigure(1, weight=1)
		self.cq_frame.rowconfigure(0, weight=1)
		self.cq_frame.rowconfigure(1, weight=1)
		self.cq_frame.rowconfigure(2, weight=1)
		self.cq_frame.rowconfigure(3, weight=1)
		self.sub_frame = Frame(self.cq_frame)
		#
		self.list_scroll = Scrollbar(self.sub_frame, orient=VERTICAL)
		self.all_consequences = re.split(',', '3_prime_UTR_variant,5_prime_UTR_variant,downstream_gene_variant,feature_elongation,feature_truncation,frameshift_variant,incomplete_terminal_codon_variant,inframe_deletion,inframe_insertion,intergenic_variant,intron_variant,mature_miRNA_variant,missense_variant,nc_transcript_variant,NMD_transcript_variant,non_coding_exon_variant,regulatory_region_ablation,regulatory_region_amplification,regulatory_region_variant,splice_acceptor_variant,splice_donor_variant,splice_region_variant,stop_gained,stop_lost,stop_retained_variant,synonymous_variant,TF_binding_site_variant,TFBS_ablation,TFBS_amplification,transcript_ablation,transcript_amplification,upstream_gene_variant')
		all_cq = tuple(self.all_consequences)
		cq_var = StringVar(value=all_cq)
		self.cq_label = Label(self.cq_frame, text='Consequence list:', bg='#C8C8C8')
		self.cq_box = Listbox(self.sub_frame, listvariable=cq_var, height=8, width=40, selectmode=MULTIPLE, yscrollcommand=self.list_scroll.set)
		self.list_scroll.config(command=self.cq_box.yview)
		self.list_scroll.pack(side=RIGHT, fill=Y)
		self.cq_label.grid(column=0, row=0, sticky=E)
		self.cq_box.pack(fill=BOTH, expand=True)
		self.sub_frame.grid(column=1, row=0, sticky=W)
		#
		self.cq_all_var = IntVar()
		self.cq_check_all = Checkbutton(self.cq_frame, text='All CQ in the list above', onvalue=1, offvalue=0, variable=self.cq_all_var, bg='#C8C8C8')
		self.cq_check_all.grid(column=1, row=1, sticky=W)
		#
		self.user_cq_label = Label(self.cq_frame, text='Other user-defined\nconsequences:', bg='#C8C8C8')
		self.user_cq_entry = Entry(self.cq_frame, highlightbackground='#C8C8C8')
		self.user_cq_label.grid(column=0, row=2, sticky=E)
		self.user_cq_entry.grid(column=1, row=2, sticky=W)
		self.cq_lof_var = IntVar()
		#
		self.cq_check = Checkbutton(self.cq_frame, text='Functional and LOF consequences', onvalue=1, offvalue=0, variable=self.cq_lof_var, bg='#C8C8C8')
		self.cq_check.grid(column=1, row=3, sticky=W)
		#
		self.help3 = Label(self.cq_frame, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help3.grid(row=4, column=1, sticky=E)
		self.help3.bind("<Button-1>", self.help3_popup)
		self.help3.bind("<Leave>", lambda event: self.help3.configure(relief=GROOVE))
		self.help3.bind("<Enter>", lambda event: self.help3.configure(cursor='hand', relief=RAISED))
		#
		self.submit_button = Button(self.widget_layer, text='Run', command=self.buffer, highlightbackground='#E0E0E0')
		self.submit_button.pack(pady=10, padx=100)
		## if the global variables that check the dot server/ddd_prod files are false or None, the Run button is disabled.
		if (not self.server_file_check or not self.ddd_prod_check):
			self.submit_button.configure(state='disabled')
	def forward(self, event):
		"""Method belongs to the Next button."""
		self.present_frame.pack_forget()
		self.next_frame.pack(fill=BOTH, expand=TRUE)
	def backward(self, event):
		"""Method belongs to the Back button."""
		self.present_frame.pack_forget()
		self.next_frame.pack_forget()
		self.previous_frame.pack(fill=BOTH, expand=TRUE)
	def get_user_input_function(self):
		"""Method that gets the user input parameters and stores them."""
		self.user_input = {}
		cq_list = []
		self.user_input['ID'] = str(self.child_id_entry.get())
		self.user_input['chrom'] = str(self.chr_var.get())
		self.user_input['start'] = str(self.start_entry.get())
		self.user_input['stop'] = str(self.stop_entry.get())
		if (self.igv_var.get()):
			self.user_input['igv'] = 'yes'
		else:
			self.user_input['igv'] = 'no'
		self.user_input['max_af_cutoff'] = self.max_af_cuttoff_entry.get() or 'ignore'
		self.user_input['max_af_value'] = self.max_af_value_entry.get() or 'ignore'
		## preparing the user-defined CQ
		if (self.cq_all_var.get()):
			cq_list.extend(self.all_consequences)
		else:
			for indx in self.cq_box.curselection():
				cq_list.append(self.all_consequences[int(indx)])
		for entry in re.split(',', self.user_cq_entry.get()):
			if (entry):
				cq_list.append(entry)
		if (self.cq_lof_var.get()):
			cq_list.extend(genomic_coords_child_id.LOF)
		self.user_input['cq'] = ','.join(list(set(cq_list)))
		## catch some errors eg. not all necessay entries are entered by the user or when start is greater than stop
		try:
			assert all([self.user_input['ID'], self.user_input['chrom'], self.user_input['start'], self.user_input['stop'], self.user_input['cq']])
			if (int(self.user_input['start']) > int(self.user_input['stop'])):
				tkMessageBox.showwarning(title='Warning', message='Start should be smaller than Stop.')
				self.error_collect = 'Start stop error.'
		except:
			tkMessageBox.showwarning(title='Warning', message='These entries are mandatory: child ID, Chromosome, Start, Stop, CQ.')
			self.error_collect = 'Input error.'
	def help1_popup(self, event):
		"""This method belongs to the first "?"."""
		help1_msg = 'ID : The child\'s id (person stable id or decipher id).\n\nChromosome/start/stop : The Genomic coordinates to query.\n\nIGV : This option will be disabled if the ".igv_user" file is not found in the current directory or its parent directory. The IGV plot for the trio is retrieved.\n'
		tkMessageBox.showinfo(title='Parameters', message=help1_msg)
	def help2_popup(self, event):
		"""This method belongs to the second "?"."""
		help2_msg = 'Max_af_cutoff (maximum alele frequency) : variants with MAX_AF below this cutoff are included.\n\nMax_af_value : variants with MAX_AF equal to this value are selected.\n'
		tkMessageBox.showinfo(title='MAX_AF', message=help2_msg)
	def help3_popup(self, event):
		"""This method belongs to the third "?"."""
		help3_msg = 'Consequence : Select variant consequence using any or all of the options given.\n\nFunctional and LOF include :\ntranscript_ablation, splice_donor_variant\nsplice_acceptor_variant, stop_gained\nframeshift_variant, stop_lost\nstart_lost, inframe_insertion\ninframe_deletion, missense_variant\ntranscript_amplification, protein_altering_variant.\n'
		tkMessageBox.showinfo(title='CQ', message=help3_msg)
	def backend_variant_execution(self):
		"""This method starts the backend execution steps for variant extraction."""
		string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
		if (not self.direct_ssh_mode):
			build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
		## do if the error collection variable is not
		if (not self.error_collect):
			## do the routine procedure: create local script, send and execute on backend, transfer result to frontend.
			os.system('python {a}local_scripts/id_coords_trio_variants_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --id {f} --chrom {g} --start {h} --stop {i} --cq {j} --max_af_cutoff {k} --max_af_value {l} --string_user_settings_dict \'{m}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['ID'], g=self.user_input['chrom'], h=self.user_input['start'], i=self.user_input['stop'], j=self.user_input['cq'], k=self.user_input['max_af_cutoff'], l=self.user_input['max_af_value'], m=string_user_settings))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
				cmd.write(server_cmd)
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='trio_variants.json', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
	def backend_igv_execution(self):
		"""This method starts the backend execution steps for IGV retrieval."""
		string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
		## do if the error collection variable is not and IGV variable is yes
		if (not self.error_collect and self.user_input['igv'] == 'yes'):
			## do the routine procedure: create local script, send and execute on backend, transfer result to frontend.
			## in this case the start and stop are both the start
			os.system('python {a}local_scripts/id_coords_trio_igv_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --id {f} --chrom {g} --start {h} --stop {i} --string_user_settings_dict \'{j}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['ID'], g=self.user_input['chrom'], h=self.user_input['start'], i=self.user_input['start'], j=string_user_settings))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(file_name='current_run.py', backend_dir_name=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
				cmd.write(server_cmd)
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='trio_igv.png', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
	def create_progress_bar(self):
		"""Aesthetic method to create an indeterminate progress bar."""
		self.progress = ttk.Progressbar(self.present_frame, orient="horizontal", length=300, mode="indeterminate")
		self.progress.pack()
		self.progress.start()
	def widget_lock(self, key_code):
		"""Aesthetic method to inactivate/activate widgets during backend execution."""
		widgets = ['self.previous_window', 'self.next_window', 'self.child_id_label', 'self.child_id_entry', 'self.chr_label', 'self.chr_menu', 'self.start_label', 'self.start_entry', 'self.stop_label', 'self.stop_entry', 'self.igv_check', 'self.help1', 'self.max_af_cuttoff_label', 'self.max_af_cuttoff_entry', 'self.max_af_value_label', 'self.max_af_value_entry', 'self.help2', 'self.cq_label', 'self.cq_box', 'self.cq_check_all', 'self.user_cq_label', 'self.user_cq_entry', 'self.cq_check', 'self.help3', 'self.submit_button']
		if (key_code == 'lock_widgets'):
			for w in widgets:
				eval(w+".config(state='disabled')")
		elif (key_code == 'open_widgets'):
			for w in widgets:
				eval(w+".config(state='normal')")
	def buffer(self):
		"""This method is bound to the Run button and it orchestrates some procedural steps."""
		try:
			local_path = self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir
			for file_found in os.listdir(local_path):
				os.remove(local_path+file_found) ## clearing out the changeable directory
		except:
			pass
		self.error_collect = '' ## reinstate error_collect in case an error with input collection was made
		## do the aesthetic "running" mode
		self.widget_lock('lock_widgets')
		self.create_progress_bar()
		## use a thread to run this method
		t1=threading.Thread(target=self.initiate_backend_process, args=())
		t1.start()
	def initiate_backend_process(self):
		"""This method starts calls other methods to do the background executions."""
		self.get_user_input_function()
		## do variant extraction
		if (not self.error_collect):
			try:
				self.backend_variant_execution()
			except:
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.config(state='disabled')
		else:
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.config(state='disabled')	
		## do IGV retrieval if required
		try:
			assert self.error_collect == ''
			assert self.user_input['igv'] == 'yes'
			self.backend_igv_execution()
		except:
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.config(state='disabled')
		## this is a check for no errors on the backend side during execution
		if (not self.error_collect):
			self.variant_sanity_check_and_proceed()
		## continue to this part in case of no errors
		if (not self.error_collect and self.user_input['igv'] == 'yes'):
			self.igv_sanity_check_and_proceed()
		## continue in case of zero errors
		## activate the Next button and prepare to display the results
		if (not self.error_collect):
			self.next_window.configure(state='active')
			self.next_window.bind("<Button-1>", self.forward)
			self.next_window.bind("<Leave>", lambda event: self.next_window.configure(relief=GROOVE))
			self.next_window.bind("<Enter>", lambda event: self.next_window.configure(cursor='hand', relief=RAISED))
			#
			self.progress.destroy()
			self.widget_lock('open_widgets')
			## clean up the existing next frame
			for widget in self.next_frame.winfo_children():
				widget.destroy()
			## this decides to add/cancel the IGV tab in the results
			if (self.user_input['igv'] == 'no'):
				prepare_result_tabs_igv_excluded(gui_abs_path=self.var_gui_abs_path,previous_frame=self.present_frame,present_frame=self.next_frame,past_frame=self.previous_frame,query_info=self.user_input,backend_dir=self.var_backend_dir)
			elif (self.user_input['igv'] == 'yes'):
				prepare_result_tabs_igv_included(direct_ssh_mode=self.direct_ssh_mode,var_backend_dir=self.var_backend_dir,gui_abs_path=self.var_gui_abs_path,user_settings_var=self.var_user_settings,previous_frame=self.present_frame,present_frame=self.next_frame,past_frame=self.previous_frame,query_info=self.user_input)
	def variant_sanity_check_and_proceed(self):
		"""This method reads the JSON file from the server and checks the error key."""
		variant_file_abs_path = self.var_gui_abs_path + 'recent_runs/' + self.var_backend_dir + 'trio_variants.json'
		if (os.access(variant_file_abs_path, os.F_OK) and os.access(variant_file_abs_path, os.R_OK)):
			with open(variant_file_abs_path, 'r') as variant_json:
				variant_json = json.load(variant_json)
			variant_related_errors = variant_json['error_msgs'].encode('utf-8')
			if (variant_related_errors == 'Error'):
				tkMessageBox.showwarning(title='Warning', message='Problem retrieving trio variants from the server.')
				self.error_collect = 'Variant retrieval error.'
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.configure(state='disabled')
		else:
				tkMessageBox.showwarning(title='Warning', message='The output file from the server was not found.')
				self.error_collect = 'Variant retrieval error.'
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.configure(state='disabled')
	def igv_sanity_check_and_proceed(self):
		"""This method checks if the IGV image is corrupt."""
		igv_file_abs_path = self.var_gui_abs_path + 'recent_runs/' + self.var_backend_dir + 'trio_igv.png'
		if (os.access(igv_file_abs_path, os.F_OK) and os.access(igv_file_abs_path, os.R_OK)):
			check_image = Image.open(igv_file_abs_path)
			check_image.verify()
		else:
			tkMessageBox.showwarning(title='Warning', message='The IGV plot output from the server was not found.')
			self.error_collect = 'IGV retrieval error.'
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.configure(state='disabled')



class genomic_coords_cohort:
	"""Query by denomic coordinates and cohort."""
	LOF = ['transcript_ablation','splice_donor_variant','splice_acceptor_variant','stop_gained','frameshift_variant','stop_lost','start_lost','inframe_insertion','inframe_deletion','missense_variant','transcript_amplification','protein_altering_variant']
	def __init__(self, **kwargs):
		## extracting the arguments
		self.direct_ssh_mode = kwargs['direct_ssh_mode']
		self.previous_frame_object = kwargs['previous_frame_object']
		self.previous_frame = kwargs['previous_frame']
		self.present_frame = kwargs['present_frame']
		self.next_frame = kwargs['next_frame']
		self.server_file_check = kwargs['check_server']
		self.ddd_prod_check = kwargs['check_ddd_prod']
		self.var_backend_dir = kwargs['var_backend_dir']
		self.var_gui_abs_path = kwargs['var_gui_abs_path']
		self.var_user_settings = kwargs['var_user_settings']
		## set up the title of the label frame
		self.present_frame['text'] = 'Query Input: Genomic Coordinates using the entire cohort'
		## activate the Next button of the previous frame
		self.previous_frame_object.next_window.configure(state='active')
		self.previous_frame_object.next_window.bind("<Button-1>", self.previous_frame_object.forward)
		self.previous_frame_object.next_window.bind("<Leave>", lambda event: self.previous_frame_object.next_window.configure(relief=GROOVE))
		self.previous_frame_object.next_window.bind("<Enter>", lambda event: self.previous_frame_object.next_window.configure(cursor='hand', relief=RAISED))
		## hide the next and previous frames. Show the present frame
		self.next_frame.pack_forget()
		self.previous_frame.pack_forget()
		self.present_frame.pack(fill=BOTH, expand=TRUE)
		## destroy the current widgets occupying this frame (in case of a previous input layout)
		for widget in self.present_frame.winfo_children():
			widget.destroy()
		time.sleep(1)
		## the error collection variable
		self.error_collect = ''
		## setting up the scrollbars
		self.present_frame_y = Scrollbar(self.present_frame, orient=VERTICAL)
		self.present_frame_y.pack(fill=Y, side=RIGHT)
		self.present_frame_x = Scrollbar(self.present_frame, orient=HORIZONTAL)
		self.present_frame_x.pack(fill=X, side=BOTTOM)
		self.present_canvas = Canvas(self.present_frame, bg='#E0E0E0', highlightbackground='#E0E0E0', highlightcolor='#E0E0E0', yscrollcommand=self.present_frame_y.set, xscrollcommand=self.present_frame_x.set)
		self.present_canvas.pack(fill=BOTH, expand=True)
		self.present_canvas.configure(scrollregion=(0,0,1000,1000))
		self.present_frame_y.config(command=self.present_canvas.yview)
		self.present_frame_x.config(command=self.present_canvas.xview)
		self.widget_layer = Frame(self.present_canvas, bg='#E0E0E0')
		self.widget_layer.pack()
		self.present_canvas.create_window(0, 0, window=self.widget_layer, anchor='nw')
		## create the Back and Next buttons of this frame and bind them to methods
		self.window_navigation = Frame(self.widget_layer, bg='#E0E0E0')
		self.window_navigation.pack(fill=X, expand=False, pady=10, padx=100)
		self.window_navigation.columnconfigure(0, weight=1)
		self.window_navigation.columnconfigure(1, weight=1)
		self.window_navigation.rowconfigure(0, weight=1)
		#
		self.previous_window = Label(self.window_navigation, text='Back', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.previous_window.grid(row=0, column=0, sticky=E)
		self.previous_window.bind("<Button-1>", self.backward)
		self.previous_window.bind("<Leave>", lambda event: self.previous_window.configure(relief=GROOVE))
		self.previous_window.bind("<Enter>", lambda event: self.previous_window.configure(cursor='hand', relief=RAISED))
		#
		self.next_window = Label(self.window_navigation, text='Next', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.next_window.grid(row=0, column=1, sticky=W)
		self.next_window.configure(state='disabled')
		## creating the labels and entries in the input layout
		self.parameters = LabelFrame(self.widget_layer, text='Parameters', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.parameters.pack(fill=X, expand=False, pady=10, padx=100)
		self.parameters.columnconfigure(0, weight=1)
		self.parameters.columnconfigure(1, weight=1)
		self.parameters.columnconfigure(2, weight=1)
		self.parameters.columnconfigure(3, weight=1)
		self.parameters.rowconfigure(0, weight=1)
		self.parameters.rowconfigure(1, weight=1)
		self.parameters.rowconfigure(2, weight=1)
		#
		self.start_label = Label(self.parameters, text='Start:', bg='#C8C8C8')
		self.start_entry = Entry(self.parameters, highlightbackground='#C8C8C8')
		self.start_label.grid(row=0, column=0, sticky=E)
		self.start_entry.grid(row=0, column=1, sticky=W)
		#
		self.stop_label = Label(self.parameters, text='Stop:', bg='#C8C8C8')
		self.stop_entry = Entry(self.parameters, highlightbackground='#C8C8C8')
		self.stop_label.grid(row=1, column=0, sticky=E)
		self.stop_entry.grid(row=1, column=1, sticky=W)
		#
		self.chr_label = Label(self.parameters, text='Chromosome:', bg='#C8C8C8')
		self.chr_var = StringVar(self.parameters)
		self.chr_var.set('1')
		self.chrs = list(range(1,23))
		self.chrs.extend(['X', 'Y'])
		self.chr_menu = OptionMenu(self.parameters, self.chr_var, *self.chrs)
		self.chr_menu.config(bg='#C8C8C8')
		self.chr_label.grid(row=0, column=2, sticky=E)
		self.chr_menu.grid(row=0, column=3, sticky=W)
		#
		self.help1 = Label(self.parameters, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help1.grid(row=2, column=3, sticky=E)
		self.help1.bind("<Button-1>", self.help1_popup)
		self.help1.bind("<Leave>", lambda event: self.help1.configure(relief=GROOVE))
		self.help1.bind("<Enter>", lambda event: self.help1.configure(cursor='hand', relief=RAISED))
		#
		self.max_af = LabelFrame(self.widget_layer, text='Maximum Allele Frequency', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.max_af.pack(fill=X, expand=False, pady=10, padx=100)
		self.max_af.columnconfigure(0, weight=1)
		self.max_af.columnconfigure(1, weight=1)
		self.max_af.columnconfigure(2, weight=1)
		self.max_af.columnconfigure(3, weight=1)
		self.max_af.rowconfigure(0, weight=1)
		self.max_af.rowconfigure(1, weight=1)
		self.max_af_cuttoff_label = Label(self.max_af, text='MAX_AF cutoff:', bg='#C8C8C8')
		self.max_af_cuttoff_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_cuttoff_label.grid(row=0, column=0, sticky=E)
		self.max_af_cuttoff_entry.grid(row=0, column=1, sticky=W)
		#
		self.max_af_value_label = Label(self.max_af, text='MAX_AF equal to:', bg='#C8C8C8')
		self.max_af_value_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_value_label.grid(row=0, column=2, sticky=E)
		self.max_af_value_entry.grid(row=0, column=3, sticky=W)
		#
		self.help2 = Label(self.max_af, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help2.grid(row=1, column=3, sticky=E)
		self.help2.bind("<Button-1>", self.help2_popup)
		self.help2.bind("<Leave>", lambda event: self.help2.configure(relief=GROOVE))
		self.help2.bind("<Enter>", lambda event: self.help2.configure(cursor='hand', relief=RAISED))
		#
		self.cq_frame = LabelFrame(self.widget_layer, text='Consequence', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.cq_frame.pack(fill=X, expand=False, pady=10, padx=100)
		self.cq_frame.columnconfigure(0, weight=1)
		self.cq_frame.columnconfigure(1, weight=1)
		self.cq_frame.rowconfigure(0, weight=1)
		self.cq_frame.rowconfigure(1, weight=1)
		self.cq_frame.rowconfigure(2, weight=1)
		self.sub_frame = Frame(self.cq_frame)
		#
		self.list_scroll = Scrollbar(self.sub_frame, orient=VERTICAL)
		self.all_consequences = re.split(',', '3_prime_UTR_variant,5_prime_UTR_variant,downstream_gene_variant,feature_elongation,feature_truncation,frameshift_variant,incomplete_terminal_codon_variant,inframe_deletion,inframe_insertion,intergenic_variant,intron_variant,mature_miRNA_variant,missense_variant,nc_transcript_variant,NMD_transcript_variant,non_coding_exon_variant,regulatory_region_ablation,regulatory_region_amplification,regulatory_region_variant,splice_acceptor_variant,splice_donor_variant,splice_region_variant,stop_gained,stop_lost,stop_retained_variant,synonymous_variant,TF_binding_site_variant,TFBS_ablation,TFBS_amplification,transcript_ablation,transcript_amplification,upstream_gene_variant')
		all_cq = tuple(self.all_consequences)
		cq_var = StringVar(value=all_cq)
		self.cq_label = Label(self.cq_frame, text='Consequence list:', bg='#C8C8C8')
		self.cq_box = Listbox(self.sub_frame, listvariable=cq_var, height=8, width=40, selectmode=MULTIPLE, yscrollcommand=self.list_scroll.set)
		self.list_scroll.config(command=self.cq_box.yview)
		self.list_scroll.pack(side=RIGHT, fill=Y)
		self.cq_label.grid(column=0, row=0, sticky=E)
		self.cq_box.pack(fill=BOTH, expand=True)
		self.sub_frame.grid(column=1, row=0, sticky=W)
		#
		self.cq_all_var = IntVar()
		self.cq_check_all = Checkbutton(self.cq_frame, text='All CQ in the list above', onvalue=1, offvalue=0, variable=self.cq_all_var, bg='#C8C8C8')
		self.cq_check_all.grid(column=1, row=1, sticky=W)
		#
		self.user_cq_label = Label(self.cq_frame, text='Other user-defined\nconsequences:', bg='#C8C8C8')
		self.user_cq_entry = Entry(self.cq_frame, highlightbackground='#C8C8C8')
		self.user_cq_label.grid(column=0, row=2, sticky=E)
		self.user_cq_entry.grid(column=1, row=2, sticky=W)
		self.cq_lof_var = IntVar()
		#
		self.cq_check = Checkbutton(self.cq_frame, text='Functional and LOF consequences', onvalue=1, offvalue=0, variable=self.cq_lof_var, bg='#C8C8C8')
		self.cq_check.grid(column=1, row=3, sticky=W)
		#
		self.help3 = Label(self.cq_frame, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help3.grid(row=4, column=1, sticky=E)
		self.help3.bind("<Button-1>", self.help3_popup)
		self.help3.bind("<Leave>", lambda event: self.help3.configure(relief=GROOVE))
		self.help3.bind("<Enter>", lambda event: self.help3.configure(cursor='hand', relief=RAISED))
		#
		self.submit_button = Button(self.widget_layer, text='Run', command=self.buffer, highlightbackground='#E0E0E0')
		self.submit_button.pack(pady=10, padx=100)
		## if the global variables that check the dot server/ddd_prod files are false or None, the Run button is disabled.
		if (not self.server_file_check or not self.ddd_prod_check):
			self.submit_button.configure(state='disabled')
	def forward(self, event):
		"""Method belongs to the Next button."""
		self.present_frame.pack_forget()
		self.next_frame.pack(fill=BOTH, expand=TRUE)
	def backward(self, event):
		"""Method belongs to the Back button."""
		self.present_frame.pack_forget()
		self.next_frame.pack_forget()
		self.previous_frame.pack(fill=BOTH, expand=TRUE)
	def get_user_input_function(self):
		"""Method that gets the user input parameters and stores them."""
		self.user_input = {}
		cq_list = []
		self.user_input['chrom'] = str(self.chr_var.get())
		self.user_input['start'] = str(self.start_entry.get())
		self.user_input['stop'] = str(self.stop_entry.get())
		self.user_input['max_af_cutoff'] = self.max_af_cuttoff_entry.get() or 'ignore'
		self.user_input['max_af_value'] = self.max_af_value_entry.get() or 'ignore'
		## preparing the user-defined CQ
		if (self.cq_all_var.get()):
			cq_list.extend(self.all_consequences)
		else:
			for indx in self.cq_box.curselection():
				cq_list.append(self.all_consequences[int(indx)])
		for entry in re.split(',', self.user_cq_entry.get()):
			if (entry):
				cq_list.append(entry)
		if (self.cq_lof_var.get()):
			cq_list.extend(genomic_coords_child_id.LOF)
		self.user_input['cq'] = ','.join(list(set(cq_list)))
		## catch some errors eg. not all necessay entries are entered by the user or when start is greater than stop
		try:
			assert all([self.user_input['chrom'], self.user_input['start'], self.user_input['stop'], self.user_input['cq']])
			if (int(self.user_input['start']) > int(self.user_input['stop'])):
				tkMessageBox.showwarning(title='Warning', message='Start should be smaller than Stop.')
				self.error_collect = 'Start stop error.'
		except:
			tkMessageBox.showwarning(title='Warning', message='These entries are mandatory: Chromosome, Start, Stop, CQ.')
			self.error_collect = 'Input error.'
	def help1_popup(self, event):
		"""This method belongs to the first "?"."""
		help1_msg = 'Chromosome/start/stop : Parse the cohort VCFs using these coordinates.\n'
		tkMessageBox.showinfo(title='Parameters', message=help1_msg)
	def help2_popup(self, event):
		"""This method belongs to the second "?"."""
		help2_msg = 'Max_af_cutoff (maximum alele frequency) : variants with MAX_AF below this cutoff are included.\n\nMax_af_value : variants with MAX_AF equal to this value are selected.\n\nNote : applying a MAX_AF threshold is advised in this case of parsing all cohort VCFs, this will decrease the number of selected variants and speed up the file transfer from the server.\n'
		tkMessageBox.showinfo(title='MAX_AF', message=help2_msg)
	def help3_popup(self, event):
		"""This method belongs to the third "?"."""
		help3_msg = 'Consequence : Select variant consequence using any or all of the options given.\n\nFunctional and LOF include :\ntranscript_ablation, splice_donor_variant\nsplice_acceptor_variant, stop_gained\nframeshift_variant, stop_lost\nstart_lost, inframe_insertion\ninframe_deletion, missense_variant\ntranscript_amplification, protein_altering_variant.\n'
		tkMessageBox.showinfo(title='CQ', message=help3_msg)
	def backend_variant_execution(self):
		"""This method starts the backend execution steps for variant extraction."""
		string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
		if (not self.direct_ssh_mode):
			build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
		## do if the error collection variable is not
		if (not self.error_collect):
			## do the routine procedure: create local script, send and execute on backend, transfer result to frontend.
			os.system('python {a}local_scripts/coords_cohort_1_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --chrom {f} --start {g} --stop {h} --cq {i} --max_af_cutoff {j} --max_af_value {k} --string_user_settings_dict \'{l}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['chrom'], g=self.user_input['start'], h=self.user_input['stop'], i=self.user_input['cq'], j=self.user_input['max_af_cutoff'], k=self.user_input['max_af_value'], l=string_user_settings))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
				cmd.write(server_cmd)
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='cohort_variants.json', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			## run the first check point
			self.sanity_check_and_proceed()
			if (not self.error_collect):
				## continue with the second part
				os.system('python {a}local_scripts/cohort_2_source_builder.py --o {b}recent_runs/{c}current_run.py --remote_dir {d}'.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_backend_dir))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				#
				server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='selected_cohort_variants.tsv.gz', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				#
				os.system('gunzip {a}recent_runs/{b}selected_cohort_variants.tsv.gz'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
	def create_progress_bar(self):
		"""Aesthetic method to create an indeterminate progress bar."""
		self.progress = ttk.Progressbar(self.present_frame, orient="horizontal", length=300, mode="indeterminate")
		self.progress.pack()
		self.progress.start()
	def widget_lock(self, key_code):
		"""Aesthetic method to inactivate/activate widgets during backend execution."""
		widgets = ['self.previous_window', 'self.next_window', 'self.start_label', 'self.start_entry', 'self.stop_label', 'self.stop_entry', 'self.chr_label', 'self.chr_menu', 'self.help1', 'self.max_af_cuttoff_label', 'self.max_af_cuttoff_entry', 'self.max_af_value_label', 'self.max_af_value_entry', 'self.help2', 'self.cq_label', 'self.cq_box', 'self.cq_check_all', 'self.user_cq_label', 'self.user_cq_entry', 'self.cq_check', 'self.help3', 'self.submit_button']
		if (key_code == 'lock_widgets'):
			for w in widgets:
				eval(w+".config(state='disabled')")
		elif (key_code == 'open_widgets'):
			for w in widgets:
				eval(w+".config(state='normal')")
	def buffer(self):
		"""This method is bound to the Run button and it orchestrates some procedural steps."""
		try:
			local_path = self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir
			for file_found in os.listdir(local_path):
				os.remove(local_path+file_found) ## clearing out the changeable directory
		except:
			pass
		self.error_collect = '' ## reinstate error_collect in case an error with input collection was made
		## do the aesthetic "running" mode
		self.widget_lock('lock_widgets')
		self.create_progress_bar()
		## use a thread to run this method, this is because 2 functions are run at the same time: the progress bar and the backend execution.
		t1=threading.Thread(target=self.initiate_backend_process, args=())
		t1.start()
	def initiate_backend_process(self):
		"""This method starts calls other methods to do the background executions."""
		self.get_user_input_function()
		## do variant extraction
		if (not self.error_collect):
			try:
				self.backend_variant_execution()
			except:
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.config(state='disabled')
		else:
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.config(state='disabled')
		## continue in case of zero errors
		## activate the Next button and prepare to display the results
		if (not self.error_collect):
			self.next_window.configure(state='active')
			self.next_window.bind("<Button-1>", self.forward)
			self.next_window.bind("<Leave>", lambda event: self.next_window.configure(relief=GROOVE))
			self.next_window.bind("<Enter>", lambda event: self.next_window.configure(cursor='hand', relief=RAISED))
			#
			self.progress.destroy()
			self.widget_lock('open_widgets')
			## clean up the existing next frame
			for widget in self.next_frame.winfo_children():
				widget.destroy()
			## display the results on the results frame
			prepare_result_tabs_cohort(gui_abs_path=self.var_gui_abs_path,previous_frame=self.present_frame,present_frame=self.next_frame,past_frame=self.previous_frame,query_info=self.user_input,backend_dir=self.var_backend_dir)
	def sanity_check_and_proceed(self):
		"""This method reads the JSON file from the server and checks the error key."""
		variant_file_abs_path = self.var_gui_abs_path + 'recent_runs/'+self.var_backend_dir+'cohort_variants.json'
		if (os.access(variant_file_abs_path, os.F_OK) and os.access(variant_file_abs_path, os.R_OK)):
			with open(variant_file_abs_path, 'r') as variant_json:
				variant_json = json.load(variant_json)
			variant_related_errors = variant_json['error_msgs'].encode('utf-8')
			if (variant_related_errors == 'Error'):
				tkMessageBox.showwarning(title='Warning', message='Problem retrieving cohort variants from the server.')
				self.error_collect = 'Variant retrieval error.'
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.configure(state='disabled')
		else:
			tkMessageBox.showwarning(title='Warning', message='The output file from the server was not found.')
			self.error_collect = 'Variant retrieval error.'
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.configure(state='disabled')



class gene_name_child_id:
	"""Query by gene name and decipher ID."""
	LOF = ['transcript_ablation','splice_donor_variant','splice_acceptor_variant','stop_gained','frameshift_variant','stop_lost','start_lost','inframe_insertion','inframe_deletion','missense_variant','transcript_amplification','protein_altering_variant']
	def __init__(self, **kwargs):
		## extracting the arguments
		self.direct_ssh_mode = kwargs['direct_ssh_mode']
		self.previous_frame_object = kwargs['previous_frame_object']
		self.previous_frame = kwargs['previous_frame']
		self.present_frame = kwargs['present_frame']
		self.next_frame = kwargs['next_frame']
		self.var_backend_dir = kwargs['var_backend_dir']
		self.server_file_check = kwargs['check_server']
		self.igv_file_check = kwargs['check_igv']
		self.ddd_prod_check = kwargs['check_ddd_prod']
		self.var_gui_abs_path = kwargs['var_gui_abs_path']
		self.var_user_settings = kwargs['var_user_settings']
		## set up the title of the label frame
		self.present_frame['text'] = 'Query Input: Gene name using a child ID'
		## activate the Next button of the previous frame
		self.previous_frame_object.next_window.configure(state='active')
		self.previous_frame_object.next_window.bind("<Button-1>", self.previous_frame_object.forward)
		self.previous_frame_object.next_window.bind("<Leave>", lambda event: self.previous_frame_object.next_window.configure(relief=GROOVE))
		self.previous_frame_object.next_window.bind("<Enter>", lambda event: self.previous_frame_object.next_window.configure(cursor='hand', relief=RAISED))
		## hide the next and previous frames. Show the present frame
		self.next_frame.pack_forget()
		self.previous_frame.pack_forget()
		self.present_frame.pack(fill=BOTH, expand=TRUE)
		## destroy the current widgets occupying this frame (in case of a previous input layout)
		for widget in self.present_frame.winfo_children():
			widget.destroy()
		time.sleep(1)
		## the error collection variable
		self.error_collect = ''
		## setting up the scrollbars
		self.present_frame_y = Scrollbar(self.present_frame, orient=VERTICAL)
		self.present_frame_y.pack(fill=Y, side=RIGHT)
		self.present_frame_x = Scrollbar(self.present_frame, orient=HORIZONTAL)
		self.present_frame_x.pack(fill=X, side=BOTTOM)
		self.present_canvas = Canvas(self.present_frame, bg='#E0E0E0', highlightbackground='#E0E0E0', highlightcolor='#E0E0E0', yscrollcommand=self.present_frame_y.set, xscrollcommand=self.present_frame_x.set)
		self.present_canvas.pack(fill=BOTH, expand=True)
		self.present_canvas.configure(scrollregion=(0,0,1000,1000))
		self.present_frame_y.config(command=self.present_canvas.yview)
		self.present_frame_x.config(command=self.present_canvas.xview)
		self.widget_layer = Frame(self.present_canvas, bg='#E0E0E0')
		self.widget_layer.pack()
		self.present_canvas.create_window(0, 0, window=self.widget_layer, anchor='nw')
		## create the Back and Next buttons of this frame and bind them to methods
		self.window_navigation = Frame(self.widget_layer, bg='#E0E0E0')
		self.window_navigation.pack(fill=X, expand=False, pady=10, padx=100)
		self.window_navigation.columnconfigure(0, weight=1)
		self.window_navigation.columnconfigure(1, weight=1)
		self.window_navigation.rowconfigure(0, weight=1)
		#
		self.previous_window = Label(self.window_navigation, text='Back', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.previous_window.grid(row=0, column=0, sticky=E)
		self.previous_window.bind("<Button-1>", self.backward)
		self.previous_window.bind("<Leave>", lambda event: self.previous_window.configure(relief=GROOVE))
		self.previous_window.bind("<Enter>", lambda event: self.previous_window.configure(cursor='hand', relief=RAISED))
		#
		self.next_window = Label(self.window_navigation, text='Next', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.next_window.grid(row=0, column=1, sticky=W)
		self.next_window.configure(state='disabled')
		## creating the labels and entries in the input layout
		self.parameters = LabelFrame(self.widget_layer, text='Parameters', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.parameters.pack(fill=X, expand=False, pady=10, padx=100)
		self.parameters.columnconfigure(0, weight=1)
		self.parameters.columnconfigure(1, weight=1)
		self.parameters.columnconfigure(2, weight=1)
		self.parameters.rowconfigure(0, weight=1)
		self.parameters.rowconfigure(1, weight=1)
		self.parameters.rowconfigure(2, weight=1)
		self.decipher_id_label = Label(self.parameters, text='ID:', bg='#C8C8C8')
		self.decipher_id_entry = Entry(self.parameters, highlightbackground='#C8C8C8')
		self.decipher_id_label.grid(row=0, column=0, sticky=E, pady=3)
		self.decipher_id_entry.grid(row=0, column=1, sticky=W, pady=3)
		#
		self.gene_label = Label(self.parameters, text='Gene name:', bg='#C8C8C8')
		self.gene_entry = Entry(self.parameters, highlightbackground='#C8C8C8')
		self.gene_label.grid(row=1, column=0, sticky=E)
		self.gene_entry.grid(row=1, column=1, sticky=W)
		#
		self.igv_var = IntVar()
		self.igv_check = Checkbutton(self.parameters, text='Get IGV plot', onvalue=1, offvalue=0, variable=self.igv_var, bg='#C8C8C8')
		self.igv_check.grid(column=2, row=0, sticky=W)
		## if the dot igv file check is not, diable the igv checkbutton
		if (not self.igv_file_check):
			self.igv_check.configure(state='disabled')
		#
		self.help1 = Label(self.parameters, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help1.grid(row=2, column=2, sticky=E)
		self.help1.bind("<Button-1>", self.help1_popup)
		self.help1.bind("<Leave>", lambda event: self.help1.configure(relief=GROOVE))
		self.help1.bind("<Enter>", lambda event: self.help1.configure(cursor='hand', relief=RAISED))
		#
		self.max_af = LabelFrame(self.widget_layer, text='Maximum Allele Frequency', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.max_af.pack(fill=X, expand=False, pady=10, padx=100)
		self.max_af.columnconfigure(0, weight=1)
		self.max_af.columnconfigure(1, weight=1)
		self.max_af.columnconfigure(2, weight=1)
		self.max_af.columnconfigure(3, weight=1)
		self.max_af.rowconfigure(0, weight=1)
		self.max_af.rowconfigure(1, weight=1)
		self.max_af_cuttoff_label = Label(self.max_af, text='MAX_AF cutoff:', bg='#C8C8C8')
		self.max_af_cuttoff_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_cuttoff_label.grid(row=0, column=0, sticky=E)
		self.max_af_cuttoff_entry.grid(row=0, column=1, sticky=W)
		#
		self.max_af_value_label = Label(self.max_af, text='MAX_AF equal to:', bg='#C8C8C8')
		self.max_af_value_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_value_label.grid(row=0, column=2, sticky=E)
		self.max_af_value_entry.grid(row=0, column=3, sticky=W)
		#
		self.help2 = Label(self.max_af, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help2.grid(row=1, column=3, sticky=E)
		self.help2.bind("<Button-1>", self.help2_popup)
		self.help2.bind("<Leave>", lambda event: self.help2.configure(relief=GROOVE))
		self.help2.bind("<Enter>", lambda event: self.help2.configure(cursor='hand', relief=RAISED))
		#
		self.cq_frame = LabelFrame(self.widget_layer, text='Consequence', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.cq_frame.pack(fill=X, expand=False, pady=10, padx=100)
		self.cq_frame.columnconfigure(0, weight=1)
		self.cq_frame.columnconfigure(1, weight=1)
		self.cq_frame.rowconfigure(0, weight=1)
		self.cq_frame.rowconfigure(1, weight=1)
		self.cq_frame.rowconfigure(2, weight=1)
		self.cq_frame.rowconfigure(3, weight=1)
		self.cq_frame.rowconfigure(4, weight=1)
		self.sub_frame = Frame(self.cq_frame)
		#
		self.list_scroll = Scrollbar(self.sub_frame, orient=VERTICAL)
		self.all_consequences = re.split(',', '3_prime_UTR_variant,5_prime_UTR_variant,downstream_gene_variant,feature_elongation,feature_truncation,frameshift_variant,incomplete_terminal_codon_variant,inframe_deletion,inframe_insertion,intergenic_variant,intron_variant,mature_miRNA_variant,missense_variant,nc_transcript_variant,NMD_transcript_variant,non_coding_exon_variant,regulatory_region_ablation,regulatory_region_amplification,regulatory_region_variant,splice_acceptor_variant,splice_donor_variant,splice_region_variant,stop_gained,stop_lost,stop_retained_variant,synonymous_variant,TF_binding_site_variant,TFBS_ablation,TFBS_amplification,transcript_ablation,transcript_amplification,upstream_gene_variant')
		all_cq = tuple(self.all_consequences)
		cq_var = StringVar(value=all_cq)
		self.cq_label = Label(self.cq_frame, text='Consequence list:', bg='#C8C8C8')
		self.cq_box = Listbox(self.sub_frame, listvariable=cq_var, height=8, width=40, selectmode=MULTIPLE, yscrollcommand=self.list_scroll.set)
		self.list_scroll.config(command=self.cq_box.yview)
		self.list_scroll.pack(side=RIGHT, fill=Y)
		self.cq_label.grid(column=0, row=0, sticky=E)
		self.cq_box.pack(fill=BOTH, expand=True)
		self.sub_frame.grid(column=1, row=0, sticky=W)
		#
		self.cq_all_var = IntVar()
		self.cq_check_all = Checkbutton(self.cq_frame, text='All CQ in the list above', onvalue=1, offvalue=0, variable=self.cq_all_var, bg='#C8C8C8')
		self.cq_check_all.grid(column=1, row=1, sticky=W)
		#
		self.user_cq_label = Label(self.cq_frame, text='Other user-defined\nconsequences:', bg='#C8C8C8')
		self.user_cq_entry = Entry(self.cq_frame, highlightbackground='#C8C8C8')
		self.user_cq_label.grid(column=0, row=2, sticky=E)
		self.user_cq_entry.grid(column=1, row=2, sticky=W)
		#
		self.cq_lof_var = IntVar()
		#
		self.cq_check = Checkbutton(self.cq_frame, text='Functional and LOF consequences', onvalue=1, offvalue=0, variable=self.cq_lof_var, bg='#C8C8C8')
		self.cq_check.grid(column=1, row=3, sticky=W)
		#
		self.help3 = Label(self.cq_frame, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help3.grid(row=4, column=1, sticky=E)
		self.help3.bind("<Button-1>", self.help3_popup)
		self.help3.bind("<Leave>", lambda event: self.help3.configure(relief=GROOVE))
		self.help3.bind("<Enter>", lambda event: self.help3.configure(cursor='hand', relief=RAISED))
		#
		self.submit_button = Button(self.widget_layer, text='Run', command=self.buffer, highlightbackground='#E0E0E0')
		self.submit_button.pack(pady=10, padx=100)
		## if the global variables that check the dot server/ddd_prod files are false or None, the Run button is disabled.
		if (not self.server_file_check or not self.ddd_prod_check):
			self.submit_button.configure(state='disabled')
	def forward(self, event):
		"""Method belongs to the Next button."""
		self.present_frame.pack_forget()
		self.next_frame.pack(fill=BOTH, expand=TRUE)
	def backward(self, event):
		"""Method belongs to the Back button."""
		self.present_frame.pack_forget()
		self.next_frame.pack_forget()
		self.previous_frame.pack(fill=BOTH, expand=TRUE)
	def get_user_input_function(self):
		"""Method that gets the user input parameters and stores them."""
		self.user_input = {}
		cq_list = []
		self.user_input['ID'] = str(self.decipher_id_entry.get())
		self.user_input['gene'] = str(self.gene_entry.get())
		if (self.igv_var.get()):
			self.user_input['igv'] = 'yes'
		else:
			self.user_input['igv'] = 'no'
		self.user_input['max_af_cutoff'] = self.max_af_cuttoff_entry.get() or 'ignore'
		self.user_input['max_af_value'] = self.max_af_value_entry.get() or 'ignore'
		## preparing the user-defined CQ
		if (self.cq_all_var.get()):
			cq_list.extend(self.all_consequences)
		else:
			for indx in self.cq_box.curselection():
				cq_list.append(self.all_consequences[int(indx)])
		for entry in re.split(',', self.user_cq_entry.get()):
			if (entry):
				cq_list.append(entry)
		if (self.cq_lof_var.get()):
			cq_list.extend(gene_name_child_id.LOF)
		self.user_input['cq'] = ','.join(list(set(cq_list)))
		## catch some errors eg. not all necessay entries are entered by the user
		try:
			assert all([self.user_input['ID'], self.user_input['gene'], self.user_input['cq']])
		except:
			tkMessageBox.showwarning(title='Warning', message='These entries are mandatory: child ID, Gene, CQ.')
			self.error_collect = 'Input error.'	
	def help1_popup(self, event):
		"""This method belongs to the first "?"."""
		help1_msg = 'ID : The child\'s id (person stable id or decipher id).\n\nGene : The Gene name of which genomic coordinates will be retrieved from ddd_prod.\n\nIGV : This option will be disabled if the ".igv_user" file is not found in the current directory or its parent directory. The IGV plot for the trio is retrieved.\n'
		tkMessageBox.showinfo(title='Parameters', message=help1_msg)
	def help2_popup(self, event):
		"""This method belongs to the second "?"."""
		help2_msg = 'Max_af_cutoff (maximum alele frequency) : variants with MAX_AF below this cutoff are included.\n\nMax_af_value : variants with MAX_AF equal to this value are selected.\n'
		tkMessageBox.showinfo(title='MAX_AF', message=help2_msg)
	def help3_popup(self, event):
		"""This method belongs to the third "?"."""
		help3_msg = 'Consequence : Select variant consequence using any or all of the options given.\n\nFunctional and LOF include :\ntranscript_ablation, splice_donor_variant\nsplice_acceptor_variant, stop_gained\nframeshift_variant, stop_lost\nstart_lost, inframe_insertion\ninframe_deletion, missense_variant\ntranscript_amplification, protein_altering_variant.\n'
		tkMessageBox.showinfo(title='CQ', message=help3_msg)
	def backend_variant_execution(self):
		"""This method starts the backend execution steps for variant extraction."""
		string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
		if (not self.direct_ssh_mode):
			build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
		## do if the error collection variable is not
		if (not self.error_collect):
			## this first part is used to provide this instance with a start and stop attributes corresponding to the gene name
			os.system('python {a}local_scripts/gene_calculator_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --gene {f} --string_user_settings_dict \'{g}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['gene'], g=string_user_settings))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='gene_calculator_out.json', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			gene_calculator_file_abs_path = self.var_gui_abs_path + 'recent_runs/'+self.var_backend_dir+'gene_calculator_out.json'
			gene_calculator_json = {}
			if (os.access(gene_calculator_file_abs_path, os.F_OK) and os.access(gene_calculator_file_abs_path, os.R_OK)):
				with open(gene_calculator_file_abs_path, 'r') as gene_calculator_json:
					gene_calculator_json = json.load(gene_calculator_json)
				if (gene_calculator_json['error_msgs'].encode('utf-8') == 'No_error'):
					try:
						regex_match = re.search('chr:(\S+)\tstart:(\S+)\tstop:(\S+)', gene_calculator_json['gene_calculator'].encode('utf-8'))
						chrom, start, stop = regex_match.group(1), regex_match.group(2), regex_match.group(3)
						self.user_input['chrom'] = chrom
						self.user_input['start'] = start
						self.user_input['stop'] = stop
					except:
						tkMessageBox.showwarning(title='Warning', message='The gene calculator script faced a problem.')
						self.error_collect = 'Gene calculator error.'
						self.progress.destroy()
						self.widget_lock('open_widgets')
						self.next_window.configure(state='disabled')
				else:
					tkMessageBox.showwarning(title='Warning', message='The script executed on the server faced an error.')
					self.error_collect = 'Gene calculator error.'
					self.progress.destroy()
					self.widget_lock('open_widgets')
					self.next_window.configure(state='disabled')
			else:
				tkMessageBox.showwarning(title='Warning', message='The output file from the gene calculator script was not found.')
				self.error_collect = 'Gene calculator error.'
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.configure(state='disabled')
			if (not self.error_collect):
				## do the routine procedure: create local script, send and execute on backend, transfer result to frontend.
				os.system('python {a}local_scripts/id_coords_trio_variants_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --id {f} --chrom {g} --start {h} --stop {i} --cq {j} --max_af_cutoff {k} --max_af_value {l} --string_user_settings_dict \'{m}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['ID'], g=self.user_input['chrom'], h=self.user_input['start'], i=self.user_input['stop'], j=self.user_input['cq'], k=self.user_input['max_af_cutoff'], l=self.user_input['max_af_value'], m=string_user_settings))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				#
				server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='trio_variants.json', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
	def backend_igv_execution(self):
		"""This method starts the backend execution steps for IGV retrieval."""
		string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
		## do if the error collection variable is not and IGV variable is yes
		if (not self.error_collect and self.user_input['igv'] == 'yes'):
			## do the routine procedure: create local script, send and execute on backend, transfer result to frontend.
			## in this case the start and stop are both the start
			os.system('python {a}local_scripts/id_coords_trio_igv_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --id {f} --chrom {g} --start {h} --stop {i} --string_user_settings_dict \'{j}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['ID'], g=self.user_input['chrom'], h=self.user_input['start'], i=self.user_input['start'], j=string_user_settings))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(file_name='current_run.py', backend_dir_name=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
				cmd.write(server_cmd)
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='trio_igv.png', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
	def create_progress_bar(self):
		"""Aesthetic method to create an indeterminate progress bar."""
		self.progress = ttk.Progressbar(self.present_frame, orient="horizontal", length=300, mode="indeterminate")
		self.progress.pack()
		self.progress.start()
	def widget_lock(self, key_code):
		"""Aesthetic method to inactivate/activate widgets during backend execution."""
		widgets = ['self.previous_window', 'self.next_window', 'self.decipher_id_label', 'self.decipher_id_entry', 'self.gene_label', 'self.gene_entry', 'self.igv_check', 'self.help1', 'self.max_af_cuttoff_label', 'self.max_af_cuttoff_entry', 'self.max_af_value_label', 'self.max_af_value_entry', 'self.help2', 'self.cq_box', 'self.cq_check_all', 'self.user_cq_label', 'self.user_cq_entry', 'self.cq_check', 'self.help3', 'self.submit_button']
		if (key_code == 'lock_widgets'):
			for w in widgets:
				eval(w+".config(state='disabled')")
		elif (key_code == 'open_widgets'):
			for w in widgets:
				eval(w+".config(state='normal')")
	def buffer(self):
		"""This method is bound to the Run button and it orchestrates some procedural steps."""
		try:
			local_path = self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir
			for file_found in os.listdir(local_path):
				os.remove(local_path+file_found) ## clearing out the changeable directory
		except:
			pass
		self.error_collect = '' ## reinstate error_collect in case an error with input collection was made
		## do the aesthetic "running" mode
		self.widget_lock('lock_widgets')
		self.create_progress_bar()
		## use a thread to run this method, this is because 2 functions are run at the same time: the progress bar and the backend execution.
		t1=threading.Thread(target=self.initiate_backend_process, args=())
		t1.start()
	def initiate_backend_process(self):
		"""This method starts calls other methods to do the background executions."""
		self.get_user_input_function()
		## do variant extraction
		if (not self.error_collect):
			try:
				self.backend_variant_execution()
			except:
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.config(state='disabled')
		else:
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.config(state='disabled')	
		## do IGV retrieval if required
		try:
			assert self.error_collect == ''
			assert self.user_input['igv'] == 'yes'
			self.backend_igv_execution()
		except:
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.config(state='disabled')
		## this is a check for no errors on the backend side during execution
		if (not self.error_collect):
			self.variant_sanity_check_and_proceed()
		## continue to this part in case of no errors
		if (not self.error_collect and self.user_input['igv'] == 'yes'):
			self.igv_sanity_check_and_proceed()
		## continue in case of zero errors
		## activate the Next button and prepare to display the results
		if (not self.error_collect):
			self.next_window.configure(state='active')
			self.next_window.bind("<Button-1>", self.forward)
			self.next_window.bind("<Leave>", lambda event: self.next_window.configure(relief=GROOVE))
			self.next_window.bind("<Enter>", lambda event: self.next_window.configure(cursor='hand', relief=RAISED))
			#
			self.progress.destroy()
			self.widget_lock('open_widgets')
			## clean up the existing next frame
			for widget in self.next_frame.winfo_children():
				widget.destroy()
			## this decides to add/cancel the IGV tab in the results
			if (self.user_input['igv'] == 'no'):
				prepare_result_tabs_igv_excluded(gui_abs_path=self.var_gui_abs_path,previous_frame=self.present_frame,present_frame=self.next_frame,past_frame=self.previous_frame,query_info=self.user_input,backend_dir=self.var_backend_dir)
			elif (self.user_input['igv'] == 'yes'):
				prepare_result_tabs_igv_included(direct_ssh_mode=self.direct_ssh_mode,var_backend_dir=self.var_backend_dir,gui_abs_path=self.var_gui_abs_path,user_settings_var=self.var_user_settings,previous_frame=self.present_frame,present_frame=self.next_frame,past_frame=self.previous_frame,query_info=self.user_input)
	def variant_sanity_check_and_proceed(self):
		"""This method reads the JSON file from the server and checks the error key."""
		variant_file_abs_path = self.var_gui_abs_path + 'recent_runs/' + self.var_backend_dir + 'trio_variants.json'
		if (os.access(variant_file_abs_path, os.F_OK) and os.access(variant_file_abs_path, os.R_OK)):
			with open(variant_file_abs_path, 'r') as variant_json:
				variant_json = json.load(variant_json)
			variant_related_errors = variant_json['error_msgs'].encode('utf-8')
			if (variant_related_errors == 'Error'):
				tkMessageBox.showwarning(title='Warning', message='Problem retrieving variants from the server.')
				self.error_collect = 'Variant retrieval error.'
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.configure(state='disabled')
		else:
			tkMessageBox.showwarning(title='Warning', message='The output file from the server was not found.')
			self.error_collect = 'Variant retrieval error.'
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.configure(state='disabled')
	def igv_sanity_check_and_proceed(self):
		"""This method checks if the IGV image is corrupt."""
		igv_file_abs_path = self.var_gui_abs_path + 'recent_runs/' + self.var_backend_dir + 'trio_igv.png'
		if (os.access(igv_file_abs_path, os.F_OK) and os.access(igv_file_abs_path, os.R_OK)):
			check_image = Image.open(igv_file_abs_path)
			check_image.verify()
		else:
			tkMessageBox.showwarning(title='Warning', message='Problem retrieving the IGV plot from the server.')
			self.error_collect = 'IGV retrieval error.'
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.configure(state='disabled')



class gene_name_cohort:
	"""Query by gene name and cohort"""
	LOF = ['transcript_ablation','splice_donor_variant','splice_acceptor_variant','stop_gained','frameshift_variant','stop_lost','start_lost','inframe_insertion','inframe_deletion','missense_variant','transcript_amplification','protein_altering_variant']
	def __init__(self, **kwargs):
		## extracting the arguments
		self.direct_ssh_mode = kwargs['direct_ssh_mode']
		self.previous_frame_object = kwargs['previous_frame_object']
		self.previous_frame = kwargs['previous_frame']
		self.present_frame = kwargs['present_frame']
		self.next_frame = kwargs['next_frame']
		self.server_file_check = kwargs['check_server']
		self.ddd_prod_check = kwargs['check_ddd_prod']
		self.var_backend_dir = kwargs['var_backend_dir']
		self.var_gui_abs_path = kwargs['var_gui_abs_path']
		self.var_user_settings = kwargs['var_user_settings']
		## set up the title of the label frame
		self.present_frame['text'] = 'Query Input: Gene name using the entire cohort'
		## activate the Next button of the previous frame
		self.previous_frame_object.next_window.configure(state='active')
		self.previous_frame_object.next_window.bind("<Button-1>", self.previous_frame_object.forward)
		self.previous_frame_object.next_window.bind("<Leave>", lambda event: self.previous_frame_object.next_window.configure(relief=GROOVE))
		self.previous_frame_object.next_window.bind("<Enter>", lambda event: self.previous_frame_object.next_window.configure(cursor='hand', relief=RAISED))
		## hide the next and previous frames. Show the present frame
		self.next_frame.pack_forget()
		self.previous_frame.pack_forget()
		self.present_frame.pack(fill=BOTH, expand=TRUE)
		## destroy the current widgets occupying this frame (in case of a previous input layout)
		for widget in self.present_frame.winfo_children():
			widget.destroy()
		time.sleep(1)
		## the error collection variable
		self.error_collect = ''
		## setting up the scrollbars
		self.present_frame_y = Scrollbar(self.present_frame, orient=VERTICAL)
		self.present_frame_y.pack(fill=Y, side=RIGHT)
		self.present_frame_x = Scrollbar(self.present_frame, orient=HORIZONTAL)
		self.present_frame_x.pack(fill=X, side=BOTTOM)
		self.present_canvas = Canvas(self.present_frame, bg='#E0E0E0', highlightbackground='#E0E0E0', highlightcolor='#E0E0E0', yscrollcommand=self.present_frame_y.set, xscrollcommand=self.present_frame_x.set)
		self.present_canvas.pack(fill=BOTH, expand=True)
		self.present_canvas.configure(scrollregion=(0,0,1000,1000))
		self.present_frame_y.config(command=self.present_canvas.yview)
		self.present_frame_x.config(command=self.present_canvas.xview)
		self.widget_layer = Frame(self.present_canvas, bg='#E0E0E0')
		self.widget_layer.pack()
		self.present_canvas.create_window(0, 0, window=self.widget_layer, anchor='nw')
		## create the Back and Next buttons of this frame and bind them to methods
		self.window_navigation = Frame(self.widget_layer, bg='#E0E0E0')
		self.window_navigation.pack(fill=X, expand=False, pady=10, padx=100)
		self.window_navigation.columnconfigure(0, weight=1)
		self.window_navigation.columnconfigure(1, weight=1)
		self.window_navigation.rowconfigure(0, weight=1)
		#
		self.previous_window = Label(self.window_navigation, text='Back', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.previous_window.grid(row=0, column=0, sticky=E)
		self.previous_window.bind("<Button-1>", self.backward)
		self.previous_window.bind("<Leave>", lambda event: self.previous_window.configure(relief=GROOVE))
		self.previous_window.bind("<Enter>", lambda event: self.previous_window.configure(cursor='hand', relief=RAISED))
		#
		self.next_window = Label(self.window_navigation, text='Next', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.next_window.grid(row=0, column=1, sticky=W)
		self.next_window.configure(state='disabled')
		## creating the labels and entries in the input layout
		self.parameters = LabelFrame(self.widget_layer, text='Parameters', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.parameters.pack(fill=X, expand=False, pady=10, padx=100)
		self.parameters.columnconfigure(0, weight=1)
		self.parameters.columnconfigure(1, weight=1)
		self.parameters.rowconfigure(0, weight=1)
		self.parameters.rowconfigure(1, weight=1)
		#
		self.gene_label = Label(self.parameters, text='Gene name:', bg='#C8C8C8')
		self.gene_entry = Entry(self.parameters, highlightbackground='#C8C8C8')
		self.gene_label.grid(row=0, column=0, sticky=E)
		self.gene_entry.grid(row=0, column=1, sticky=W)
		#
		self.help1 = Label(self.parameters, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help1.grid(row=1, column=1, sticky=E)
		self.help1.bind("<Button-1>", self.help1_popup)
		self.help1.bind("<Leave>", lambda event: self.help1.configure(relief=GROOVE))
		self.help1.bind("<Enter>", lambda event: self.help1.configure(cursor='hand', relief=RAISED))
		#
		self.max_af = LabelFrame(self.widget_layer, text='Maximum Allele Frequency', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.max_af.pack(fill=X, expand=False, pady=10, padx=100)
		self.max_af.columnconfigure(0, weight=1)
		self.max_af.columnconfigure(1, weight=1)
		self.max_af.columnconfigure(2, weight=1)
		self.max_af.columnconfigure(3, weight=1)
		self.max_af.rowconfigure(0, weight=1)
		self.max_af.rowconfigure(1, weight=1)
		self.max_af_cuttoff_label = Label(self.max_af, text='MAX_AF cutoff:', bg='#C8C8C8')
		self.max_af_cuttoff_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_cuttoff_label.grid(row=0, column=0, sticky=E)
		self.max_af_cuttoff_entry.grid(row=0, column=1, sticky=W)
		#
		self.max_af_value_label = Label(self.max_af, text='MAX_AF equal to:', bg='#C8C8C8')
		self.max_af_value_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_value_label.grid(row=0, column=2, sticky=E)
		self.max_af_value_entry.grid(row=0, column=3, sticky=W)
		#
		self.help2 = Label(self.max_af, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help2.grid(row=1, column=3, sticky=E)
		self.help2.bind("<Button-1>", self.help2_popup)
		self.help2.bind("<Leave>", lambda event: self.help2.configure(relief=GROOVE))
		self.help2.bind("<Enter>", lambda event: self.help2.configure(cursor='hand', relief=RAISED))
		#
		self.cq_frame = LabelFrame(self.widget_layer, text='Consequence', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.cq_frame.pack(fill=X, expand=False, pady=10, padx=100)
		self.cq_frame.columnconfigure(0, weight=1)
		self.cq_frame.columnconfigure(1, weight=1)
		self.cq_frame.rowconfigure(0, weight=1)
		self.cq_frame.rowconfigure(1, weight=1)
		self.cq_frame.rowconfigure(2, weight=1)
		self.cq_frame.rowconfigure(3, weight=1)
		self.cq_frame.rowconfigure(4, weight=1)
		self.sub_frame = Frame(self.cq_frame)
		#
		self.list_scroll = Scrollbar(self.sub_frame, orient=VERTICAL)
		self.all_consequences = re.split(',', '3_prime_UTR_variant,5_prime_UTR_variant,downstream_gene_variant,feature_elongation,feature_truncation,frameshift_variant,incomplete_terminal_codon_variant,inframe_deletion,inframe_insertion,intergenic_variant,intron_variant,mature_miRNA_variant,missense_variant,nc_transcript_variant,NMD_transcript_variant,non_coding_exon_variant,regulatory_region_ablation,regulatory_region_amplification,regulatory_region_variant,splice_acceptor_variant,splice_donor_variant,splice_region_variant,stop_gained,stop_lost,stop_retained_variant,synonymous_variant,TF_binding_site_variant,TFBS_ablation,TFBS_amplification,transcript_ablation,transcript_amplification,upstream_gene_variant')
		all_cq = tuple(self.all_consequences)
		cq_var = StringVar(value=all_cq)
		self.cq_label = Label(self.cq_frame, text='Consequence list:', bg='#C8C8C8')
		self.cq_box = Listbox(self.sub_frame, listvariable=cq_var, height=8, width=40, selectmode=MULTIPLE, yscrollcommand=self.list_scroll.set)
		self.list_scroll.config(command=self.cq_box.yview)
		self.list_scroll.pack(side=RIGHT, fill=Y)
		self.cq_label.grid(column=0, row=0, sticky=E)
		self.cq_box.pack(fill=BOTH, expand=True)
		self.sub_frame.grid(column=1, row=0, sticky=W)
		#
		self.cq_all_var = IntVar()
		self.cq_check_all = Checkbutton(self.cq_frame, text='All CQ in the list above', onvalue=1, offvalue=0, variable=self.cq_all_var, bg='#C8C8C8')
		self.cq_check_all.grid(column=1, row=1, sticky=W)
		#
		self.user_cq_label = Label(self.cq_frame, text='Other user-defined\nconsequences:', bg='#C8C8C8')
		self.user_cq_entry = Entry(self.cq_frame, highlightbackground='#C8C8C8')
		self.user_cq_label.grid(column=0, row=2, sticky=E)
		self.user_cq_entry.grid(column=1, row=2, sticky=W)
		self.cq_lof_var = IntVar()
		#
		self.cq_check = Checkbutton(self.cq_frame, text='Functional and LOF consequences', onvalue=1, offvalue=0, variable=self.cq_lof_var, bg='#C8C8C8')
		self.cq_check.grid(column=1, row=3, sticky=W)
		#
		self.help3 = Label(self.cq_frame, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help3.grid(row=4, column=1, sticky=E)
		self.help3.bind("<Button-1>", self.help3_popup)
		self.help3.bind("<Leave>", lambda event: self.help3.configure(relief=GROOVE))
		self.help3.bind("<Enter>", lambda event: self.help3.configure(cursor='hand', relief=RAISED))
		#
		self.submit_button = Button(self.widget_layer, text='Run', command=self.buffer, highlightbackground='#E0E0E0')
		self.submit_button.pack(pady=10, padx=100)
		## if the global variables that check the dot server/ddd_prod files are false or None, the Run button is disabled.
		if (not self.server_file_check or not self.ddd_prod_check):
			self.submit_button.configure(state='disabled')
	def forward(self, event):
		"""Method belongs to the Next button."""
		self.present_frame.pack_forget()
		self.next_frame.pack(fill=BOTH, expand=TRUE)
	def backward(self, event):
		"""Method belongs to the Back button."""
		self.present_frame.pack_forget()
		self.next_frame.pack_forget()
		self.previous_frame.pack(fill=BOTH, expand=TRUE)
	def get_user_input_function(self):
		"""Method that gets the user input parameters and stores them."""
		self.user_input = {}
		cq_list = []
		self.user_input['gene'] = str(self.gene_entry.get())
		self.user_input['max_af_cutoff'] = self.max_af_cuttoff_entry.get() or 'ignore'
		self.user_input['max_af_value'] = self.max_af_value_entry.get() or 'ignore'
		## preparing the user-defined CQ
		if (self.cq_all_var.get()):
			cq_list.extend(self.all_consequences)
		else:
			for indx in self.cq_box.curselection():
				cq_list.append(self.all_consequences[int(indx)])
		for entry in re.split(',', self.user_cq_entry.get()):
			if (entry):
				cq_list.append(entry)
		if (self.cq_lof_var.get()):
			cq_list.extend(gene_name_cohort.LOF)
		self.user_input['cq'] = ','.join(list(set(cq_list)))
		## catch some errors eg. not all necessay entries are entered by the user
		try:
			assert all([self.user_input['gene'], self.user_input['cq']])
		except:
			tkMessageBox.showwarning(title='Warning', message='These entries are mandatory: Gene, CQ.')
			self.error_collect = 'Input error.'
	def help1_popup(self, event):
		"""This method belongs to the first "?"."""
		help1_msg = 'Gene : The Gene name of which genomic coordinates will be retrieved from ddd_prod.\n'
		tkMessageBox.showinfo(title='Parameters', message=help1_msg)
	def help2_popup(self, event):
		"""This method belongs to the second "?"."""
		help2_msg = 'Max_af_cutoff (maximum alele frequency) : variants with MAX_AF below this cutoff are included.\n\nMax_af_value : variants with MAX_AF equal to this value are selected.\n\nNote : applying a MAX_AF threshold is advised in this case of parsing all cohort VCFs, this will decrease the number of selected variants and speed up the file transfer from the server.\n'
		tkMessageBox.showinfo(title='MAX_AF', message=help2_msg)
	def help3_popup(self, event):
		"""This method belongs to the third "?"."""
		help3_msg = 'Consequence : Select variant consequence using any or all of the options given.\n\nFunctional and LOF include :\ntranscript_ablation, splice_donor_variant\nsplice_acceptor_variant, stop_gained\nframeshift_variant, stop_lost\nstart_lost, inframe_insertion\ninframe_deletion, missense_variant\ntranscript_amplification, protein_altering_variant.\n'
		tkMessageBox.showinfo(title='CQ', message=help3_msg)
	def backend_variant_execution(self):
		"""This method starts the backend execution steps for variant extraction."""
		string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
		if (not self.direct_ssh_mode):
			build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)		
		## do if the error collection variable is not
		if (not self.error_collect):
			## do the routine procedure: create local script, send and execute on backend, transfer result to frontend.
			os.system('python {a}local_scripts/gene_cohort_1_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --gene {f} --cq {g} --max_af_cutoff {h} --max_af_value {i} --string_user_settings_dict \'{j}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['gene'], g=self.user_input['cq'], h=self.user_input['max_af_cutoff'], i=self.user_input['max_af_value'], j=string_user_settings))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
				cmd.write(server_cmd)
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='cohort_variants.json', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			self.sanity_check_and_proceed()
			## do if the error collection variable is not
			if (not self.error_collect):
				#
				os.system('python {a}local_scripts/cohort_2_source_builder.py --o {b}recent_runs/{c}current_run.py --remote_dir {d}'.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_backend_dir))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				#
				server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='selected_cohort_variants.tsv.gz', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				#
				os.system('gunzip {a}recent_runs/{b}selected_cohort_variants.tsv.gz'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
	def create_progress_bar(self):
		"""Aesthetic method to create an indeterminate progress bar."""
		self.progress = ttk.Progressbar(self.present_frame, orient="horizontal", length=300, mode="indeterminate")
		self.progress.pack()
		self.progress.start()
	def widget_lock(self, key_code):
		"""Aesthetic method to inactivate/activate widgets during backend execution."""
		widgets = ['self.previous_window', 'self.next_window', 'self.gene_label', 'self.gene_entry', 'self.help1', 'self.max_af_cuttoff_label', 'self.max_af_cuttoff_entry', 'self.max_af_value_label', 'self.max_af_value_entry', 'self.help2', 'self.cq_label', 'self.cq_box', 'self.cq_check_all', 'self.user_cq_label', 'self.user_cq_entry', 'self.cq_check', 'self.help3', 'self.submit_button']
		if (key_code == 'lock_widgets'):
			for w in widgets:
				eval(w+".config(state='disabled')")
		elif (key_code == 'open_widgets'):
			for w in widgets:
				eval(w+".config(state='normal')")
	def buffer(self):
		"""This method is bound to the Run button and it orchestrates some procedural steps."""
		try:
			local_path = self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir
			for file_found in os.listdir(local_path):
				os.remove(local_path+file_found) ## clearing out the changeable directory
		except:
			pass
		self.error_collect = '' ## reinstate error_collect in case an error with input collection was made
		## do the aesthetic "running" mode
		self.widget_lock('lock_widgets')
		self.create_progress_bar()
		## use a thread to run this method, this is because 2 functions are run at the same time: the progress bar and the backend execution.
		t1=threading.Thread(target=self.initiate_backend_process, args=())
		t1.start()
	def initiate_backend_process(self):
		"""This method starts calls other methods to do the background executions."""
		self.get_user_input_function()
		## do variant extraction
		if (not self.error_collect):
			try:
				self.backend_variant_execution()
			except:
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.config(state='disabled')
		else:
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.config(state='disabled')
		## continue in case of zero errors
		## activate the Next button and prepare to display the results
		if (not self.error_collect):
			self.next_window.configure(state='active')
			self.next_window.bind("<Button-1>", self.forward)
			self.next_window.bind("<Leave>", lambda event: self.next_window.configure(relief=GROOVE))
			self.next_window.bind("<Enter>", lambda event: self.next_window.configure(cursor='hand', relief=RAISED))
			#
			self.progress.destroy()
			self.widget_lock('open_widgets')
			## clean up the existing next frame
			for widget in self.next_frame.winfo_children():
				widget.destroy()
			## prepare to display results
			prepare_result_tabs_cohort(gui_abs_path=self.var_gui_abs_path,previous_frame=self.present_frame,present_frame=self.next_frame,past_frame=self.previous_frame,query_info=self.user_input,backend_dir=self.var_backend_dir)
	def sanity_check_and_proceed(self):
		"""This method checks if the IGV image is corrupt."""
		variant_file_abs_path = self.var_gui_abs_path + 'recent_runs/' + self.var_backend_dir + 'cohort_variants.json'
		if (os.access(variant_file_abs_path, os.F_OK) and os.access(variant_file_abs_path, os.R_OK)):
			with open(variant_file_abs_path, 'r') as variant_json:
				variant_json = json.load(variant_json)
			variant_related_errors = variant_json['error_msgs'].encode('utf-8')
			if (variant_related_errors == 'Error'):
				tkMessageBox.showwarning(title='Warning', message='Problem retrieving variants from the server.')
				self.error_collect = 'Variant retrieval error.'
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.configure(state='disabled')
		else:
			tkMessageBox.showwarning(title='Warning', message='The output file from the server was not found.')
			self.error_collect = 'Variant retrieval error.'
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.configure(state='disabled')



class hgvs_child_id:
	"""Query by HGVS term and decipher ID"""
	LOF = ['transcript_ablation','splice_donor_variant','splice_acceptor_variant','stop_gained','frameshift_variant','stop_lost','start_lost','inframe_insertion','inframe_deletion','missense_variant','transcript_amplification','protein_altering_variant']
	def __init__(self, **kwargs):
		## extracting the arguments
		self.direct_ssh_mode = kwargs['direct_ssh_mode']
		self.previous_frame_object = kwargs['previous_frame_object']
		self.previous_frame = kwargs['previous_frame']
		self.present_frame = kwargs['present_frame']
		self.next_frame = kwargs['next_frame']
		self.var_backend_dir = kwargs['var_backend_dir']
		self.server_file_check = kwargs['check_server']
		self.igv_file_check = kwargs['check_igv']
		self.ddd_prod_check = kwargs['check_ddd_prod']
		self.var_gui_abs_path = kwargs['var_gui_abs_path']
		self.var_user_settings = kwargs['var_user_settings']
		## set up the title of the label frame
		self.present_frame['text'] = 'Query Input: HGVS term using a child ID'
		## activate the Next button of the previous frame
		self.previous_frame_object.next_window.configure(state='active')
		self.previous_frame_object.next_window.bind("<Button-1>", self.previous_frame_object.forward)
		self.previous_frame_object.next_window.bind("<Leave>", lambda event: self.previous_frame_object.next_window.configure(relief=GROOVE))
		self.previous_frame_object.next_window.bind("<Enter>", lambda event: self.previous_frame_object.next_window.configure(cursor='hand', relief=RAISED))
		## hide the next and previous frames. Show the present frame
		self.next_frame.pack_forget()
		self.previous_frame.pack_forget()
		self.present_frame.pack(fill=BOTH, expand=TRUE)
		## destroy the current widgets occupying this frame (in case of a previous input layout)
		for widget in self.present_frame.winfo_children():
			widget.destroy()
		time.sleep(1)
		## the error collection variable
		self.error_collect = ''
		## setting up the scrollbars
		self.present_frame_y = Scrollbar(self.present_frame, orient=VERTICAL)
		self.present_frame_y.pack(fill=Y, side=RIGHT)
		self.present_frame_x = Scrollbar(self.present_frame, orient=HORIZONTAL)
		self.present_frame_x.pack(fill=X, side=BOTTOM)
		self.present_canvas = Canvas(self.present_frame, bg='#E0E0E0', highlightbackground='#E0E0E0', highlightcolor='#E0E0E0', yscrollcommand=self.present_frame_y.set, xscrollcommand=self.present_frame_x.set)
		self.present_canvas.pack(fill=BOTH, expand=True)
		self.present_canvas.configure(scrollregion=(0,0,1000,1000))
		self.present_frame_y.config(command=self.present_canvas.yview)
		self.present_frame_x.config(command=self.present_canvas.xview)
		self.widget_layer = Frame(self.present_canvas, bg='#E0E0E0')
		self.widget_layer.pack()
		self.present_canvas.create_window(0, 0, window=self.widget_layer, anchor='nw')
		## create the Back and Next buttons of this frame and bind them to methods
		self.window_navigation = Frame(self.widget_layer, bg='#E0E0E0')
		self.window_navigation.pack(fill=X, expand=False, pady=10, padx=100)
		self.window_navigation.columnconfigure(0, weight=1)
		self.window_navigation.columnconfigure(1, weight=1)
		self.window_navigation.rowconfigure(0, weight=1)
		#
		self.previous_window = Label(self.window_navigation, text='Back', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.previous_window.grid(row=0, column=0, sticky=E)
		self.previous_window.bind("<Button-1>", self.backward)
		self.previous_window.bind("<Leave>", lambda event: self.previous_window.configure(relief=GROOVE))
		self.previous_window.bind("<Enter>", lambda event: self.previous_window.configure(cursor='hand', relief=RAISED))
		#
		self.next_window = Label(self.window_navigation, text='Next', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.next_window.grid(row=0, column=1, sticky=W)
		self.next_window.configure(state='disabled')
		## creating the labels and entries in the input layout
		self.parameters = LabelFrame(self.widget_layer, text='Parameters', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.parameters.pack(fill=X, expand=False, pady=10, padx=100)
		self.parameters.columnconfigure(0, weight=1)
		self.parameters.columnconfigure(1, weight=1)
		self.parameters.columnconfigure(2, weight=1)
		self.parameters.rowconfigure(0, weight=1)
		self.parameters.rowconfigure(1, weight=1)
		self.parameters.rowconfigure(2, weight=1)
		self.decipher_id_label = Label(self.parameters, text='ID:', bg='#C8C8C8')
		self.decipher_id_entry = Entry(self.parameters, highlightbackground='#C8C8C8')
		self.decipher_id_label.grid(row=0, column=0, sticky=E)
		self.decipher_id_entry.grid(row=0, column=1, sticky=W)
		#
		self.hgvs_label = Label(self.parameters, text='HGVS term:', bg='#C8C8C8')
		self.hgvs_entry = Entry(self.parameters, highlightbackground='#C8C8C8')
		self.hgvs_label.grid(row=1, column=0, sticky=E)
		self.hgvs_entry.grid(row=1, column=1, sticky=W)
		#
		self.igv_var = IntVar()
		self.igv_check = Checkbutton(self.parameters, text='Get IGV plot', onvalue=1, offvalue=0, variable=self.igv_var, bg='#C8C8C8')
		self.igv_check.grid(column=2, row=0, sticky=W)
		## if the dot igv file check is not, diable the igv checkbutton
		if (not self.igv_file_check):
			self.igv_check.configure(state='disabled')
		#
		self.help1 = Label(self.parameters, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help1.grid(row=2, column=2, sticky=E)
		self.help1.bind("<Button-1>", self.help1_popup)
		self.help1.bind("<Leave>", lambda event: self.help1.configure(relief=GROOVE))
		self.help1.bind("<Enter>", lambda event: self.help1.configure(cursor='hand', relief=RAISED))
		#
		self.max_af = LabelFrame(self.widget_layer, text='Maximum Allele Frequency', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.max_af.pack(fill=X, expand=False, pady=10, padx=100)
		self.max_af.columnconfigure(0, weight=1)
		self.max_af.columnconfigure(1, weight=1)
		self.max_af.columnconfigure(2, weight=1)
		self.max_af.columnconfigure(3, weight=1)
		self.max_af.rowconfigure(0, weight=1)
		self.max_af.rowconfigure(1, weight=1)
		self.max_af_cuttoff_label = Label(self.max_af, text='MAX_AF cutoff:', bg='#C8C8C8')
		self.max_af_cuttoff_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_cuttoff_label.grid(row=0, column=0, sticky=E)
		self.max_af_cuttoff_entry.grid(row=0, column=1, sticky=W)
		#
		self.max_af_value_label = Label(self.max_af, text='MAX_AF equal to:', bg='#C8C8C8')
		self.max_af_value_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_value_label.grid(row=0, column=2, sticky=E)
		self.max_af_value_entry.grid(row=0, column=3, sticky=W)
		#
		self.help2 = Label(self.max_af, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help2.grid(row=1, column=3, sticky=E)
		self.help2.bind("<Button-1>", self.help2_popup)
		self.help2.bind("<Leave>", lambda event: self.help2.configure(relief=GROOVE))
		self.help2.bind("<Enter>", lambda event: self.help2.configure(cursor='hand', relief=RAISED))
		#
		self.cq_frame = LabelFrame(self.widget_layer, text='Consequence', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.cq_frame.pack(fill=X, expand=False, pady=10, padx=100)
		self.cq_frame.columnconfigure(0, weight=1)
		self.cq_frame.columnconfigure(1, weight=1)
		self.cq_frame.rowconfigure(0, weight=1)
		self.cq_frame.rowconfigure(1, weight=1)
		self.cq_frame.rowconfigure(2, weight=1)
		self.cq_frame.rowconfigure(3, weight=1)
		self.cq_frame.rowconfigure(4, weight=1)
		self.sub_frame = Frame(self.cq_frame)
		#
		self.list_scroll = Scrollbar(self.sub_frame, orient=VERTICAL)
		self.all_consequences = re.split(',', '3_prime_UTR_variant,5_prime_UTR_variant,downstream_gene_variant,feature_elongation,feature_truncation,frameshift_variant,incomplete_terminal_codon_variant,inframe_deletion,inframe_insertion,intergenic_variant,intron_variant,mature_miRNA_variant,missense_variant,nc_transcript_variant,NMD_transcript_variant,non_coding_exon_variant,regulatory_region_ablation,regulatory_region_amplification,regulatory_region_variant,splice_acceptor_variant,splice_donor_variant,splice_region_variant,stop_gained,stop_lost,stop_retained_variant,synonymous_variant,TF_binding_site_variant,TFBS_ablation,TFBS_amplification,transcript_ablation,transcript_amplification,upstream_gene_variant')
		all_cq = tuple(self.all_consequences)
		cq_var = StringVar(value=all_cq)
		self.cq_label = Label(self.cq_frame, text='Consequence list:', bg='#C8C8C8')
		self.cq_box = Listbox(self.sub_frame, listvariable=cq_var, height=8, width=40, selectmode=MULTIPLE, yscrollcommand=self.list_scroll.set)
		self.list_scroll.config(command=self.cq_box.yview)
		self.list_scroll.pack(side=RIGHT, fill=Y)
		self.cq_label.grid(column=0, row=0, sticky=E)
		self.cq_box.pack(fill=BOTH, expand=True)
		self.sub_frame.grid(column=1, row=0, sticky=W)
		#
		self.cq_all_var = IntVar()
		self.cq_check_all = Checkbutton(self.cq_frame, text='All CQ in the list above', onvalue=1, offvalue=0, variable=self.cq_all_var, bg='#C8C8C8')
		self.cq_check_all.grid(column=1, row=1, sticky=W)
		#
		self.user_cq_label = Label(self.cq_frame, text='Other user-defined\nconsequences:', bg='#C8C8C8')
		self.user_cq_entry = Entry(self.cq_frame, highlightbackground='#C8C8C8')
		self.user_cq_label.grid(column=0, row=2, sticky=E)
		self.user_cq_entry.grid(column=1, row=2, sticky=W)
		#
		self.cq_lof_var = IntVar()
		#
		self.cq_check = Checkbutton(self.cq_frame, text='Functional and LOF consequences', onvalue=1, offvalue=0, variable=self.cq_lof_var, bg='#C8C8C8')
		self.cq_check.grid(column=1, row=3, sticky=W)
		#
		self.help3 = Label(self.cq_frame, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help3.grid(row=4, column=1, sticky=E)
		self.help3.bind("<Button-1>", self.help3_popup)
		self.help3.bind("<Leave>", lambda event: self.help3.configure(relief=GROOVE))
		self.help3.bind("<Enter>", lambda event: self.help3.configure(cursor='hand', relief=RAISED))
		#
		self.submit_button = Button(self.widget_layer, text='Run', command=self.buffer, highlightbackground='#E0E0E0')
		self.submit_button.pack(pady=10, padx=100)
		## if the global variables that check the dot server/ddd_prod files are false or None, the Run button is disabled.
		if (not self.server_file_check or not self.ddd_prod_check):
			self.submit_button.configure(state='disabled')
	def forward(self, event):
		"""Method belongs to the Next button."""
		self.present_frame.pack_forget()
		self.next_frame.pack(fill=BOTH, expand=TRUE)
	def backward(self, event):
		"""Method belongs to the Back button."""
		self.present_frame.pack_forget()
		self.present_frame.pack_forget()
		self.previous_frame.pack(fill=BOTH, expand=TRUE)
	def get_user_input_function(self):
		"""Method that gets the user input parameters and stores them."""
		self.user_input = {}
		cq_list = []
		self.user_input['ID'] = str(self.decipher_id_entry.get())
		self.user_input['hgvs'] = str(self.hgvs_entry.get())
		if (self.igv_var.get()):
			self.user_input['igv'] = 'yes'
		else:
			self.user_input['igv'] = 'no'
		self.user_input['max_af_cutoff'] = self.max_af_cuttoff_entry.get() or 'ignore'
		self.user_input['max_af_value'] = self.max_af_value_entry.get() or 'ignore'
		## preparing the user-defined CQ
		if (self.cq_all_var.get()):
			cq_list.extend(self.all_consequences)
		else:
			for indx in self.cq_box.curselection():
				cq_list.append(self.all_consequences[int(indx)])
		for entry in re.split(',', self.user_cq_entry.get()):
			if (entry):
				cq_list.append(entry)
		if (self.cq_lof_var.get()):
			cq_list.extend(hgvs_child_id.LOF)
		self.user_input['cq'] = ','.join(list(set(cq_list)))
		## catch some errors eg. not all necessay entries are entered by the user or when start is greater than stop
		try:
			assert all([self.user_input['ID'], self.user_input['hgvs'], self.user_input['cq']])
		except:
			tkMessageBox.showwarning(title='Warning', message='These entries are mandatory: child ID, HGVS, CQ.')
			self.error_collect = 'Input error.'
	def help1_popup(self, event):
		"""This method belongs to the first "?"."""
		help1_msg = 'ID : The child\'s id (person stable id or decipher id).\n\nHGVS : The HGVS term of which genomic coordinates will be retrieved from ddd_prod.\n\nIGV : This option will be disabled if the ".igv_user" file is not found in the current directory or its parent directory. The IGV plot for the trio is retrieved.\n'
		tkMessageBox.showinfo(title='Parameters', message=help1_msg)
	def help2_popup(self, event):
		"""This method belongs to the second "?"."""
		help2_msg = 'Max_af_cutoff (maximum alele frequency) : variants with MAX_AF below this cutoff are included.\n\nMax_af_value : variants with MAX_AF equal to this value are selected.\n'
		tkMessageBox.showinfo(title='MAX_AF', message=help2_msg)
	def help3_popup(self, event):
		"""This method belongs to the third "?"."""
		help3_msg = 'Consequence : Select variant consequence using any or all of the options given.\n\nFunctional and LOF include :\ntranscript_ablation, splice_donor_variant\nsplice_acceptor_variant, stop_gained\nframeshift_variant, stop_lost\nstart_lost, inframe_insertion\ninframe_deletion, missense_variant\ntranscript_amplification, protein_altering_variant.\n'
		tkMessageBox.showinfo(title='CQ', message=help3_msg)
	def backend_variant_execution(self):
		"""This method starts the backend execution steps for variant extraction."""
		string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
		if (not self.direct_ssh_mode):
			build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
		## do if the error collection variable is not
		if (not self.error_collect):
			is_an_ensemble_transcript = None
			is_a_refseq_transcript = None
			if (re.search('^(ENST\d+)', self.user_input['hgvs'])):
				is_an_ensemble_transcript = True
				is_a_refseq_transcript = False
			elif (re.search('^[NX]', self.user_input['hgvs'])):
				is_a_refseq_transcript = True
				is_an_ensemble_transcript = False
			## Ensemble case procedure:
			if (is_an_ensemble_transcript):
				## extract the transcript name
				regex_m = re.search('^(ENST\d+)', self.user_input['hgvs'])
				user_transcript = regex_m.group(1)
				##
				if (not self.direct_ssh_mode):
					build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
				##
				os.system('python {a}local_scripts/hgvs_calculator_ensemble_source_builder.py --o {b}recent_runs/{c}current_run.pl --remote_dir {d} --hgvs_transcript \'{e}\' --hgvs_term \'{f}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_backend_dir, e=user_transcript, f=self.user_input['hgvs']))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.pl', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.pl', command='perl {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.pl'))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='hgvs_coords.tsv', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				hgvs_calculator_file_abs_path = self.var_gui_abs_path + 'recent_runs/' + self.var_backend_dir + 'hgvs_coords.tsv'
				##
				if (os.access(hgvs_calculator_file_abs_path, os.F_OK) and os.access(hgvs_calculator_file_abs_path, os.R_OK)):
					with open(hgvs_calculator_file_abs_path, 'r') as hgvs_calculator_tsv:
						hgvs_calculator_tsv = hgvs_calculator_tsv.readlines()
					try:
						hgvs_calculator_tsv_line = re.sub('\n', '', hgvs_calculator_tsv[0])
						temp = hgvs_calculator_tsv_line.split('\t')
						self.user_input['chrom'] = temp[0]
						self.user_input['start'] = temp[1]
						self.user_input['stop'] = temp[1]
					except:
						self.error_collect = 'HGVS calculator error.'
				else:
					self.error_collect = 'HGVS calculator error.'
			elif (is_a_refseq_transcript):# Refseq case procedure:
				## create expect file
				if (not self.direct_ssh_mode):
					build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
				##
				os.system('python {a}local_scripts/hgvs_calculator_refseq_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --hgvs \'{f}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['hgvs']))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='hgvs_coords.tsv', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				hgvs_calculator_file_abs_path = self.var_gui_abs_path + 'recent_runs/' + self.var_backend_dir + 'hgvs_coords.tsv'
				##
				if (os.access(hgvs_calculator_file_abs_path, os.F_OK) and os.access(hgvs_calculator_file_abs_path, os.R_OK)):
					with open(hgvs_calculator_file_abs_path, 'r') as hgvs_calculator_tsv:
						hgvs_calculator_tsv = hgvs_calculator_tsv.readlines()
					try:
						hgvs_calculator_tsv_line = re.sub('\n', '', hgvs_calculator_tsv[0])
						temp = hgvs_calculator_tsv_line.split('\t')
						self.user_input['chrom'] = temp[0]
						self.user_input['start'] = temp[1]
						self.user_input['stop'] = temp[1]
					except:
						self.error_collect = 'HGVS calculator error.'
				else:
					self.error_collect = 'HGVS calculator error.'
		## do if the error collection variable is not
		if (not self.error_collect):
			## do the routine procedure: create local script, send and execute on backend, transfer result to frontend.
			os.system('python {a}local_scripts/id_coords_trio_variants_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --id {f} --chrom {g} --start {h} --stop {i} --cq {j} --max_af_cutoff {k} --max_af_value {l} --string_user_settings_dict \'{m}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['ID'], g=self.user_input['chrom'], h=self.user_input['start'], i=self.user_input['stop'], j=self.user_input['cq'], k=self.user_input['max_af_cutoff'], l=self.user_input['max_af_value'], m=string_user_settings))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
				cmd.write(server_cmd)
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='trio_variants.json', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
	def backend_igv_execution(self):
		"""This method starts the backend execution steps for IGV retrieval."""
		string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
		if (not self.error_collect and self.user_input['igv'] == 'yes'):
			#
			os.system('python {a}local_scripts/id_coords_trio_igv_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --id {f} --chrom {g} --start {h} --stop {i} --string_user_settings_dict \'{j}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['ID'], g=self.user_input['chrom'], h=self.user_input['start'], i=self.user_input['start'], j=string_user_settings))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(file_name='current_run.py', backend_dir_name=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
				cmd.write(server_cmd)
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='trio_igv.png', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))	
	def create_progress_bar(self):
		"""Aesthetic method to create an indeterminate progress bar."""
		self.progress = ttk.Progressbar(self.present_frame, orient="horizontal", length=300, mode="indeterminate")
		self.progress.pack()
		self.progress.start()
	def widget_lock(self, key_code):
		"""Aesthetic method to inactivate/activate widgets during backend execution."""
		widgets = ['self.previous_window', 'self.next_window', 'self.decipher_id_label', 'self.decipher_id_entry', 'self.hgvs_label', 'self.hgvs_entry', 'self.igv_check', 'self.help1', 'self.max_af_cuttoff_label', 'self.max_af_cuttoff_entry', 'self.max_af_value_label', 'self.max_af_value_entry', 'self.help2', 'self.cq_label', 'self.cq_box', 'self.cq_check_all', 'self.user_cq_label', 'self.user_cq_entry', 'self.cq_check', 'self.help3', 'self.submit_button']
		if (key_code == 'lock_widgets'):
			for w in widgets:
				eval(w+".config(state='disabled')")
		elif (key_code == 'open_widgets'):
			for w in widgets:
				eval(w+".config(state='normal')")
	def buffer(self):
		"""This method is bound to the Run button and it orchestrates some procedural steps."""
		try:
			local_path = self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir
			for file_found in os.listdir(local_path):
				os.remove(local_path+file_found) ## clearing out the changeable directory
		except:
			pass
		self.error_collect = '' ## reinstate error_collect in case an error with input collection was made
		## do the aesthetic "running" mode
		self.widget_lock('lock_widgets')
		self.create_progress_bar()
		## use a thread to run this method
		t1=threading.Thread(target=self.initiate_backend_process, args=())
		t1.start()
	def initiate_backend_process(self):
		"""This method starts calls other methods to do the background executions."""
		self.get_user_input_function()
		## do variant extraction
		if (not self.error_collect):
			try:
				self.backend_variant_execution()
			except:
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.config(state='disabled')
		else:
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.config(state='disabled')	
		## do IGV retrieval if required
		try:
			assert self.error_collect == ''
			assert self.user_input['igv'] == 'yes'
			self.backend_igv_execution()
		except:
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.config(state='disabled')
		## this is a check for no errors on the backend side during execution
		if (not self.error_collect):
			self.variant_sanity_check_and_proceed()
		## continue to this part in case of no errors
		if (not self.error_collect and self.user_input['igv'] == 'yes'):
			self.igv_sanity_check_and_proceed()
		## continue in case of zero errors
		## activate the Next button and prepare to display the results
		if (not self.error_collect):
			self.next_window.configure(state='active')
			self.next_window.bind("<Button-1>", self.forward)
			self.next_window.bind("<Leave>", lambda event: self.next_window.configure(relief=GROOVE))
			self.next_window.bind("<Enter>", lambda event: self.next_window.configure(cursor='hand', relief=RAISED))
			#
			self.progress.destroy()
			self.widget_lock('open_widgets')
			## clean up the existing next frame
			for widget in self.next_frame.winfo_children():
				widget.destroy()
			## this decides to add/cancel the IGV tab in the results
			if (self.user_input['igv'] == 'no'):
				prepare_result_tabs_igv_excluded(gui_abs_path=self.var_gui_abs_path,previous_frame=self.present_frame,present_frame=self.next_frame,past_frame=self.previous_frame,query_info=self.user_input,backend_dir=self.var_backend_dir)
			elif (self.user_input['igv'] == 'yes'):
				prepare_result_tabs_igv_included(direct_ssh_mode=self.direct_ssh_mode,var_backend_dir=self.var_backend_dir,gui_abs_path=self.var_gui_abs_path,user_settings_var=self.var_user_settings,previous_frame=self.present_frame,present_frame=self.next_frame,past_frame=self.previous_frame,query_info=self.user_input)
	def variant_sanity_check_and_proceed(self):
		"""This method reads the JSON file from the server and checks the error key."""
		variant_file_abs_path = self.var_gui_abs_path + 'recent_runs/'+self.var_backend_dir+'trio_variants.json'
		if (os.access(variant_file_abs_path, os.F_OK) and os.access(variant_file_abs_path, os.R_OK)):
			with open(variant_file_abs_path, 'r') as variant_json:
				variant_json = json.load(variant_json)
			variant_related_errors = variant_json['error_msgs'].encode('utf-8')
			if (variant_related_errors == 'Error'):
				tkMessageBox.showwarning(title='Warning', message='Problem retrieving variants from the server.')
				self.error_collect = 'Variant retrieval error.'
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.configure(state='disabled')
		else:
			tkMessageBox.showwarning(title='Warning', message='The output file from the server was not found.')
			self.error_collect = 'Variant retrieval error.'
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.configure(state='disabled')
	def igv_sanity_check_and_proceed(self):
		"""This method checks if the IGV image is corrupt."""
		igv_file_abs_path = self.var_gui_abs_path + 'recent_runs/'+self.var_backend_dir+'trio_igv.png'
		if (os.access(igv_file_abs_path, os.F_OK) and os.access(igv_file_abs_path, os.R_OK)):
			check_image = Image.open(igv_file_abs_path)
			check_image.verify()
		else:
			tkMessageBox.showwarning(title='Warning', message='Problem retrieving the IGV plot from the server.')
			self.error_collect = 'IGV retrieval error.'
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.configure(state='disabled')



class hgvs_cohort:
	"""Query by HGVS term and cohort"""
	LOF = ['transcript_ablation','splice_donor_variant','splice_acceptor_variant','stop_gained','frameshift_variant','stop_lost','start_lost','inframe_insertion','inframe_deletion','missense_variant','transcript_amplification','protein_altering_variant']
	def __init__(self, **kwargs):
		## extracting the arguments
		self.direct_ssh_mode = kwargs['direct_ssh_mode']
		self.previous_frame_object = kwargs['previous_frame_object']
		self.previous_frame = kwargs['previous_frame']
		self.present_frame = kwargs['present_frame']
		self.next_frame = kwargs['next_frame']
		self.server_file_check = kwargs['check_server']
		self.ddd_prod_check = kwargs['check_ddd_prod']
		self.var_backend_dir = kwargs['var_backend_dir']
		self.var_gui_abs_path = kwargs['var_gui_abs_path']
		self.var_user_settings = kwargs['var_user_settings']
		## set up the title of the label frame
		self.present_frame['text'] = 'Query Input: HGVS term using the entire cohort'
		## activate the Next button of the previous frame
		self.previous_frame_object.next_window.configure(state='active')
		self.previous_frame_object.next_window.bind("<Button-1>", self.previous_frame_object.forward)
		self.previous_frame_object.next_window.bind("<Leave>", lambda event: self.previous_frame_object.next_window.configure(relief=GROOVE))
		self.previous_frame_object.next_window.bind("<Enter>", lambda event: self.previous_frame_object.next_window.configure(cursor='hand', relief=RAISED))
		## hide the next and previous frames. Show the present frame
		self.next_frame.pack_forget()
		self.previous_frame.pack_forget()
		self.present_frame.pack(fill=BOTH, expand=TRUE)
		## destroy the current widgets occupying this frame (in case of a previous input layout)
		for widget in self.present_frame.winfo_children():
			widget.destroy()
		time.sleep(1)
		## the error collection variable
		self.error_collect = ''
		## setting up the scrollbars
		self.present_frame_y = Scrollbar(self.present_frame, orient=VERTICAL)
		self.present_frame_y.pack(fill=Y, side=RIGHT)
		self.present_frame_x = Scrollbar(self.present_frame, orient=HORIZONTAL)
		self.present_frame_x.pack(fill=X, side=BOTTOM)
		self.present_canvas = Canvas(self.present_frame, bg='#E0E0E0', highlightbackground='#E0E0E0', highlightcolor='#E0E0E0', yscrollcommand=self.present_frame_y.set, xscrollcommand=self.present_frame_x.set)
		self.present_canvas.pack(fill=BOTH, expand=True)
		self.present_canvas.configure(scrollregion=(0,0,1000,1000))
		self.present_frame_y.config(command=self.present_canvas.yview)
		self.present_frame_x.config(command=self.present_canvas.xview)
		self.widget_layer = Frame(self.present_canvas, bg='#E0E0E0')
		self.widget_layer.pack()
		self.present_canvas.create_window(0, 0, window=self.widget_layer, anchor='nw')
		## create the Back and Next buttons of this frame and bind them to methods
		self.window_navigation = Frame(self.widget_layer, bg='#E0E0E0')
		self.window_navigation.pack(fill=X, expand=False, pady=10, padx=100)
		self.window_navigation.columnconfigure(0, weight=1)
		self.window_navigation.columnconfigure(1, weight=1)
		self.window_navigation.rowconfigure(0, weight=1)
		#
		self.previous_window = Label(self.window_navigation, text='Back', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.previous_window.grid(row=0, column=0, sticky=E)
		self.previous_window.bind("<Button-1>", self.backward)
		self.previous_window.bind("<Leave>", lambda event: self.previous_window.configure(relief=GROOVE))
		self.previous_window.bind("<Enter>", lambda event: self.previous_window.configure(cursor='hand', relief=RAISED))
		#
		self.next_window = Label(self.window_navigation, text='Next', bg='#E0E0E0', font='bold 14', padx=10, relief=GROOVE)
		self.next_window.grid(row=0, column=1, sticky=W)
		self.next_window.configure(state='disabled')
		## creating the labels and entries in the input layout
		self.parameters = LabelFrame(self.widget_layer, text='Parameters', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.parameters.pack(fill=X, expand=False, pady=10, padx=100)
		self.parameters.columnconfigure(0, weight=1)
		self.parameters.columnconfigure(1, weight=1)
		self.parameters.rowconfigure(0, weight=1)
		self.parameters.rowconfigure(1, weight=1)
		#
		self.hgvs_label = Label(self.parameters, text='HGVS term:', bg='#C8C8C8')
		self.hgvs_entry = Entry(self.parameters, highlightbackground='#C8C8C8')
		self.hgvs_label.grid(row=0, column=0, sticky=E)
		self.hgvs_entry.grid(row=0, column=1, sticky=W)
		#
		self.help1 = Label(self.parameters, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help1.grid(row=1, column=1, sticky=E)
		self.help1.bind("<Button-1>", self.help1_popup)
		self.help1.bind("<Leave>", lambda event: self.help1.configure(relief=GROOVE))
		self.help1.bind("<Enter>", lambda event: self.help1.configure(cursor='hand', relief=RAISED))
		#
		self.max_af = LabelFrame(self.widget_layer, text='Maximum Allele Frequency', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.max_af.pack(fill=X, expand=False, pady=10, padx=100)
		self.max_af.columnconfigure(0, weight=1)
		self.max_af.columnconfigure(1, weight=1)
		self.max_af.columnconfigure(2, weight=1)
		self.max_af.columnconfigure(3, weight=1)
		self.max_af.rowconfigure(0, weight=1)
		self.max_af_cuttoff_label = Label(self.max_af, text='MAX_AF cutoff:', bg='#C8C8C8')
		self.max_af_cuttoff_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_cuttoff_label.grid(row=0, column=0, sticky=E)
		self.max_af_cuttoff_entry.grid(row=0, column=1, sticky=W)
		#
		self.max_af_value_label = Label(self.max_af, text='MAX_AF equal to:', bg='#C8C8C8')
		self.max_af_value_entry = Entry(self.max_af, highlightbackground='#C8C8C8')
		self.max_af_value_label.grid(row=0, column=2, sticky=E)
		self.max_af_value_entry.grid(row=0, column=3, sticky=W)
		#
		self.help2 = Label(self.max_af, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help2.grid(row=1, column=3, sticky=E)
		self.help2.bind("<Button-1>", self.help2_popup)
		self.help2.bind("<Leave>", lambda event: self.help2.configure(relief=GROOVE))
		self.help2.bind("<Enter>", lambda event: self.help2.configure(cursor='hand', relief=RAISED))
		#
		self.cq_frame = LabelFrame(self.widget_layer, text='Consequence', font='-weight bold', labelanchor='nw', bg='#C8C8C8', borderwidth=2, relief=GROOVE)
		self.cq_frame.pack(fill=X, expand=False, pady=10, padx=100)
		self.cq_frame.columnconfigure(0, weight=1)
		self.cq_frame.columnconfigure(1, weight=1)
		self.cq_frame.rowconfigure(0, weight=1)
		self.cq_frame.rowconfigure(1, weight=1)
		self.cq_frame.rowconfigure(2, weight=1)
		self.cq_frame.rowconfigure(3, weight=1)
		self.cq_frame.rowconfigure(4, weight=1)
		self.sub_frame = Frame(self.cq_frame)
		#
		self.list_scroll = Scrollbar(self.sub_frame, orient=VERTICAL)
		self.all_consequences = re.split(',', '3_prime_UTR_variant,5_prime_UTR_variant,downstream_gene_variant,feature_elongation,feature_truncation,frameshift_variant,incomplete_terminal_codon_variant,inframe_deletion,inframe_insertion,intergenic_variant,intron_variant,mature_miRNA_variant,missense_variant,nc_transcript_variant,NMD_transcript_variant,non_coding_exon_variant,regulatory_region_ablation,regulatory_region_amplification,regulatory_region_variant,splice_acceptor_variant,splice_donor_variant,splice_region_variant,stop_gained,stop_lost,stop_retained_variant,synonymous_variant,TF_binding_site_variant,TFBS_ablation,TFBS_amplification,transcript_ablation,transcript_amplification,upstream_gene_variant')
		all_cq = tuple(self.all_consequences)
		cq_var = StringVar(value=all_cq)
		self.cq_label = Label(self.cq_frame, text='Consequence list:', bg='#C8C8C8')
		self.cq_box = Listbox(self.sub_frame, listvariable=cq_var, height=8, width=40, selectmode=MULTIPLE, yscrollcommand=self.list_scroll.set)
		self.list_scroll.config(command=self.cq_box.yview)
		self.list_scroll.pack(side=RIGHT, fill=Y)
		self.cq_label.grid(column=0, row=0, sticky=E)
		self.cq_box.pack(fill=BOTH, expand=True)
		self.sub_frame.grid(column=1, row=0, sticky=W)
		#
		self.cq_all_var = IntVar()
		self.cq_check_all = Checkbutton(self.cq_frame, text='All CQ in the list above', onvalue=1, offvalue=0, variable=self.cq_all_var, bg='#C8C8C8')
		self.cq_check_all.grid(column=1, row=1, sticky=W)
		#
		self.user_cq_label = Label(self.cq_frame, text='Other user-defined\nconsequences:', bg='#C8C8C8')
		self.user_cq_entry = Entry(self.cq_frame, highlightbackground='#C8C8C8')
		self.user_cq_label.grid(column=0, row=2, sticky=E)
		self.user_cq_entry.grid(column=1, row=2, sticky=W)
		self.cq_lof_var = IntVar()
		#
		self.cq_check = Checkbutton(self.cq_frame, text='Functional and LOF consequences', onvalue=1, offvalue=0, variable=self.cq_lof_var, bg='#C8C8C8')
		self.cq_check.grid(column=1, row=3, sticky=W)
		#
		self.help3 = Label(self.cq_frame, bg='#C8C8C8', fg='#0066FF', text='?', font='bold 16', padx=10, relief=GROOVE)
		self.help3.grid(row=4, column=1, sticky=E)
		self.help3.bind("<Button-1>", self.help3_popup)
		self.help3.bind("<Leave>", lambda event: self.help3.configure(relief=GROOVE))
		self.help3.bind("<Enter>", lambda event: self.help3.configure(cursor='hand', relief=RAISED))
		#
		self.submit_button = Button(self.widget_layer, text='Run', command=self.buffer, highlightbackground='#E0E0E0')
		self.submit_button.pack(pady=10, padx=100)
		## if the global variables that check the dot server/ddd_prod files are false or None, the Run button is disabled.
		if (not self.server_file_check or not self.ddd_prod_check):
			self.submit_button.configure(state='disabled')
	def forward(self, event):
		"""Method belongs to the Next button."""
		self.present_frame.pack_forget()
		self.next_frame.pack(fill=BOTH, expand=TRUE)
	def backward(self, event):
		"""Method belongs to the Back button."""
		self.present_frame.pack_forget()
		self.next_frame.pack_forget()
		self.previous_frame.pack(fill=BOTH, expand=TRUE)
	def get_user_input_function(self):
		"""Method that gets the user input parameters and stores them."""
		self.user_input = {}
		cq_list = []
		self.user_input['hgvs'] = str(self.hgvs_entry.get())
		self.user_input['max_af_cutoff'] = self.max_af_cuttoff_entry.get() or 'ignore'
		self.user_input['max_af_value'] = self.max_af_value_entry.get() or 'ignore'
		## preparing the user-defined CQ
		if (self.cq_all_var.get()):
			cq_list.extend(self.all_consequences)
		else:
			for indx in self.cq_box.curselection():
				cq_list.append(self.all_consequences[int(indx)])
		for entry in re.split(',', self.user_cq_entry.get()):
			if (entry):
				cq_list.append(entry)
		if (self.cq_lof_var.get()):
			cq_list.extend(hgvs_cohort.LOF)
		self.user_input['cq'] = ','.join(cq_list)
		## catch some errors eg. not all necessay entries are entered by the user
		try:
			assert all([self.user_input['hgvs'], self.user_input['cq']])
		except:
			tkMessageBox.showwarning(title='Warning', message='These entries are mandatory: HGVS, CQ.')
			self.error_collect = 'Input error.'
	def help1_popup(self, event):
		"""This method belongs to the first "?"."""
		help1_msg = 'HGVS : The HGVS term of which genomic coordinates will be retrieved from ddd_prod.\n'
		tkMessageBox.showinfo(title='Parameters', message=help1_msg)
	def help2_popup(self, event):
		"""This method belongs to the second "?"."""
		help2_msg = 'Max_af_cutoff (maximum alele frequency) : variants with MAX_AF below this cutoff are included.\n\nMax_af_value : variants with MAX_AF equal to this value are selected.\n\nNote : applying a MAX_AF threshold is advised in this case of parsing all cohort VCFs, this will decrease the number of selected variants and speed up the file transfer from the server.\n'
		tkMessageBox.showinfo(title='MAX_AF', message=help2_msg)
	def help3_popup(self, event):
		"""This method belongs to the third "?"."""
		help3_msg = 'Consequence : Select variant consequence using any or all of the options given.\n\nFunctional and LOF include :\ntranscript_ablation, splice_donor_variant\nsplice_acceptor_variant, stop_gained\nframeshift_variant, stop_lost\nstart_lost, inframe_insertion\ninframe_deletion, missense_variant\ntranscript_amplification, protein_altering_variant.\n'
		tkMessageBox.showinfo(title='CQ', message=help3_msg)
	def backend_variant_execution(self):
		"""This method starts the backend execution steps for variant extraction."""
		string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
		if (not self.direct_ssh_mode):
			build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
		## do if the error collection variable is not
		if (not self.error_collect):
			is_an_ensemble_transcript = None
			is_a_refseq_transcript = None
			if (re.search('^(ENST\d+)', self.user_input['hgvs'])):
				is_an_ensemble_transcript = True
				is_a_refseq_transcript = False
			elif (re.search('^[NX]', self.user_input['hgvs'])):
				is_a_refseq_transcript = True
				is_an_ensemble_transcript = False
			## Ensemble case procedure:
			if (is_an_ensemble_transcript):
				## extract the transcript name
				regex_m = re.search('^(ENST\d+)', self.user_input['hgvs'])
				user_transcript = regex_m.group(1)
				##
				if (not self.direct_ssh_mode):
					build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
				##
				os.system('python {a}local_scripts/hgvs_calculator_ensemble_source_builder.py --o {b}recent_runs/{c}current_run.pl --remote_dir {d} --hgvs_transcript \'{e}\' --hgvs_term \'{f}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_backend_dir, e=user_transcript, f=self.user_input['hgvs']))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.pl', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.pl', command='perl {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.pl'))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='hgvs_coords.tsv', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				hgvs_calculator_file_abs_path = self.var_gui_abs_path + 'recent_runs/' + self.var_backend_dir + 'hgvs_coords.tsv'
				##
				if (os.access(hgvs_calculator_file_abs_path, os.F_OK) and os.access(hgvs_calculator_file_abs_path, os.R_OK)):
					with open(hgvs_calculator_file_abs_path, 'r') as hgvs_calculator_tsv:
						hgvs_calculator_tsv = hgvs_calculator_tsv.readlines()
					try:
						hgvs_calculator_tsv_line = re.sub('\n', '', hgvs_calculator_tsv[0])
						temp = hgvs_calculator_tsv_line.split('\t')
						self.user_input['chrom'] = temp[0]
						self.user_input['start'] = temp[1]
						self.user_input['stop'] = temp[1]
					except:
						self.error_collect = 'HGVS calculator error.'
				else:
					self.error_collect = 'HGVS calculator error.'
			elif (is_a_refseq_transcript):# Refseq case procedure:
				## create expect file
				if (not self.direct_ssh_mode):
					build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
				##
				os.system('python {a}local_scripts/hgvs_calculator_refseq_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --hgvs \'{f}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['hgvs']))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='hgvs_coords.tsv', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
				##
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				##
				hgvs_calculator_file_abs_path = self.var_gui_abs_path + 'recent_runs/' + self.var_backend_dir + 'hgvs_coords.tsv'
				##
				if (os.access(hgvs_calculator_file_abs_path, os.F_OK) and os.access(hgvs_calculator_file_abs_path, os.R_OK)):
					with open(hgvs_calculator_file_abs_path, 'r') as hgvs_calculator_tsv:
						hgvs_calculator_tsv = hgvs_calculator_tsv.readlines()
					try:
						hgvs_calculator_tsv_line = re.sub('\n', '', hgvs_calculator_tsv[0])
						temp = hgvs_calculator_tsv_line.split('\t')
						self.user_input['chrom'] = temp[0]
						self.user_input['start'] = temp[1]
						self.user_input['stop'] = temp[1]
					except:
						self.error_collect = 'HGVS calculator error.'
				else:
					self.error_collect = 'HGVS calculator error.'
				## do if the error collection variable is not
		if (not self.error_collect):
			## do the routine procedure: create local script, send and execute on backend, transfer result to frontend.
			os.system('python {a}local_scripts/coords_cohort_1_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --chrom {f} --start {g} --stop {h} --cq {i} --max_af_cutoff {j} --max_af_value {k} --string_user_settings_dict \'{l}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.user_input['chrom'], g=self.user_input['start'], h=self.user_input['stop'], i=self.user_input['cq'], j=self.user_input['max_af_cutoff'], k=self.user_input['max_af_value'], l=string_user_settings))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
				cmd.write(server_cmd)
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			#
			with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
				cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='cohort_variants.json', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
			#
			if (self.direct_ssh_mode):
				os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
			else:
				os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
			## run the first check point
			self.sanity_check_and_proceed()
			if (not self.error_collect):
				## continue with the second part
				os.system('python {a}local_scripts/cohort_2_source_builder.py --o {b}recent_runs/{c}current_run.py --remote_dir {d}'.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_backend_dir))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				#
				server_cmd = r"""#!/usr/bin/env bash
source /software/ddd/etc/profile.ddd
chmod 777 {backend_dir_name}{file_name}
{command}
""".format(backend_dir_name=self.var_backend_dir, file_name='current_run.py', command='python {backend_dir_name}{file_name}'.format(backend_dir_name=self.var_backend_dir, file_name='current_run.py'))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', 'w') as cmd:
					cmd.write(server_cmd)
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'cat {file_name} | ssh {user}@{server} bash\n'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'server_command', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'])]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				#
				with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
					cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}\n'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='selected_cohort_variants.tsv.gz', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
				#
				if (self.direct_ssh_mode):
					os.system('bash {dir_name}recent_runs/{local_dump}current_command'.format(dir_name=self.var_gui_abs_path, local_dump=self.var_backend_dir))
				else:
					os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
				#
				os.system('gunzip {a}recent_runs/{b}selected_cohort_variants.tsv.gz'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
	def create_progress_bar(self):
		"""Aesthetic method to create an indeterminate progress bar."""
		self.progress = ttk.Progressbar(self.present_frame, orient="horizontal", length=300, mode="indeterminate")
		self.progress.pack()
		self.progress.start()
	def widget_lock(self, key_code):
		"""Aesthetic method to inactivate/activate widgets during backend execution."""
		widgets = ['self.previous_window', 'self.next_window', 'self.hgvs_label', 'self.hgvs_entry', 'self.help1', 'self.max_af_cuttoff_label', 'self.max_af_cuttoff_entry', 'self.max_af_value_label', 'self.max_af_value_entry', 'self.help2', 'self.cq_label', 'self.cq_box', 'self.cq_check_all', 'self.user_cq_label', 'self.user_cq_entry', 'self.cq_check', 'self.help3', 'self.submit_button']
		if (key_code == 'lock_widgets'):
			for w in widgets:
				eval(w+".config(state='disabled')")
		elif (key_code == 'open_widgets'):
			for w in widgets:
				eval(w+".config(state='normal')")
	def buffer(self):
		"""This method is bound to the Run button and it orchestrates some procedural steps."""
		try:
			local_path = self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir
			for file_found in os.listdir(local_path):
				os.remove(local_path+file_found) ## clearing out the changeable directory
		except:
			pass
		self.error_collect = '' ## reinstate error_collect in case an error with input collection was made
		## do the aesthetic "running" mode
		self.widget_lock('lock_widgets')
		self.create_progress_bar()
		## use a thread to run this method
		t1=threading.Thread(target=self.initiate_backend_process, args=())
		t1.start()
	def initiate_backend_process(self):
		"""This method starts calls other methods to do the background executions."""
		self.get_user_input_function()
		## do variant extraction
		if (not self.error_collect):
			try:
				self.backend_variant_execution()
			except:
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.config(state='disabled')
		else:
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.config(state='disabled')
		## continue in case of zero errors
		## activate the Next button and prepare to display the results
		if (not self.error_collect):
			self.next_window.configure(state='active')
			self.next_window.bind("<Button-1>", self.forward)
			self.next_window.bind("<Leave>", lambda event: self.next_window.configure(relief=GROOVE))
			self.next_window.bind("<Enter>", lambda event: self.next_window.configure(cursor='hand', relief=RAISED))
			#
			self.progress.destroy()
			self.widget_lock('open_widgets')
			## clean up the existing next frame
			for widget in self.next_frame.winfo_children():
				widget.destroy()
			## prepare results for display
			prepare_result_tabs_cohort(gui_abs_path=self.var_gui_abs_path,previous_frame=self.present_frame,present_frame=self.next_frame,past_frame=self.previous_frame,query_info=self.user_input,backend_dir=self.var_backend_dir)
	def sanity_check_and_proceed(self):
		"""This method reads the JSON file from the server and checks the error key."""
		variant_file_abs_path = self.var_gui_abs_path + r'recent_runs/'+self.var_backend_dir+'cohort_variants.json'
		if (os.access(variant_file_abs_path, os.F_OK) and os.access(variant_file_abs_path, os.R_OK)):
			with open(variant_file_abs_path, 'r') as variant_json:
				variant_json = json.load(variant_json)
			variant_related_errors = variant_json['error_msgs'].encode('utf-8')
			if (variant_related_errors == 'Error'):
				tkMessageBox.showwarning(title='Warning', message='Problem retrieving cohort variants from the server.')
				self.error_collect = 'Variant retrieval error.'
				self.progress.destroy()
				self.widget_lock('open_widgets')
				self.next_window.configure(state='disabled')
		else:
			tkMessageBox.showwarning(title='Warning', message='The output file from the server was not found.')
			self.error_collect = 'Variant retrieval error.'
			self.progress.destroy()
			self.widget_lock('open_widgets')
			self.next_window.configure(state='disabled')

