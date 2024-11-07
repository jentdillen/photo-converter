import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import tkinterdnd2
import threading
import subprocess

class PhotoConverterApp:
    def __init__(self, master):
        self.master = master
        self.master.title("Foto Converter")
        
        # Fullscreen windowed modus
        self.master.state('zoomed')

        # Variabelen
        self.source_files = []
        self.thumbnails = []
        self.size = (600, 600)  # Standaard grootte

        # GUI-elementen
        self.create_widgets()

    def create_widgets(self):
        # Hoofdframe voor de layout
        main_frame = tk.Frame(self.master)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Linker frame voor drag-and-drop
        left_frame = tk.Frame(main_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Add right frame
        right_frame = tk.Frame(main_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))

        # Maak een nieuw frame voor de drop zone en de miniaturen
        drop_and_thumbnails_frame = tk.Frame(left_frame)
        drop_and_thumbnails_frame.pack(fill=tk.BOTH, expand=True)

        # Maak de drop zone groter
        self.drop_frame = tk.Frame(drop_and_thumbnails_frame, height=200)  # Verhoogd van 100 naar 200
        self.drop_frame.pack(fill=tk.X, pady=(0, 10))
        self.drop_frame.pack_propagate(False)
        self.drop_frame.drop_target_register(tkinterdnd2.DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.drop_files)

        self.drop_label = tk.Label(self.drop_frame, text="Sleep foto's hierheen", bg="lightgray")
        self.drop_label.pack(fill=tk.BOTH, expand=True)

        # Knop om bestanden te selecteren toevoegen
        self.select_files_button = tk.Button(right_frame, text="Selecteer Bestanden", command=self.select_files)
        self.select_files_button.pack(fill=tk.X, pady=(0, 10))

        # Frame voor doelmap selectie
        dir_frame = tk.Frame(right_frame)
        dir_frame.pack(fill=tk.X, pady=(0, 10))

        self.dir_button = tk.Button(dir_frame, text="Selecteer Doelmap", command=self.select_directory)
        self.dir_button.pack(fill=tk.X)

        self.dir_label = tk.Label(dir_frame, text="Geen map geselecteerd", wraplength=150)
        self.dir_label.pack(fill=tk.X, pady=(5, 0))

        # Frame voor breedte en hoogte invoer
        size_frame = tk.Frame(right_frame)
        size_frame.pack(fill=tk.X, pady=(0, 10))

        tk.Label(size_frame, text="Breedte:").grid(row=0, column=0, sticky='w')
        self.width_entry = tk.Entry(size_frame)
        self.width_entry.grid(row=0, column=1, sticky='ew')
        self.width_entry.insert(0, "600")

        tk.Label(size_frame, text="Hoogte:").grid(row=1, column=0, sticky='w')
        self.height_entry = tk.Entry(size_frame)
        self.height_entry.grid(row=1, column=1, sticky='ew')
        self.height_entry.insert(0, "600")

        size_frame.grid_columnconfigure(1, weight=1)

        # Frame voor de scrollbare canvas (miniaturen)
        self.canvas_frame = tk.Frame(drop_and_thumbnails_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', self.on_canvas_configure)

        self.thumbnails_frame = tk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.thumbnails_frame, anchor=tk.NW)

        self.thumbnails_frame.bind('<Configure>', self.on_frame_configure)

        # Knop om conversie te starten (groter en gecentreerd onderaan)
        self.convert_button = tk.Button(self.master, text="Converteer Foto's", command=self.start_conversion, 
                                        font=('Helvetica', 14, 'bold'), padx=20, pady=10)
        self.convert_button.pack(pady=20)

        # Voortgangsbalk
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.master, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=10, pady=5)

        # Label voor de voortgangsstatus
        self.status_label = tk.Label(self.master, text="")
        self.status_label.pack(pady=5)

    def on_canvas_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        self.add_files(files)

    def drop_files(self, event):
        files = self.drop_frame.tk.splitlist(event.data)
        valid_extensions = ('.jpg', '.jpeg', '.png')
        new_files = [f for f in files if f.lower().endswith(valid_extensions)]
        self.add_files(new_files)

    def add_files(self, files):
        for file in files:
            if file not in self.source_files:
                self.source_files.append(file)
                self.add_thumbnail(file)
        self.update_canvas()

    def add_thumbnail(self, file):
        frame = tk.Frame(self.thumbnails_frame)
        frame.pack(fill=tk.X, padx=5, pady=2)

        # Miniatuur
        img = Image.open(file)
        img.thumbnail((30, 30))
        photo = ImageTk.PhotoImage(img)
        img_label = tk.Label(frame, image=photo)
        img_label.image = photo
        img_label.grid(row=0, column=0, padx=(0, 5))

        # Bestandsnaam (met ellipsis als de naam te lang is)
        name = os.path.basename(file)
        if len(name) > 30:
            name = name[:27] + "..."
        name_label = tk.Label(frame, text=name, anchor='w', width=30)
        name_label.grid(row=0, column=1, sticky='w', padx=(0, 5))

        # Verwijderknop
        delete_button = tk.Button(frame, text="X", fg="red", command=lambda f=file: self.remove_file(f))
        delete_button.grid(row=0, column=2)

        self.thumbnails.append((frame, file))

    def remove_file(self, file):
        self.source_files.remove(file)
        for frame, f in self.thumbnails:
            if f == file:
                frame.destroy()
                self.thumbnails.remove((frame, f))
                break
        self.update_canvas()

    def update_canvas(self):
        self.thumbnails_frame.update_idletasks()
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def select_directory(self):
        self.target_directory = filedialog.askdirectory()
        if self.target_directory:
            self.dir_label.config(text=f"Doelmap: {self.target_directory}")
        else:
            self.dir_label.config(text="Geen map geselecteerd")

    def start_conversion(self):
        if not self.source_files:
            messagebox.showwarning("Geen bestanden", "Selecteer eerst enkele foto's om te converteren.")
            return

        if not hasattr(self, 'target_directory') or not self.target_directory:
            messagebox.showwarning("Geen doelmap", "Selecteer eerst een doelmap via de 'Selecteer Doelmap' knop.")
            return

        # Schakel knoppen uit tijdens conversie
        self.convert_button.config(state=tk.DISABLED)
        self.select_files_button.config(state=tk.DISABLED)

        # Toon bezig-indicator
        self.status_label.config(text="Bezig met converteren...")
        self.progress_var.set(0)

        # Start de conversie in een aparte thread
        threading.Thread(target=self.convert_photos, args=(self.target_directory,), daemon=True).start()

    def convert_photos(self, output_dir):
        total_files = len(self.source_files)
        target_width = int(self.width_entry.get())
        target_height = int(self.height_entry.get())
        
        for i, file in enumerate(self.source_files):
            try:
                with Image.open(file) as img:
                    # Bereken de bijsnijdafmetingen
                    img_width, img_height = img.size
                    aspect_ratio = img_width / img_height
                    target_ratio = target_width / target_height

                    if aspect_ratio > target_ratio:
                        new_width = int(img_height * target_ratio)
                        offset = (img_width - new_width) // 2
                        crop_box = (offset, 0, offset + new_width, img_height)
                    else:
                        new_height = int(img_width / target_ratio)
                        offset = (img_height - new_height) // 2
                        crop_box = (0, offset, img_width, offset + new_height)

                    img_cropped = img.crop(crop_box)
                    img_resized = img_cropped.resize((target_width, target_height), Image.LANCZOS)

                    # Maak een nieuwe bestandsnaam voor de geconverteerde afbeelding
                    base_name = os.path.splitext(os.path.basename(file))[0]
                    output_file = os.path.join(output_dir, f"{base_name}_converted.png")
                    img_resized.save(output_file, "PNG")
                
                progress = (i + 1) / total_files * 100
                self.progress_var.set(progress)
                self.status_label.config(text=f"Verwerkt: {i+1}/{total_files}")
                self.master.update_idletasks()

            except Exception as e:
                print(f"Fout bij het converteren van {file}: {str(e)}")

        # Na conversie, herstel de knoppen en update status
        self.master.after(0, self.finish_conversion)

    def finish_conversion(self):
        self.convert_button.config(state=tk.NORMAL)
        self.select_files_button.config(state=tk.NORMAL)
        self.status_label.config(text="Conversie voltooid!")
        
        total_files = len(self.source_files)
        width = int(self.width_entry.get())
        height = int(self.height_entry.get())
        
        # Toon het voltooiingsbericht
        self.show_completion_message(total_files, width, height, self.target_directory)
        
        # Verwijder alle foto's na conversie
        self.remove_all_files(show_message=False)

    def remove_all_files(self, show_message=True):
        if not self.source_files:
            if show_message:
                messagebox.showinfo("Geen bestanden", "Er zijn geen bestanden om te verwijderen.")
            return

        self.source_files.clear()
        for frame, _ in self.thumbnails:
            frame.destroy()
        self.thumbnails.clear()
        self.update_canvas()
        
        if show_message:
            messagebox.showinfo("Verwijderd", "Alle geüploade foto's zijn verwijderd.")

    def show_completion_message(self, total_files, width, height, output_dir):
        def open_output_folder():
            if os.name == 'nt':  # Voor Windows
                os.startfile(output_dir)
            else:  # Voor macOS en Linux
                subprocess.call(['xdg-open', output_dir])

        message_window = tk.Toplevel(self.master)
        message_window.title("Conversie Voltooid")
        
        message = f"Alle {total_files} foto's zijn geconverteerd naar PNG en bijgesneden naar {width}x{height}.\n"
        message += "De geüploade foto's zijn automatisch verwijderd. U kunt nu nieuwe foto's uploaden."
        tk.Label(message_window, text=message, padx=20, pady=10).pack()
        
        tk.Button(message_window, text="Open Doelmap", command=open_output_folder).pack(pady=10)
        tk.Button(message_window, text="OK", command=message_window.destroy).pack(pady=10)

# Hoofdprogramma
if __name__ == "__main__":
    root = tkinterdnd2.TkinterDnD.Tk()
    app = PhotoConverterApp(root)
    root.mainloop()
