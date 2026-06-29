"""
A program that updates sections of a plex library.

It works by opening a URL. 
In config file there will be the following items:
Plex IP adress
Plex token

If no config file exist, prompt for these values, and add them to a config file.

GUI:
Button for get library keys:
http://[IP-Adress]:32400/library/sections?X-Plex-Token=[Plex Token]
This will give an xml file similar to this:
            [xml]
            <MediaContainer size="27" allowSync="0" title1="Plex Library">
            <Directory allowSync="1" filters="1" refreshing="0" key="10" type="movie" title="3D Movies" agent="tv.plex.agents.movie" scanner="Plex Movie" language="en-US" uuid="5188266e-86e8-4149-af16-b7b7fc5047e9" updatedAt="1753660920" createdAt="1393891775" scannedAt="1753660865" content="1" directory="1" contentChangedAt="137711405" hidden="1">
            <Location id="145" path="//mediajob5/media/Movies II/3D Movies"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="24" type="movie" title="Cartoons" agent="tv.plex.agents.movie" scanner="Plex Movie" language="en-US" uuid="6c08a633-9e94-444c-95a5-6e705772f586" updatedAt="1753661066" createdAt="1420711726" scannedAt="1753661011" content="1" directory="1" contentChangedAt="152084769" hidden="1">
            <Location id="208" path="\\mediajob5\media\Diverse Kids"/>
            <Location id="183" path="\\mediajob\media\Diverse Kids"/>
            <Location id="161" path="\\mediajob2\media\Diverse Kids"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="50" type="movie" title="Dolby Vision" agent="tv.plex.agents.movie" scanner="Plex Movie" language="nb-NO" uuid="c8f0f627-72b1-4308-bcf6-102e550ca62a" updatedAt="1706403768" createdAt="1702818423" scannedAt="1753661022" content="1" directory="1" contentChangedAt="151556711" hidden="0">
            <Location id="205" path="//mediajob5/media/dovi"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="44" type="movie" title="Erotikk" agent="tv.plex.agents.movie" scanner="Plex Movie" language="en-US" uuid="9f918b3b-ee27-4e95-9763-0a7df7e465a2" updatedAt="1753661077" createdAt="1590696262" scannedAt="1753661030" content="1" directory="1" contentChangedAt="162239185" hidden="1">
            <Location id="202" path="\\mediajob5\media\movies II\erotikk"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="49" type="movie" title="Foreign Movies" agent="tv.plex.agents.movie" scanner="Plex Movie" language="en-US" uuid="a8ef50af-532e-4369-89a3-689ff1569a1d" updatedAt="1753661123" createdAt="1676634874" scannedAt="1753661068" content="1" directory="1" contentChangedAt="161441065" hidden="0">
            <Location id="195" path="\\mediajob5\media\movies II\foreign movies"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="37" type="movie" title="Moon Movies" agent="tv.plex.agents.movie" scanner="Plex Movie" language="en-US" uuid="b7b5e311-decd-4423-bdb2-7a24b3700e4f" updatedAt="1753661123" createdAt="1544773088" scannedAt="1753661070" content="1" directory="1" contentChangedAt="161004176" hidden="1">
            <Location id="126" path="\\mediajob5\media\movies\Moon Movies"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="26" type="movie" title="Movies" agent="tv.plex.agents.movie" scanner="Plex Movie" language="en-US" uuid="6c1702ba-ec7a-4a34-b116-0691b1987157" updatedAt="1753662222" createdAt="1455960415" scannedAt="1753662167" content="1" directory="1" contentChangedAt="162415883" hidden="0">
            <Location id="228" path="\\mediajob5\media\movies II\foreign movies"/>
            <Location id="227" path="\\mediajob5\media\movies II\Norske Filmer"/>
            <Location id="220" path="\\mediajob5\media\movies II\movies klassisk"/>
            <Location id="137" path="//mediajob5/media/movies"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="53" type="movie" title="Movies II" agent="tv.plex.agents.movie" scanner="Plex Movie" language="en-US" uuid="d2493212-0977-4dcb-95a3-e4ce65dd1b67" updatedAt="1753663522" createdAt="1734776460" scannedAt="1753663467" content="1" directory="1" contentChangedAt="162241020" hidden="2">
            <Location id="234" path="\\mediajob5\media\movies III"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="46" type="movie" title="Movies Klassisk" agent="tv.plex.agents.movie" scanner="Plex Movie" language="en-US" uuid="4c891901-cf5c-48f6-a131-a9e1959453ef" updatedAt="1753663741" createdAt="1619336680" scannedAt="1753663686" content="1" directory="1" contentChangedAt="162241054" hidden="0">
            <Location id="201" path="\\mediajob5\media\movies II\movies klassisk"/>
            <Location id="191" path="\\mediajob5\media\movies klassisk"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="21" type="movie" title="Nordiske Filmer" agent="tv.plex.agents.movie" scanner="Plex Movie" language="nb-NO" uuid="a093e9ae-3aee-4544-8c85-5e63b8df1bc0" updatedAt="1753663817" createdAt="1415451904" scannedAt="1753663762" content="1" directory="1" contentChangedAt="161702162" hidden="0">
            <Location id="200" path="//mediajob5/media/Movies II/Norske Filmer"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="34" type="movie" title="Russiske Filmer" agent="tv.plex.agents.movie" scanner="Plex Movie" language="ru-RU" uuid="32e2a2ee-e341-4156-b483-90ac560ba593" updatedAt="1753663968" createdAt="1521716764" scannedAt="1753663913" content="1" directory="1" contentChangedAt="161004474" hidden="1">
            <Location id="222" path="\\mediajob5\media\Movies\Russian Movies"/>
            <Location id="196" path="\\mediajob5\media\movies II\russian movies"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="40" type="movie" title="Xmas Movies" agent="tv.plex.agents.movie" scanner="Plex Movie" language="en-US" uuid="dbddc4fc-4f4b-4b6b-b824-97114b7fde29" updatedAt="1753665890" createdAt="1545579206" scannedAt="1753665835" content="1" directory="1" contentChangedAt="161441455" hidden="1">
            <Location id="199" path="//mediajob5/media/movies II/Xmas Movies"/>
            <Location id="156" path="//mediajob5/media/movies/Xmas Movies"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="42" type="show" title="Anime" agent="tv.plex.agents.series" scanner="Plex TV Series" language="en-US" uuid="79f05540-612e-4055-9c67-ca0e2103057f" updatedAt="1753660977" createdAt="1577294749" scannedAt="1753660920" content="1" directory="1" contentChangedAt="162414752" hidden="0">
            <Location id="218" path="\\mediajob2\media\Serier Anime"/>
            <Location id="209" path="\\mediajob5\media\Serier Anime"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="57" type="show" title="Car Shows" agent="tv.plex.agents.series" scanner="Plex TV Series" language="nb-NO" uuid="bab364b1-72df-451b-9bd0-e2194ef9d2a3" updatedAt="1753661049" createdAt="1748793694" scannedAt="1753660993" content="1" directory="1" contentChangedAt="161392202" hidden="0">
            <Location id="233" path="\\mediajob2\media\Car Shows"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="48" type="show" title="Cooking Shows" agent="tv.plex.agents.series" scanner="Plex TV Series" language="en-US" uuid="60c9b645-0d5c-4462-833b-abc91fad48bc" updatedAt="1753661077" createdAt="1662417780" scannedAt="1753661021" content="1" directory="1" contentChangedAt="162155250" hidden="0">
            <Location id="219" path="\\mediajob2\media\cooking"/>
            <Location id="211" path="\\mediajob5\media\cooking"/>
            <Location id="235" path="\\mediajob\media\cooking"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="47" type="show" title="Nordiske Serier" agent="tv.plex.agents.series" scanner="Plex TV Series" language="nb-NO" uuid="6ab55ffc-ae44-41a5-aaf1-92e63f460da1" updatedAt="1753663881" createdAt="1631744566" scannedAt="1753663824" content="1" directory="1" contentChangedAt="162241181" hidden="0">
            <Location id="221" path="\\mediajob2\media\Norske Serier"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="55" type="show" title="Reality Shows" agent="tv.plex.agents.series" scanner="Plex TV Series" language="en-US" uuid="7b9974e7-5999-46ae-920d-325d35dca08b" updatedAt="1753663956" createdAt="1746791529" scannedAt="1753663900" content="1" directory="1" contentChangedAt="162175322" hidden="0">
            <Location id="230" path="\\mediajob\media\Reality Shows"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="35" type="show" title="Russiske Show" agent="tv.plex.agents.series" scanner="Plex TV Series" language="ru-RU" uuid="4f84205c-30e1-456f-8f0c-b404c9060c6f" updatedAt="1753663969" createdAt="1521718380" scannedAt="1753663916" content="1" directory="1" contentChangedAt="0" hidden="1">
            <Location id="215" path="//mediajob5/media/Russiske Serier"/>
            <Location id="184" path="//mediajob/media/Russiske Serier"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="56" type="show" title="Talk Shows" agent="tv.plex.agents.series" scanner="Plex TV Series" language="nb-NO" uuid="5059beff-63ed-404b-9235-43da86524d4d" updatedAt="1753664072" createdAt="1748792489" scannedAt="1753664016" content="1" directory="1" contentChangedAt="162228414" hidden="0">
            <Location id="231" path="\\mediajob\media\Talk Shows"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="6" type="show" title="TV Shows" agent="tv.plex.agents.series" scanner="Plex TV Series" language="en-US" uuid="4f9a36ce-0492-4458-ad29-3c89a1a91a52" updatedAt="1753665885" createdAt="1393087162" scannedAt="1753665810" content="1" directory="1" contentChangedAt="162417456" hidden="0">
            <Location id="226" path="\\mediajob2\media\Kids Serier"/>
            <Location id="179" path="//mediajob/media/Serier"/>
            <Location id="138" path="//mediajob2/media/Serier"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="45" type="movie" title="Demo" agent="com.plexapp.agents.none" scanner="Plex Video Files Scanner" language="xn" uuid="f5d01b8d-e1e0-45c9-9c46-156331313a04" updatedAt="1753661077" createdAt="1609757424" scannedAt="1753661022" content="1" directory="1" contentChangedAt="124095195" hidden="2">
            <Location id="190" path="\\mediajob2\media\Demo"/>
            <Location id="189" path="\\mediajob5\media\Demo"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="41" type="movie" title="Karaoke" agent="com.plexapp.agents.none" scanner="Plex Video Files Scanner" language="xn" uuid="e3c5ebba-c429-4a8a-9ab4-c646082f5df8" updatedAt="1753661123" createdAt="1572466498" scannedAt="1753661069" content="1" directory="1" contentChangedAt="106380255" hidden="1">
            <Location id="180" path="\\mediajob\media\karaoke"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="52" type="movie" title="Plex is no more, too expensive" agent="com.plexapp.agents.none" scanner="Plex Video Files Scanner" language="xn" uuid="4bff30e7-ce0b-446e-b51a-66865794aae4" updatedAt="1723752924" createdAt="1718172873" scannedAt="1753663825" content="1" directory="1" contentChangedAt="0" hidden="0">
            <Location id="214" path="C:\tom"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="51" type="movie" title="Prøveperiode utløpt." agent="com.plexapp.agents.none" scanner="Plex Video Files Scanner" language="xn" uuid="fdca35e4-5fd2-40f7-8214-45b7d877dfff" updatedAt="1708976452" createdAt="1708976452" scannedAt="1753663825" content="1" directory="1" contentChangedAt="15" hidden="0">
            <Location id="207" path="/media/unraid2/NRK/Dizzie"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="13" type="movie" title="Racing" agent="com.plexapp.agents.none" scanner="Plex Video Files Scanner" language="xn" uuid="4d7d1e27-0440-4433-919f-7fb9acb82b08" updatedAt="1753663881" createdAt="1394737247" scannedAt="1753663825" content="1" directory="1" contentChangedAt="129048726" hidden="1">
            <Location id="115" path="/media/unraid5/Movies II/Racing"/>
            <Location id="88" path="/media/unraid2/Racing"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="28" type="movie" title="Vipps 200 pr. mnd. 92411800 m.br.navn for tilgang." agent="com.plexapp.agents.none" scanner="Plex Video Files Scanner" language="xn" uuid="4eb48e41-06ac-4986-a8e6-88dfce006549" updatedAt="1753665885" createdAt="1483183783" scannedAt="1753665813" content="1" directory="1" contentChangedAt="0" hidden="1">
            <Location id="75" path="/media/unraid2/NRK/Dizzie"/>
            </Directory>
            <Directory allowSync="1" filters="1" refreshing="0" key="54" type="movie" title="XXX" agent="tv.plex.agents.none" scanner="Plex Video Files" language="en-US" uuid="19320288-ea55-4bbb-bf07-d43519beaffa" updatedAt="1753665961" createdAt="1735510667" scannedAt="1753665906" content="1" directory="1" contentChangedAt="161266438" hidden="2">
            <Location id="225" path="\\mediajob5\media\Kremt\Nytt"/>
            </Directory>
            </MediaContainer>
            [/xml]

Parse this xml and show the keys in a listbox.
When a key is selected, show the path[s] in a dropdown.
When A path i selected, Show the path in a textbox, and give the user the option to add a sub path to the path.
Add a button for scan selected key and path.
Make sure that you “URL Encode” the path. If you’re using this in a browser address bar, then the browser will automatically do so for you.
"""

import os
import configparser
import tkinter as tk
from tkinter import messagebox, simpledialog, Listbox, END, Scrollbar, Text, StringVar, OptionMenu, Entry
import requests
import xml.etree.ElementTree as ET
import urllib.parse

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
    textbox.config(state='normal')
    textbox.delete(1.0, END)
    textbox.config(state='disabled')
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
    path_var.set('')
    path_dropdown['menu'].delete(0, 'end')
    for p in paths:
        path_dropdown['menu'].add_command(label=p, command=tk._setit(path_var, p))
    # Clear textbox and subpath entry
    textbox.config(state='normal')
    textbox.delete(1.0, END)
    textbox.config(state='disabled')
    entry_subpath.delete(0, END)

def on_path_select(*args):
    selected_path = path_var.get()
    textbox.config(state='normal')
    textbox.delete(1.0, END)
    textbox.insert(END, selected_path)
    textbox.config(state='disabled')
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
    # Show the result (simulate scan)
    messagebox.showinfo("Scan", f"Key: {key}\nPath: {full_path}\nURL Encoded Path: {encoded_path}")
    # Here you could add code to perform the scan using the encoded path and key

root = tk.Tk()
root.title("Plex Library Sections")

get_keys_btn = tk.Button(root, text="Get Library Keys", command=on_get_keys)
get_keys_btn.pack(pady=5)

frame = tk.Frame(root)
frame.pack(fill='both', expand=True)

listbox = Listbox(frame, width=40)
listbox.pack(side='left', fill='y')
listbox.bind('<<ListboxSelect>>', on_select)

scrollbar = Scrollbar(frame, orient='vertical', command=listbox.yview)
scrollbar.pack(side='left', fill='y')
listbox.config(yscrollcommand=scrollbar.set)

# Path dropdown
path_var = StringVar()
path_dropdown = OptionMenu(root, path_var, '')
path_dropdown.config(width=60)
path_dropdown.pack(pady=5)
path_var.trace('w', on_path_select)

# Textbox for showing path
textbox = Text(root, height=2, width=60, state='disabled')
textbox.pack(pady=5)

# Entry for subpath
entry_subpath = Entry(root, width=60)
entry_subpath.pack(pady=5)
entry_subpath.insert(0, "")  # Placeholder

# Button to scan
scan_btn = tk.Button(root, text="Scan Selected Key and Path", command=on_scan)
scan_btn.pack(pady=5)

root.mainloop()