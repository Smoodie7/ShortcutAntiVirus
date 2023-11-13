# By Smoodie (0.5)

import os
import subprocess
import threading
import logging
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import platform
import re
import queue

class ShortcutVirusRemover:
    def __init__(self):
        self.root = tk.Tk()
        self.root.geometry("300x150")
        self.root.title("Shortcut Antivirus")

        self.setup_logging()

        self.drive_var = tk.StringVar()
        self.drives = self.get_drives()
        if self.drives:
            self.drive_var.set(self.drives[0])
        else:
            messagebox.showinfo("Error", "No drives detected!")
            return

        self.drive_select = tk.OptionMenu(self.root, self.drive_var, *self.drives)
        self.drive_select.pack(pady=16)

        self.fix_button = tk.Button(self.root, text="Fix drive", width=15, command=self.on_fix_drive)
        self.fix_button.pack(pady=10)

        self.progress_label = tk.Label(self.root, text="", anchor="w")
        self.progress_label.pack(fill=tk.X, pady=10)

        self.state_label = tk.Label(self.root, text="", anchor="w")
        self.state_label.pack(fill=tk.X, pady=5)

        self.progress_queue = queue.Queue()
        self.remove_shortcut_virus_thread = None  # Initialize as None initially

        self.root.after(100, self.update_progress)
        self.root.mainloop()

    def setup_logging(self):
        logging.basicConfig(filename='antivirus.log', level=logging.INFO)

    def get_drives(self):
        """
        Get the list of available drives
        """
        try:
            system = platform.system()
            if system == 'Windows':
                output = subprocess.check_output(['wmic', 'logicaldisk', 'get', 'caption'])
                output = output.decode('utf-8').split('\r\r\n')[1:-1]
                return [drive.strip() for drive in output]
            elif system == 'Linux':
                output = subprocess.check_output(['lsblk', '-no', 'name'])
                output = output.decode('utf-8').split('\n')[:-1]
                return [drive.strip() for drive in output]
            elif system == 'Darwin':
                output = subprocess.check_output(['diskutil', 'list', '-plist'])
                output = output.decode('utf-8')
                drives = re.findall(r'/dev/(disk\d+)', output)
                return [drive.strip() for drive in drives]
            else:
                logging.warning("Unsupported operating system.")
                return []
        except Exception as e:
            logging.error(f"Error in get_drives(): {str(e)}")
            return []

    def is_removable(self, drive):
        """
        Check if the drive is removable
        """
        try:
            system = platform.system()
            if system == 'Windows':
                drive_type = subprocess.check_output(['wmic', 'logicaldisk', 'where', f"name='{drive}'", 'get', 'drivetype']).decode('utf-8').split()[1]
                return drive_type == '2'
            elif system == 'Linux':
                sys_path = os.path.join('/sys/block', os.path.basename(drive))
                removable = os.path.exists(os.path.join(sys_path, 'removable')) and int(open(os.path.join(sys_path, 'removable')).read())
                return removable
            elif system == 'Darwin':
                output = subprocess.check_output(['diskutil', 'info', '-plist', drive])
                output = output.decode('utf-8')
                removable = re.search(r'<key>Removable Media</key>\s+<[^>]+>(\w+)', output)
                return removable and removable.group(1) == 'Yes'
            else:
                return False
        except Exception as e:
            logging.error(f"Error in is_removable(): {str(e)}")
            return False

    def remove_shortcut_virus(self, drive):
        """
        Remove the shortcut virus from the given drive
        """
        try:
            infected = False
            for entry in os.scandir(drive):
                if entry.is_file() and entry.name.lower().endswith('.lnk'):
                    logging.info(f"{drive} is infected. Attempting to clean...")
                    infected = True
                    os.system(f'attrib -h -r -s /s /d "{entry.path}"')

                    try:
                        os.remove(os.path.join(drive, "autorun.inf"))
                    except Exception as e:
                        logging.warning("Error while removing 'autorun.inf'.")

                    system = platform.system()
                    if system == 'Windows':
                        subprocess.call(['chkdsk', drive, '/f'])
                    elif system == 'Linux':
                        subprocess.call(['fsck', '-y', drive])
                    elif system == 'Darwin':
                        subprocess.call(['diskutil', 'repairVolume', drive])

                    for file in os.listdir(drive):
                        if file.endswith(".lnk"):
                            os.remove(os.path.join(drive, file))
                        if file.lower() == 'system volume information':
                            folder_path = os.path.join(drive, file)
                            subprocess.call(['attrib', '+h', folder_path])

            if infected:
                logging.info(f"The infected files have been removed from {drive}.")
            else:
                logging.info(f"The peripheral isn't infected.")

            self.progress_queue.put((drive, infected))

        except Exception as e:
            logging.error(f"Error in remove_shortcut_virus(): {str(e)}")
            self.progress_queue.put((drive, False))

    def on_fix_drive(self):
        selected_drive = self.drive_var.get()
        if selected_drive:
            if self.is_removable(selected_drive):
                if self.remove_shortcut_virus_thread and self.remove_shortcut_virus_thread.is_alive():
                    messagebox.showinfo("Information", "Virus cleaning process is already in progress.")
                else:
                    self.progress_label.config(text="Scanning and cleaning in progress...")
                    self.state_label.config(text="")
                    self.remove_shortcut_virus_thread = threading.Thread(target=self.remove_shortcut_virus, args=(selected_drive,))
                    self.remove_shortcut_virus_thread.start()
            else:
                messagebox.showinfo("Error", f"{selected_drive} isn't a removable drive!")
        else:
            messagebox.showinfo("Error", "No drive selected!")

    def update_progress(self):
        try:
            drive, infected = self.progress_queue.get(0)
            if infected:
                self.state_label.config(text=f"The infected peripheral {drive} has been repaired successfully.")
            else:
                self.state_label.config(text=f"The peripheral {drive} isn't infected.")
            self.progress_label.config(text="")
        except queue.Empty:
            self.root.after(100, self.update_progress)

if __name__ == "__main__":
    ShortcutVirusRemover()
