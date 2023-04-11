# BY Smoodie (1.0)

import subprocess
import os

from tkinter import *
from tkinter import filedialog, simpledialog
import tkinter.messagebox as mbox

root = Tk()

def select_drive():
    drives = []
    output = subprocess.check_output(['wmic', 'logicaldisk', 'get', 'caption'])
    output = output.decode('utf-8').split('\r\r\n')[1:-1]
    for drive in output:
        drives.append(drive.strip())
    drive = simpledialog.askstring("Select Drive", "Select the drive to fix", parent=root, 
                                   initialvalue=drives[0], 
                                   selectbackground='lightblue', selectforeground='black', 
                                   show='*')
    if drive:
        fix_drive(drive)

def fix_drive(drive):
    infected_drives = []
    drive_type = subprocess.check_output(['wmic', 'logicaldisk', 'where', f"name='{drive}'", 'get', 'drivetype']).decode('utf-8').split()[1]
    if drive_type == '2': # Verify if is an USB
        for entry in os.scandir(drive):
            if entry.is_file() and entry.name.lower().endswith('.lnk'):
                mbox.showinfo("Information", f"{drive} is infected. The program will try to clean it.")
                os.system(f'attrib -h -r -s /s /d "{entry.path}"') # Del hidden attribut
                try:
                    os.remove(os.path.join(drive, "autorun.inf"))
                except Exception:
                    print("Error while removing 'autorun.inf'.")
                subprocess.call(['chkdsk', drive, '/f']) # Use chdsk
                # Del .lnk files
                for file in os.listdir(drive):
                    if file.endswith(".lnk"):
                        os.remove(os.path.join(drive, file))
                    if file.lower() == 'system volume information':
                        folder_path = os.path.join(drive, file)
                        subprocess.call(['attrib', '+h', folder_path])
                    
                
        else: # Not infected
            mbox.showinfo("Information", "The peripheral isn't infected.")
            return
    else:
        mbox.showinfo("Error", f"{drive} isn't a removable drive!")
        return
        
    mbox.showinfo("Information", "The infected peripheral has been repaired succesfully.")


root.geometry("300x150")
root.title("Shortcut Antivirus")

drives = []
output = subprocess.check_output(['wmic', 'logicaldisk', 'get', 'caption'])
output = output.decode('utf-8').split('\r\r\n')[1:-1]
for drive in output:
    drives.append(drive.strip())

drive_var = StringVar(value=drives[0])
drive_select = OptionMenu(root, drive_var, *drives)
drive_select.pack(pady=16)

fix_button = Button(root, text="Fix drive", width=15, command=lambda: fix_drive(drive_var.get()))
fix_button.pack(pady=10)

root.mainloop()
