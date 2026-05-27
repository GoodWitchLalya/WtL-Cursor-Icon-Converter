import os
import sys
import shutil
import tarfile
import json
from configparser import ConfigParser
import tkinter as tk
from tkinter import messagebox, simpledialog
import multiprocessing
from win2xcur.main.win2xcurtheme import main as win2xcurtheme_main
from win2xcur.main.win2xcur import main as win2xcur_main

# --- SET TRUE WORKING DIRECTORY ---
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
        "Please copy your cursor files (and the 'Install.inf' file if available) into the 'input' folder now, then click OK."
    )
    root.destroy()

def run_conversion(temp_dir):
    os.makedirs(os.path.join(temp_dir, "cursors"), exist_ok=True)

    input_dir = os.path.join(BASE_DIR, "input")
    input_inf_upper = os.path.join(input_dir, "Install.inf")
    input_inf_lower = os.path.join(input_dir, "install.inf")
    out_cursors_dir = os.path.abspath(os.path.join(temp_dir, "cursors"))

    # Case 1: A valid INF file exists
    inf_file = None
    if os.path.exists(input_inf_upper):
        inf_file = input_inf_upper
    elif os.path.exists(input_inf_lower):
        inf_file = input_inf_lower

    if inf_file:
        old_argv = sys.argv
        sys.argv = ["win2xcurtheme", inf_file, "-o", out_cursors_dir]
        try:
            win2xcurtheme_main()
            print(f"Theme conversion completed successfully using {inf_file}!")
            sys.argv = old_argv
            return True
        except Exception as e:
            print(f"Error occurred during win2xcurtheme execution: {e}")
            sys.argv = old_argv
            return False

    # Case 2: No INF file found, fallback to raw conversion of .cur/.ani files
    cursor_files = []
    for file in os.listdir(input_dir):
        if file.lower().endswith(('.cur', '.ani')):
            cursor_files.append(os.path.join(input_dir, file))
    
    if cursor_files:
        print("No INF file found. Proceeding with raw cursor files conversion...")
        old_argv = sys.argv
        sys.argv = ["win2xcur"] + cursor_files + ["-o", out_cursors_dir]
        try:
            win2xcur_main()
            print("Raw conversion completed successfully!")
            sys.argv = old_argv
            
            # --- AUTOMATIC TRANSLATION MAPPING VIA 'dict.json' ---
            # 1. Cerca un file esterno (per eventuali personalizzazioni utente)
            external_dict = os.path.join(BASE_DIR, "dict.json")
            
            # 2. Cerca il file inglobato da PyInstaller (il fallback invisibile)
            if getattr(sys, 'frozen', False):
                internal_dict = os.path.join(sys._MEIPASS, "dict.json")
            else:
                internal_dict = external_dict
                
            dict_path = None
            if os.path.exists(external_dict):
                dict_path = external_dict
                print("Using external dict.json...")
            elif os.path.exists(internal_dict):
                dict_path = internal_dict
                print("Using internal bundled dict.json...")

            if dict_path:
                try:
                    with open(dict_path, "r", encoding="utf-8") as dict_file:
                        raw_dict = json.load(dict_file)
                    
                    normalized_dict = {
                        k.lower().replace("_", "").replace(" ", ""): v 
                        for k, v in raw_dict.items()
                    }
                    
                    generated_files = os.listdir(out_cursors_dir)
                    for filename in generated_files:
                        file_path = os.path.join(out_cursors_dir, filename)
                        if os.path.isfile(file_path):
                            lookup_key = filename.lower().replace("_", "").replace(" ", "")
                            
                            if lookup_key in normalized_dict:
                                linux_names = normalized_dict[lookup_key]
                                if isinstance(linux_names, str):
                                    linux_names = [linux_names]
                                
                                for linux_name in linux_names:
                                    dest_path = os.path.join(out_cursors_dir, linux_name)
                                    shutil.copy2(file_path, dest_path)
                                
                                os.remove(file_path)
                    print("Dictionary translation mapping applied successfully!")
                except Exception as dict_err:
                    print(f"Warning: Failed to apply dictionary mapping: {dict_err}")
            else:
                print("Warning: No dict.json found. Keeping original Windows file names.")
                
            return True
        except Exception as e:
            print(f"Error occurred during win2xcur execution: {e}")
            sys.argv = old_argv
            return False

    # Case 3: Nothing useful found in input directory
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror("Error", "No valid INF file or cursor files (.cur/.ani) found in the input/ folder.")
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
    
    theme_data = {
        "Name": theme_name,
        "Inherits": "core"
    }
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