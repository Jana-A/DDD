#!/usr/bin/env python

from Tkinter import *
import sys
import ttk
import os
import re
import getpass
import time
import subprocess
from subprocess import PIPE
from StringIO import StringIO
import json
import threading
import multiprocessing
import PIL
from PIL import Image, ImageTk
from tkFileDialog import askopenfilenames
import tkMessageBox
from result_widget_setups import *
from widget_layouts import *




def config_I(event):
	"""This function is executed every time there is a size change in the window of the interface.
		It scales and adjusts the sizes and positions of the main frames according to window size."""
	current_width, current_height = event.width, event.height
	x = current_width*0.05 ## padding on horizontal axis
	y = current_height*0.05
	#
	mainframe_width = int(current_width*0.7) ## 70% of the window width
	mainframe_height = int(current_height*0.85) ## 85% of the window height
	#
	sideframe_frame_width = int(current_width*0.2) ## 20% of the window width and 90% of that
	sideframe_frame_height = int(current_height*0.9)
	#
	mainframe.place(x=x+10+current_width*0.2, y=0, width=mainframe_width, height=mainframe_height) ## add 10 to the x to give the mainframe and the options frame some space
	sidebar_frame.place(x=x, y=y, width=sideframe_frame_width, height=sideframe_frame_height)
	#
	terminal_stderr_frame.place(x=x+10+current_width*0.2, y=mainframe_height+5, width=mainframe_width, height=int(current_height*0.13))



def build_server_tester_expect_file(gui_path, temp_dump, user_info):
	"""This function is only used during the server connection step. It has a timeout of 5 seconds."""
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


## -------------------------
## Start __main__ execution:
## -------------------------
if (__name__ == '__main__'):
	## find the absolute path of index.py
	index_file_path = os.path.abspath(sys.argv[0])
	## find the absolute path of the interface that is the parent folder of index.py (this will be used many times later on)
	gui_abs_path = os.path.split(index_file_path)[0] + r'/'
	sanger_network_connect_check = None  ## variable used to check if the user is successfully connected to the Sanger network
	## initialize some variables that are later used during widget setups
	direct_ssh_mode = None ## if the user does not enter their password manually
	igv_file_check = None ## if the IGV user file is found
	server_file_check = None ## if the server user file is found
	ddd_prod_file_check = None ## if the ddd_prod user file is found
	user_settings = {}  ## the user logins for IGV, ddd_prod and server will be stored in this variable
	notifications = [] ## a variable that will contain notifications about the IGV, ddd_prod and server files and these notifications will be displayed in the startup page
	## prepare the backend/frontend temporary directory character string that includes current year, month, day, hour, minute, second
	backend_frontend_dir = 'temp_interface_dump_' + time.strftime('%S_%M_%H_%d_%m_%y' + r'/')
	## create the local temporary directory in ./variant_explorer_tool/recent_runs/
	os.system('mkdir {gui_path}recent_runs/{temp_dump}'.format(gui_path=gui_abs_path, temp_dump=backend_frontend_dir))
	## get the files that are in the interface folder
	current_files = os.listdir(gui_abs_path)
	## look for the 3 files in the current dir
	server_file_curr = '.server_user' in current_files
	igv_file_curr = '.igv_user' in current_files
	ddd_prod_file_curr = '.ddd_prod_user' in current_files
	#
	tick = u"\u2713".encode('utf8') ## a unary tick symbol used in the notifications
	#
	## look for the 3 files in the parent dir
	gui_parent_path = os.path.split(os.path.abspath(gui_abs_path))[0] + r'/'
	parent_files = os.listdir(gui_parent_path)
	server_file_par = '.server_user' in parent_files
	igv_file_par = '.igv_user' in parent_files
	ddd_prod_file_par = '.ddd_prod_user' in parent_files
	## finding and reading the dot server file and assiging the global variable relating to the dot server file
	if (not server_file_curr and not server_file_par):
		server_file_check = False
		notifications.append(('X', 'The server user file was not detected. Please ensure it is present.', '#FF0000'))
	elif (server_file_curr):
		server_file_check = True
		server_file_path = os.path.abspath(gui_abs_path+'.server_user')
		server_reading_dict = read_server_user_file(server_file_path)
		user_settings.update(server_reading_dict)
		if (len(server_reading_dict.keys()) == 2):
			direct_ssh_mode = True
		else:
			direct_ssh_mode = False
		notifications.append((tick, 'Detected the server user file in "{}"'.format(gui_abs_path), '#00CC00'))
	elif (server_file_par):
		server_file_check = True
		server_file_path = os.path.abspath(gui_parent_path + '.server_user')
		server_reading_dict = read_server_user_file(server_file_path)
		user_settings.update(server_reading_dict)
		if (len(server_reading_dict.keys()) == 2):
			direct_ssh_mode = True
		else:
			direct_ssh_mode = False
		notifications.append((tick, 'Detected the server user file in "{}"'.format(gui_parent_path), '#00CC00'))
	## finding and reading the dot igv file and assiging the global variable relating to the dot igv file
	if (not igv_file_curr and not igv_file_par):
		igv_file_check = False
		notifications.append(('X', 'The igv user file was not detected. Ignore if you will not be using the igv plot option.', '#FF0000'))
	elif (igv_file_curr):
		igv_file_check = True
		igv_file_path = os.path.abspath(gui_abs_path+'.igv_user')
		user_settings.update(read_igv_user_file(igv_file_path))
		notifications.append((tick, 'Detected the igv user file in "{}"'.format(gui_abs_path), '#00CC00'))
	elif (igv_file_par):
		igv_file_check = True
		igv_file_path = os.path.abspath(gui_parent_path+'.igv_user')
		user_settings.update(read_igv_user_file(igv_file_path))
		notifications.append((tick, 'Detected the igv user file in "{}"'.format(gui_parent_path), '#00CC00'))
	## finding and reading the dot ddd_prod file and assiging the global variable relating to the dot ddd_prod file
	if (not ddd_prod_file_curr and not ddd_prod_file_par):
		ddd_prod_file_check = False
		notifications.append(('X', 'The ddd_prod user file was not detected. Please ensure it is present.', '#FF0000'))
	elif (ddd_prod_file_curr):
		ddd_prod_file_check = True
		ddd_prod_file_path = os.path.abspath(gui_abs_path+'.ddd_prod_user')
		user_settings.update(read_ddd_prod_user_file(ddd_prod_file_path))
		notifications.append((tick, 'Detected the ddd_prod user file in "{}".'.format(gui_abs_path), '#00CC00'))
	elif (ddd_prod_file_par):
		ddd_prod_file_check = True
		ddd_prod_file_path = os.path.abspath(gui_parent_path+'.ddd_prod_user')
		user_settings.update(read_ddd_prod_user_file(ddd_prod_file_path))
		notifications.append((tick, 'Detected the ddd_prod user file in "{}"'.format(gui_parent_path), '#00CC00'))
	if (all(map(lambda x: re.match('\w', x), user_settings.values())) and all(map(lambda x: re.search('\w$', x), user_settings.values()))):
		## this part decides if the Sanger server connection is successful using the login parameters from the dot server file
		try:
			if (not direct_ssh_mode):
				build_server_tester_expect_file(gui_abs_path, backend_frontend_dir, user_settings)
			with open(gui_abs_path+'recent_runs/'+backend_frontend_dir+'current_command', 'w') as cmd:
				cmd.write('ssh {user}@{server} "pwd"\n'.format(user=user_settings['server_username'], server=user_settings['server_name']))
			if (not direct_ssh_mode):
				cmd_exec = subprocess.Popen(['expect','{}recent_runs/{}current_expect'.format(gui_abs_path, backend_frontend_dir)], stdout=PIPE, stderr=PIPE)
			else:
				cmd_exec = subprocess.Popen(['bash', '{}recent_runs/{}current_command'.format(gui_abs_path, backend_frontend_dir)], stdout=PIPE, stderr=PIPE)
			standard_out, standard_err = cmd_exec.communicate()
			if (re.search('/nfs/users/', standard_out) and not standard_err):
				sanger_network_connect_check = True
			else:
				sanger_network_connect_check = False
		except:
			pass
		if (sanger_network_connect_check and server_file_check and ddd_prod_file_check):
			create_temp_backend_dir(direct_ssh_mode, gui_abs_path, backend_frontend_dir, user_settings)
			## the corresponding forntend dir has already been created
		if (not sanger_network_connect_check):
			igv_file_check = False
			server_file_check = False
			ddd_prod_file_check = False
	else:
		sanger_network_connect_check = False
		igv_file_check = False
		server_file_check = False
		ddd_prod_file_check = False
	## initialising the interface widgets (see documentation diagram for more info)
	root = Tk()
	root.geometry("1200x750+10+10") ## dimensions and coordinates of the root window
	root.wm_title('variant explorer tool')
	## see documentation diagram about these frames
	container_frame = Frame(root, bg='#F0F0F0')
	container_frame.pack(fill=BOTH, expand=YES)
	#
	sidebar_frame = Frame(container_frame, bg='#F0F0F0', width=900*0.2, height=600*0.9, relief=FLAT, borderwidth=2)
	mainframe = Frame(container_frame, bg='#E0E0E0')
	#
	startup_frame = LabelFrame(mainframe, text='Startup', labelanchor='n', font='Aerial 18 bold', bg='#E0E0E0', width=900*0.8, height=600*0.9)
	startup_frame.pack(fill=BOTH, expand=TRUE)
	##-------------------------------
	## The standard error bottom box:
	##-------------------------------
	def stderr_config(event):
		"""This function is used to adjust the scrollbar height depending on the length of the error message in the stderr box."""
		stderr_box_height, x, y = stderr_label.winfo_reqheight(), bottom_box_container.winfo_x(), bottom_box_container.winfo_y()
		bottom_canvas_layer.configure(scrollregion=(0,0,2000,stderr_box_height))
	## redirecting the standard error to a handle
	sys.stderr = mystderr = StringIO()
	def stderr_check():
		"""This function is run every 500 ms.
			It will refresh the stderr variable."""
		for a_widget in bottom_box_container.winfo_children():
			a_widget.destroy()
		my_var = StringVar()
		my_var.set('Error record :\n-----------\n' + mystderr.getvalue())
		global stderr_label
		stderr_label = Label(bottom_box_container, bg='#E0E0E0', fg='red', textvariable=my_var, font='Aerial 8 bold', justify=LEFT)
		stderr_label.pack(fill=BOTH, expand=True, padx=10)
		root.after(500, stderr_check)
	## setting up the stderr bottom box
	terminal_stderr_frame = Frame(container_frame, bg='#E0E0E0', relief=RIDGE, borderwidth=2)
	## preparing the scrollbars
	terminal_stderr_frame_scroll_y = Scrollbar(terminal_stderr_frame, orient=VERTICAL)
	terminal_stderr_frame_scroll_y.pack(fill=Y, side=RIGHT)
	terminal_stderr_frame_scroll_x = Scrollbar(terminal_stderr_frame, orient=HORIZONTAL)
	terminal_stderr_frame_scroll_x.pack(fill=X, side=BOTTOM)
	#
	bottom_canvas_layer = Canvas(terminal_stderr_frame, bg='#E0E0E0', yscrollcommand=terminal_stderr_frame_scroll_y.set, xscrollcommand=terminal_stderr_frame_scroll_x.set)
	bottom_canvas_layer.pack(fill=BOTH, expand=True)
	#
	terminal_stderr_frame_scroll_y.config(command=bottom_canvas_layer.yview)
	terminal_stderr_frame_scroll_x.config(command=bottom_canvas_layer.xview)
	#
	bottom_box_container = Frame(bottom_canvas_layer, bg='#E0E0E0')
	bottom_box_container.pack()
	#
	bottom_box_container.bind("<Configure>", stderr_config)
	bottom_canvas_layer.create_window(0, 0, window=bottom_box_container, anchor='nw')
	root.after(0, stderr_check) ## run the function as soon as the interface is created
	##-------------------------------
	## create and hide the user_input and the result frames
	user_input_frame = LabelFrame(mainframe, text='', labelanchor='n', font='Aerial 18 bold', bg='#E0E0E0')
	user_input_frame.pack(fill=BOTH, expand=TRUE)
	user_input_frame.pack_forget()
	#
	results_frame = Frame(mainframe, bg='#E0E0E0')
	results_frame.pack(fill=BOTH, expand=TRUE)
	results_frame.pack_forget()
	#
	## create instances of some classes
	options_sidebar = options_sidebar_setup(direct_ssh_mode=direct_ssh_mode,var_user_settings=user_settings, master=root, side_frame_var=sidebar_frame, check_server=server_file_check, check_ddd_prod=ddd_prod_file_check, var_gui_abs_path=gui_abs_path,var_backend_dir=backend_frontend_dir)
	calculator_widget = calculator_setup(direct_ssh_mode=direct_ssh_mode,master=root, side_frame_var=sidebar_frame, var_backend_dir=backend_frontend_dir, check_server=server_file_check, check_ddd_prod=ddd_prod_file_check, var_gui_abs_path=gui_abs_path, var_user_settings=user_settings)
	startup = startup_setup(startup_frame_var=startup_frame, next_frame=user_input_frame,future_frame=results_frame,current_dir_var='',parent_dir_var='',var_backend_dir=backend_frontend_dir,var_gui_abs_path=gui_abs_path, check_server=server_file_check, check_ddd_prod=ddd_prod_file_check, check_igv=igv_file_check, prepared_notifications=notifications, var_user_settings=user_settings,calculator_var=calculator_widget)
	top_menu = top_menu_setup(direct_ssh_mode=direct_ssh_mode,container_frame_var=container_frame,root_var=root, mainframe_var=mainframe, startup_object_var=startup, startup_frame_var=startup_frame, user_input_frame_var=user_input_frame, results_frame=results_frame, backend_dir=backend_frontend_dir, check_server=server_file_check, check_ddd_prod=ddd_prod_file_check, check_igv=igv_file_check, gui_abs_path=gui_abs_path, user_info=user_settings)
	#
	## binding some configuration functions upon a change in the size of the container frame
	container_frame.bind("<Configure>", config_I)
	container_frame.bind("<Configure>", options_sidebar.configure, add='+')
	container_frame.bind("<Configure>", calculator_widget.configure, add='+')
	#
	## bind a function to the event of quiting the interface
	root.protocol("WM_DELETE_WINDOW", lambda: the_quiting_callback(True, True, root, user_settings, gui_abs_path, backend_frontend_dir))
	## this mainloop method of the root window is called to keep the script re-executing and not "execute and exit"
	root.mainloop()
