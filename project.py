import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import os
import requests
import zipfile
import csv

class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Flashcard System - Admin and User Access")
        self.decks_path = os.getcwd()
        self.current_deck = None
        self.cards = []
        self.card_index = 0

        # Load background image and set it to fit the window
        image_path = "F:\\APP\\decks\\propic.jpg"  # Update this path to the correct location of your background image
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Background image not found at {image_path}")
        
        self.background_image = Image.open(image_path)
        self.background_image = self.background_image.resize((root.winfo_screenwidth(), root.winfo_screenheight()), Image.LANCZOS)
        self.bg_photo = ImageTk.PhotoImage(self.background_image)

        # Create a Canvas for the background image
        self.canvas = tk.Canvas(root, width=root.winfo_screenwidth(), height=root.winfo_screenheight())
        self.canvas.pack(fill="both", expand=True)
        
        # Place the background image on the canvas
        self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")

        # Configure grid to center everything
        root.grid_rowconfigure(0, weight=1)
        root.grid_rowconfigure(1, weight=1)
        root.grid_rowconfigure(2, weight=1)
        root.grid_columnconfigure(0, weight=1)

        # Admin Block
        admin_frame = tk.LabelFrame(root, text="Admin Block: Deck Management", padx=90, pady=10)
        self.canvas.create_window(root.winfo_screenwidth()//2, 50, window=admin_frame, anchor="n")

        # Create a sub-frame for the row of buttons
        button_row_frame = tk.Frame(admin_frame)
        button_row_frame.pack(pady=5)

        tk.Button(button_row_frame, text="Choose Deck Directory", command=self.choose_deck_directory, bg="green", fg="black", width=20).pack(side="left", padx=5)
        tk.Button(button_row_frame, text="Download Sample Decks", command=self.download_decks, bg="light blue", fg="black", width=20).pack(side="left", padx=5)
        tk.Button(admin_frame, text="Refresh", command=self.show_csv_files, bg="black", fg="white", width=20).pack(pady=5)

        # User Block
        user_frame = tk.LabelFrame(root, text="User Block: Select and Load Deck", padx=19, pady=10)
        self.canvas.create_window(root.winfo_screenwidth() // 2, 200, window=user_frame, anchor="n")

        # Set a fixed width for OptionMenu to prevent resizing
        self.deck_var = tk.StringVar()
        self.deck_menu = tk.OptionMenu(user_frame, self.deck_var, "")
        self.deck_menu.config(width=40)  # Set a fixed width for OptionMenu
        self.deck_menu.grid(row=0, column=0, padx=0, pady=5, sticky="w")

        # Align "Load Deck" button to the far right
        load_button = tk.Button(user_frame, text="Load Deck", command=self.load_deck, bg="grey", fg="white", width=20)
        load_button.grid(row=0, column=1, padx=(20, 5), pady=5, sticky="e")  # Pad left side for gap

        # Review Mode Block
        review_frame = tk.LabelFrame(root, text="Review Mode", padx=10, pady=10)
        self.canvas.create_window(root.winfo_screenwidth()//2, 300, window=review_frame, anchor="n")

        # Question Box
        self.question_label = tk.Label(review_frame, text="Question:", font=("Helvetica", 14, "bold"))
        self.question_label.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        self.question_box = tk.Text(review_frame, wrap="word", height=4, width=40, font=("Helvetica", 12))
        self.question_box.grid(row=1, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        self.question_box.config(state="disabled")

        # Answer Box
        self.answer_label = tk.Label(review_frame, text="Answer:", font=("Helvetica", 14, "bold"))
        self.answer_label.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        self.answer_box = tk.Text(review_frame, wrap="word", height=4, width=40, font=("Helvetica", 12), fg="dark green")
        self.answer_box.grid(row=3, column=1, columnspan=2, padx=5, pady=5, sticky="ew")
        self.answer_box.config(state="disabled")

        # Navigation Buttons
        tk.Button(review_frame, text="Show Answer", command=self.show_answer, bg="black", fg="white").grid(row=4, column=1, pady=5, padx=(0,250), sticky="ew")
        tk.Button(review_frame, text="Next Card", command=self.next_card, bg="orange", fg="white").grid(row=4, column=1, pady=5, padx=(250,0), sticky="ew")

        # Place "Previous Card" button centered in the next row
        tk.Button(review_frame, text="Previous Card", command=self.previous_card, bg="grey", fg="white").grid(row=5, column=1, columnspan=2, pady=5, padx=(230,0), sticky="ew")

        self.stats_label = tk.Label(review_frame, text=" ", font=("Arial", 10))
        self.stats_label.grid(row=6, column=0, columnspan=2, pady=5, sticky="ew")

    def choose_deck_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.decks_path = directory
            messagebox.showinfo("Directory Selected", f"Deck directory set to: {self.decks_path}")

    def download_decks(self):
        url = "https://drive.google.com/uc?export=download&id=1R_uuTI6SpZ1Cs0henj7Xzb3JhfKCckK6"
        download_folder = self.decks_path

        if not os.path.exists(download_folder):
            os.makedirs(download_folder)

        try:
            response = requests.get(url)
            if response.status_code == 200:
                zip_path = os.path.join(download_folder, "decks.zip")
                with open(zip_path, 'wb') as file:
                    file.write(response.content)
                self.unzip_decks(zip_path)
            else:
                messagebox.showerror("Error", "Failed to download the decks.")
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while downloading the decks: {e}")

    def unzip_decks(self, zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.decks_path)
            os.remove(zip_path)
            messagebox.showinfo("Success", "Decks downloaded and extracted successfully!")
            self.show_csv_files()
        except Exception as e:
            messagebox.showerror("Error", f"An error occurred while extracting the decks: {e}")

    def show_csv_files(self):
        decks_folder = os.path.join(self.decks_path, 'decks')
        if not os.path.exists(decks_folder):
            messagebox.showwarning("Warning", "No 'decks' folder found in the selected directory.")
            return

        csv_files = [f for f in os.listdir(decks_folder) if f.endswith('.csv')]
        if csv_files:
            self.deck_var.set(csv_files[0])
            menu = self.deck_menu['menu']
            menu.delete(0, 'end')
            for file in csv_files:
                menu.add_command(label=file, command=lambda value=file: self.deck_var.set(value))
        else:
            messagebox.showinfo("Info", "No CSV files found.")

    def load_deck(self):
        file_name = self.deck_var.get()
        if file_name:
            try:
                deck_path = os.path.join(self.decks_path, 'decks', file_name)
                with open(deck_path, "r") as file:
                    reader = csv.reader(file)
                    next(reader)
                    self.cards = [row for row in reader]
                self.card_index = 0
                self.show_card()
                messagebox.showinfo("Deck Loaded", f"Successfully loaded deck: {file_name}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load deck: {e}")
        else:
            messagebox.showwarning("Warning", "Please select a deck to load.")

    def show_card(self):
        if self.cards:
            self.question_box.config(state="normal")
            self.question_box.delete("1.0", tk.END)
            self.question_box.insert(tk.END, self.cards[self.card_index][0])
            self.question_box.config(state="disabled")

            self.answer_box.config(state="normal")
            self.answer_box.delete("1.0", tk.END)
            self.answer_box.config(state="disabled")
            
            self.stats_label.config(text=f"Card {self.card_index + 1} of {len(self.cards)}")
        else:
            self.question_box.config(state="normal")
            self.question_box.delete("1.0", tk.END)
            self.question_box.insert(tk.END, "No cards available.")
            self.question_box.config(state="disabled")
            
            self.answer_box.config(state="normal")
            self.answer_box.delete("1.0", tk.END)
            self.answer_box.config(state="disabled")
            
            self.stats_label.config(text=" ")

    def show_answer(self):
        if self.cards:
            self.answer_box.config(state="normal")
            self.answer_box.delete("1.0", tk.END)
            self.answer_box.insert(tk.END, self.cards[self.card_index][1])
            self.answer_box.config(state="disabled")

    def next_card(self):
        if self.cards and self.card_index < len(self.cards) - 1:
            self.card_index += 1
            self.show_card()

    def previous_card(self):
        if self.cards and self.card_index > 0:
            self.card_index -= 1
            self.show_card()

if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()
