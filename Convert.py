import os
import sys
import shutil
import tarfile
from configparser import ConfigParser
import tkinter as tk
from tkinter import messagebox, simpledialog
import multiprocessing
from win2xcur.main.win2xcurtheme import main as win2xcurtheme_main

# --- FISSARE LA DIRECTORY DI LAVORO REALE ---
if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

os.chdir(BASE_DIR)

def setup_input_directory():
    input_dir = "input"
    os.makedirs(input_dir, exist_ok=True)
    
    root = tk.Tk()
    root.withdraw()
    
    messagebox.showinfo(
        "Theme Converter Setup",
        f"The '{input_dir}' directory has been checked/created.\n\n"
        "WARNING: All files inside the input directory will be DELETED once the conversion is complete.\n\n"
        "Please copy your cursor files and the 'Install.inf' file into the 'input' folder now, then click OK."
    )
    root.destroy()

def run_conversion(temp_dir):
    os.makedirs(os.path.join(temp_dir, "cursors"), exist_ok=True)

    input_inf_upper = os.path.join(BASE_DIR, "input", "Install.inf")
    input_inf_lower = os.path.join(BASE_DIR, "input", "install.inf")
    out_cursors_dir = os.path.abspath(os.path.join(temp_dir, "cursors"))

    attempts = [
        ["win2xcurtheme", input_inf_upper, "-o", out_cursors_dir],
        ["win2xcurtheme", input_inf_lower, "-o", out_cursors_dir]
    ]

    for args in attempts:
        if os.path.exists(args[1]):
            old_argv = sys.argv
            sys.argv = args
            try:
                win2xcurtheme_main()
                print(f"Conversion completed successfully using {args[1]}!")
                sys.argv = old_argv
                return True
            except Exception as e:
                print(f"Error occurred during win2xcur execution: {e}")
                sys.argv = old_argv
                return False
                
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", "No valid INF file found in input/ folder.\nMake sure 'Install.inf' is inside the 'input' directory.")
    root.destroy()
    return False

def create_index_and_rename(temp_dir):
    root = tk.Tk()
    root.withdraw()
    
    while True:
        theme_name = simpledialog.askstring("Theme Configuration", "Enter theme Name (Required):")
        if theme_name is not None:
            theme_name = theme_name.strip()
        if theme_name:
            break
        messagebox.showwarning("Warning", "Theme name cannot be empty. Please try again.")

    theme_comment = simpledialog.askstring("Theme Configuration", "Enter theme Comment (Optional):")
    if theme_comment is not None:
        theme_comment = theme_comment.strip()

    config = ConfigParser()
    config.optionxform = str
    
    theme_data = {"Name": theme_name}
    if theme_comment:
        theme_data["Comment"] = theme_comment
        
    config["Icon Theme"] = theme_data

    index_path = os.path.join(temp_dir, "index.theme")
    try:
        with open(index_path, "w", encoding="utf-8") as configfile:
            config.write(configfile, space_around_delimiters=True)
    except IOError as e:
        messagebox.showerror("Error", f"Error writing index.theme: {e}")
        root.destroy()
        return

    final_dir = os.path.join(BASE_DIR, theme_name)

    if os.path.exists(final_dir):
        shutil.rmtree(final_dir)

    try:
        shutil.move(temp_dir, final_dir)
    except Exception as e:
        messagebox.showerror("Error", f"Error renaming output directory: {e}")
        root.destroy()
        return

    archive_name = os.path.join(BASE_DIR, f"{theme_name}.tar.gz")
    archive_success = False
    try:
        with tarfile.open(archive_name, "w:gz") as tar:
            tar.add(final_dir, arcname=theme_name)
        archive_success = True
    except Exception as e:
        messagebox.showerror("Error", f"Error creating tar.gz archive: {e}")

    if archive_success:
        try:
            shutil.rmtree(final_dir)
            messagebox.showinfo("Success", f"Theme successfully generated!\nSaved as: {theme_name}.tar.gz")
        except Exception as e:
            print(f"Error cleaning up theme directory: {e}")
            
    root.destroy()

if __name__ == "__main__":
    # --- RIGA MAGICA PER RISOLVERE I LOOP DEI PROCESSI IN PYINSTALLER ---
    multiprocessing.freeze_support()
    
    target_temp_dir = os.path.join(BASE_DIR, "temp")
    input_dir = os.path.join(BASE_DIR, "input")
    
    if os.path.exists(target_temp_dir):
        shutil.rmtree(target_temp_dir)

    setup_input_directory()

    conversion_success = False
    try:
        if run_conversion(target_temp_dir):
            create_index_and_rename(target_temp_dir)
            conversion_success = True
        else:
            if os.path.exists(target_temp_dir):
                shutil.rmtree(target_temp_dir)
    finally:
        if conversion_success and os.path.exists(input_dir):
            try:
                shutil.rmtree(input_dir)
            except Exception as e:
                print(f"Error removing input directory: {e}")
