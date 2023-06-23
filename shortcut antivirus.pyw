# BY Smoodie (2.0)

import os
import subprocess
import logging
import tkinter as tk
from tkinter import filedialog, simpledialog, messagebox


def get_drives():
    """
    Get the list of available drives
    """
    try:
        output = subprocess.check_output(['wmic', 'logicaldisk', 'get', 'caption'])
        output = output.decode('utf-8').split('\r\r\n')[1:-1]
        return [drive.strip() for drive in output]
    except Exception as e:
        logging.error(f"Error in get_drives(): {str(e)}")
        return []


def is_removable(drive):
    """
    Check if the drive is removable
    """
    try:
        drive_type = subprocess.check_output(['wmic', 'logicaldisk', 'where', f"name='{drive}'", 'get', 'drivetype']).decode('utf-8').split()[1]
        return drive_type == '2'
    except Exception as e:
        logging.error(f"Error in is_removable(): {str(e)}")
        return False


def remove_shortcut_virus(drive):
    """
    Remove the shortcut virus from the given drive
    """
    try:
        for entry in os.scandir(drive):
            if entry.is_file() and entry.name.lower().endswith('.lnk'):
                logging.info(f"{drive} is infected. Attempting to clean...")
                os.system(f'attrib -h -r -s /s /d "{entry.path}"')  # Remove hidden attribute
                
                try:
                    os.remove(os.path.join(drive, "autorun.inf"))
                except Exception as e:
                    logging.warning("Error while removing 'autorun.inf'.")
                
                # Run chkdsk
                subprocess.call(['chkdsk', drive, '/f'])

                # Delete .lnk files
                for file in os.listdir(drive):
                    if file.endswith(".lnk"):
                        os.remove(os.path.join(drive, file))
                    if file.lower() == 'system volume information':
                        folder_path = os.path.join(drive, file)
                        subprocess.call(['attrib', '+h', folder_path])
                return True
        logging.info("The peripheral isn't infected.")
        return False
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
        if is_removable(selected_drive):
            if remove_shortcut_virus(selected_drive):
                messagebox.showinfo("Information", "The infected peripheral has been repaired successfully.")
            else:
                messagebox.showinfo("Information", "The peripheral isn't infected.")
        else:
            messagebox.showinfo("Error", f"{selected_drive} isn't a removable drive!")

    drives = get_drives()
    drive_var = tk.StringVar(value=drives[0])
    drive_select = tk.OptionMenu(root, drive_var, *drives)
    drive_select.pack(pady=16)

    fix_button = tk.Button(root, text="Fix drive", width=15, command=on_fix_drive)
    fix_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    main()
