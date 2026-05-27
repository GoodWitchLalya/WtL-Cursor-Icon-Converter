# WtL Cursor Icon Converter

A simple program to convert windows cursor icon packs into linux icon packs.

The program is rudimentary now, but it does its job.

##### This program uses win2xcur.

---

A lightweight and smart graphical tool to automatically convert Windows cursor packs (`.cur`, `.ani`) into native Linux themes (X11/Wayland), ready to be installed.

Developed to simplify the conversion as much as possible: forget long terminal commands, missing symlinks, or themes showing the wrong arrow on Linux.

## ✨ Main Features

* **Integrated Graphical Interface:** No terminal required for the end user. The program uses convenient popups to guide you through the process.
* **Full `.inf` Files Support:** If the Windows pack includes an `Install.inf` file, the program reads it to map the cursors accurately (using `win2xcurtheme`).
* **Automatic Translation (Raw Fallback):** Added support for cursor icon packs without an `Install.inf` file. The program analyzes the `.cur` and `.ani` files and automatically translates standard Windows names (e.g., `Normal_select`) into those required by Linux (e.g., `left_ptr`) thanks to a smart integrated dictionary.
* **Integrated Fail-safe:** Automatically generates the `index.theme` file including the `Inherits="core"` directive. If a specific cursor is missing from the theme, Linux will use the default one without visually "crashing" the entire pack.
* **Ready-to-Use Package:** At the end of the process, you will receive a clean, compressed `.tar.gz` archive, ready to be applied from your desktop environment settings (KDE, GNOME, etc.).
* **Single Executable:** No dependencies to install, everything you need is packed into a single file.

---

## 🚀 How to use it

1. **Launch the program** by double-clicking on the executable.
2. A warning will appear: the program has just created a folder named `input` next to the executable.
3. **Move your Windows cursors** (`.cur`, `.ani` and the optional `Install.inf` file) inside the `input` folder.
4. Go back to the program and **press OK**.
5. Enter the **name** you want to give to your new theme and (optionally) a short description.
6. Done! The `input` folder will be emptied to clean up, and you will find a `YourThemeName.tar.gz` file ready to be installed on Linux.

---

## ⚙️ Advanced Operation: The `dict.json` file

On Linux, a single cursor often needs to respond to different names (e.g., the base arrow must be named `left_ptr`, but also `default` and `arrow`). When a Windows theme lacks an `.inf` file, the program must manually rename and duplicate the files.

To do this, the executable has a **JSON translation dictionary bundled** inside it.

### 🛠️ How to add custom translations
If you notice that a specific theme uses weird names (e.g., `main_arrow.cur`) and isn't converted properly, **you don't need to recompile the program**. 

Just create a text file named `dict.json` and place it exactly **next to the executable**. The program will prioritize your external file over the internal one.

**Structure of the `dict.json` file:**
```json
{
    "normal_select": ["left_ptr", "default", "arrow"],
    "busy": ["watch", "wait"],
    "weird_windows_name": ["linux_name_1", "linux_name_2"]
}
```
*(Note: the program automatically ignores uppercase letters, spaces, and underscores to always guarantee proper recognition!)*

---

## 💻 Compiling from source code

If you wish to modify the code (`Convert.py`) and recompile the executable from scratch, make sure you have Python installed and proceed as follows:

1. Clone the repository or download the source files.
2. Create a virtual environment (recommended): `python -m venv venv` and activate it.
3. Install the dependencies:
   ```bash
   pip install win2xcur pyinstaller
   ```
4. Compile the file bundling the internal dictionary:
   ```bash
   pyinstaller --onefile --noconsole --add-data "dict.json:." Convert.py
   ```
5. You will find your new executable ready in the `dist/` folder.

*(Arch/Manjaro/CachyOS users: if PyInstaller struggles to find the Tkinter interface, it might be necessary to pass the `tcl` and `tk` library paths via environment variables during compilation, e.g., `env TCL_LIBRARY=/usr/lib/tcl8.6 TK_LIBRARY=/usr/lib/tk8.6 ...`).*
