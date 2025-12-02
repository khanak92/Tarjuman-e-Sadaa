"""
Main GUI application for MSTUTS
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import threading
import os
from audio_processor import AudioProcessor
from transcription_engine import TranscriptionEngine
from output_formatter import OutputFormatter
from config import SUPPORTED_LANGUAGES, SUPPORTED_AUDIO_FORMATS, DEFAULT_MODEL, DEFAULT_TRANSLATION_TARGET


class MSTUTSApp:
    """
    Main application window for MSTUTS
    """
    
    def __init__(self, root):
        self.root = root
        self.root.title("Tarjuman-e-Sadaa - Multilingual Speech Transcription System")
        self.root.geometry("1200x800")
        self.root.resizable(True, True)
        
        self.army_colors = {
            "bg_main": "#2F4F2F",
            "bg_panel": "#3D5A3D",
            "bg_light": "#4A6B4A",
            "accent": "#556B2F",
            "khaki": "#C3B091",
            "tan": "#D2B48C",
            "text_light": "#F5F5DC",
            "text_dark": "#2F2F2F",
            "success": "#8B9A46",
            "warning": "#B8860B",
            "error": "#8B4513",
            "border": "#556B2F"
        }
        
        self.root.configure(bg=self.army_colors["bg_main"])
        
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Title.TLabel", font=("Segoe UI", 26, "bold"), background=self.army_colors["bg_main"], foreground=self.army_colors["text_light"])
        style.configure("Heading.TLabel", font=("Segoe UI", 12, "bold"), background=self.army_colors["bg_panel"], foreground=self.army_colors["text_light"])
        style.configure("Section.TFrame", background=self.army_colors["bg_panel"], relief="flat")
        style.configure("Action.TButton", font=("Segoe UI", 11, "bold"), padding=12, background=self.army_colors["accent"], foreground=self.army_colors["text_light"])
        style.map("Action.TButton", background=[("active", self.army_colors["khaki"]), ("pressed", self.army_colors["tan"])])
        style.configure("Secondary.TButton", font=("Segoe UI", 9), padding=8, background=self.army_colors["bg_light"], foreground=self.army_colors["text_light"])
        style.map("Secondary.TButton", background=[("active", self.army_colors["accent"]), ("pressed", self.army_colors["khaki"])])
        style.configure("TNotebook", background=self.army_colors["bg_panel"], borderwidth=0)
        style.configure("TNotebook.Tab", 
                       background=self.army_colors["bg_light"], 
                       foreground=self.army_colors["text_light"], 
                       padding=[10, 6],
                       font=("Segoe UI", 9))
        style.map("TNotebook.Tab", 
                  background=[("selected", self.army_colors["accent"])])
        style.configure("TCombobox", 
                        fieldbackground=self.army_colors["bg_light"], 
                        foreground=self.army_colors["text_light"],
                        borderwidth=1,
                        relief="solid")
        style.map("TCombobox",
                 fieldbackground=[("readonly", self.army_colors["accent"])],
                 foreground=[("readonly", self.army_colors["text_light"])],
                 bordercolor=[("focus", self.army_colors["khaki"])])
        style.configure("TCombobox.Listbox",
                        background=self.army_colors["bg_light"],
                        foreground=self.army_colors["text_light"],
                        selectbackground=self.army_colors["accent"],
                        selectforeground=self.army_colors["text_light"],
                        font=("Segoe UI", 10))
        style.configure("TProgressbar", background=self.army_colors["accent"], troughcolor=self.army_colors["bg_light"])
        
        self.audio_file_path = None
        self.transcription_result = None
        self.audio_processor = AudioProcessor()
        self.transcription_engine = None
        self.output_formatter = OutputFormatter()
        self.animation_running = False
        self.transcription_start_time = None
        self.total_chunks = 0
        self.processed_chunks = 0
        self.transcription_in_progress = False
        self.ai_text_tags_configured = False
        
        self._setup_ui()
        self._animate_fade_in()
    
    def _setup_ui(self):
        """
        Set up the user interface
        """
        main_container = tk.Frame(self.root, bg=self.army_colors["bg_main"])
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        header_frame = tk.Frame(main_container, bg=self.army_colors["bg_main"])
        header_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.title_label = ttk.Label(
            header_frame,
            text="Tarjuman-e-Sadaa",
            style="Title.TLabel"
        )
        self.title_label.pack()
        
        self.subtitle_label = tk.Label(
            header_frame,
            text="Tarjuman-e-Sadaa",
            font=("Segoe UI", 11),
            bg=self.army_colors["bg_main"],
            fg=self.army_colors["khaki"]
        )
        self.subtitle_label.pack(pady=(5, 0))
        
        content_frame = tk.Frame(main_container, bg=self.army_colors["bg_main"])
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        left_panel = tk.Frame(content_frame, bg=self.army_colors["bg_panel"], relief="flat", bd=2, highlightbackground=self.army_colors["border"], highlightthickness=1)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, padx=(0, 10), ipadx=20, ipady=20)
        left_panel.pack_propagate(False)
        left_panel.config(width=400)
        
        right_panel = tk.Frame(content_frame, bg=self.army_colors["bg_panel"], relief="flat", bd=2, highlightbackground=self.army_colors["border"], highlightthickness=1)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, ipadx=20, ipady=20)
        
        self._setup_left_panel(left_panel)
        self._setup_right_panel(right_panel)
    
    def _animate_fade_in(self):
        """
        Animate fade in effect for the window
        """
        self.root.attributes('-alpha', 0.0)
        def fade_in(alpha=0.0):
            if alpha < 1.0:
                alpha += 0.05
                self.root.attributes('-alpha', alpha)
                self.root.after(20, lambda: fade_in(alpha))
        fade_in()
    
    def _animate_pulse(self, widget, color1, color2, duration=1000):
        """
        Animate pulsing effect for a widget
        
        Args:
            widget: Widget to animate
            color1: First color
            color2: Second color
            duration: Animation duration in ms
        """
        if not self.animation_running:
            return
        
        def pulse(step=0):
            if not self.animation_running:
                return
            progress = (step % 20) / 20.0
            if progress < 0.5:
                alpha = progress * 2
            else:
                alpha = 2 - (progress * 2)
            
            r1, g1, b1 = int(color1[1:3], 16), int(color1[3:5], 16), int(color1[5:7], 16)
            r2, g2, b2 = int(color2[1:3], 16), int(color2[3:5], 16), int(color2[5:7], 16)
            
            r = int(r1 + (r2 - r1) * alpha)
            g = int(g1 + (g2 - g1) * alpha)
            b = int(b1 + (b2 - b1) * alpha)
            
            color = f"#{r:02x}{g:02x}{b:02x}"
            try:
                widget.config(fg=color)
            except:
                pass
            
            if self.animation_running:
                self.root.after(50, lambda: pulse(step + 1))
        
        pulse()
    
    def _setup_left_panel(self, parent):
        """
        Set up the left control panel
        """
        section_title = ttk.Label(
            parent,
            text="⚙️ Settings",
            style="Heading.TLabel"
        )
        section_title.pack(anchor=tk.W, pady=(0, 20))
        
        file_frame = tk.Frame(parent, bg=self.army_colors["bg_panel"])
        file_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            file_frame,
            text="📁 Audio File",
            font=("Segoe UI", 10, "bold"),
            bg=self.army_colors["bg_panel"],
            fg=self.army_colors["text_light"]
        ).pack(anchor=tk.W, pady=(0, 5))
        
        file_select_frame = tk.Frame(file_frame, bg=self.army_colors["bg_panel"])
        file_select_frame.pack(fill=tk.X, pady=(0, 5))
        
        self.file_label = tk.Label(
            file_select_frame,
            text="No file selected",
            font=("Segoe UI", 9),
            bg=self.army_colors["bg_panel"],
            fg=self.army_colors["khaki"],
            anchor=tk.W,
            wraplength=300
        )
        self.file_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        select_btn = ttk.Button(
            file_select_frame,
            text="Browse",
            command=self._select_file,
            style="Secondary.TButton"
        )
        select_btn.pack(side=tk.RIGHT)
        
        separator1 = ttk.Separator(parent, orient="horizontal")
        separator1.pack(fill=tk.X, pady=15)
        
        language_frame = tk.Frame(parent, bg=self.army_colors["bg_panel"])
        language_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            language_frame,
            text="🌐 Input Language",
            font=("Segoe UI", 10, "bold"),
            bg=self.army_colors["bg_panel"],
            fg=self.army_colors["text_light"]
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.language_var = tk.StringVar(value="auto")
        language_combo = ttk.Combobox(
            language_frame,
            textvariable=self.language_var,
            values=list(SUPPORTED_LANGUAGES.keys()),
            state="readonly",
            font=("Segoe UI", 10, "bold"),
            width=25
        )
        language_combo.pack(fill=tk.X)
        language_combo.bind("<<ComboboxSelected>>", lambda e: self._on_combobox_selected(language_combo))
        
        model_frame = tk.Frame(parent, bg=self.army_colors["bg_panel"])
        model_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(
            model_frame,
            text="🤖 Model Size",
            font=("Segoe UI", 10, "bold"),
            bg=self.army_colors["bg_panel"],
            fg=self.army_colors["text_light"]
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.model_var = tk.StringVar(value=DEFAULT_MODEL)
        model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            values=["base", "small", "medium", "large-v3"],
            state="readonly",
            font=("Segoe UI", 10, "bold"),
            width=25
        )
        model_combo.pack(fill=tk.X)
        model_combo.bind("<<ComboboxSelected>>", lambda e: self._on_combobox_selected(model_combo))
        
        format_frame = tk.Frame(parent, bg=self.army_colors["bg_panel"])
        format_frame.pack(fill=tk.X, pady=(0, 20))
        
        tk.Label(
            format_frame,
            text="📄 Output Format",
            font=("Segoe UI", 10, "bold"),
            bg=self.army_colors["bg_panel"],
            fg=self.army_colors["text_light"]
        ).pack(anchor=tk.W, pady=(0, 5))
        
        self.format_var = tk.StringVar(value="paragraphs")
        format_combo = ttk.Combobox(
            format_frame,
            textvariable=self.format_var,
            values=["plain", "paragraphs", "timestamped"],
            state="readonly",
            font=("Segoe UI", 10, "bold"),
            width=25
        )
        format_combo.pack(fill=tk.X)
        format_combo.bind("<<ComboboxSelected>>", lambda e: self._on_combobox_selected(format_combo))
        
        separator2 = ttk.Separator(parent, orient="horizontal")
        separator2.pack(fill=tk.X, pady=15)
        
        self.transcribe_button = ttk.Button(
            parent,
            text="▶ Start Transcription",
            command=self._start_transcription,
            style="Action.TButton",
            state="disabled"
        )
        self.transcribe_button.pack(fill=tk.X, pady=(0, 15))
        
        self.progress_var = tk.StringVar(value="Ready")
        self.progress_label = tk.Label(
            parent,
            textvariable=self.progress_var,
            font=("Segoe UI", 9),
            bg=self.army_colors["bg_panel"],
            fg=self.army_colors["khaki"]
        )
        self.progress_label.pack(pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(
            parent,
            mode='indeterminate',
            length=300
        )
        self.progress_bar.pack(fill=tk.X, pady=(0, 15))
        
        self.status_label = tk.Label(
            parent,
            text="Status: Ready",
            font=("Segoe UI", 9, "bold"),
            bg=self.army_colors["bg_panel"],
            fg=self.army_colors["success"]
        )
        self.status_label.pack()
        
        action_frame = tk.Frame(parent, bg=self.army_colors["bg_panel"])
        action_frame.pack(fill=tk.X, pady=(20, 0))
        
        self.save_button = ttk.Button(
            action_frame,
            text="💾 Save",
            command=self._save_transcription,
            style="Secondary.TButton",
            state="disabled"
        )
        self.save_button.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        clear_btn = ttk.Button(
            action_frame,
            text="🗑️ Clear",
            command=self._clear_results,
            style="Secondary.TButton"
        )
        clear_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(5, 0))
    
    def _setup_right_panel(self, parent):
        """
        Set up the right results panel
        """
        header_frame = tk.Frame(parent, bg=self.army_colors["bg_panel"])
        header_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(
            header_frame,
            text="📋 Transcription Results",
            style="Heading.TLabel"
        ).pack(side=tk.LEFT)
        
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        
        urdu_frame = tk.Frame(self.notebook, bg=self.army_colors["bg_light"])
        self.notebook.add(urdu_frame, text="🇵🇰 Urdu")
        
        self.urdu_text = scrolledtext.ScrolledText(
            urdu_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            bg=self.army_colors["bg_light"],
            fg=self.army_colors["text_light"],
            padx=15,
            pady=15,
            relief="flat",
            borderwidth=0,
            insertbackground=self.army_colors["text_light"]
        )
        self.urdu_text.pack(fill=tk.BOTH, expand=True)
        self._configure_text_tags(self.urdu_text)
        self.urdu_text.bind("<KeyPress>", self._on_text_edit)
        
        english_frame = tk.Frame(self.notebook, bg=self.army_colors["bg_light"])
        self.notebook.add(english_frame, text="🇬🇧 English")
        
        self.english_text = scrolledtext.ScrolledText(
            english_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            bg=self.army_colors["bg_light"],
            fg=self.army_colors["text_light"],
            padx=15,
            pady=15,
            relief="flat",
            borderwidth=0,
            insertbackground=self.army_colors["text_light"]
        )
        self.english_text.pack(fill=tk.BOTH, expand=True)
        self._configure_text_tags(self.english_text)
        self.english_text.bind("<KeyPress>", self._on_text_edit)
        
        combined_frame = tk.Frame(self.notebook, bg=self.army_colors["bg_light"])
        self.notebook.add(combined_frame, text="📄 Combined")
        
        self.result_text = scrolledtext.ScrolledText(
            combined_frame,
            wrap=tk.WORD,
            font=("Segoe UI", 11),
            bg=self.army_colors["bg_light"],
            fg=self.army_colors["text_light"],
            padx=15,
            pady=15,
            relief="flat",
            borderwidth=0,
            insertbackground=self.army_colors["text_light"]
        )
        self.result_text.pack(fill=tk.BOTH, expand=True)
        self._configure_text_tags(self.result_text)
        self.result_text.bind("<KeyPress>", self._on_text_edit)
        
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)
        self._update_tab_styles()
    
    def _configure_text_tags(self, text_widget):
        """
        Configure text tags for AI vs human-added text distinction
        
        Args:
            text_widget: Text widget to configure
        """
        text_widget.tag_configure("ai_text", 
                                 foreground=self.army_colors["text_light"],
                                 font=("Segoe UI", 11),
                                 background="")
        text_widget.tag_configure("human_text",
                                 foreground=self.army_colors["tan"],
                                 font=("Segoe UI", 11, "italic", "bold"),
                                 background=self.army_colors["bg_panel"],
                                 underline=True)
    
    def _on_text_edit(self, event):
        """
        Handle text editing to mark human-added text
        
        Args:
            event: Key press event
        """
        if self.transcription_in_progress:
            self.root.bell()
            messagebox.showinfo(
                "Transcription in Progress",
                "Please wait for transcription to complete before editing.\n\n"
                "You can edit the text once transcription is finished."
            )
            return "break"
        
        widget = event.widget
        if event.keysym not in ["Return", "Tab", "Shift_L", "Shift_R", "Control_L", "Control_R", "Alt_L", "Alt_R", "Up", "Down", "Left", "Right", "Home", "End", "Prior", "Next", "BackSpace", "Delete"]:
            self.root.after(50, lambda: self._mark_human_text(widget, event))
        elif event.keysym in ["BackSpace", "Delete"]:
            self.root.after(50, lambda: self._mark_human_text(widget, event))
    
    def _mark_human_text(self, widget, event):
        """
        Mark newly typed text as human-added
        
        Args:
            widget: Text widget to mark
            event: Key event
        """
        try:
            cursor_pos = widget.index("insert")
            
            if event.keysym in ["BackSpace", "Delete"]:
                line_start = widget.index(f"{cursor_pos} linestart")
                line_end = widget.index(f"{cursor_pos} lineend")
                widget.tag_add("human_text", line_start, line_end)
            else:
                char_before = widget.get(f"{cursor_pos}-1c", cursor_pos)
                if char_before and char_before.strip():
                    start_pos = f"{cursor_pos}-1c"
                    end_pos = cursor_pos
                    widget.tag_add("human_text", start_pos, end_pos)
        except:
            pass
    
    def _on_combobox_selected(self, combobox):
        """
        Handle combobox selection to make it more visible
        
        Args:
            combobox: The combobox widget that was selected
        """
        self.root.focus_set()
        self.root.after(10, lambda: combobox.focus_set())
    
    def _on_tab_changed(self, event=None):
        """
        Handle tab change event to update tab styles
        """
        self._update_tab_styles()
    
    def _update_tab_styles(self):
        """
        Update tab styles to make selected tab bigger and unselected tabs smaller
        """
        try:
            selected_index = self.notebook.index(self.notebook.select())
            
            for i in range(self.notebook.index("end")):
                tab_id = self.notebook.tabs()[i]
                if i == selected_index:
                    self.notebook.tab(tab_id, padding=[22, 16])
                else:
                    self.notebook.tab(tab_id, padding=[8, 5])
        except:
            pass
    
    def _load_model(self, callback=None):
        """
        Load Whisper model in background thread
        
        Args:
            callback: Optional callback function to call after model is loaded
        """
        def load():
            try:
                self.root.after(0, lambda: self.progress_var.set("Loading model..."))
                self.root.after(0, lambda: self.status_label.config(text="Status: Loading model...", fg=self.army_colors["warning"]))
                self.root.after(0, lambda: self.progress_bar.start())
                self.animation_running = True
                self.root.after(0, lambda: self._animate_pulse(self.status_label, self.army_colors["warning"], self.army_colors["khaki"]))
                
                model_size = self.model_var.get()
                self.transcription_engine = TranscriptionEngine(model_size=model_size, load_translator=False)
                
                self.animation_running = False
                self.root.after(0, lambda: self.progress_bar.stop())
                self.root.after(0, lambda: self.progress_var.set("Model loaded successfully!"))
                self.root.after(0, lambda: self.status_label.config(text="Status: Model loaded", fg=self.army_colors["success"]))
                
                if callback:
                    callback()
            except Exception as e:
                self.animation_running = False
                self.root.after(0, lambda: self.progress_bar.stop())
                messagebox.showerror("Error", f"Failed to load model: {str(e)}")
                self.root.after(0, lambda: self.status_label.config(text="Status: Error loading model", fg=self.army_colors["error"]))
                self.root.after(0, lambda: self.transcribe_button.config(state="normal"))
        
        threading.Thread(target=load, daemon=True).start()
    
    def _select_file(self):
        """
        Open file dialog to select audio file
        """
        file_path = filedialog.askopenfilename(
            title="Select Audio File",
            filetypes=[
                ("Audio Files", "*.mp3 *.wav *.m4a *.mpeg *.mp4 *.webm"),
                ("MP3 Files", "*.mp3"),
                ("WAV Files", "*.wav"),
                ("M4A Files", "*.m4a"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext not in SUPPORTED_AUDIO_FORMATS:
                messagebox.showerror(
                    "Invalid File",
                    f"Unsupported file format. Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS)}"
                )
                return
            
            self.audio_file_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.config(text=filename, fg=self.army_colors["text_light"])
            
            try:
                audio_info = self.audio_processor.get_audio_info(file_path)
                duration_min = int(audio_info["duration"] // 60)
                duration_sec = int(audio_info["duration"] % 60)
                info_text = f"{filename}\n({duration_min}m {duration_sec}s)"
                self.file_label.config(text=info_text, fg=self.army_colors["text_light"])
            except Exception as e:
                messagebox.showwarning("Warning", f"Could not read audio info: {str(e)}")
            
            if self.audio_file_path:
                self.transcribe_button.config(state="normal")
                self.status_label.config(text="Status: File selected", fg=self.army_colors["success"])
    
    def _start_transcription(self):
        """
        Start transcription process in background thread
        """
        if not self.audio_file_path:
            messagebox.showerror("Error", "Please select an audio file first")
            return
        
        self.transcribe_button.config(state="disabled")
        self.save_button.config(state="disabled")
        
        current_model = self.model_var.get()
        
        if not self.transcription_engine or (self.transcription_engine and self.transcription_engine.model_size != current_model):
            self._load_model(callback=self._start_transcription_after_load)
            return
        
        self._start_transcription_after_load()
    
    def _start_transcription_after_load(self):
        """
        Start transcription after model is loaded
        """
        import time
        
        self.transcription_start_time = time.time()
        self.processed_chunks = 0
        self.total_chunks = 0
        self.transcription_in_progress = True
        
        self.urdu_text.config(state="disabled")
        self.english_text.config(state="disabled")
        self.result_text.config(state="disabled")
        
        self.progress_bar.start()
        self.progress_var.set("Transcribing file...")
        self.status_label.config(text="Status: Transcribing file...", fg=self.army_colors["warning"])
        self.animation_running = True
        self._animate_pulse(self.status_label, self.army_colors["warning"], self.army_colors["khaki"])
        
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "⏳ Transcription in progress... Please wait.\n\nYou cannot edit the text until transcription is complete.", "ai_text")
        self.result_text.config(state="disabled")
        
        self.urdu_text.config(state="normal")
        self.urdu_text.delete(1.0, tk.END)
        self.urdu_text.insert(tk.END, "⏳ Transcription in progress... Please wait.\n\nYou cannot edit the text until transcription is complete.", "ai_text")
        self.urdu_text.config(state="disabled")
        
        self.english_text.config(state="normal")
        self.english_text.delete(1.0, tk.END)
        self.english_text.insert(tk.END, "⏳ Transcription in progress... Please wait.\n\nYou cannot edit the text until transcription is complete.", "ai_text")
        self.english_text.config(state="disabled")
        
        def transcribe():
            try:
                import time
                
                input_language = self.language_var.get()
                if input_language == "auto":
                    input_language = None
                
                self.root.after(0, lambda: self.progress_var.set("Loading audio..."))
                audio_array, sample_rate = self.audio_processor.load_audio(self.audio_file_path)
                audio_array = self.audio_processor.normalize_audio(audio_array)
                
                self.root.after(0, lambda: self.progress_var.set("Splitting audio into chunks..."))
                current_model_size = self.transcription_engine.model_size if self.transcription_engine else None
                chunks, chunk_duration = self.audio_processor.split_audio(
                    audio_array,
                    sample_rate,
                    model_size=current_model_size
                )
                
                self.total_chunks = len(chunks)
                self.processed_chunks = 0
                
                def progress_callback(current, total):
                    import time
                    self.processed_chunks = current
                    
                    if self.transcription_start_time and current > 0:
                        elapsed_time = time.time() - self.transcription_start_time
                        avg_time_per_chunk = elapsed_time / current
                        remaining_chunks = total - current
                        eta_seconds = avg_time_per_chunk * remaining_chunks
                        
                        eta_minutes = int(eta_seconds // 60)
                        eta_secs = int(eta_seconds % 60)
                        
                        if eta_minutes > 0:
                            eta_text = f"Processing chunk {current}/{total}... ETA: {eta_minutes}m {eta_secs}s"
                        else:
                            eta_text = f"Processing chunk {current}/{total}... ETA: {eta_secs}s"
                        
                        self.root.after(0, lambda: self.progress_var.set(eta_text))
                    else:
                        self.root.after(0, lambda: self.progress_var.set(f"Processing chunk {current}/{total}..."))
                
                self.root.after(0, lambda: self.progress_var.set("Transcribing and translating..."))
                if len(chunks) > 1:
                    result = self.transcription_engine.transcribe_chunks(
                        chunks,
                        input_language,
                        progress_callback,
                        chunk_duration,
                        "ur"
                    )
                else:
                    try:
                        audio_info = self.audio_processor.get_audio_info(self.audio_file_path)
                        audio_duration = audio_info["duration"]
                        estimated_time = audio_duration * 2.5
                        eta_minutes = int(estimated_time // 60)
                        eta_secs = int(estimated_time % 60)
                        if eta_minutes > 0:
                            self.root.after(0, lambda: self.progress_var.set(f"Transcribing... ETA: ~{eta_minutes}m {eta_secs}s"))
                        else:
                            self.root.after(0, lambda: self.progress_var.set(f"Transcribing... ETA: ~{eta_secs}s"))
                    except:
                        self.root.after(0, lambda: self.progress_var.set("Transcribing..."))
                    
                    result = self.transcription_engine.transcribe_to_urdu(
                        audio_array,
                        input_language,
                        "ur"
                    )
                
                self.transcription_result = result
                
                output_format = self.format_var.get()
                
                urdu_text = result.get("urdu_text", "")
                english_text = result.get("english_text", "")
                
                if output_format == "plain":
                    formatted_text = "Urdu:\n"
                    formatted_text += urdu_text if urdu_text else "[No Urdu text]"
                    formatted_text += "\n\nEnglish:\n"
                    formatted_text += english_text if english_text else "[No English text]"
                elif output_format == "timestamped":
                    formatted_text = "Urdu:\n"
                    if result.get("urdu_segments"):
                        formatted_text += self.output_formatter.format_timestamped({
                            "segments": result.get("urdu_segments", [])
                        })
                    else:
                        formatted_text += urdu_text if urdu_text else "[No Urdu text]"
                    formatted_text += "\n\nEnglish:\n"
                    if result.get("english_segments"):
                        formatted_text += self.output_formatter.format_timestamped({
                            "segments": result.get("english_segments", [])
                        })
                    else:
                        formatted_text += english_text if english_text else "[No English text]"
                else:
                    formatted_text = "Urdu:\n"
                    formatted_text += urdu_text if urdu_text else "[No Urdu text]"
                    formatted_text += "\n\nEnglish:\n"
                    formatted_text += english_text if english_text else "[No English text]"
                
                urdu_display = urdu_text if urdu_text else "[No Urdu text available]"
                english_display = english_text if english_text else "[No English text available]"
                
                self.root.after(0, self._transcription_complete, formatted_text, urdu_display, english_display)
                
            except Exception as e:
                self.root.after(0, self._transcription_error, str(e))
        
        threading.Thread(target=transcribe, daemon=True).start()
    
    def _transcription_complete(self, formatted_text: str, urdu_display: str, english_display: str):
        """
        Update UI after transcription completes
        
        Args:
            formatted_text: Formatted transcription text
            urdu_display: Urdu text to display
            english_display: English text to display
        """
        self.animation_running = False
        self.transcription_in_progress = False
        self.progress_bar.stop()
        self.progress_var.set("Transcription complete!")
        self.status_label.config(text="Status: Transcription complete", fg=self.army_colors["success"])
        
        self.result_text.config(state="normal")
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, formatted_text, "ai_text")
        
        self.urdu_text.config(state="normal")
        self.urdu_text.delete(1.0, tk.END)
        self.urdu_text.insert(tk.END, urdu_display, "ai_text")
        
        self.english_text.config(state="normal")
        self.english_text.delete(1.0, tk.END)
        self.english_text.insert(tk.END, english_display, "ai_text")
        
        self.transcribe_button.config(state="normal")
        self.save_button.config(state="normal")
        
        messagebox.showinfo(
            "Transcription Complete",
            "Transcription completed successfully!\n\n"
            "You can now edit the text. Any changes you make will be highlighted "
            "in a different color to distinguish them from AI-generated text."
        )
    
    def _transcription_error(self, error_message: str):
        """
        Handle transcription errors
        
        Args:
            error_message: Error message to display
        """
        self.animation_running = False
        self.transcription_in_progress = False
        self.progress_bar.stop()
        self.progress_var.set("Error occurred")
        self.status_label.config(text="Status: Error", fg=self.army_colors["error"])
        
        self.urdu_text.config(state="normal")
        self.english_text.config(state="normal")
        self.result_text.config(state="normal")
        
        messagebox.showerror("Transcription Error", f"An error occurred:\n{str(error_message)}")
        self.transcribe_button.config(state="normal")
    
    def _save_transcription(self):
        """
        Save transcription to file
        """
        if not self.transcription_result:
            messagebox.showwarning("Warning", "No transcription to save")
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Transcription",
            defaultextension=".txt",
            filetypes=[
                ("Text Files", "*.txt"),
                ("All Files", "*.*")
            ]
        )
        
        if file_path:
            try:
                output_format = self.format_var.get()
                if output_format == "plain":
                    formatted_text = self.output_formatter.format_plain_text(self.transcription_result)
                elif output_format == "timestamped":
                    formatted_text = self.output_formatter.format_timestamped(self.transcription_result)
                else:
                    formatted_text = self.output_formatter.format_paragraphs(self.transcription_result)
                
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(formatted_text)
                
                messagebox.showinfo("Success", f"Transcription saved to:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save file: {str(e)}")
    
    def _clear_results(self):
        """
        Clear transcription results
        """
        self.transcription_in_progress = False
        self.result_text.config(state="normal")
        self.urdu_text.config(state="normal")
        self.english_text.config(state="normal")
        
        self.result_text.delete(1.0, tk.END)
        self.urdu_text.delete(1.0, tk.END)
        self.english_text.delete(1.0, tk.END)
        self.transcription_result = None
        self.save_button.config(state="disabled")
        self.progress_var.set("Ready")
        self.status_label.config(text="Status: Ready", fg=self.army_colors["success"])


def main():
    """
    Main entry point for the application
    """
    root = tk.Tk()
    app = MSTUTSApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()

