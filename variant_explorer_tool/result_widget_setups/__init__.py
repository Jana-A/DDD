#!/usr/bin/env python

from Tkinter import *
import os
import re
import time
import imp
import json
import threading
import base64
import PIL
from PIL import Image, ImageTk
from tkFileDialog import askopenfilenames
import tkMessageBox
import tkFileDialog


class populate_query_info_tab:
	"""Used to organize the user input into a tab."""
	def __init__(self, frame, input_dict):
		self.frame = frame
		self.input_dict = input_dict
		## clean up frame
		for w in self.frame.winfo_children():
			w.destroy()
		## procedure to display query input key/value
		for k,v in self.input_dict.items():
			if (k != 'cq'):
				line_v = '\n'.join(v.split(',')) + '\n~ ~ ~'
				label = Label(self.frame, text='{} : {}'.format(k.capitalize(),line_v), bg='#E0E0E0', font='bold 14', pady=10)
				label.pack(padx=20)
			elif (k == 'cq'):
				self.user_cq = v
				cq_label = Label(self.frame, text='View your selected CQ list', bg='#E0E0E0', font='bold 14', borderwidth=2, relief=GROOVE, pady=10)
				cq_label.bind("<Button-1>", self.view_cq)
				cq_label.bind("<Leave>", lambda event: cq_label.configure(bg='#E0E0E0', relief=GROOVE))
				cq_label.bind("<Enter>", lambda event: cq_label.configure(bg='#C8C8C8', cursor='hand', relief=RAISED))
				cq_label.pack()
				design_label = Label(self.frame, text='~ ~ ~', bg='#E0E0E0')
				design_label.pack()
	def view_cq(self, event):
		"""To view the user-defined CQ."""
		tkMessageBox.showinfo(title='Input CQ', message=self.user_cq)



class populate_trio_variants_tab:
	"""Used to display trio variant data."""
	def __init__(self, frame, gui_path, backend_dir):
		self.frame = frame
		self.gui_abs_path = gui_path
		self.var_backend_dir = backend_dir
		## clean up frame
		for w in self.frame.winfo_children():
			w.destroy()
		## the tool bar containing the edit options of the variant box
		self.toolbar_frame2 = Frame(self.frame, bg='#C8C8C8', relief=GROOVE, borderwidth=2)
		#
		self.remove = Button(self.toolbar_frame2, text='Remove', command=self.removing, highlightbackground='#C8C8C8')
		self.remove.place(x=20, y=0)
		#
		self.export = Button(self.toolbar_frame2, text='Export', command=self.exporting, highlightbackground='#C8C8C8')
		self.export.place(x=100, y=0)
		#
		self.find = Button(self.toolbar_frame2, text='Find', command=self.popup, highlightbackground='#C8C8C8')
		self.find.place(x=170, y=0)
		#
		self.info = Button(self.toolbar_frame2, text='Info', command=self.get_info, highlightbackground='#C8C8C8')
		self.info.place(x=230, y=0)
		#
		self.filter = Menubutton(self.toolbar_frame2, text='Filter out', bg='#C8C8C8')
		self.filter_menu = Menu(self.filter)
		self.filter.config(menu=self.filter_menu)
		self.filter_menu.add_checkbutton(label='Variants with no "PASS"', command=self.filter_no_pass_alt)
		self.filter_menu.add_checkbutton(label='Variants with "<DEL>" ALT', command=self.filter_del_alt)
		self.filter_menu.add_checkbutton(label='Variants with "<DUP>" ALT', command=self.filter_dup_alt)
		self.filter_menu.add_checkbutton(label='Variants with no rs "."', command=self.filter_dot)
		self.filter.place(x=290, y=2)
		## divide the trio variants
		self.child_frame = LabelFrame(self.frame, text='Child variants', labelanchor='nw', font='bold 16', bg='#E0E0E0', relief=RIDGE, borderwidth=2)
		#
		self.mum_frame = LabelFrame(self.frame, text='Mother variants', labelanchor='nw', font='bold 16', bg='#E0E0E0', relief=RIDGE, borderwidth=2)
		#
		self.dad_frame = LabelFrame(self.frame, text='Father variants', labelanchor='nw', font='bold 16', bg='#E0E0E0', relief=RIDGE, borderwidth=2)
		#
		self.frame.bind("<Configure>", self.config)
	def config(self, event):
		"""Method called upon any size change."""
		self.current_width, self.current_height = event.width, event.height
		x = self.current_width*0.05 ## padding on horizontal axis
		y = self.current_height*0.05
		#
		self.mainframe_width = int(self.current_width*0.9)
		self.mainframe_height = int(self.current_height*0.9)
		#
		self.toolbar_frame2.place(x=x, y=10, height=40, width=450)
		self.child_frame.place(x=x, y=80, width=self.mainframe_width, height=self.mainframe_height*0.27)
		self.mum_frame.place(x=x, y=90+self.mainframe_height*0.3, width=self.mainframe_width, height=self.mainframe_height*0.27)
		self.dad_frame.place(x=x, y=100+self.mainframe_height*0.3*2, width=self.mainframe_width, height=self.mainframe_height*0.27)
	def prepare_varaints_for_display(self):
		"""Reading the result file and displaying it."""
		variant_file_abs_path = self.gui_abs_path + 'recent_runs/'+ self.var_backend_dir + 'trio_variants.json'
		## at this point the file exists because it passed the previous existance test.
		with open(variant_file_abs_path, 'r') as variant_json:
			variant_json = json.load(variant_json)
		variants = re.split('\n', variant_json['variants'].encode('utf-8'))
		trio_ids = variant_json['trio_ids'].encode('utf-8')
		ids = re.split('\t', trio_ids)
		ids = list(map(lambda y: re.sub('\n', '', y), ids))
		trio_object = {}
		trio_object['child'] = [x for x in variants if re.match(ids[0], x)]
		trio_object['mum'] = [x for x in variants if re.match(ids[1], x)]
		trio_object['dad'] = [x for x in variants if re.match(ids[2], x)]
		## child variants
		self.child_lines = tuple(trio_object['child'])
		child_lines_var = StringVar(value=self.child_lines)
		self.child_y_list_scroll = Scrollbar(self.child_frame, orient=VERTICAL)
		self.child_x_list_scroll = Scrollbar(self.child_frame, orient=HORIZONTAL)
		self.child_box = Listbox(self.child_frame, listvariable=child_lines_var, selectmode=MULTIPLE, xscrollcommand=self.child_x_list_scroll.set, yscrollcommand=self.child_y_list_scroll.set)
		self.child_x_list_scroll.config(command=self.child_box.xview)
		self.child_x_list_scroll.pack(side=RIGHT, fill=X)
		self.child_y_list_scroll.config(command=self.child_box.yview)
		self.child_y_list_scroll.pack(side=RIGHT, fill=Y)
		self.child_x_list_scroll.pack(side=BOTTOM, fill=X)
		self.child_y_list_scroll.pack(side=RIGHT, fill=Y)
		self.child_box.pack(fill=BOTH, expand=True)
		## mother variants
		self.mum_lines = tuple(trio_object['mum'])
		mum_lines_var = StringVar(value=self.mum_lines)
		self.mum_y_list_scroll = Scrollbar(self.mum_frame, orient=VERTICAL)
		self.mum_x_list_scroll = Scrollbar(self.mum_frame, orient=HORIZONTAL)
		self.mum_box = Listbox(self.mum_frame, listvariable=mum_lines_var, selectmode=MULTIPLE, xscrollcommand=self.mum_x_list_scroll.set, yscrollcommand=self.mum_y_list_scroll.set)
		self.mum_x_list_scroll.config(command=self.mum_box.xview)
		self.mum_x_list_scroll.pack(side=RIGHT, fill=X)
		self.mum_y_list_scroll.config(command=self.mum_box.yview)
		self.mum_y_list_scroll.pack(side=RIGHT, fill=Y)
		self.mum_x_list_scroll.pack(side=BOTTOM, fill=X)
		self.mum_y_list_scroll.pack(side=RIGHT, fill=Y)
		self.mum_box.pack(fill=BOTH, expand=True)
		## father variants
		self.dad_lines = tuple(trio_object['dad'])
		dad_lines_var = StringVar(value=self.dad_lines)
		self.dad_y_list_scroll = Scrollbar(self.dad_frame, orient=VERTICAL)
		self.dad_x_list_scroll = Scrollbar(self.dad_frame, orient=HORIZONTAL)
		self.dad_box = Listbox(self.dad_frame, listvariable=dad_lines_var, selectmode=MULTIPLE, xscrollcommand=self.dad_x_list_scroll.set, yscrollcommand=self.dad_y_list_scroll.set)
		self.dad_x_list_scroll.config(command=self.dad_box.xview)
		self.dad_x_list_scroll.pack(side=RIGHT, fill=X)
		self.dad_y_list_scroll.config(command=self.dad_box.yview)
		self.dad_y_list_scroll.pack(side=RIGHT, fill=Y)
		self.dad_x_list_scroll.pack(side=BOTTOM, fill=X)
		self.dad_y_list_scroll.pack(side=RIGHT, fill=Y)
		self.dad_box.pack(fill=BOTH, expand=True)		
	def removing(self):
		"""Used to remove selected variants."""
		individuals = ['child', 'mum', 'dad']
		for indiv in individuals:
			items = eval('self.{}_box.curselection()'.format(indiv))
			position_tracker = 0 ## recovers indexing since lines are removed
			for i in items :
				idx = int(i) - position_tracker
				eval('self.{}_box.delete(idx, idx)'.format(indiv))
				position_tracker = position_tracker + 1
	def filter_no_pass_alt(self):
		"""Remove variants without PASS."""
		family_box = ['self.child_box', 'self.mum_box', 'self.dad_box']
		count = 0
		while (count < 3):
			position_tracker = 0
			for n,i in enumerate(eval(family_box[count]+'.get(0, last=END)')):
				temp_line = i.split('\t')
				if (temp_line[7] != 'PASS'):
					idx = int(n) - position_tracker
					eval(family_box[count]+'.delete(idx, idx)')
					position_tracker = position_tracker + 1
			count = count + 1
	def filter_del_alt(self):
		"""Remove variants with <DEL> alt."""
		family_box = ['self.child_box', 'self.mum_box', 'self.dad_box']
		count = 0
		while (count < 3):
			position_tracker = 0
			for n,i in enumerate(eval(family_box[count]+'.get(0, last=END)')):
				temp_line = i.split('\t')
				if (re.search('<DEL>', temp_line[5])):
					idx = int(n) - position_tracker
					eval(family_box[count]+'.delete(idx, idx)')
					position_tracker = position_tracker + 1
			count = count + 1
	def filter_dup_alt(self):
		"""Remove variants with <DUP> alt."""
		family_box = ['self.child_box', 'self.mum_box', 'self.dad_box']
		count = 0
		while (count < 3):
			position_tracker = 0
			for n,i in enumerate(eval(family_box[count]+'.get(0, last=END)')):
				temp_line = i.split('\t')
				if (re.search('<DUP>', temp_line[5])):
					idx = int(n) - position_tracker
					eval(family_box[count]+'.delete(idx, idx)')
					position_tracker = position_tracker + 1
			count = count + 1
	def filter_dot(self):
		"""Remove variants with dot IDs."""
		family_box = ['self.child_box', 'self.mum_box', 'self.dad_box']
		count = 0
		while (count < 3):
			position_tracker = 0
			for n,i in enumerate(eval(family_box[count]+'.get(0, last=END)')):
				temp_line = i.split('\t')
				if (temp_line[3] == '.'):
					idx = int(n) - position_tracker
					eval(family_box[count]+'.delete(idx, idx)')
					position_tracker = position_tracker + 1
			count = count + 1
	def popup(self):
		"""To get user query location for highlighting variants within the variant boxes."""
		self.top = Toplevel(self.frame)
		self.top.geometry("350x350+10+10")
		#
		Label(self.top, text="Chromosome").pack()
		self.chrom_top = Entry(self.top)
		self.chrom_top.pack()
		#
		Label(self.top, text="Position").pack()
		self.pos_top = Entry(self.top)
		self.pos_top.pack()
		#
		count = 0
		family_box = ['self.child_box', 'self.mum_box', 'self.dad_box']
		while (count < 3):
			for n,i in enumerate(eval(family_box[count]+'.get(0, last=END)')):
				eval(family_box[count]+'.itemconfig(n, background=\'white\')')
			count = count + 1
		top_btn = Button(self.top, text="OK", command=self.go)
		top_btn.pack()
	def go(self):
		"""Highlighting target variants."""
		chrom_top = self.chrom_top.get()
		pos_top = self.pos_top.get()
		self.top.destroy()
		if (chrom_top and pos_top):
			family_box = ['self.child_box', 'self.mum_box', 'self.dad_box']
			count = 0
			while (count < 3):
				for n,i in enumerate(eval(family_box[count]+'.get(0, last=END)')):
					eval(family_box[count]+'.itemconfig(n, background=\'white\')')
				for n,i in enumerate(eval(family_box[count]+'.get(0, last=END)')):
					temp = i.split('\t')
					temp_chr, temp_pos = temp[1], temp[2]
					if (temp_chr == chrom_top and temp_pos == pos_top):
						eval(family_box[count]+'.itemconfig(n, background=\'lightgreen\')')
				count = count + 1
	def exporting(self):
		"""Export variants to a file."""
		filename = tkFileDialog.asksaveasfile(mode='w', defaultextension='.txt')
		out_file = filename
		if (out_file):
			family_box = ['self.child_box', 'self.mum_box', 'self.dad_box']
			count = 0
			while (count < 3):
				for line in eval(family_box[count]+'.get(0, last=END)'):
					out_file.write(line+'\n')
				count = count + 1
			out_file.close()
	def get_info(self):
		"""Used to display the VCF line in a more human readable/alphabetically sorted format."""
		VCF = {'INDIVIDUAL':'', 'CHROM':'', 'POS':'', 'ID':'', 'REF':'', 'ALT':'', 'QUAL':'', 'FILTER':'', 'INFO':'', 'FORMAT':''}
		individuals = ['child', 'mum', 'dad']
		lines_selected = []
		for indiv in individuals:
			items = eval('self.{}_box.curselection()'.format(indiv))
			for i in items :
				lines_selected.append(eval('self.{}_box'.format(indiv)+'.get(i, last=i)'))
		if (lines_selected):
			all_but_info = ''
			## indiv ,chrom, pos, ID, ref, alt, qual, filter, info, format, sample
			target = lines_selected[-1][-1].split('\t')
			all_but_info = 'Individual : {}\tChromosome : {}\tPosition : {}\tID : {}\tREF : {}\tALT : {}\tQUAL : {}\tFilter : {}\tFormat : {}\tSample : {}\t'.format(target[0], target[1], target[2], target[3], target[4], target[5], target[6], target[7], target[9], target[10])
			info_fields = ''
			for x in target[8].split(';'):
				re_match_pairs = re.search('(\S+)=(\S+)', x)
				if (re_match_pairs):
					info_fields = info_fields + '{} : {}\t'.format(re_match_pairs.group(1), re_match_pairs.group(2))
			all_fields = all_but_info + info_fields
			all_fields_list = all_fields.split('\t')
			all_fields_list.sort(key=lambda x: x.lower())
			#
			track_label_height = 0
			#
			top = Toplevel(self.frame)
			top.geometry("500x500+50+50")
			#
			ground_layer_scroll_y = Scrollbar(top, orient=VERTICAL)
			ground_layer_scroll_y.pack(fill=Y, side=RIGHT)
			ground_layer_scroll_x = Scrollbar(top, orient=HORIZONTAL)
			ground_layer_scroll_x.pack(fill=X, side=BOTTOM)
			#
			canvas_layer = Canvas(top, bg='#E0E0E0', bd=0, highlightthickness=0, yscrollcommand=ground_layer_scroll_y.set, xscrollcommand=ground_layer_scroll_x.set)
			canvas_layer.pack(fill=BOTH, expand=True)
			#
			ground_layer_scroll_y.config(command=canvas_layer.yview)
			ground_layer_scroll_x.config(command=canvas_layer.xview)
			#
			result_container = Frame(canvas_layer, bg='#E0E0E0')
			result_container.pack(fill=BOTH, expand=True)
			for elem in all_fields_list:
				temp_lbl = Label(result_container, bg='#E0E0E0', text=elem, wraplength=1000)
				temp_lbl.pack(anchor=W)
				track_label_height += temp_lbl.winfo_reqheight()
			#
			canvas_layer.configure(scrollregion=(0,0,2000,track_label_height))
			canvas_layer.create_window(0, 0, window=result_container, anchor='nw')



class populate_cohort_tab:
	"""Reading the result file and displaying it."""
	def __init__(self, frame, gui_path, backend_dir):
		self.frame = frame
		self.gui_abs_path = gui_path
		self.var_backend_dir = backend_dir
		## clean up frame
		for w in self.frame.winfo_children():
			w.destroy()
		## the tool bar containing the edit options of the variant box
		self.toolbar_frame2 = Frame(self.frame, bg='#C8C8C8', relief=GROOVE, borderwidth=2)
		#
		self.remove = Button(self.toolbar_frame2, text='Remove', command=self.removing, highlightbackground='#C8C8C8')
		self.remove.place(x=20, y=0)
		#
		self.export = Button(self.toolbar_frame2, text='Export', command=self.exporting, highlightbackground='#C8C8C8')
		self.export.place(x=100, y=0)
		#
		self.find = Button(self.toolbar_frame2, text='Find', command=self.popup, highlightbackground='#C8C8C8')
		self.find.place(x=170, y=0)
		#
		self.info = Button(self.toolbar_frame2, text='Info', command=self.get_info, highlightbackground='#C8C8C8')
		self.info.place(x=230, y=0)
		#
		self.filter = Menubutton(self.toolbar_frame2, text='Filter out', bg='#C8C8C8')
		self.filter_menu = Menu(self.filter)
		self.filter.config(menu=self.filter_menu)
		self.filter_menu.add_checkbutton(label='Variants with no "PASS"', command=self.filter_no_pass_alt)
		self.filter_menu.add_checkbutton(label='Variants with "<DEL>" ALT', command=self.filter_del_alt)
		self.filter_menu.add_checkbutton(label='Variants with "<DUP>" ALT', command=self.filter_dup_alt)
		self.filter_menu.add_checkbutton(label='Variants with no rs "."', command=self.filter_dot)
		self.filter.place(x=290, y=2)
		#
		self.cohort_frame = LabelFrame(self.frame, text='Cohort variants', labelanchor='nw', font='Aerial 16 bold', bg='#E0E0E0', relief=RIDGE, borderwidth=2)
		#
		self.frame.bind("<Configure>", self.config)
	def config(self, event):
		"""Method called upon any size change."""
		self.current_width, self.current_height = event.width, event.height
		x = self.current_width*0.05 ## padding on horizontal axis
		y = self.current_height*0.05
		#
		self.mainframe_width = int(self.current_width*0.9)
		self.mainframe_height = int(self.current_height*0.9)
		#
		self.toolbar_frame2.place(x=x, y=10, height=40, width=450)
		self.cohort_frame.place(x=x, y=80, width=self.mainframe_width, height=self.mainframe_height*0.9)
	def prepare_varaints_for_display(self):
		"""Reading the result file and displaying it."""
		## at this point the file exists because it passed the previous existance test.
		with open('{a}recent_runs/{b}selected_cohort_variants.tsv'.format(a=self.gui_abs_path, b=self.var_backend_dir), 'r') as infile:
			infile = infile.readlines()
		infile = list(map(lambda x: re.sub('\n', '', x), infile))
		#
		self.cohort_lines = tuple(infile)
		lines_var = StringVar(value=self.cohort_lines)
		self.cohort_y_list_scroll = Scrollbar(self.cohort_frame, orient=VERTICAL)
		self.cohort_x_list_scroll = Scrollbar(self.cohort_frame, orient=HORIZONTAL)
		self.cohort_box = Listbox(self.cohort_frame, listvariable=lines_var, selectmode=MULTIPLE, xscrollcommand=self.cohort_x_list_scroll.set, yscrollcommand=self.cohort_y_list_scroll.set)
		self.cohort_x_list_scroll.config(command=self.cohort_box.xview)
		self.cohort_x_list_scroll.pack(side=RIGHT, fill=X)
		self.cohort_y_list_scroll.config(command=self.cohort_box.yview)
		self.cohort_y_list_scroll.pack(side=RIGHT, fill=Y)
		self.cohort_x_list_scroll.pack(side=BOTTOM, fill=X)
		self.cohort_y_list_scroll.pack(side=RIGHT, fill=Y)
		self.cohort_box.pack(fill=BOTH, expand=True)
	def removing(self):
		"""Used to remove selected variants."""
		items = self.cohort_box.curselection()
		position_tracker = 0 ## recovers indexing since lines are removed
		for i in items :
			idx = int(i) - position_tracker
			self.cohort_box.delete(idx, idx)
			position_tracker = position_tracker + 1
	def filter_no_pass_alt(self):
		"""Remove variants without PASS."""
		position_tracker = 0
		for n,i in enumerate(self.cohort_box.get(0, last=END)):
			temp_line = i.split('\t')
			if (temp_line[7] != 'PASS'):
				idx = int(n) - position_tracker
				self.cohort_box.delete(idx, idx)
				position_tracker = position_tracker + 1
	def filter_del_alt(self):
		"""Remove variants with <DEL> alt."""
		position_tracker = 0
		for n,i in enumerate(self.cohort_box.get(0, last=END)):
			temp_line = i.split('\t')
			if (re.search('<DEL>', temp_line[5])):
				idx = int(n) - position_tracker
				self.cohort_box.delete(idx, idx)
				position_tracker = position_tracker + 1
	def filter_dup_alt(self):
		"""Remove variants with <DUP> alt."""
		position_tracker = 0
		for n,i in enumerate(self.cohort_box.get(0, last=END)):
			temp_line = i.split('\t')
			if (re.search('<DUP>', temp_line[5])):
				idx = int(n) - position_tracker
				self.cohort_box.delete(idx, idx)
				position_tracker = position_tracker + 1
	def filter_dot(self):
		"""Remove variants with dot IDs."""
		position_tracker = 0
		for n,i in enumerate(self.cohort_box.get(0, last=END)):
			temp_line = i.split('\t')
			if (temp_line[3] == '.'):
				idx = int(n) - position_tracker
				self.cohort_box.delete(idx, idx)
				position_tracker = position_tracker + 1
	def popup(self):
		"""To get user query location for highlighting variants within the variant box."""
		self.top = Toplevel(self.frame)
		self.top.geometry("350x350+10+10")
		#
		Label(self.top, text="Chromosome").pack()
		self.chrom_top = Entry(self.top)
		self.chrom_top.pack()
		#
		Label(self.top, text="Position").pack()
		self.pos_top = Entry(self.top)
		self.pos_top.pack()
		#
		for n,i in enumerate(self.cohort_box.get(0, last=END)):
			self.cohort_box.itemconfig(n, background='white')
		#
		top_btn = Button(self.top, text="OK", command=self.go)
		top_btn.pack()
	def go(self):
		"""Highlighting target variants."""
		chrom_top = self.chrom_top.get()
		pos_top = self.pos_top.get()
		self.top.destroy()
		if (chrom_top and pos_top):
			for n,i in enumerate(self.cohort_box.get(0, last=END)):
				self.cohort_box.itemconfig(n, background='white')
			for n,i in enumerate(self.cohort_box.get(0, last=END)):
				temp = i.split('\t')
				temp_chr, temp_pos = temp[1], temp[2]
				if (temp_chr == chrom_top and temp_pos == pos_top):
					self.cohort_box.itemconfig(n, background='lightgreen')
	def exporting(self):
		"""Export variants to a file."""
		filename = tkFileDialog.asksaveasfile(mode='w', defaultextension='.txt')
		out_file = filename
		if (out_file):
			for line in self.cohort_box.get(0, last=END):
				out_file.write(line+'\n')
			out_file.close()
	def get_info(self):
		"""Used to display the VCF line in a more human readable/alphabetically sorted format."""
		VCF = {'INDIVIDUAL':'', 'CHROM':'', 'POS':'', 'ID':'', 'REF':'', 'ALT':'', 'QUAL':'', 'FILTER':'', 'INFO':'', 'FORMAT':''}
		lines_selected = []
		items = self.cohort_box.curselection()
		for i in items :
			lines_selected.append(self.cohort_box.get(i, last=i))
		if (lines_selected):
			all_but_info = ''
			## indiv ,chrom, pos, ID, ref, alt, qual, filter, info, format, sample
			target = lines_selected[-1][-1].split('\t')
			all_but_info = 'Individual : {}\tChromosome : {}\tPosition : {}\tID : {}\tREF : {}\tALT : {}\tQUAL : {}\tFilter : {}\tFormat : {}\tSample : {}\t'.format(target[0], target[1], target[2], target[3], target[4], target[5], target[6], target[7], target[9], target[10])
			info_fields = ''
			for x in target[8].split(';'):
				re_match_pairs = re.search('(\S+)=(\S+)', x)
				if (re_match_pairs):
					key_ = re_match_pairs.group(1)
					value_list = re.split('[,|]', re_match_pairs.group(2))
					value_ = ','.join(list(set(value_list)))
					info_fields = info_fields + '{} : {}\t'.format(key_, value_)
			all_fields = all_but_info + info_fields
			all_fields_list = all_fields.split('\t')
			all_fields_list.sort(key=lambda x: x.lower())
			#
			track_label_height = 0
			#
			top = Toplevel(self.frame)
			top.geometry("500x500+50+50")
			#
			ground_layer_scroll_y = Scrollbar(top, orient=VERTICAL)
			ground_layer_scroll_y.pack(fill=Y, side=RIGHT)
			ground_layer_scroll_x = Scrollbar(top, orient=HORIZONTAL)
			ground_layer_scroll_x.pack(fill=X, side=BOTTOM)
			#
			canvas_layer = Canvas(top, bg='#E0E0E0', bd=0, highlightthickness=0, yscrollcommand=ground_layer_scroll_y.set, xscrollcommand=ground_layer_scroll_x.set)
			canvas_layer.pack(fill=BOTH, expand=True)
			#
			ground_layer_scroll_y.config(command=canvas_layer.yview)
			ground_layer_scroll_x.config(command=canvas_layer.xview)
			#
			result_container = Frame(canvas_layer, bg='#E0E0E0')
			result_container.pack(fill=BOTH, expand=True)
			for elem in all_fields_list:
				temp_lbl = Label(result_container, bg='#E0E0E0', text=elem, wraplength=1000)
				temp_lbl.pack(anchor=W)
				track_label_height += temp_lbl.winfo_reqheight()
			#
			canvas_layer.configure(scrollregion=(0,0,2000,track_label_height))
			canvas_layer.create_window(0, 0, window=result_container, anchor='nw')



def build_expect_file(gui_path, temp_dump, user_info):
	#
	expect_lines = r"""#!/usr/bin/expect -f
set timeout -1
spawn bash {dir_name}recent_runs/{local_dump}current_command
expect -re {{[Pp]assword}}
send "{passw}\n"
expect "Permission denied, please try again."
exit 1
expect eof
""".format(dir_name=gui_path, local_dump=temp_dump, passw=user_info['server_user_password'])
	#
	with open(gui_path+'recent_runs/'+temp_dump+'current_expect', 'w') as cmd:
		cmd.write(expect_lines)



class populate_trio_igv_tab:
	"""Populating the IGV tab."""
	def __init__(self, **kwargs):
		self.frame = kwargs['frame']
		self.var_backend_dir = kwargs['var_backend_dir']
		self.var_gui_abs_path = kwargs['gui_abs_path']
		self.var_user_settings = kwargs['user_settings_var']
		self.query_info = kwargs['query_info']
		## clean up frame
		for w in self.frame.winfo_children():
			w.destroy()
		## the tool bar containing the edit options of the variant box
		self.toolbar_igv = Frame(self.frame, bg='#C8C8C8', relief=GROOVE, borderwidth=2)
		#
		self.z_out = Button(self.toolbar_igv, text=' - ', font='bold 20', command=lambda: self.local_zoom_out(30), highlightbackground='#C8C8C8')
		self.z_out.place(x=20, y=0)
		#
		self.z_in = Button(self.toolbar_igv, text=' + ', font='bold 20', command=lambda: self.local_zoom_in(30), highlightbackground='#C8C8C8')
		self.z_in.place(x=80, y=0)
		#
		self.reload = Button(self.toolbar_igv, text='Reload flanking bases', command=self.reload_flanking_area, highlightbackground='#C8C8C8')
		self.reload.place(x=150, y=0)
		#
		self.export = Button(self.toolbar_igv, text='Export', command=self.exporting, highlightbackground='#C8C8C8')
		self.export.place(x=330, y=0)
		#
		self.ground_layer = Frame(self.frame, bg='#E0E0E0')
		#
		self.place_image('{a}recent_runs/{b}trio_igv.png'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
		self.frame.bind("<Configure>", self.config)
	def place_image(self, pic):
		"""Displaying the IGV plot."""
		## clean up frame
		for w in self.ground_layer.winfo_children():
			w.destroy()
		## prepare canvas
		self.ground_layer_scroll_y = Scrollbar(self.ground_layer, orient=VERTICAL)
		self.ground_layer_scroll_y.pack(fill=Y, side=RIGHT)
		self.ground_layer_scroll_x = Scrollbar(self.ground_layer, orient=HORIZONTAL)
		self.ground_layer_scroll_x.pack(fill=X, side=BOTTOM)
		#
		self.canvas_layer = Canvas(self.ground_layer, bg='#E0E0E0', scrollregion=(0,0,800,500), bd=0, highlightthickness=0, yscrollcommand=self.ground_layer_scroll_y.set, xscrollcommand=self.ground_layer_scroll_x.set)
		self.canvas_layer.pack(fill=BOTH, expand=True)
		#
		self.ground_layer_scroll_y.config(command=self.canvas_layer.yview)
		self.ground_layer_scroll_x.config(command=self.canvas_layer.xview)
		#
		self.result_container = Frame(self.canvas_layer, bg='#E0E0E0')
		self.result_container.pack(fill=BOTH, expand=True)
		#
		self.canvas_layer.create_window(0, 0, window=self.result_container, anchor='nw')
		## resize into a size
		self.image = Image.open(pic)
		self.image_width,self.image_height = self.image.size
		self.size = (700,430)
		self.resized = self.image.resize(self.size, Image.ANTIALIAS)
		self.photo = ImageTk.PhotoImage(self.resized)
		self.label = Label(self.result_container, image=self.photo)
		self.label.pack(fill=BOTH, expand=TRUE)
	def config(self, event):
		"""Method called upon any size change."""
		self.current_width, self.current_height = event.width, event.height
		x = self.current_width*0.05 ## padding on horizontal axis
		y = self.current_height*0.05
		#
		self.mainframe_width = int(self.current_width*0.9)
		self.mainframe_height = int(self.current_height*0.9)
		#
		self.toolbar_igv.place(x=x, y=10, height=40, width=500)
		self.ground_layer.place(x=x,y=80,width=self.mainframe_width,height=self.mainframe_height*0.9)
	def exporting(self):
		"""Export the IGV plot."""
		filename = tkFileDialog.asksaveasfile(mode='w', defaultextension='.png')
		out_file = filename
		if (out_file):
			temp_image = Image.open('{}local_scripts/recent_runs/trio_igv.png'.format(self.var_gui_abs_path))
			temp_image.save(filename)
	def local_zoom_in(self, factor):
		"""Zoom in the image locally."""
		if (self.size[0] < 13000 and self.size[1] < 1000):
			self.factor = factor
			self.new_width = self.size[0] + self.factor
			self.new_height = self.size[1] + self.factor
			self.size = (self.new_width , self.new_height)
			self.canvas_layer.configure(scrollregion = (0,0,self.size[0]+10,self.size[1]+10))
			for w in self.result_container.winfo_children():
				w.destroy()
			self.resized = self.image.resize(self.size, Image.ANTIALIAS)
			self.photo = ImageTk.PhotoImage(self.resized)
			self.label = Label(self.result_container, image=self.photo)
			self.label.pack(fill=BOTH, expand=TRUE)
	def local_zoom_out(self, factor):
		"""Zoom out the image locally."""
		if (self.size[0] > 400 and self.size[1] > 120):
			self.factor = factor
			self.new_width = self.size[0] - self.factor
			self.new_height = self.size[1] - self.factor
			self.size = (self.new_width , self.new_height)
			self.canvas_layer.configure(scrollregion = (0,0,self.size[0]+10,self.size[1]+10))
			for w in self.result_container.winfo_children():
				w.destroy()
			self.resized = self.image.resize(self.size, Image.ANTIALIAS)
			self.photo = ImageTk.PhotoImage(self.resized)
			self.label = Label(self.result_container, image=self.photo)
			self.label.pack(fill=BOTH, expand=TRUE)
	def reload_flanking_area(self):
		"""Reloading the image from the server by chosing flanking base count."""
		self.flank_top = Toplevel(self.frame)
		self.flank_top.geometry("600x350+400+50")
		#
		Label(self.flank_top, text='Reload IGV plot. Choose the size of the flanking region in base pairs\neg. -(left side bases):+(right side bases)', font='Aerial 16 bold').grid(row=0, column=0, padx=5, pady=20)
		#
		self.flank_var = StringVar()
		#
		flank_60 = Radiobutton(self.flank_top, text='-60:+60', variable=self.flank_var, value='60')
		flank_60.grid(row=1, column=0, sticky=W, pady=10, padx=5)
		#
		flank_500 = Radiobutton(self.flank_top, text='-500:+500', variable=self.flank_var, value='500')
		flank_500.grid(row=2, column=0, sticky=W, pady=10, padx=5)
		#
		flank_1000 = Radiobutton(self.flank_top, text='-1000:+1000', variable=self.flank_var, value='1000')
		flank_1000.grid(row=3, column=0, sticky=W, pady=10, padx=5)
		#
		flank_10000 = Radiobutton(self.flank_top, text='-10000:+10000', variable=self.flank_var, value='10000')
		flank_10000.grid(row=4, column=0, sticky=W, pady=10, padx=5)
		#
		go_btn = Button(self.flank_top, text='Reload', command=self.buffers_image)
		go_btn.grid(row=5, column=0, sticky=W, pady=10, padx=5)
	def buffers_image(self):
		self.place_image('{}loading.png'.format(self.var_gui_abs_path))
		t2=threading.Thread(target=self.reload_igv_plot, args=())
		t2.start()
	def reload_igv_plot(self):
		"""Procedure to reload IGV plot from server."""
		flank_area = self.flank_var.get()
		original_start = self.query_info['start']
		self.flank_top.destroy()
		lower_limit = int(original_start) - int(flank_area)
		upper_limit = int(original_start) + int(flank_area)
		try:
			local_path = self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir
			for fl_1 in os.listdir(local_path):
				os.remove(local_path+fl_1)
		except:
			pass
		#
		build_expect_file(self.var_gui_abs_path, self.var_backend_dir, self.var_user_settings)
		#
		string_user_settings = ';'.join([':'.join([str(k),str(v)]) for k,v in self.var_user_settings.items()])
		#
		os.system('python {a}local_scripts/id_coords_trio_igv_source_builder.py --o {b}recent_runs/{c}current_run.py --gui_path {d} --remote_dir {e} --id {f} --chrom {g} --start {h} --stop {i} --string_user_settings_dict \'{j}\''.format(a=self.var_gui_abs_path, b=self.var_gui_abs_path, c=self.var_backend_dir, d=self.var_gui_abs_path, e=self.var_backend_dir, f=self.query_info['ID'], g=self.query_info['chrom'], h=str(lower_limit), i=str(upper_limit), j=string_user_settings))
		#
		with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
			cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {file_name} {user}@{server}:~/{backend_dir_name}'.format(file_name=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_run.py', user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir)]))
		#
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
		os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
		#
		with open(self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir+'current_command', 'w') as cmd:
			cmd.write('\n'.join(['#!/usr/bin/env bash', 'scp {user}@{server}:~/{backend_dir_name}{file_name} {location}'.format(user=self.var_user_settings['server_username'], server=self.var_user_settings['server_name'], backend_dir_name=self.var_backend_dir, file_name='trio_igv.png', location=self.var_gui_abs_path+'recent_runs/'+self.var_backend_dir)]))
		#
		os.system('expect {a}recent_runs/{b}current_expect'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))
		#
		self.place_image('{a}recent_runs/{b}trio_igv.png'.format(a=self.var_gui_abs_path, b=self.var_backend_dir))











