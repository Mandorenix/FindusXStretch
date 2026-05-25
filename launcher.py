import tkinter as tk
from tkinter import scrolledtext, messagebox, font
import subprocess
import threading
import sys
import os
import re
import datetime

class Launcher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("FINDUS>x<STRETCHING Developer Launcher")
        self.geometry("1100x800")
        self.configure(bg="#212224")
        
        self.python_cmd = sys.executable.replace("pythonw.exe", "python.exe")
        self.version = self.get_version()

        # Fonts
        self.title_font = font.Font(family="Segoe UI", size=14, weight="bold")
        self.header_font = font.Font(family="Segoe UI", size=11, weight="bold")
        self.normal_font = font.Font(family="Segoe UI", size=10)
        self.desc_font = font.Font(family="Segoe UI", size=10, slant="italic")
        
        self._build_ui()
        cat_logo = r"""
       /\_/\      F I N D U S  > x <  S T R E T C H I N G
      ( o.o )     Ambient Drone Workstation & Launcher
       > ^ <
"""
        self.log(cat_logo)
        self.log(f"Workspace: {os.getcwd()}")
        self.log(f"Python: {self.python_cmd}")
        self.log(f"Version: {self.version}\n")

    def _build_ui(self):
        # Top Header
        top_frame = tk.Frame(self, bg="#2b2d30", height=60)
        top_frame.pack(side=tk.TOP, fill=tk.X)
        top_frame.pack_propagate(False)
        
        title_lbl = tk.Label(top_frame, text="FINDUS>x<STRETCHING", font=self.title_font, bg="#2b2d30", fg="#5294e2")
        title_lbl.pack(side=tk.LEFT, padx=20, pady=15)
        
        ver_lbl = tk.Label(top_frame, text=f"Version: {self.version}", font=self.normal_font, bg="#2b2d30", fg="#a9b7c6")
        ver_lbl.pack(side=tk.RIGHT, padx=20, pady=15)

        # Main Body
        body_frame = tk.Frame(self, bg="#212224")
        body_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Left Column (Buttons)
        left_col = tk.Frame(body_frame, bg="#212224", width=350)
        left_col.pack(side=tk.LEFT, fill=tk.Y)
        left_col.pack_propagate(False)

        # Right Column (Description + Log)
        right_col = tk.Frame(body_frame, bg="#212224")
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(20, 0))

        # Description Box
        desc_frame = tk.Frame(right_col, bg="#2b2d30", bd=1, relief="flat", height=100)
        desc_frame.pack(fill=tk.X, pady=(0, 20))
        desc_frame.pack_propagate(False)
        
        self.desc_title = tk.Label(desc_frame, text="Info", font=self.header_font, bg="#2b2d30", fg="#a9b7c6", anchor="w")
        self.desc_title.pack(fill=tk.X, padx=10, pady=(10, 5))
        
        self.desc_label = tk.Label(desc_frame, text="Håll musen över en knapp för att se vad den gör.", font=self.normal_font, bg="#2b2d30", fg="#7a7e85", anchor="nw", justify="left", wraplength=600)
        self.desc_label.pack(fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        # Output Text
        log_frame = tk.Frame(right_col, bg="#1e1e1e", bd=1)
        log_frame.pack(fill=tk.BOTH, expand=True)
        self.log_area = scrolledtext.ScrolledText(log_frame, bg="#1e1e1e", fg="#cccccc", font=("Consolas", 10), bd=0, padx=10, pady=10)
        self.log_area.pack(fill=tk.BOTH, expand=True)

        # Create Buttons in Left Column
        categories = {
            "🚀 Start & Dev": [
                ("Start App", self.run_app, "Startar FINDUS>x<STRETCHING i bakgrunden utan en CMD-ruta."),
                ("Start PWA (Light)", self.start_pwa, "Startar en lokal webbserver för mobila PWA-versionen och öppnar i webbläsaren."),
                ("Deploy PWA (Upload)", self.deploy_pwa, "Laddar upp dina senaste ändringar till webben så de uppdateras på mobilen."),
                ("Quick Start", self.quick_start, "Installerar bas-tillägg, kör tester och startar sedan appen."),
                ("Python REPL", self.python_repl, "Öppnar en ren Python-tolk i ett nytt fönster för snabba tester."),
                ("Open README", lambda: os.startfile("README.md"), "Öppnar projektets README-fil i standardredigeraren."),
            ],
            "📦 Miljö & Tillägg": [
                ("Install Dependencies", self.install_deps, "Installerar de paket som krävs för att köra appen (från requirements.txt)."),
                ("Install Extras", self.install_extras, "Installerar rekommenderade tillägg, t.ex. pyqtgraph för snabbare vågform och sounddevice för bättre ljudstöd."),
                ("Create .venv", self.create_venv, "Skapar en virtuell Python-miljö (.venv) i projektmappen."),
                ("Show Pip List", self.pip_list, "Visar alla installerade Python-paket i logg-fönstret."),
            ],
            "🔨 Bygge & Releaser": [
                ("Run Tests", self.run_tests, "Kör igenom alla enhetstester via pytest för att verifiera koden."),
                ("Build Windows .exe", self.build_exe, "Kompilerar appen till en körbar fil (.exe) med PyInstaller i mappen dist/."),
                ("Build Setup.exe", self.build_installer, "Skapar en installationsfil med Inno Setup i mappen dist/installer/."),
                ("Minor Release", self.minor_release, "Höjer minor-versionen (t.ex. 0.1 -> 0.2), bygger appen, skapar zip och installer."),
                ("Full Release (Patch)", self.full_release, "Höjer patch-versionen (t.ex. 0.1.1 -> 0.1.2) och kör ett komplett byggflöde."),
            ],
            "🛠️ Diagnostik & Verktyg": [
                ("Skapa Felsökningsrapport", self.write_diagnostics, "Kör diagnostics.py för att spara information om ljudenheter och drivrutiner till diagnostics_report.txt."),
                ("Sync Help Tab med Changelog", self.sync_help_tab, "Läser CHANGELOG_RELEASES.md och bygger automatiskt in historiken i appens Help-flik (gui.py)."),
                ("Code Quality Check (Ruff)", self.run_ruff, "Kör Ruff linter för att hitta fel och stilmissar i koden."),
                ("Clean Build Artifacts", self.clean_artifacts, "Raderar build/ och dist/ mapparna för att kunna bygga från en helt ren miljö."),
                ("Hard Reset", self.hard_reset, "VARNING: Raderar .venv, __pycache__, build, och dist för en helt ren start."),
                ("Open Explorer", lambda: os.startfile("."), "Öppnar nuvarande projektmapp i Utforskaren."),
            ]
        }

        # Render Canvas for scrolling if buttons exceed window
        canvas = tk.Canvas(left_col, bg="#212224", highlightthickness=0)
        scrollbar = tk.Scrollbar(left_col, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#212224")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            
        left_col.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        left_col.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        for cat_name, btns in categories.items():
            cat_lbl = tk.Label(scrollable_frame, text=cat_name, font=self.header_font, bg="#212224", fg="#a9b7c6")
            cat_lbl.pack(anchor="w", pady=(15, 5))
            
            for text, cmd, desc in btns:
                btn = tk.Button(scrollable_frame, text=text, command=cmd, font=self.normal_font,
                                bg="#3c3f41", fg="#ffffff", activebackground="#4b4d4f", activeforeground="#ffffff", 
                                relief="flat", width=32, anchor="w", padx=15, pady=4, cursor="hand2")
                btn.pack(pady=2, padx=5)
                
                # Hover bindings
                btn.bind("<Enter>", lambda e, t=text, d=desc, b=btn: self._on_hover(t, d, b))
                btn.bind("<Leave>", lambda e, b=btn: self._on_leave(b))

    def _on_hover(self, title, desc, btn):
        btn.configure(bg="#5294e2") # Highlight color
        self.desc_title.config(text=title, fg="#5294e2")
        self.desc_label.config(text=desc, fg="#cccccc")

    def _on_leave(self, btn):
        btn.configure(bg="#3c3f41")
        self.desc_title.config(text="Info", fg="#a9b7c6")
        self.desc_label.config(text="Håll musen över en knapp för att se vad den gör.", fg="#7a7e85")

    def log(self, text):
        self.log_area.insert(tk.END, text + "\n")
        self.log_area.see(tk.END)

    def run_cmd(self, cmd, show_console=False):
        def task():
            self.log(f"> {cmd}")
            if show_console:
                os.system(f"start cmd /c \"{cmd} & pause\"")
                self.after(0, self.log, "[Started in new console window]\n")
            else:
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in process.stdout:
                    self.after(0, self.log, line.strip())
                process.wait()
                self.after(0, self.log, f"[Done with exit code {process.returncode}]\n")

        threading.Thread(target=task, daemon=True).start()

    def get_version(self):
        try:
            with open("assets/version_info.txt", "r", encoding="utf-8") as f:
                content = f.read()
                match = re.search(r'StringStruct\("ProductVersion", "(.*?)"\)', content)
                if match:
                    return match.group(1)
        except Exception as e:
            self.log(f"Could not read version: {e}")
        return "0.1.1"

    def bump_version(self, bump_type="patch"):
        version = self.get_version()
        parts = version.split(".")
        if len(parts) == 3:
            if bump_type == "minor":
                parts[1] = str(int(parts[1]) + 1)
                parts[2] = "0"
            else:
                parts[2] = str(int(parts[2]) + 1)
                
            new_version = ".".join(parts)
            self.log(f"Bumping {bump_type} version from {version} to {new_version}...")
            
            try:
                with open("assets/version_info.txt", "r", encoding="utf-8") as f:
                    content = f.read()

                quad = f"{parts[0]}, {parts[1]}, {parts[2]}, 0"
                content = re.sub(r'filevers=\(.*\)', f'filevers=({quad})', content)
                content = re.sub(r'prodvers=\(.*\)', f'prodvers=({quad})', content)
                content = re.sub(r'StringStruct\("FileVersion", ".*?"\)', f'StringStruct("FileVersion", "{new_version}")', content)
                content = re.sub(r'StringStruct\("ProductVersion", ".*?"\)', f'StringStruct("ProductVersion", "{new_version}")', content)

                with open("assets/version_info.txt", "w", encoding="utf-8") as f:
                    f.write(content)
                self.version = new_version
                return True
            except Exception as e:
                self.log(f"Error bumping version: {e}")
        return False

    def sync_help_tab(self):
        def task():
            self.log("> Reading CHANGELOG_RELEASES.md...")
            if not os.path.exists("CHANGELOG_RELEASES.md"):
                self.after(0, self.log, "[ERROR] CHANGELOG_RELEASES.md not found.")
                return

            with open("CHANGELOG_RELEASES.md", "r", encoding="utf-8") as f:
                md_text = f.read()

            self.log("> Converting to HTML...")
            html_lines = ["    <h3>Latest Release History (Auto-Synced)</h3>", "    <ul>"]
            in_list = False
            for line in md_text.splitlines():
                line = line.strip()
                if not line or line.startswith("# Release History"):
                    continue
                if line.startswith("## "):
                    if in_list:
                        html_lines.append("    </ul>")
                    html_lines.append(f"    <h4>{line[3:]}</h4>")
                    html_lines.append("    <ul>")
                    in_list = True
                elif line.startswith("- "):
                    html_lines.append(f"      <li>{line[2:]}</li>")
            
            if in_list:
                html_lines.append("    </ul>")

            html_snippet = "\n".join(html_lines)
            
            gui_path = os.path.join("paulstretch_light", "gui.py")
            self.log(f"> Injecting into {gui_path}...")
            
            if not os.path.exists(gui_path):
                self.after(0, self.log, f"[ERROR] {gui_path} not found.")
                return

            with open(gui_path, "r", encoding="utf-8") as f:
                gui_content = f.read()

            # Replace everything between <!-- CHANGELOG_START --> and <!-- CHANGELOG_END -->
            start_marker = "<!-- CHANGELOG_START -->"
            end_marker = "<!-- CHANGELOG_END -->"
            
            if start_marker in gui_content and end_marker in gui_content:
                pattern = re.compile(f"{start_marker}.*?{end_marker}", re.DOTALL)
                replacement = f"{start_marker}\n{html_snippet}\n    {end_marker}"
                new_gui_content = pattern.sub(replacement, gui_content)
                
                with open(gui_path, "w", encoding="utf-8") as f:
                    f.write(new_gui_content)
                self.after(0, self.log, "[OK] Help tab successfully updated with latest changelog!")
            else:
                self.after(0, self.log, f"[ERROR] Could not find the CHANGELOG placeholders in {gui_path}.")
                
        threading.Thread(target=task, daemon=True).start()

    def run_app(self):
        self.log(f"> Starting app...")
        subprocess.Popen(f'"{self.python_cmd}" app.py', shell=True)

    def start_pwa(self):
        self.log(f"> Starting PWA local server...")
        import webbrowser
        os.system(f"start cmd /c \"cd web && \"{self.python_cmd}\" -m http.server 8000\"")
        def open_browser():
            import time
            time.sleep(1)
            webbrowser.open("http://localhost:8000")
            self.after(0, self.log, "[Browser opened for PWA]")
        threading.Thread(target=open_browser, daemon=True).start()

    def deploy_pwa(self):
        self.log("> Deploying PWA to GitHub / Netlify...")
        self.run_cmd('git add . && git commit -m "Auto-deploy update to PWA" && git push', show_console=True)

    def quick_start(self):
        self.run_cmd(f'"{self.python_cmd}" -m pip install -r requirements.txt && "{self.python_cmd}" -m pytest -q && "{self.python_cmd}" app.py')

    def install_deps(self):
        self.run_cmd(f'"{self.python_cmd}" -m pip install -r requirements.txt')

    def install_extras(self):
        self.run_cmd(f'"{self.python_cmd}" -m pip install -r requirements-optional.txt')

    def run_tests(self):
        self.run_cmd(f'"{self.python_cmd}" -m pytest -q')

    def create_venv(self):
        self.run_cmd(f'"{self.python_cmd}" -m venv .venv')

    def open_venv_shell(self):
        os.system(f"start cmd /k \".venv\\Scripts\\activate.bat\"")
        
    def python_repl(self):
        self.run_cmd(f'"{self.python_cmd}"', show_console=True)

    def compile_check(self):
        self.run_cmd(f'"{self.python_cmd}" -m compileall app.py paulstretch_light tests')

    def build_exe(self):
        self.run_cmd(f'"{self.python_cmd}" -m PyInstaller --noconfirm --clean findus_stretching.spec')

    def build_zip(self):
        self.run_cmd(f'"{self.python_cmd}" tools/build_release_zip.py dist/findus_stretching dist/release/findus_stretching_v{self.version}.zip')

    def build_installer(self):
        iscc = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
        if not os.path.exists(iscc):
            iscc = r"C:\Program Files\Inno Setup 6\ISCC.exe"
        self.run_cmd(f'"{iscc}" /Qp /DMyAppVersion={self.version} findus_stretching_installer.iss')

    def pip_list(self):
        self.run_cmd(f'"{self.python_cmd}" -m pip list')

    def run_ruff(self):
        self.run_cmd(f'"{self.python_cmd}" -m pip install ruff -q && "{self.python_cmd}" -m ruff check .')

    def clean_artifacts(self):
        self.run_cmd('rmdir /s /q build & rmdir /s /q dist')

    def hard_reset(self):
        if messagebox.askyesno("Confirm Hard Reset", "VARNING: Detta raderar .venv, __pycache__, build, och dist.\nÄr du helt säker?"):
            self.log("> Starting Hard Reset...")
            def task():
                import shutil
                for d in ["build", "dist", ".venv"]:
                    if os.path.exists(d):
                        try:
                            shutil.rmtree(d)
                            self.after(0, self.log, f"Removed {d}/")
                        except Exception as e:
                            self.after(0, self.log, f"Failed to remove {d}/: {e}")
                for root, dirs, files in os.walk("."):
                    if "__pycache__" in dirs:
                        try:
                            shutil.rmtree(os.path.join(root, "__pycache__"))
                        except:
                            pass
                self.after(0, self.log, "Removed __pycache__ directories.")
                self.after(0, self.log, "[Hard Reset Complete]")
            threading.Thread(target=task, daemon=True).start()

    def write_diagnostics(self):
        self.run_cmd(f'"{self.python_cmd}" diagnostics.py')

    def do_release_flow(self, bump_type):
        def task():
            self.log(f"Starting {bump_type} release flow...")
            if not self.bump_version(bump_type):
                return
                
            cmds = [
                (f'"{self.python_cmd}" -m pytest -q', "Running tests"),
                (f'"{self.python_cmd}" -m PyInstaller --noconfirm --clean findus_stretching.spec', "Building EXE"),
            ]
            
            iscc = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
            if not os.path.exists(iscc):
                iscc = r"C:\Program Files\Inno Setup 6\ISCC.exe"
            cmds.append((f'"{iscc}" /Qp /DMyAppVersion={self.version} findus_stretching_installer.iss', "Building Installer"))
            
            os.makedirs(r"dist\release", exist_ok=True)
            zip_path = rf"dist\release\findus_stretching_v{self.version}.zip"
            cmds.append((f'"{self.python_cmd}" tools/build_release_zip.py dist/findus_stretching "{zip_path}"', "Creating Zip"))

            for cmd, desc in cmds:
                self.after(0, self.log, f"\n> {desc}...")
                process = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
                for line in process.stdout:
                    self.after(0, self.log, line.strip())
                process.wait()
                if process.returncode != 0:
                    self.after(0, self.log, f"\n[ERROR] {desc} failed with code {process.returncode}! Aborting.")
                    return

            stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.after(0, self.log, "\n> Updating changelog...")
            with open("CHANGELOG_RELEASES.md", "a", encoding="utf-8") as f:
                f.write(f"\n## {self.version} - {stamp}\n\n- Built with launcher automated release flow.\n- Artifacts: `dist\\findus_stretching`, `dist\\installer`, `dist\\release`.\n")
                
            with open(r"dist\release\release_log.txt", "a", encoding="utf-8") as f:
                f.write(f"[{stamp}] version {self.version}\n")
                
            self.after(0, self.log, f"\n--- {bump_type.capitalize()} release done! ---")
            
        threading.Thread(target=task, daemon=True).start()

    def full_release(self):
        if messagebox.askyesno("Confirm Release", "Do a patch release bump and build everything?"):
            self.do_release_flow("patch")

    def minor_release(self):
        if messagebox.askyesno("Confirm Release", "Do a minor release bump and build everything?"):
            self.do_release_flow("minor")


if __name__ == "__main__":
    app = Launcher()
    app.mainloop()
