import os
import configparser
import tkinter as tk
from tkinter import messagebox, simpledialog, Listbox, END, Scrollbar, StringVar, OptionMenu, Entry
import requests
import xml.etree.ElementTree as ET
import urllib.parse
import webbrowser

try:
    import pyperclip  # type: ignore
except ImportError:
    pyperclip = None

CONFIG_FILE = "plex_config.ini"

def load_config():
    config = configparser.ConfigParser()
    if not os.path.exists(CONFIG_FILE):
        ip = simpledialog.askstring("Plex IP", "Enter Plex IP address:")
        token = simpledialog.askstring("Plex Token", "Enter Plex Token:")
        config['PLEX'] = {'ip': ip, 'token': token}
        with open(CONFIG_FILE, 'w') as configfile:
            config.write(configfile)
    else:
        config.read(CONFIG_FILE)
    return config['PLEX']['ip'], config['PLEX']['token']

def get_library_sections():
    ip, token = load_config()
    url = f"http://{ip}:32400/library/sections?X-Plex-Token={token}"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        messagebox.showerror("Error", f"Failed to get library sections:\n{e}")
        return None

def parse_sections(xml_data):
    keys_titles = []
    paths_by_key = {}
    root = ET.fromstring(xml_data)
    for directory in root.findall('Directory'):
        key = directory.attrib.get('key')
        title = directory.attrib.get('title')
        keys_titles.append((key, title))
        paths = []
        for loc in directory.findall('Location'):
            paths.append(loc.attrib.get('path'))
        paths_by_key[key] = paths
    return keys_titles, paths_by_key

def on_get_keys():
    xml_data = get_library_sections()
    if not xml_data:
        return
    keys_titles, paths_by_key = parse_sections(xml_data)
    listbox.delete(0, END)
    listbox.keys = []
    for key, title in keys_titles:
        listbox.insert(END, f"{title} (key={key})")
        listbox.keys.append(key)
    listbox.paths_by_key = paths_by_key
    # Clear path dropdown and textbox
    path_var.set('')
    path_dropdown['menu'].delete(0, 'end')
    entry_subpath.delete(0, END)

def on_select(event):
    if not hasattr(listbox, 'keys'):
        return
    selection = listbox.curselection()
    if not selection:
        return
    idx = selection[0]
    key = listbox.keys[idx]
    paths = listbox.paths_by_key.get(key, [])
    # Update path dropdown
    path_dropdown['menu'].delete(0, 'end')
    if paths:
        for p in paths:
            path_dropdown['menu'].add_command(label=p, command=tk._setit(path_var, p))
        path_var.set(paths[0])  # Set the first path as selected
    else:
        path_var.set('')
    # Clear subpath entry
    entry_subpath.delete(0, END)

def on_path_select(*args):
    selected_path = path_var.get()
    entry_subpath.delete(0, END)

def on_scan():
    # Get selected key
    if not hasattr(listbox, 'keys'):
        messagebox.showerror("Error", "No key selected.")
        return
    selection = listbox.curselection()
    if not selection:
        messagebox.showerror("Error", "No key selected.")
        return
    idx = selection[0]
    key = listbox.keys[idx]
    # Get selected path
    path = path_var.get()
    if not path:
        messagebox.showerror("Error", "No path selected.")
        return
    # Get subpath
    subpath = entry_subpath.get().strip()
    full_path = path
    if subpath:
        # Ensure proper joining
        if not full_path.endswith('/') and not subpath.startswith('/'):
            full_path += '/'
        full_path += subpath
    # URL encode the path
    encoded_path = urllib.parse.quote(full_path)
    ip, token = load_config()
    scan_url = f"http://{ip}:32400/library/sections/{key}/refresh?path={encoded_path}&X-Plex-Token={token}"
    # Copy only the scan_url to clipboard if possible
    clipboard_msg = ""
    if pyperclip:
        try:
            pyperclip.copy(scan_url)
            clipboard_msg = "\n\n(The scan URL has been copied to your clipboard.)"
        except Exception:
            clipboard_msg = "\n\n(Could not copy scan URL to clipboard.)"
    else:
        clipboard_msg = "\n\n(pyperclip not installed: scan URL not copied to clipboard.)"
    # Show the result (simulate scan) with Cancel/OK and show full path and scan URL
    confirm = tk.messagebox.askokcancel(
        "Scan",
        f"Key: {key}\nFull Path: {full_path}\nURL Encoded Path: {encoded_path}\n\nScan URL:\n{scan_url}{clipboard_msg}\n\nProceed with scan?"
    )
    if not confirm:
        return
    # Actually trigger the scan by opening the constructed URL in the default browser
    webbrowser.open(scan_url)

root = tk.Tk()
root.title("Plex Library Sections")
root.configure(bg="#222222")  # Set background to dark grey
root.geometry("500x800")      # Set window size to 500x800

get_keys_btn = tk.Button(root, text="Get Library Keys", command=on_get_keys)
get_keys_btn.pack(pady=5, fill='x')

frame = tk.Frame(root, bg="#222222")  # Match background
frame.pack(fill='both', expand=True)

listbox = Listbox(frame, width=0, bg="#333333", fg="#ffffff", highlightbackground="#222222", selectbackground="#444444")
listbox.pack(side='left', fill='both', expand=True)
listbox.bind('<<ListboxSelect>>', on_select)

scrollbar = Scrollbar(frame, orient='vertical', command=listbox.yview)
scrollbar.pack(side='left', fill='y')
listbox.config(yscrollcommand=scrollbar.set)

# Path dropdown label
label_path_dropdown = tk.Label(root, text="Select Path:", bg="#222222", fg="#ffffff")
label_path_dropdown.pack(pady=(10, 0))

# Path dropdown
path_var = StringVar()
path_dropdown = OptionMenu(root, path_var, '')
path_dropdown.config(width=60, bg="#333333", fg="#ffffff", highlightbackground="#222222")
path_dropdown.pack(pady=5)
path_var.trace('w', on_path_select)

# Entry for subpath label
label_subpath = tk.Label(root, text="Add Sub Path:", bg="#222222", fg="#ffffff")
label_subpath.pack(pady=(10, 0))

# Entry for subpath
entry_subpath = Entry(root, width=60, bg="#333333", fg="#ffffff", highlightbackground="#222222", insertbackground="#ffffff")
entry_subpath.pack(pady=5)
entry_subpath.insert(0, "")  # Placeholder

# Button to scan
scan_btn = tk.Button(root, text="Scan Selected Key and Path", command=on_scan)
scan_btn.pack(pady=5)

root.mainloop()