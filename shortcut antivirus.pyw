# By Smoodie (3.0)
# TODO: Multi Threading, MacOS better compatibility

import os
import subprocess
import logging
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox
import platform
import re


def get_drives():
    """
    Get the list of available drives
    """
    try:
        system = platform.system()
        if system == 'Windows':
            # Use 'wmic' command to get drive information on Windows
            output = subprocess.check_output(['wmic', 'logicaldisk', 'get', 'caption'])
            output = output.decode('utf-8').split('\r\r\n')[1:-1]
            return [drive.strip() for drive in output]
        elif system == 'Linux':
            # Use 'lsblk' command to get drive information on Linux
            output = subprocess.check_output(['lsblk', '-no', 'name'])
            output = output.decode('utf-8').split('\n')[:-1]
            return [drive.strip() for drive in output]
        elif system == 'Darwin':
            # Use 'diskutil' command to get drive information on macOS
            output = subprocess.check_output(['diskutil', 'list', '-plist'])
            output = output.decode('utf-8')
            drives = re.findall(r'/dev/(disk\d+)', output)
            return [drive.strip() for drive in drives]
        else:
            # For unsupported systems, log a warning and return an empty list
            logging.warning("Unsupported operating system.")
            return []
    except Exception as e:
        logging.error(f"Error in get_drives(): {str(e)}")
        return []


def is_removable(drive):
    """
    Check if the drive is removable
    """
    try:
        system = platform.system()
        if system == 'Windows':
            # Use 'wmic' command to check drive type on Windows
            drive_type = subprocess.check_output(['wmic', 'logicaldisk', 'where', f"name='{drive}'", 'get', 'drivetype']).decode('utf-8').split()[1]
            return drive_type == '2'
        elif system == 'Linux':
            # Check if the drive is removable based on the 'removable' file in sysfs
            sys_path = os.path.join('/sys/block', os.path.basename(drive))
            removable = os.path.exists(os.path.join(sys_path, 'removable')) and int(open(os.path.join(sys_path, 'removable')).read())
            return removable
        elif system == 'Darwin':
            # Check if the drive is removable on macOS
            output = subprocess.check_output(['diskutil', 'info', '-plist', drive])
            output = output.decode('utf-8')
            removable = re.search(r'<key>Removable Media</key>\s+<[^>]+>(\w+)', output)
            return removable and removable.group(1) == 'Yes'
        else:
            # For unsupported systems, assume the drive is not removable
            return False
    except Exception as e:
        logging.error(f"Error in is_removable(): {str(e)}")
        return False


def remove_shortcut_virus(drive):
    """
    Remove the shortcut virus from the given drive
    """
    try:
        infected = False
        for entry in os.scandir(drive):
            if entry.is_file() and entry.name.lower().endswith('.lnk'):
                logging.info(f"{drive} is infected. Attempting to clean...")
                infected = True
                os.system(f'attrib -h -r -s /s /d "{entry.path}"')  # Remove hidden attribute
                
                try:
                    os.remove(os.path.join(drive, "autorun.inf"))
                except Exception as e:
                    logging.warning("Error while removing 'autorun.inf'.")
                
                system = platform.system()
                if system == 'Windows':
                    # Run chkdsk on Windows
                    subprocess.call(['chkdsk', drive, '/f'])
                elif system == 'Linux':
                    # Run fsck on Linux
                    subprocess.call(['fsck', '-y', drive])
                elif system == 'Darwin':
                    # Run diskutil repairVolume on macOS
                    subprocess.call(['diskutil', 'repairVolume', drive])

                # Delete all .lnk files
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
        
        return infected

    except Exception as e:
        logging.error(f"Error in remove_shortcut_virus(): {str(e)}")
        return False


def main():
    # Configure logging
    logging.basicConfig(filename='antivirus.log', level=logging.INFO)

    # GUI
    root = tk.Tk()
    root.geometry("300x150")
    root.title("Shortcut Antivirus")

    def on_fix_drive():
        selected_drive = drive_var.get()
        if selected_drive:
            if is_removable(selected_drive):
                if remove_shortcut_virus(selected_drive):
                    messagebox.showinfo("Information", "The infected peripheral has been repaired successfully.")
                else:
                    messagebox.showinfo("Information", "The peripheral isn't infected.")
            else:
                messagebox.showinfo("Error", f"{selected_drive} isn't a removable drive!")
        else:
            messagebox.showinfo("Error", "No drive selected!")

    drives = get_drives()
    drive_var = tk.StringVar()
    if drives:
        drive_var.set(drives[0])
    else:
        messagebox.showinfo("Error", "No drives detected!")
    drive_select = tk.OptionMenu(root, drive_var, *drives)
    drive_select.pack(pady=16)

    fix_button = tk.Button(root, text="Fix drive", width=15, command=on_fix_drive)
    fix_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
