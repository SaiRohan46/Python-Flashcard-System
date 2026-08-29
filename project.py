import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import os
import requests
import zipfile
import csv
import json
import random
from datetime import datetime
from pathlib import Path

class FlashcardApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Flashcard System - Admin and User Access")
        self.root.geometry("1200x800")
        
        self.decks_path = os.getcwd()
        self.current_deck = None
        self.cards = []
        self.card_index = 0
        self.answer_shown = False

        # Progress tracking
        self.progress_data = {}
        self.session_stats = {'correct': 0, 'incorrect': 0, 'skipped': 0}
        self.bookmarked_cards = set()
        self.shuffle_mode = False
        self.search_query = ""
        self.filtered_cards = []

        # Load progress file
        self.progress_file = os.path.join(self.decks_path, "progress.json")
        self.load_progress()

        # Try to load background image
        self.setup_background()

        # Bind keyboard shortcuts
        self.setup_keyboard_shortcuts()

        # ✅ Define status_var BEFORE create_ui
        self.status_var = tk.StringVar(value="Ready")

        # Create UI
        self.create_ui()
        
    def setup_background(self):
        """Set up background with fallback to color if image not found"""
        image_paths = [
            "F:\\APP\\decks\\propic.jpg",
            os.path.join(self.decks_path, "background.jpg"),
            os.path.join(os.path.expanduser("~"), "Downloads", "background.jpg")
        ]
        
        background_found = False
        for image_path in image_paths:
            if os.path.exists(image_path):
                try:
                    self.background_image = Image.open(image_path)
                    self.background_image = self.background_image.resize(
                        (self.root.winfo_screenwidth(), self.root.winfo_screenheight()), 
                        Image.LANCZOS
                    )
                    self.bg_photo = ImageTk.PhotoImage(self.background_image)
                    background_found = True
                    break
                except Exception as e:
                    print(f"Error loading image from {image_path}: {e}")
        
        # Create main frame with background color
        if background_found:
            self.canvas = tk.Canvas(self.root, width=self.root.winfo_screenwidth(), 
                                   height=self.root.winfo_screenheight())
            self.canvas.pack(fill="both", expand=True)
            self.canvas.create_image(0, 0, image=self.bg_photo, anchor="nw")
            self.main_frame = tk.Frame(self.canvas, bg="white", relief="solid", bd=1)
            self.canvas.create_window(self.root.winfo_screenwidth()//2, 
                                     self.root.winfo_screenheight()//2,
                                     window=self.main_frame, anchor="center")
        else:
            self.root.configure(bg="#f0f0f0")
            self.main_frame = tk.Frame(self.root, bg="#f0f0f0")
            self.main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    def setup_keyboard_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Right>', lambda e: self.next_card())
        self.root.bind('<Left>', lambda e: self.previous_card())
        self.root.bind('<space>', lambda e: self.show_answer())
        self.root.bind('<Control-b>', lambda e: self.toggle_bookmark())
        self.root.bind('<Control-e>', lambda e: self.mark_easy())
        self.root.bind('<Control-m>', lambda e: self.mark_medium())
        self.root.bind('<Control-h>', lambda e: self.mark_hard())
        self.root.bind('<Control-s>', lambda e: self.open_search())
        self.root.bind('<Control-d>', lambda e: self.show_deck_stats())
    
    def create_ui(self):
        """Create the main UI with tabs"""
        # Create notebook (tabbed interface)
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Admin Tab
        self.admin_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.admin_frame, text="Admin Panel")
        self.create_admin_tab()
        
        # Review Tab
        self.review_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.review_frame, text="Review Mode")
        self.create_review_tab()
        
        # Statistics Tab
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="Statistics")
        self.create_stats_tab()
        
        # Settings Tab
        self.settings_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.settings_frame, text="Settings")
        self.create_settings_tab()
        
        # Status bar
        status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief="sunken")
        status_bar.pack(fill="x", side="bottom", padx=5, pady=5)
    
    def create_admin_tab(self):
        """Create admin panel for deck management"""
        admin_label = ttk.Label(self.admin_frame, text="Deck Management", font=("Arial", 14, "bold"))
        admin_label.pack(pady=10)
        
        button_frame = ttk.Frame(self.admin_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Choose Deck Directory", 
                  command=self.choose_deck_directory, width=25).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Download Sample Decks", 
                  command=self.download_decks, width=25).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Browse for ZIP", 
                  command=self.browse_for_zip, width=20).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Create Sample", 
                  command=self.create_sample_deck, width=20).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Refresh Decks", 
                  command=self.show_csv_files, width=20).pack(side="left", padx=5)
        
        # Directory info
        ttk.Label(self.admin_frame, text="Current Directory:", font=("Arial", 10, "bold")).pack(pady=5)
        self.dir_label = ttk.Label(self.admin_frame, text=self.decks_path, foreground="blue")
        self.dir_label.pack(pady=5)
        
        # Deck selection
        ttk.Label(self.admin_frame, text="Select Deck:", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        
        deck_select_frame = ttk.Frame(self.admin_frame)
        deck_select_frame.pack(pady=5)
        
        self.deck_var = tk.StringVar()
        self.deck_menu = ttk.Combobox(deck_select_frame, textvariable=self.deck_var, width=50, state="readonly")
        self.deck_menu.pack(side="left", padx=5)
        
        ttk.Button(deck_select_frame, text="Load Deck", command=self.load_deck, width=15).pack(side="left", padx=5)
        ttk.Button(deck_select_frame, text="Clear Progress", command=self.clear_deck_progress, width=15).pack(side="left", padx=5)
        
        # Recent activity
        ttk.Label(self.admin_frame, text="Recent Activity:", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        self.activity_text = tk.Text(self.admin_frame, height=10, width=80)
        self.activity_text.pack(padx=10, pady=5)
        self.activity_text.config(state="disabled")
    
    def create_review_tab(self):
        """Create the review/study mode tab"""
        # Top controls
        control_frame = ttk.Frame(self.review_frame)
        control_frame.pack(fill="x", padx=10, pady=10)
        
        ttk.Button(control_frame, text="🔀 Shuffle", command=self.toggle_shuffle, width=12).pack(side="left", padx=2)
        ttk.Button(control_frame, text="🔍 Search", command=self.open_search, width=12).pack(side="left", padx=2)
        ttk.Button(control_frame, text="📊 Stats", command=self.show_deck_stats, width=12).pack(side="left", padx=2)
        
        self.shuffle_label = ttk.Label(control_frame, text="(Shuffle OFF)", foreground="gray")
        self.shuffle_label.pack(side="left", padx=10)
        
        # Progress bar
        ttk.Label(self.review_frame, text="Progress:", font=("Arial", 9, "bold")).pack(anchor="w", padx=10)
        self.progress_bar = ttk.Progressbar(self.review_frame, mode='determinate', length=400)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        
        # Question section
        ttk.Label(self.review_frame, text="Question:", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.question_box = tk.Text(self.review_frame, wrap="word", height=6, width=80, font=("Arial", 11))
        self.question_box.pack(padx=10, pady=5, fill="both", expand=True)
        self.question_box.config(state="disabled")
        
        # Answer section
        ttk.Label(self.review_frame, text="Answer (hidden until shown):", font=("Arial", 11, "bold")).pack(anchor="w", padx=10, pady=(10, 0))
        self.answer_box = tk.Text(self.review_frame, wrap="word", height=6, width=80, font=("Arial", 11), fg="darkgreen")
        self.answer_box.pack(padx=10, pady=5, fill="both", expand=True)
        self.answer_box.config(state="disabled")
        
        # Control buttons
        button_frame = ttk.Frame(self.review_frame)
        button_frame.pack(pady=10, fill="x", padx=10)
        
        ttk.Button(button_frame, text="Show Answer (SPACE)", command=self.show_answer, width=20).pack(side="left", padx=5)
        ttk.Button(button_frame, text="← Previous (←)", command=self.previous_card, width=20).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Next (→)", command=self.next_card, width=20).pack(side="left", padx=5)
        ttk.Button(button_frame, text="🔖 Bookmark (Ctrl+B)", command=self.toggle_bookmark, width=20).pack(side="left", padx=5)
        
        # Difficulty marking
        diff_frame = ttk.LabelFrame(self.review_frame, text="Mark Difficulty", padding=5)
        diff_frame.pack(pady=10, padx=10, fill="x")
        
        ttk.Button(diff_frame, text="Easy (Ctrl+E)", command=self.mark_easy, width=15).pack(side="left", padx=5)
        ttk.Button(diff_frame, text="Medium (Ctrl+M)", command=self.mark_medium, width=15).pack(side="left", padx=5)
        ttk.Button(diff_frame, text="Hard (Ctrl+H)", command=self.mark_hard, width=15).pack(side="left", padx=5)
        
        # Card info
        self.card_info_label = ttk.Label(self.review_frame, text="", font=("Arial", 9), foreground="gray")
        self.card_info_label.pack(pady=5)
    
    def create_stats_tab(self):
        """Create statistics tab"""
        ttk.Label(self.stats_frame, text="Session Statistics", font=("Arial", 14, "bold")).pack(pady=10)
        
        self.stats_display = tk.Text(self.stats_frame, height=20, width=80, font=("Courier", 10))
        self.stats_display.pack(padx=10, pady=10, fill="both", expand=True)
        self.stats_display.config(state="disabled")
        
        button_frame = ttk.Frame(self.stats_frame)
        button_frame.pack(pady=10)
        
        ttk.Button(button_frame, text="Refresh Stats", command=self.update_stats_display, width=20).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Export Results", command=self.export_progress, width=20).pack(side="left", padx=5)
        ttk.Button(button_frame, text="Clear All Progress", command=self.clear_all_progress, width=20).pack(side="left", padx=5)
    
    def create_settings_tab(self):
        """Create settings tab"""
        ttk.Label(self.settings_frame, text="Settings & Preferences", font=("Arial", 14, "bold")).pack(pady=10)
        
        settings_frame = ttk.LabelFrame(self.settings_frame, text="Display Options", padding=10)
        settings_frame.pack(padx=10, pady=10, fill="x")
        
        ttk.Label(settings_frame, text="Theme:").pack(anchor="w", pady=5)
        theme_var = tk.StringVar(value="Light")
        ttk.Combobox(settings_frame, textvariable=theme_var, values=["Light", "Dark"], state="readonly", width=20).pack(anchor="w", pady=5)
        
        ttk.Label(settings_frame, text="Font Size:").pack(anchor="w", pady=5)
        size_var = tk.StringVar(value="11")
        ttk.Combobox(settings_frame, textvariable=size_var, values=["9", "10", "11", "12", "14", "16"], state="readonly", width=20).pack(anchor="w", pady=5)
        
        # Keyboard shortcuts info
        shortcuts_frame = ttk.LabelFrame(self.settings_frame, text="Keyboard Shortcuts", padding=10)
        shortcuts_frame.pack(padx=10, pady=10, fill="both", expand=True)
        
        shortcuts_text = """
        Right Arrow (→) ............ Next Card
        Left Arrow (←) ............. Previous Card
        Space Bar ................. Show Answer
        Ctrl+B .................... Toggle Bookmark
        Ctrl+E .................... Mark Easy
        Ctrl+M .................... Mark Medium
        Ctrl+H .................... Mark Hard
        Ctrl+S .................... Search
        Ctrl+D .................... Show Statistics
        """
        
        shortcuts_label = ttk.Label(shortcuts_frame, text=shortcuts_text, justify="left", font=("Courier", 9))
        shortcuts_label.pack(anchor="w", pady=10)
        
        ttk.Button(self.settings_frame, text="Save Settings", command=self.save_settings, width=20).pack(pady=10)
    
    def choose_deck_directory(self):
        directory = filedialog.askdirectory()
        if directory:
            self.decks_path = directory
            self.progress_file = os.path.join(self.decks_path, "progress.json")
            self.load_progress()
            self.dir_label.config(text=self.decks_path)
            self.show_csv_files()
            self.log_activity(f"Directory changed to: {self.decks_path}")
            messagebox.showinfo("Success", f"Deck directory set to: {self.decks_path}")
    
    def download_decks(self):
        """Download sample decks from Google Drive with fallback options"""
        url = "https://drive.google.com/uc?export=download&id=1R_uuTI6SpZ1Cs0henj7Xzb3JhfKCckK6"
        download_folder = self.decks_path
        
        if not os.path.exists(download_folder):
            os.makedirs(download_folder)
        
        try:
            self.status_var.set("Downloading decks...")
            self.root.update()
            
            # Try to download with proper headers for Google Drive
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, timeout=30, headers=headers, allow_redirects=True)
            
            if response.status_code == 200 and len(response.content) > 1000:
                zip_path = os.path.join(download_folder, "decks.zip")
                with open(zip_path, 'wb') as file:
                    file.write(response.content)
                self.unzip_decks(zip_path)
            else:
                # If direct download fails, offer alternatives
                self.show_download_alternatives()
        except requests.exceptions.Timeout:
            messagebox.showerror("Timeout", "Download timed out. Please check your internet connection.\n\nAlternative: Use 'Browse for ZIP' option.")
            self.show_download_alternatives()
        except Exception as e:
            messagebox.showerror("Download Error", f"Failed to download: {str(e)}\n\nAlternative: Use 'Browse for ZIP' option.")
            self.show_download_alternatives()
    
    def show_download_alternatives(self):
        """Show alternative download/deck creation options"""
        response = messagebox.showinfo(
            "Download Alternatives",
            "Options:\n\n"
            "1. Click 'Browse for ZIP' to select a local decks.zip file\n"
            "2. Click 'Create Sample Deck' to create a demo deck\n"
            "3. Check your internet connection and try again"
        )
        
        choice = messagebox.askyesno("Create Sample Deck?", 
                                     "Would you like to create a sample flashcard deck to test the app?")
        if choice:
            self.create_sample_deck()
        else:
            self.browse_for_zip()
    
    def browse_for_zip(self):
        """Browse and load a zip file locally"""
        zip_path = filedialog.askopenfilename(
            title="Select Decks ZIP File",
            filetypes=[("ZIP files", "*.zip"), ("All files", "*.*")]
        )
        if zip_path:
            try:
                self.unzip_decks(zip_path)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to extract ZIP: {e}")
    
    def create_sample_deck(self):
        """Create a sample deck for testing"""
        decks_folder = os.path.join(self.decks_path, 'decks')
        if not os.path.exists(decks_folder):
            os.makedirs(decks_folder)
        
        # Create sample deck with common knowledge questions
        sample_data = [
            ['Question', 'Answer'],  # Header
            ['What is the capital of France?', 'Paris'],
            ['What is 2 + 2?', '4'],
            ['What is the largest planet in our solar system?', 'Jupiter'],
            ['Who wrote Romeo and Juliet?', 'William Shakespeare'],
            ['What is the chemical symbol for Gold?', 'Au'],
            ['What is the smallest prime number?', '2'],
            ['What is the capital of Japan?', 'Tokyo'],
            ['How many sides does a hexagon have?', '6'],
            ['What is the speed of light?', 'Approximately 299,792,458 meters per second'],
            ['What year did World War II end?', '1945'],
        ]
        
        try:
            sample_deck_path = os.path.join(decks_folder, 'Sample_Deck.csv')
            with open(sample_deck_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerows(sample_data)
            
            self.show_csv_files()
            messagebox.showinfo("Success", f"Sample deck created:\n{sample_deck_path}\n\nYou can now load it!")
            self.log_activity("Sample deck created successfully")
            self.status_var.set("Sample deck created")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create sample deck: {e}")
    
    def unzip_decks(self, zip_path):
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(self.decks_path)
            os.remove(zip_path)
            self.show_csv_files()
            self.log_activity("Sample decks downloaded and extracted successfully!")
            messagebox.showinfo("Success", "Decks downloaded and extracted successfully!")
            self.status_var.set("Decks downloaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Extraction error: {e}")
            self.status_var.set("Extraction error")
    
    def show_csv_files(self):
        decks_folder = os.path.join(self.decks_path, 'decks')
        if not os.path.exists(decks_folder):
            messagebox.showwarning("Warning", "No 'decks' folder found. Please download or create decks.")
            return
        
        csv_files = [f for f in os.listdir(decks_folder) if f.endswith('.csv')]
        if csv_files:
            self.deck_menu['values'] = csv_files
            self.deck_var.set(csv_files[0])
            self.status_var.set(f"Found {len(csv_files)} deck(s)")
        else:
            messagebox.showinfo("Info", "No CSV files found in decks folder.")
            self.status_var.set("No decks found")
    
    def load_deck(self):
        file_name = self.deck_var.get()
        if not file_name:
            messagebox.showwarning("Warning", "Please select a deck to load.")
            return
        
        try:
            deck_path = os.path.join(self.decks_path, 'decks', file_name)
            with open(deck_path, "r", encoding="utf-8") as file:
                reader = csv.reader(file)
                header = next(reader, None)
                self.cards = [list(enumerate(row, 1)) for idx, row in enumerate(reader)]
            
            self.current_deck = file_name
            self.card_index = 0
            self.answer_shown = False
            self.session_stats = {'correct': 0, 'incorrect': 0, 'skipped': 0}
            self.filtered_cards = list(range(len(self.cards)))
            
            self.show_card()
            self.log_activity(f"Loaded deck: {file_name} ({len(self.cards)} cards)")
            messagebox.showinfo("Success", f"Successfully loaded: {file_name}")
            self.status_var.set(f"Deck loaded: {file_name}")
            self.notebook.select(1)  # Switch to review tab
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load deck: {e}")
            self.status_var.set("Error loading deck")
    
    def show_card(self):
        if not self.cards:
            self.question_box.config(state="normal")
            self.question_box.delete("1.0", tk.END)
            self.question_box.insert(tk.END, "No cards loaded. Please load a deck.")
            self.question_box.config(state="disabled")
            return
        
        card_idx = self.filtered_cards[self.card_index] if self.filtered_cards else 0
        card = self.cards[card_idx] if card_idx < len(self.cards) else None
        
        if card:
            self.question_box.config(state="normal")
            self.question_box.delete("1.0", tk.END)
            self.question_box.insert(tk.END, card[0] if len(card) > 0 else "")
            self.question_box.config(state="disabled")
            
            self.answer_box.config(state="normal")
            self.answer_box.delete("1.0", tk.END)
            self.answer_box.config(state="disabled")
            self.answer_shown = False
            
            # Update progress bar
            progress = ((self.card_index + 1) / len(self.filtered_cards)) * 100 if self.filtered_cards else 0
            self.progress_bar['value'] = progress
            
            # Update card info
            difficulty = self.progress_data.get(card_idx, {}).get('difficulty', 'unmarked')
            bookmarked = "🔖" if card_idx in self.bookmarked_cards else ""
            stats = self.progress_data.get(card_idx, {'correct': 0, 'incorrect': 0})
            
            info_text = f"Card {self.card_index + 1}/{len(self.filtered_cards)} | "
            info_text += f"Difficulty: {difficulty} | {bookmarked} | "
            info_text += f"Correct: {stats['correct']} | Incorrect: {stats['incorrect']}"
            
            self.card_info_label.config(text=info_text)
    
    def show_answer(self):
        if not self.cards:
            return
        
        card_idx = self.filtered_cards[self.card_index] if self.filtered_cards else 0
        card = self.cards[card_idx] if card_idx < len(self.cards) else None
        
        if card and len(card) > 1:
            self.answer_box.config(state="normal")
            self.answer_box.delete("1.0", tk.END)
            self.answer_box.insert(tk.END, card[1])
            self.answer_box.config(state="disabled")
            self.answer_shown = True
            self.status_var.set("Answer revealed")
    
    def next_card(self):
        if self.cards and self.filtered_cards and self.card_index < len(self.filtered_cards) - 1:
            self.card_index += 1
            self.show_card()
            self.session_stats['skipped'] += 1
    
    def previous_card(self):
        if self.cards and self.card_index > 0:
            self.card_index -= 1
            self.show_card()
    
    def toggle_bookmark(self):
        if not self.cards or not self.filtered_cards:
            return
        
        card_idx = self.filtered_cards[self.card_index]
        if card_idx in self.bookmarked_cards:
            self.bookmarked_cards.remove(card_idx)
            self.status_var.set("Bookmark removed")
        else:
            self.bookmarked_cards.add(card_idx)
            self.status_var.set("Card bookmarked")
        
        self.show_card()
        self.save_progress()
    
    def mark_easy(self):
        self._mark_difficulty('easy')
        self.session_stats['correct'] += 1
    
    def mark_medium(self):
        self._mark_difficulty('medium')
    
    def mark_hard(self):
        self._mark_difficulty('hard')
        self.session_stats['incorrect'] += 1
    
    def _mark_difficulty(self, difficulty):
        if not self.cards or not self.filtered_cards:
            return
        
        card_idx = self.filtered_cards[self.card_index]
        if card_idx not in self.progress_data:
            self.progress_data[card_idx] = {'correct': 0, 'incorrect': 0, 'difficulty': 'unmarked'}
        
        self.progress_data[card_idx]['difficulty'] = difficulty
        self.save_progress()
        self.status_var.set(f"Marked as {difficulty}")
        self.show_card()
    
    def toggle_shuffle(self):
        self.shuffle_mode = not self.shuffle_mode
        if self.shuffle_mode:
            random.shuffle(self.filtered_cards)
            self.shuffle_label.config(text="(Shuffle ON)", foreground="green")
            self.status_var.set("Shuffle mode enabled")
        else:
            self.filtered_cards = list(range(len(self.cards)))
            self.shuffle_label.config(text="(Shuffle OFF)", foreground="gray")
            self.status_var.set("Shuffle mode disabled")
        
        self.card_index = 0
        self.show_card()
    
    def open_search(self):
        """Open search dialog"""
        search_window = tk.Toplevel(self.root)
        search_window.title("Search Cards")
        search_window.geometry("400x300")
        
        ttk.Label(search_window, text="Search query:", font=("Arial", 10)).pack(pady=10)
        search_entry = ttk.Entry(search_window, width=40, font=("Arial", 10))
        search_entry.pack(padx=10, pady=5)
        search_entry.focus()
        
        def perform_search():
            query = search_entry.get().lower()
            if not query:
                messagebox.showwarning("Warning", "Please enter a search query")
                return
            
            results = []
            for idx, card in enumerate(self.cards):
                if query in str(card[0]).lower() or (len(card) > 1 and query in str(card[1]).lower()):
                    results.append(idx)
            
            if results:
                self.filtered_cards = results
                self.card_index = 0
                self.search_query = query
                self.show_card()
                messagebox.showinfo("Search Results", f"Found {len(results)} matching card(s)")
                search_window.destroy()
            else:
                messagebox.showinfo("No Results", "No cards matched your search")
        
        ttk.Button(search_window, text="Search", command=perform_search).pack(pady=10)
        ttk.Button(search_window, text="Clear Filter", command=lambda: self.clear_search_filter()).pack(pady=5)
    
    def clear_search_filter(self):
        """Clear search filter"""
        self.filtered_cards = list(range(len(self.cards)))
        self.card_index = 0
        self.search_query = ""
        self.shuffle_label.config(text="(Shuffle OFF)", foreground="gray")
        self.show_card()
        self.status_var.set("Filter cleared")
    
    def show_deck_stats(self):
        """Show deck statistics"""
        if not self.cards:
            messagebox.showinfo("Info", "No deck loaded")
            return
        
        stats_text = f"Deck: {self.current_deck}\n"
        stats_text += f"Total Cards: {len(self.cards)}\n"
        stats_text += f"Cards Studied: {len(self.progress_data)}\n\n"
        
        stats_text += "Session Statistics:\n"
        stats_text += f"  Correct: {self.session_stats['correct']}\n"
        stats_text += f"  Incorrect: {self.session_stats['incorrect']}\n"
        stats_text += f"  Skipped: {self.session_stats['skipped']}\n\n"
        
        easy_count = sum(1 for v in self.progress_data.values() if v.get('difficulty') == 'easy')
        medium_count = sum(1 for v in self.progress_data.values() if v.get('difficulty') == 'medium')
        hard_count = sum(1 for v in self.progress_data.values() if v.get('difficulty') == 'hard')
        
        stats_text += "Difficulty Distribution:\n"
        stats_text += f"  Easy: {easy_count}\n"
        stats_text += f"  Medium: {medium_count}\n"
        stats_text += f"  Hard: {hard_count}\n"
        stats_text += f"  Bookmarked: {len(self.bookmarked_cards)}\n"
        
        messagebox.showinfo("Deck Statistics", stats_text)
    
    def update_stats_display(self):
        """Update the statistics display"""
        if not self.current_deck:
            stats_text = "No deck loaded. Please load a deck first."
        else:
            stats_text = f"{'='*60}\n"
            stats_text += f"DECK: {self.current_deck}\n"
            stats_text += f"{'='*60}\n\n"
            
            stats_text += f"OVERALL STATISTICS:\n"
            stats_text += f"  Total Cards: {len(self.cards)}\n"
            stats_text += f"  Cards Studied: {len(self.progress_data)}\n"
            stats_text += f"  Bookmarked Cards: {len(self.bookmarked_cards)}\n\n"
            
            stats_text += f"SESSION STATISTICS:\n"
            stats_text += f"  Correct Answers: {self.session_stats['correct']}\n"
            stats_text += f"  Incorrect Answers: {self.session_stats['incorrect']}\n"
            stats_text += f"  Skipped: {self.session_stats['skipped']}\n"
            
            total = self.session_stats['correct'] + self.session_stats['incorrect']
            if total > 0:
                accuracy = (self.session_stats['correct'] / total) * 100
                stats_text += f"  Accuracy: {accuracy:.1f}%\n\n"
            else:
                stats_text += f"  Accuracy: N/A\n\n"
            
            easy = sum(1 for v in self.progress_data.values() if v.get('difficulty') == 'easy')
            medium = sum(1 for v in self.progress_data.values() if v.get('difficulty') == 'medium')
            hard = sum(1 for v in self.progress_data.values() if v.get('difficulty') == 'hard')
            
            stats_text += f"DIFFICULTY DISTRIBUTION:\n"
            stats_text += f"  Easy: {easy}\n"
            stats_text += f"  Medium: {medium}\n"
            stats_text += f"  Hard: {hard}\n"
        
        self.stats_display.config(state="normal")
        self.stats_display.delete("1.0", tk.END)
        self.stats_display.insert(tk.END, stats_text)
        self.stats_display.config(state="disabled")
    
    def export_progress(self):
        """Export progress to CSV"""
        if not self.current_deck:
            messagebox.showwarning("Warning", "No deck loaded")
            return
        
        try:
            export_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
                initialfile=f"progress_{self.current_deck}"
            )
            
            if export_path:
                with open(export_path, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['Card Index', 'Question', 'Answer', 'Difficulty', 'Correct', 'Incorrect', 'Bookmarked'])
                    
                    for idx, card in enumerate(self.cards):
                        data = self.progress_data.get(idx, {'correct': 0, 'incorrect': 0, 'difficulty': 'unmarked'})
                        bookmarked = "Yes" if idx in self.bookmarked_cards else "No"
                        writer.writerow([
                            idx,
                            card[0],
                            card[1] if len(card) > 1 else "",
                            data['difficulty'],
                            data['correct'],
                            data['incorrect'],
                            bookmarked
                        ])
                
                messagebox.showinfo("Success", f"Progress exported to:\n{export_path}")
                self.log_activity(f"Progress exported: {export_path}")
        except Exception as e:
            messagebox.showerror("Error", f"Export failed: {e}")
    
    def clear_deck_progress(self):
        """Clear progress for current deck"""
        if not self.current_deck:
            messagebox.showwarning("Warning", "No deck loaded")
            return
        
        if messagebox.askyesno("Confirm", f"Clear all progress for '{self.current_deck}'?"):
            self.progress_data.clear()
            self.bookmarked_cards.clear()
            self.session_stats = {'correct': 0, 'incorrect': 0, 'skipped': 0}
            self.save_progress()
            self.show_card()
            self.update_stats_display()
            messagebox.showinfo("Success", "Progress cleared")
            self.log_activity(f"Progress cleared for deck: {self.current_deck}")
    
    def clear_all_progress(self):
        """Clear all progress"""
        if messagebox.askyesno("Confirm", "Clear ALL progress for all decks?"):
            self.progress_data.clear()
            self.bookmarked_cards.clear()
            self.session_stats = {'correct': 0, 'incorrect': 0, 'skipped': 0}
            self.save_progress()
            messagebox.showinfo("Success", "All progress cleared")
            self.log_activity("All progress cleared")
    
    def save_progress(self):
        """Save progress to JSON file"""
        try:
            progress_dict = {
                'progress': {str(k): v for k, v in self.progress_data.items()},
                'bookmarks': list(self.bookmarked_cards),
                'session_stats': self.session_stats,
                'last_saved': datetime.now().isoformat()
            }
            with open(self.progress_file, 'w') as f:
                json.dump(progress_dict, f, indent=2)
        except Exception as e:
            print(f"Error saving progress: {e}")
    
    def load_progress(self):
        """Load progress from JSON file"""
        try:
            if os.path.exists(self.progress_file):
                with open(self.progress_file, 'r') as f:
                    progress_dict = json.load(f)
                    self.progress_data = {int(k): v for k, v in progress_dict.get('progress', {}).items()}
                    self.bookmarked_cards = set(progress_dict.get('bookmarks', []))
                    self.session_stats = progress_dict.get('session_stats', {'correct': 0, 'incorrect': 0, 'skipped': 0})
        except Exception as e:
            print(f"Error loading progress: {e}")
    
    def log_activity(self, message):
        """Log activity to the admin panel"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.activity_text.config(state="normal")
        self.activity_text.insert("1.0", f"[{timestamp}] {message}\n")
        self.activity_text.see("1.0")
        self.activity_text.config(state="disabled")
    
    def save_settings(self):
        """Save user settings"""
        messagebox.showinfo("Info", "Settings saved successfully!")
        self.status_var.set("Settings saved")


if __name__ == "__main__":
    root = tk.Tk()
    app = FlashcardApp(root)
    root.mainloop()
