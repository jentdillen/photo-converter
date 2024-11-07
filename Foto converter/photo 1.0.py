import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image
import os
import tkinterdnd2

class PhotoConverterApp:
    def __init__(self, master):
        self.master = master
        master.title("Foto Converter")
        
        # Fullscreen windowed modus
        master.state('zoomed')

        # Variabelen
        self.source_files = []
        self.target_directory = ""
        self.size = (600, 600)  # Standaard grootte

        # GUI-elementen
        self.create_widgets()

    def create_widgets(self):
        # Frame voor drag-and-drop
        self.drop_frame = tk.Frame(self.master)
        self.drop_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        self.drop_frame.drop_target_register(tkinterdnd2.DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.drop_files)

        # Label voor drag-and-drop instructies
        self.drop_label = tk.Label(self.drop_frame, text="Sleep foto's hierheen", bg="lightgray", height=10)
        self.drop_label.pack(fill=tk.BOTH, expand=True)

        # Knop om foto's te selecteren via bestandsverkenner
        self.select_files_button = tk.Button(self.master, text="Selecteer Foto's", command=self.select_files)
        self.select_files_button.pack(pady=5)

        # Label om geselecteerde foto's weer te geven
        self.files_label = tk.Label(self.master, text="Geen foto's geselecteerd")
        self.files_label.pack()

        # Knop om doelmap te selecteren
        self.dir_button = tk.Button(self.master, text="Selecteer Doelmap", command=self.select_directory)
        self.dir_button.pack(pady=10)

        # Label om geselecteerde map weer te geven
        self.dir_label = tk.Label(self.master, text="Geen map geselecteerd")
        self.dir_label.pack()

        # Invoervelden voor afmetingen
        self.size_frame = tk.Frame(self.master)
        self.size_frame.pack(pady=10)

        tk.Label(self.size_frame, text="Breedte:").grid(row=0, column=0)
        self.width_entry = tk.Entry(self.size_frame)
        self.width_entry.grid(row=0, column=1)
        self.width_entry.insert(0, "600")

        tk.Label(self.size_frame, text="Hoogte:").grid(row=1, column=0)
        self.height_entry = tk.Entry(self.size_frame)
        self.height_entry.grid(row=1, column=1)
        self.height_entry.insert(0, "600")

        # Knop om conversie te starten
        self.convert_button = tk.Button(self.master, text="Converteer Foto's", command=self.convert_photos)
        self.convert_button.pack(pady=10)

    def select_files(self):
        files = filedialog.askopenfilenames(filetypes=[("Image files", "*.jpg *.jpeg *.png")])
        self.source_files.extend(files)
        self.files_label.config(text=f"{len(self.source_files)} foto('s) geselecteerd")

    def drop_files(self, event):
        files = self.drop_frame.tk.splitlist(event.data)
        valid_extensions = ('.jpg', '.jpeg', '.png')
        new_files = [f for f in files if f.lower().endswith(valid_extensions)]
        self.source_files.extend(new_files)
        self.files_label.config(text=f"{len(self.source_files)} foto('s) geselecteerd")

    def select_directory(self):
        self.target_directory = filedialog.askdirectory()
        self.dir_label.config(text=f"Doelmap: {self.target_directory}")

    def convert_photos(self):
        if not self.source_files or not self.target_directory:
            messagebox.showerror("Fout", "Selecteer eerst foto's en een doelmap.")
            return

        try:
            width = int(self.width_entry.get())
            height = int(self.height_entry.get())
            self.size = (width, height)
        except ValueError:
            messagebox.showerror("Fout", "Voer geldige getallen in voor breedte en hoogte.")
            return

        for file in self.source_files:
            with Image.open(file) as img:
                img_resized = img.resize(self.size, Image.LANCZOS)
                filename = os.path.basename(file)
                save_path = os.path.join(self.target_directory, filename)
                img_resized.save(save_path)

        messagebox.showinfo("Succes", f"{len(self.source_files)} foto('s) geconverteerd en opgeslagen.")

root = tkinterdnd2.TkinterDnD.Tk()
app = PhotoConverterApp(root)
root.mainloop()
