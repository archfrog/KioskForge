#!/usr/bin/env python3

# Import Python v3.x's type hints as these are used extensively in order to allow MyPy to perform static checks on the code.
from typing import Any, Dict, List, Optional, TextIO, Tuple

from enum import Enum
from functools import partial
import os
import pathlib
import platform
import sys
import webbrowser

import tkinter as tk
import tkinter.font as tkfont
import tkinter.ttk as ttk
import tkinter.filedialog as tkfile

from kiosklib.driver import KioskDriver
from kiosklib.kiosk import Kiosk
from kiosklib.locales import LOCALES
from kiosklib.timezones import TIMEZONES
from kiosklib.version import Version

if sys.platform == "win32":
	# Make Tkinter aware of high-DPI displays with and without scaling (otherwise the reported screen size is wildly wrong).
	# From: https://stackoverflow.com/questions/3949844/how-can-i-get-the-screen-size-in-tkinter
	import ctypes
	try: # Windows 8.1 and later
		# NOTE: The '2' makes Windows High-DPI aware on all monitors, not just the primary monitor (which uses the value '1').
		ctypes.windll.shcore.SetProcessDpiAwareness(2)
	except Exception as e:
		pass

# From: https://stackoverflow.com/questions/16803686/how-to-create-a-modal-dialog-in-tkinter
class ModalWindow(tk.Toplevel):

	def __init__(self, parent):
		tk.Toplevel.__init__(self, parent)

		self._build()

		# Modal window.
		# NOTE: Wait for visibility or grab_set doesn't seem to work.
		self.wait_visibility()
		self.grab_set()
		self.transient(parent)

	def _build(self) -> None:
		raise Exception("Abstract method called")


class ModalSample(ModalWindow):

	def __init__(self) -> None:
		ModalWindow.__init__(self)

	def _build(self) -> None:
		self.__entry = tk.Entry(self)
		self.__entry.pack()

		ok_btn = tk.Button(self, text="OK", command=self.ok)
		ok_btn.pack()

	def ok(self):
		self.data = self.__entry.get()
		self.grab_release()
		self.destroy()


class SortableTreeview(ttk.Treeview):
	"""
		Makes a TkInter Treeview sortable by clicking a column.  See https://stackoverflow.com/a/63432251 for more information.

		NOTE: This currently works very poorly together with even-odd color schemes as they are messed up by the sort operation.
	"""

	# NOTE: Inherits the parent's constructor.

	def heading(self, column, sort_by=None, **kwargs):
		if sort_by and not hasattr(kwargs, 'command'):
			func = getattr(self, f"_sort_by_{sort_by}", None)
			if func:
				kwargs['command'] = partial(func, column, False)
		return super().heading(column, **kwargs)

	def _sort(self, column, reverse, data_type, callback):
		l = [(self.set(k, column), k) for k in self.get_children('')]
		l.sort(key=lambda t: data_type(t[0]), reverse=reverse)
		for index, (_, k) in enumerate(l):
			self.move(k, '', index)
		self.heading(column, command=partial(callback, column, not reverse))

	def _sort_by_int(self, column, reverse):
		"""Sorts integers with or without thousand separators (,)."""
		def _strip_commas(value : str):
			return int(value.replace(",", ""))

		self._sort(column, reverse, _strip_commas, self._sort_by_int)

	def _sort_by_str(self, column, reverse):
		"""Sorts strings case-insensitively."""
		def _str_to_lower(value : str) -> str:
			return value.lower()

		self._sort(column, reverse, _str_to_lower, self._sort_by_str)

	def _sort_by_date(self, column, reverse):
		"""Sorts dates without a time part."""
		def _str_to_datetime(value : str):
			return datetime.datetime.strptime(value, "%Y-%m-%d")

		self._sort(column, reverse, _str_to_datetime, self._sort_by_date)

	def _sort_by_version(self, column, reverse):
		"""Sorts version numbers."""
		def _version_to_str(value : str):
			path = value.split(".")
			ints = [*map(lambda x: int(x), path)]
			return ints

		self._sort(column, reverse, _version_to_str, self._sort_by_version)


class TreeviewColumn:

	def __init__(self, name : str, type : str, width : int, alignment : str) -> None:
		self.name = name
		self.type = type
		self.width = width
		self.alignment = alignment


class KioskBrowser(SortableTreeview):

	def __init__(self, parent) -> None:
		columns = [
			TreeviewColumn("Status",    "str",     100, "w"),
			TreeviewColumn("Host Name", "str",     100, "w"),
			TreeviewColumn("LAN IP",    "version", 100, "w"),
			TreeviewColumn("Version",   "version", 100, "w"),
			TreeviewColumn("Comment",   "str",     200, "w"),
		]
		headings = [*map(lambda x: x.name, columns)]
		SortableTreeview.__init__(self, parent, columns=headings, show="headings", selectmode=tk.BROWSE)

		style = ttk.Style()

		# Write the headings using a bold font.
		style.configure('Treeview.Heading', font=('TkDefaultFont', 10, 'bold'))

		# Fix broken height of Treeview rows as ttk.Treeview doesn't bother to do this so the rows overlap visually.
		style.configure("Treeview", rowheight=30)

		self.tag_configure("even", background="white")
		self.tag_configure("odd", background="lightgray")

		# Create each column in turn.
		for column in columns:
			self.heading(column.name, text=column.name, sort_by=column.type, anchor=column.alignment)
			self.column(column.name, width=column.width, stretch=True, anchor=column.alignment)

		# Assign test data.
		rows = [
			["Running", "ubuntu", "192.168.1.20", "0.24", "Mikael's web server"],
			["Offline", "pi4b",   "192.168.1.30", "0.25", "Mikael's pi4B kiosk"],
			["Running", "pi5",    "192.168.1.50", "0.23", "Mikael's Pi5 kiosk"],
		]
		self.assign(rows)

	def assign(self, rows) -> None:
		even = True
		for row in rows:
			self.insert("", "end", values=row)	# , tag='even' if even else 'odd')
			even = not even

	def clear(self) -> None:
		self.delete(*self.get_children())


SUPPORTED_EXTENSION = ".kiosk"

SUPPORTED_FILE_TYPES = [
	("KioskForge files", "*" + SUPPORTED_EXTENSION),
	("All files", "*")
]


class Target:

	pass


class KioskForgeApp(tk.Tk):

	def __init__(self, origin : str, master=None) -> None:
		# Initialize base class.
		tk.Tk.__init__(self, master)

		self.__version = Version("KioskForge")
		self.__origin = origin
		self.__kiosk = Kiosk(self.__version)
		self.__banner = f"{self.__version.product} v{self.__version.version}"

		self.__active : Optional[tk.Widget] = None

		# Assign the loaded kiosk filename (sets the main program window title).
		self.filename = ""

		# xxx_w is the width, xxx_h is the height.
		(screen_w, screen_h) = (self.winfo_screenwidth(), self.winfo_screenheight())
		(self_w, self_h) = (screen_w // 2, screen_h // 2)
		(self_x, self_y) = (screen_w // 2 - self_w // 2, screen_h // 2 - self_h // 2)
		self.geometry("%dx%d+%d+%d" % (self_w, self_h, self_x, self_y))
		# NOTE: (Places the window way to the left.) self.eval('tk::PlaceWindow . center')
		self.grid()

		# Create main menu.
		menu = tk.Menu(self, tearoff=False)
		self.config(menu=menu)

		file_menu = tk.Menu(menu, tearoff=False)
		menu.add_cascade(label='File', accelerator="Alt-F", underline=0, menu=file_menu)
		file_menu.add_command(label='New', accelerator="Ctrl-N", command=self.handle_menu_file_new)
		file_menu.add_command(label='Open...', accelerator="Ctrl-O", command=self.handle_menu_file_open)
		file_menu.add_command(label='Save', accelerator="Ctrl-S", command=self.handle_menu_file_save)
		file_menu.add_command(label='Save as...', accelerator="Ctrl-V", command=self.handle_menu_file_save_as)
		file_menu.add_separator()
		file_menu.add_command(label='Exit', accelerator="Ctrl-X", command=self.handle_menu_file_exit)

		kiosk_menu = tk.Menu(menu, tearoff=False)
		menu.add_cascade(label='Kiosk', accelerator="Alt-K", underline=0, menu=kiosk_menu)
		kiosk_menu.add_command(label='Browse', accelerator="Ctrl-B", command=self.handle_menu_kiosk_browse)
		kiosk_menu.add_separator()
		kiosk_menu.add_command(label='Edit', accelerator="Ctrl-E", command=self.handle_menu_kiosk_edit)
		kiosk_menu.add_separator()
		kiosk_menu.add_command(label='Install', accelerator="Ctrl-I", command=self.handle_menu_kiosk_install)

		help_menu = tk.Menu(menu, tearoff=False)
		menu.add_cascade(label='Help', accelerator="Alt-H", underline=0, menu=help_menu)
		help_menu.add_command(label='FAQ', accelerator="Ctrl-A", command=self.handle_menu_help_faq)
		help_menu.add_command(label='Manual', accelerator="Ctrl-H", command=self.handle_menu_help_manual)
		help_menu.add_command(label='About', accelerator="Ctrl-A", command=self.handle_menu_help_about)

		# File menu keyboard shortcuts.
		self.bind_all('<Control-n>', lambda event: self.handle_menu_file_new())
		self.bind_all('<Control-o>', lambda event: self.handle_menu_file_open())
		self.bind_all('<Control-s>', lambda event: self.handle_menu_file_save())
		self.bind_all('<Control-v>', lambda event: self.handle_menu_file_save_as())
		self.bind_all('<Control-x>', lambda event: self.handle_menu_file_exit())

		# Kiosk menu keyboard shortcuts.
		self.bind_all('<Control-b>', lambda event: self.handle_menu_kiosk_browse())
		self.bind_all('<Control-e>', lambda event: self.handle_menu_kiosk_edit())
		self.bind_all('<Control-i>', lambda event: self.handle_menu_kiosk_install())

		# About menu keyboard shortcuts.
		self.bind_all('<Control-a>', lambda event: self.handle_menu_help_about())
		self.bind_all('<Control-h>', lambda event: self.handle_menu_help_manual())

	@property
	def filename(self) -> str:
		return self.__kiosk_filename

	@filename.setter
	def filename(self, value : str) -> None:
		# Make the title bar display a Windows-style path with backslashes instead of slashes.
		if sys.platform == "win32":
			value = value.replace('/', os.sep)

		self.__kiosk_filename = value
		if value:
			self.title(f"{self.__banner} - {value}")
		else:
			self.title(self.__banner)

	def handle_menu_file_new(self):
		# TODO: Ask for confirmation if the kiosk has changed.
		done = False
		while not done and self.__kiosk.edited:
			answer = tk.messagebox.askyesno(
				"The kiosk has changed!",
				message="Do you want to save your kiosk before making a new kiosk?"
			)
			if answer:
				if self.filename:
					filename = tkfile.asksaveasfilename(
						initialdir=os.path.dirname(self.filename),
						initialfile=os.path.basename(self.filename),
						filetypes=SUPPORTED_FILE_TYPES,
						defaultextension=SUPPORTED_EXTENSION
					)
				else:
					filename = tkfile.asksaveasfilename(filetypes=SUPPORTED_FILE_TYPES, defaultextension=SUPPORTED_EXTENSION)

				if filename:
					try:
						# NOTE: Successfully saving a kiosk, clears its "edited" flag so that 'self.__kiosk.edited' returns 'False'.
						self.__kiosk.save(filename)

						done = True
					except IOError as that:
						tk.messagebox.showerror(title="Error saving kiosk!", message="Please press OK to try again.")

		# Create new kiosk.
		self.__kiosk = Kiosk(self.__version)
		self.filename = ""

	def handle_menu_file_open(self):
		# TODO: Save last 'initialdir' and reuse it if it has been set (not possible?).
		filename = tkfile.askopenfilename(
			initialdir=os.getcwd(),
			title="Select a kiosk to load",
			filetypes=SUPPORTED_FILE_TYPES
		)
		if not filename:
			return

		errors = self.__kiosk.load_list(filename)
		if errors:
			# TODO: Display errors.
			pass
		else:
			self.filename = filename

	def handle_menu_file_save(self):
		# If not edited, report error and return.
		if not self.__kiosk.edited:
			tk.messagebox.showerror(title="Kiosk not changed!", message="Please use File, Save As to save an empty kiosk.")
			return

		# If the kiosk doesn't have a name yet, ask "Save As" to handle the save operation and return.
		if not self.filename:
			self.handle_menu_file_save_as()
			return

		self.__kiosk.save(self.filename)

	def handle_menu_file_save_as(self):
		filename = tkfile.asksaveasfilename(filetypes=SUPPORTED_FILE_TYPES, defaultextension=SUPPORTED_EXTENSION)
		if filename:
			# NOTE: Successfully saving a kiosk, clears its "edited" flag so that 'self.__kiosk.edited' returns 'False'.
			self.__kiosk.save(filename)
			self.filename = filename

	def handle_menu_file_exit(self):
		# Check if the current kiosk configuration needs to be saved and prompt the user to do so, if applicable.
		while self.__kiosk.edited:
			if not tk.messagebox.askyesno("The kiosk has changed!", message="Do you want to save your kiosk before exiting?"):
				break

			if self.filename:
				filename = tkfile.asksaveasfilename(
					initialdir=os.path.dirname(self.filename),
					initialfile=os.path.basename(self.filename),
					filetypes=SUPPORTED_FILE_TYPES,
					defaultextension=SUPPORTED_EXTENSION
				)
			else:
				filename = tkfile.asksaveasfilename(filetypes=SUPPORTED_FILE_TYPES, defaultextension=SUPPORTED_EXTENSION)
			if not filename:
				break

			try:
				# NOTE: Successfully saving a kiosk, clears its "edited" flag so that 'self.__kiosk.edited' returns 'False'.
				self.__kiosk.save(filename)
				self.filename = filename
				break
			except IOError as that:
				tk.messagebox.showerror(title="Error saving kiosk!", message="Please press OK to try again.")

		self.quit()

	def handle_menu_kiosk_browse(self):
		frame1 = ttk.Frame(self)
		frame1.pack(side=tk.TOP, fill=tk.BOTH)

		label1 = tk.Label(frame1, text="Kiosks found on LAN")
		label1.pack()

		browser = KioskBrowser(frame1)
		browser.pack(side=tk.TOP, fill=tk.BOTH)

	def handle_menu_kiosk_edit(self):
		if not self.filename:
			tk.messagebox.showerror("Error", "No kiosk loaded!")
			return

		errors = self.__kiosk.load_list(self.filename)
		if not errors:
			errors = ["Kiosk is valid."]

		# Create a frame to track all subwidgets of the editor (the editor itself and the log window below).
		frame = tk.Frame(self)
		frame.pack(side=tk.TOP, fill=tk.BOTH)

		# TODO: Add vertical scroll bar as the Text() widget does not resize itself when the window is shrunk.
		fixed_font = tkfont.nametofont("TkFixedFont")
		fixed_font.configure(size=12)
		fixed_font.configure(weight=tkfont.NORMAL)

		text = tk.Text(frame, font=fixed_font)
		text.pack(side=tk.TOP, fill=tk.BOTH)

		status = tk.Text(frame, font=fixed_font)

		status.bind("<1>", lambda event: status.focus_set())

		status.pack(side=tk.BOTTOM, fill=tk.BOTH)
		status.insert('1.0', '\n'.join(errors))
		# Make the status part read-only (to insert text, first enable it again, insert, and then disable once again).
		status.config(state=tk.DISABLED)

		return

		# TODO: Finish up 'handle_menu_kiosk_edit'.
		errors = self.__kiosk.check()
		if errors:
			print()
			print("Errors(s) detected in kiosk (please correct or fill out all listed fields):")
			print()
			for error in errors:
				print("  " + error)
		del errors

	def handle_menu_kiosk_edit_tabbed(self):
		# Hack to avoid creating multiple tabs on the same page.
		if self.__active:
			self.__active.destroy()
			self.__active = None

		# Create a frame to track all subwidgets on the tabbed editor.
		self.__active = tk.Frame(self)
		self.__active.pack(side=tk.TOP, fill=tk.BOTH)

		# TODO: Add vertical scroll bar as the Text() widget does not resize itself when the window is shrunk.
		notebook = ttk.Notebook(self.__active)

		notebook.pack(side=tk.TOP, fill=tk.BOTH)
		# TODO: notebook.enable_traversal()

		title_font = tkfont.Font(family="TkCaptionFont")
		title_font.configure(size=15)
		title_font.configure(weight="bold")

		# Create General tab and populate it.
		frame1 = ttk.Frame(self.__active)
		notebook.add(frame1, text="General")

		label1 = tk.Label(frame1, text="General Settings", font=title_font)
		label1.pack(side=tk.TOP, fill=tk.X)

		label1a = tk.Label(frame1, text="Comment:")
		label1a.pack(side=tk.TOP, fill=tk.X)

		(parent_w, parent_h) = (self.__active.winfo_width(), self.__active.winfo_height())
		frame1b = tk.Frame(self.__active, width=int(parent_w * 0.6))
		frame1b.pack(fill=tk.BOTH, expand=1, padx=10, pady=10)

		fixed_font = tkfont.nametofont("TkFixedFont")
		#fixed_font.configure(size=12)
		fixed_font.configure(weight=tkfont.NORMAL)

		widget1a = tk.Text(frame1, height=10, font=fixed_font)
		widget1a.pack(side=tk.TOP, fill=tk.X)

		label1c = tk.Label(frame1, text="The comment is only for your internal use: Record what you wish to record.")
		label1c.pack()

		# Create Browser tab and populate it.
		frame2 = ttk.Frame(self.__active)
		notebook.add(frame2, text="Browser", padding="10 10 10 10")

		label2 = tk.Label(frame2, text="Browser Settings", font=title_font)
		label2.pack(side=tk.TOP, fill=tk.X)

		# Create Network tab and populate it.
		frame3 = ttk.Frame(self.__active)
		notebook.add(frame3, text="Network", padding="10 10 10 10")

		label3 = tk.Label(frame3, text="Network Settings", font=title_font)
		label3.pack(side=tk.TOP, fill=tk.X)

		# Create Platform tab and populate it.
		frame4 = ttk.Frame(self.__active)
		notebook.add(frame4, text="Platform", padding="10 10 10 10")

		label4 = tk.Label(frame4, text="Platform Settings", font=title_font)
		label4.pack(side=tk.TOP, fill=tk.X)

		# Create System tab and populate it.
		frame5 = ttk.Frame(self.__active)
		notebook.add(frame5, text="System", padding="10 10 10 10")

		label5 = tk.Label(frame5, text="System Settings", font=title_font)
		label5.pack(side=tk.TOP, fill=tk.X)

		notebook.pack(fill=tk.BOTH)

		# Create status bar.
		if True:
			status = tk.Label(self.__active, text="", bd=1, relief=tk.SUNKEN, anchor=tk.W)
			status.pack(side=tk.BOTTOM, fill=tk.X)

	def handle_menu_kiosk_edit_browser(self):
		self.handle_unfinished()
		return

	def handle_menu_kiosk_edit_network(self):
		self.handle_unfinished()
		return

	def handle_menu_kiosk_edit_platform(self):
		self.handle_unfinished()
		return

	def handle_menu_kiosk_edit_system(self):
		self.handle_unfinished()
		return

	def handle_menu_kiosk_install(self):
		# Install the kiosk by updating the installation media so the installation automatically forges the new kiosk.
		self.handle_unfinished()
		return

		# Report success to the user.
		tk.messagebox.showinfo(
			"Success",
			"Preparation of boot image successfully completed - please eject/unmount %s safely." % target.basedir
		)

	def handle_menu_help_about(self):
		# Create a Tkinter top-level window for displaying various information about the program.
		window = tk.Toplevel(self)
		window.title("About")

		# Center the About window in the middle of the KioskForge window (NOTE: I never did manage to center it precisely...).
		(parent_x, parent_y) = (self.winfo_rootx(), self.winfo_rooty())
		(parent_w, parent_h) = (self.winfo_width(), self.winfo_height())
		(window_w, window_h) = (800, 400) #(parent_w // 2, parent_h // 2)
		(window_x, window_y) = (parent_x + parent_w // 2 - window_w // 2, parent_y + parent_h // 2 - window_h // 2)
		window.geometry("%dx%d+%d+%d" % (window_w, window_h, window_x, window_y))
		window.update()

		banner_font = tkfont.Font(family="TkCaptionFont")
		banner_font.configure(size=20)
		banner_font.configure(weight="bold")

		label1 = tk.Label(window, text=self.__banner, font=banner_font)
		label1.pack()

		label2 = tk.Label(window, text="Copyright © 2024-2025 Vendsyssel Historiske Museum (Denmark)")
		label2.pack()

		label3 = tk.Label(window, text="https://kioskforge.org/", fg="blue")
		label3.bind("<Button-1>", lambda event: webbrowser.open(event.widget.cget("text")))
		label3.pack()

		button = tk.Button(window, text="OK", command=window.destroy)
		button.pack(side="bottom", pady=10)
		button.focus_set()

		window.mainloop()

	def _handle_view_documentation(self, basename : str) -> None:
		# Build list of documentation files to look for (.html is for end-users, .md is for developers).
		filenames = []
		for extension in [".html", ".md"]:
			filenames += [self.__origin + "docs" + os.sep + basename + extension]

		# Check if any of the documentations exist on this system.
		found = []
		for filename in filenames:
			if os.path.isfile(filename):
				found.append(filename)

		# If no documentation file found, report error and return.
		if not found:
			tk.messagebox.showerror("Unable to locate file!", f"Unable to open the file '{basename}'")
			return

		# Open a web browser to display the file (this may cause associated apps to be opened on Winblows).
		webbrowser.open_new(pathlib.Path(found[0]).as_uri())

	def handle_menu_help_faq(self):
		self._handle_view_documentation("FAQ")

	def handle_menu_help_manual(self):
		self._handle_view_documentation("Manual")

	def handle_unfinished(self):
		tk.messagebox.showerror("Error", "Feature not implemented yet!")


def main(arguments : List[str]) -> int:
	# TODO: Optionally restore previous window position(s) and size(s).

	# Parse command-line arguments.
	if len(arguments) != 1:
		raise SyntaxError("\"KioskForge.py\"")

	(homedir, basename) = os.path.split(arguments[0])
	if homedir[-1] != os.sep:
		homedir += os.sep

	forge = KioskForgeApp(homedir)

	# Change theme to Windows Native as the default theme is rather boring.
	style = ttk.Style(forge)
	style.theme_use('winnative')

	forge.mainloop()

	# TODO: Save window position(s) and size(s).
	return 0


if __name__ == "__main__":
	import sys
	status = main(sys.argv)
	sys.exit(status)

