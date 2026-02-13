"""
Open Ollama Toolkit GUI - OTK

A comprehensive GUI for:
- Browsing available models from ollama.com
- Managing installed models
- Generating starter templates
- Running Ollama commands
"""

import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox, filedialog
import threading
import subprocess
import os
import sys
import time
import re
import webbrowser
import requests
from bs4 import BeautifulSoup
from otk import OllamaClient, ModelManager

# Modern Coder Dark Theme - Sleek & Professional
COLORS = {
    'bg': '#0d1117',              # Deep GitHub dark
    'bg_secondary': '#161b22',    # Slightly lighter panels
    'bg_tertiary': '#010409',     # Darkest, for depth
    'bg_hover': '#1c2128',        # Hover states
    'accent': '#58a6ff',          # Modern blue (VS Code blue)
    'accent_hover': '#79c0ff',    # Lighter blue hover
    'accent_dim': '#1f6feb',      # Dimmed accent
    'success': '#3fb950',         # GitHub green
    'warning': '#d29922',         # Warm amber
    'error': '#f85149',           # Soft red
    'text': '#c9d1d9',            # Soft white (easier on eyes)
    'text_secondary': '#8b949e',  # Muted grey
    'text_bright': '#f0f6fc',     # Pure white for emphasis
    'border': '#30363d',          # Subtle borders
    'shadow': '#010409',          # Shadows for depth
}


class OllamaModelScraper:
    """Scrapes available models from ollama.com"""
    
    def __init__(self):
        self.base_url = "https://ollama.com/search"
        self.models = []
    
    def scrape_models(self, max_pages=5, progress_callback=None, model_callback=None):
        """
        Scrape models from ollama.com
        
        Args:
            max_pages: Maximum pages to scrape
            progress_callback: Function to call with progress updates
            model_callback: Function to call with each batch of models found
        """
        self.models = []
        page = 1
        
        while page <= max_pages:
            if progress_callback:
                progress_callback(f"Loading models... (page {page}/{max_pages})")
            
            try:
                url = self.base_url if page == 1 else f"{self.base_url}?page={page}"
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                h2_tags = soup.find_all('h2')
                page_models = [h2.get_text(strip=True) for h2 in h2_tags if h2.get_text(strip=True)]
                
                if not page_models:
                    break
                
                self.models.extend(page_models)
                
                # Immediately send models to UI
                if model_callback:
                    model_callback(page_models, page, max_pages)
                
                if len(page_models) < 15:
                    break
                
                page += 1
                time.sleep(0.5)  # Be polite
                
            except Exception as e:
                if progress_callback:
                    progress_callback(f"Error: {str(e)}")
                break
        
        return self.models
    
    def scrape_model_tags(self, model_name):
        """
        Scrape available tags for a specific model
        
        Args:
            model_name: Name of the model (e.g., 'translategemma')
            
        Returns:
            List of tag names: ['translategemma:4b', 'translategemma:12b', ...]
        """
        try:
            # Clean model name (remove 'library/' if present)
            clean_name = model_name.replace('library/', '').strip()
            url = f"https://ollama.com/library/{clean_name}/tags"
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            tags = []
            
            # Method 1: Look for table with tag names
            table = soup.find('table')
            if table:
                tbody = table.find('tbody')
                rows = tbody.find_all('tr') if tbody else table.find_all('tr')
                
                for row in rows:
                    cols = row.find_all('td')
                    if not cols:
                        cols = row.find_all('th')
                        if cols:  # This is a header row, skip it
                            continue
                    
                    if cols:
                        # First column is tag name
                        tag_name = cols[0].get_text(strip=True)
                        
                        # Skip if it's a header
                        if tag_name.lower() in ['name', 'tag', 'model']:
                            continue
                        
                        # Validate it looks like a tag name (contains colon)
                        if tag_name and ':' in tag_name:
                            tags.append(tag_name)
            
            # Method 2: Try regex pattern matching
            if not tags:
                all_text = soup.get_text()
                tag_pattern = rf"{re.escape(clean_name)}:[\w\-.]+"
                potential_tags = re.findall(tag_pattern, all_text)
                tags = sorted(set(potential_tags))  # Remove duplicates and sort
            
            # Method 3: If still no tags, add default
            if not tags:
                tags = [f"{clean_name}:latest"]
            
            return tags
            
        except Exception as e:
            # If scraping fails, return a default :latest tag
            clean_name = model_name.replace('library/', '').strip()
            return [f"{clean_name}:latest"]


class ModelBrowserTab(ttk.Frame):
    """Tab for browsing and searching available models"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.scraper = OllamaModelScraper()
        self.all_models = []
        self.current_model = None  # Store selected model name
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create browser interface"""
        # Header
        header = tk.Label(
            self,
            text="🌐 Browse Available Models",
            font=('Segoe UI', 18, 'bold'),
            bg=COLORS['bg'],
            fg=COLORS['accent']
        )
        header.pack(pady=25)
        
        # Info message about internet requirement
        info_frame = tk.Frame(self, bg=COLORS['bg_secondary'], relief='solid', borderwidth=1)
        info_frame.pack(fill='x', padx=20, pady=(0, 15))
        
        info_label = tk.Label(
            info_frame,
            text="ℹ️  Internet connection required to browse models from ollama",
            font=('Segoe UI', 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary'],
            anchor='w',
            padx=15,
            pady=10
        )
        info_label.pack(fill='x')
        
        # Search frame
        search_frame = tk.Frame(self, bg=COLORS['bg'])
        search_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(
            search_frame,
            text="🔍 Search:",
            font=('Segoe UI', 10),
            bg=COLORS['bg'],
            fg=COLORS['text']
        ).pack(side='left', padx=5)
        
        self.search_var = tk.StringVar()
        self.search_var.trace_add('write', lambda *args: self.filter_models())
        
        search_entry = tk.Entry(
            search_frame,
            textvariable=self.search_var,
            font=('Segoe UI', 11),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text'],
            insertbackground=COLORS['accent'],
            relief='flat',
            width=40,
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['accent']
        )
        search_entry.pack(side='left', padx=5, fill='x', expand=True, ipady=6)
        
        # Buttons frame
        btn_frame = tk.Frame(search_frame, bg=COLORS['bg'])
        btn_frame.pack(side='right', padx=5)
        
        self.refresh_btn = tk.Button(
            btn_frame,
            text="🔄 Refresh",
            command=self.refresh_models,
            bg=COLORS['accent'],
            fg=COLORS['text_bright'],
            font=('Segoe UI', 10, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=8,
            borderwidth=0,
            activebackground=COLORS['accent_hover'],
            activeforeground=COLORS['text_bright']
        )
        self.refresh_btn.pack(side='left', padx=2)
        
        # Hover effect
        self.refresh_btn.bind('<Enter>', lambda e: self.refresh_btn.config(bg=COLORS['accent_hover']))
        self.refresh_btn.bind('<Leave>', lambda e: self.refresh_btn.config(bg=COLORS['accent']))
        
        # Main content frame - split into two panes
        content_frame = tk.Frame(self, bg=COLORS['bg'])
        content_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # LEFT PANE - Models list
        left_frame = tk.Frame(content_frame, bg=COLORS['bg'])
        left_frame.pack(side='left', fill='both', expand=True, padx=(0, 10))
        
        tk.Label(
            left_frame,
            text="Names",
            font=('Segoe UI', 12, 'bold'),
            bg=COLORS['bg'],
            fg=COLORS['text']
        ).pack(anchor='w', pady=(0, 5))
        
        # Models listbox
        models_scroll = tk.Scrollbar(left_frame)
        models_scroll.pack(side='right', fill='y')
        
        self.models_listbox = tk.Listbox(
            left_frame,
            font=('Consolas', 11),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text'],
            selectbackground=COLORS['accent'],
            selectforeground=COLORS['text_bright'],
            relief='flat',
            borderwidth=0,
            yscrollcommand=models_scroll.set,
            activestyle='none',
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['accent']
        )
        self.models_listbox.pack(side='left', fill='both', expand=True)
        models_scroll.config(command=self.models_listbox.yview)
        
        # Bind selection event to load tags
        self.models_listbox.bind('<<ListboxSelect>>', self.on_model_select)
        
        # RIGHT PANE - Tags list
        right_frame = tk.Frame(content_frame, bg=COLORS['bg'])
        right_frame.pack(side='right', fill='both', expand=True, padx=(10, 0))
        
        tags_header_frame = tk.Frame(right_frame, bg=COLORS['bg'])
        tags_header_frame.pack(fill='x', pady=(0, 5))
        
        tk.Label(
            tags_header_frame,
            text="Available Models",
            font=('Segoe UI', 11, 'bold'),
            bg=COLORS['bg'],
            fg=COLORS['text']
        ).pack(side='left')
        
        # "See More" button
        self.see_more_btn = tk.Button(
            tags_header_frame,
            text="🔗 See More on ollama.com",
            font=('Segoe UI', 9),
            bg=COLORS['bg_hover'],
            fg=COLORS['accent'],
            activebackground=COLORS['accent'],
            activeforeground=COLORS['text_bright'],
            relief='flat',
            padx=10,
            pady=3,
            cursor='hand2',
            state='disabled',
            command=self.open_tags_page
        )
        self.see_more_btn.pack(side='right')
        
        # Hover effect for see more button
        self.see_more_btn.bind('<Enter>', lambda e: self.see_more_btn.config(bg=COLORS['accent'], fg=COLORS['text_bright']) if self.see_more_btn['state'] == 'normal' else None)
        self.see_more_btn.bind('<Leave>', lambda e: self.see_more_btn.config(bg=COLORS['bg_hover'], fg=COLORS['accent']) if self.see_more_btn['state'] == 'normal' else None)
        
        # Tags listbox
        tags_scroll = tk.Scrollbar(right_frame)
        tags_scroll.pack(side='right', fill='y')
        
        self.tags_listbox = tk.Listbox(
            right_frame,
            font=('Consolas', 10),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text'],
            selectbackground=COLORS['accent'],
            selectforeground=COLORS['text_bright'],
            relief='flat',
            borderwidth=0,
            yscrollcommand=tags_scroll.set,
            activestyle='none',
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['accent']
        )
        self.tags_listbox.pack(side='left', fill='both', expand=True)
        tags_scroll.config(command=self.tags_listbox.yview)
        
        self.tags_listbox.insert(tk.END, "  ← Select a name to view models")
        self.tags_listbox.config(fg=COLORS['text_secondary'])
        
        self.current_tags = []
        
        # Install button
        install_frame = tk.Frame(self, bg=COLORS['bg'])
        install_frame.pack(fill='x', padx=20, pady=10)
        
        self.install_btn = tk.Button(
            install_frame,
            text="📥 Install Selected Model",
            command=self.install_selected,
            bg=COLORS['success'],
            fg=COLORS['text_bright'],
            font=('Segoe UI', 11, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=30,
            pady=12,
            borderwidth=0,
            activebackground='#56d364',
            activeforeground=COLORS['text_bright']
        )
        self.install_btn.pack(pady=10)
        
        # Hover effect
        self.install_btn.bind('<Enter>', lambda e: self.install_btn.config(bg='#56d364'))
        self.install_btn.bind('<Leave>', lambda e: self.install_btn.config(bg=COLORS['success']))
        
        # Status label
        self.status_label = tk.Label(
            self,
            text="1. Click 'Refresh' to load models  →  2. Select a model  →  3. Select a tag  →  4. Click 'Install'",
            font=('Segoe UI', 9),
            bg=COLORS['bg'],
            fg=COLORS['text_secondary']
        )
        self.status_label.pack(pady=10)
        
        # Show initial placeholder
        self.models_listbox.insert(tk.END, "  Click 'Refresh' to browse models from ollama.com")
        self.models_listbox.config(fg=COLORS['text_secondary'])
        
        # Auto-load on startup
        self.after(500, self.refresh_models)
    
    def on_model_select(self, event):
        """Called when a model is selected - load its tags"""
        selection = self.models_listbox.curselection()
        if not selection:
            return
        
        model_name = self.models_listbox.get(selection[0])
        self.current_model = model_name  # Store for URL generation
        
        # Update status
        self.status_label.config(
            text=f"Loading models for {model_name}...",
            fg=COLORS['text_secondary']
        )
        
        # Clear tags list and show loading
        self.tags_listbox.delete(0, tk.END)
        self.tags_listbox.insert(tk.END, "  Loading models...")
        self.tags_listbox.config(fg=COLORS['text_secondary'])
        self.current_tags = []
        self.see_more_btn.config(state='disabled')
        
        def load_tags():
            tags = self.scraper.scrape_model_tags(model_name)
            self.after(0, lambda: self.display_tags(tags))
        
        threading.Thread(target=load_tags, daemon=True).start()
    
    def open_tags_page(self):
        """Open the model's tags page on ollama.com in browser"""
        if self.current_model:
            clean_name = self.current_model.replace('library/', '').strip()
            url = f"https://ollama.com/library/{clean_name}/tags"
            webbrowser.open(url)
    
    def display_tags(self, tags):
        """Display the loaded tags"""
        self.tags_listbox.delete(0, tk.END)
        self.tags_listbox.config(fg=COLORS['text'])
        self.current_tags = tags
        
        if not tags:
            self.tags_listbox.insert(tk.END, "  No tags found")
            self.tags_listbox.config(fg=COLORS['text_secondary'])
            self.status_label.config(
                text="⚠ No tags found for this model",
                fg=COLORS['warning']
            )
            self.see_more_btn.config(state='disabled')
            return
        
        # Display tags (simple list, one per line)
        for tag in tags:
            self.tags_listbox.insert(tk.END, f"  {tag}")
        
        # Enable "See More" button
        self.see_more_btn.config(state='normal')
        
        self.status_label.config(
            text=f"✓ Found {len(tags)} tags  →  Select a tag and click 'Install' (or 'See More' for details)",
            fg=COLORS['success']
        )
    
    def filter_models(self, *args):
        """Filter models based on search"""
        search_term = self.search_var.get().lower()
        
        self.models_listbox.delete(0, tk.END)
        
        filtered = [m for m in self.all_models if search_term in m.lower()]
        
        for model in filtered:
            self.models_listbox.insert(tk.END, model)
        
        self.status_label.config(text=f"Showing {len(filtered)} of {len(self.all_models)} models")
    
    def refresh_models(self):
        """Refresh models list from ollama.com"""
        self.refresh_btn.config(state='disabled', text="Loading...")
        self.status_label.config(text="Loading models from ollama.com...")
        
        # Clear listbox and show loading
        self.models_listbox.delete(0, tk.END)
        self.models_listbox.config(fg=COLORS['text'])
        self.all_models = []
        
        def scrape_thread():
            def progress(msg):
                self.after(0, lambda m=msg: self.status_label.config(text=m))
            
            def add_models(models_batch, current_page, max_pages):
                # Add models to list as they are found
                self.after(0, lambda: self.add_models_incremental(models_batch, current_page, max_pages))
            
            models = self.scraper.scrape_models(
                max_pages=5, 
                progress_callback=progress,
                model_callback=add_models
            )
            
            self.after(0, lambda: self.finalize_models())
        
        threading.Thread(target=scrape_thread, daemon=True).start()
    
    def add_models_incremental(self, models_batch, current_page, max_pages):
        """Add batch of models to listbox incrementally"""
        # Remove loading message if first batch
        if not self.all_models:
            self.models_listbox.delete(0, tk.END)
        
        # Add new models
        for model in models_batch:
            if model not in self.all_models:
                self.all_models.append(model)
                self.models_listbox.insert(tk.END, model)
        
        # Show status
        count_msg = f"Loaded {len(self.all_models)} models"
        if current_page < max_pages:
            count_msg += " - Loading more..."
        self.status_label.config(text=count_msg)
    
    def finalize_models(self):
        """Finalize model loading"""
        # Sort and deduplicate
        self.all_models = sorted(set(self.all_models))
        
        self.models_listbox.delete(0, tk.END)
        for model in self.all_models:
            self.models_listbox.insert(tk.END, model)
        
        self.refresh_btn.config(state='normal', text="🔄 Refresh")
        self.status_label.config(
            text=f"✓ Loaded {len(self.all_models)} models  →  Select a model to view available tags",
            fg=COLORS['success']
        )
    
    def install_selected(self):
        """Install selected model tag"""
        # Check if a tag is selected
        tag_selection = self.tags_listbox.curselection()
        if not tag_selection or not self.current_tags:
            messagebox.showwarning(
                "No Tag Selected", 
                "Please select a model from the left, then select a specific tag/variant from the right to install."
            )
            return
        
        # Get the selected tag
        selected_index = tag_selection[0]
        
        if selected_index >= len(self.current_tags):
            return
        
        tag_name = self.current_tags[selected_index]
        
        # Confirmation
        info_msg = f"Install '{tag_name}'?\n\n"
        info_msg += "This may take several minutes depending on the model size and your connection.\n\n"
        info_msg += "Click 'See More on ollama.com' for size and other details."
        
        if messagebox.askyesno("Install Model", info_msg):
            self.app.install_model(tag_name)


class ModelManagerTab(ttk.Frame):
    """Tab for managing installed models"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.manager = ModelManager()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create manager interface"""
        # Header
        header = tk.Label(
            self,
            text="🔧 Manage Installed Models",
            font=('Segoe UI', 18, 'bold'),
            bg=COLORS['bg'],
            fg=COLORS['accent']
        )
        header.pack(pady=25)
        
        # Models list frame
        list_frame = tk.Frame(self, bg=COLORS['bg'])
        list_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        # Create treeview for models
        columns = ('Name', 'Size', 'Modified')
        self.tree = ttk.Treeview(list_frame, columns=columns, show='headings', height=15)
        
        self.tree.heading('Name', text='Model Name')
        self.tree.heading('Size', text='Size')
        self.tree.heading('Modified', text='Last Modified')
        
        self.tree.column('Name', width=300)
        self.tree.column('Size', width=100)
        self.tree.column('Modified', width=200)
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(list_frame, orient='vertical', command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Buttons frame
        btn_frame = tk.Frame(self, bg=COLORS['bg'])
        btn_frame.pack(fill='x', padx=20, pady=20)
        
        buttons = [
            ("🔄 Refresh", self.refresh_models, COLORS['accent']),
            ("▶️  Run Model", self.run_model, COLORS['success']),
            ("🗑️  Delete Model", self.delete_model, COLORS['error']),
            ("ℹ️  Model Info", self.show_model_info, COLORS['accent_dim']),
        ]
        
        for text, command, color in buttons:
            btn = tk.Button(
                btn_frame,
                text=text,
                command=command,
                bg=color,
                fg=COLORS['text_bright'],
                font=('Segoe UI', 10, 'bold'),
                relief='flat',
                cursor='hand2',
                padx=18,
                pady=10,
                borderwidth=0,
                activebackground=COLORS['accent_hover'] if 'accent' in str(color) else color
            )
            btn.pack(side='left', padx=5, expand=True, fill='x')
            
            # Add hover effects
            if color == COLORS['accent'] or color == COLORS['accent_dim']:
                btn.bind('<Enter>', lambda e, b=btn: b.config(bg=COLORS['accent_hover']))
                btn.bind('<Leave>', lambda e, b=btn, c=color: b.config(bg=c))
            elif color == COLORS['success']:
                btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#56d364'))
                btn.bind('<Leave>', lambda e, b=btn: b.config(bg=COLORS['success']))
            elif color == COLORS['error']:
                btn.bind('<Enter>', lambda e, b=btn: b.config(bg='#ff6b6b'))
                btn.bind('<Leave>', lambda e, b=btn: b.config(bg=COLORS['error']))
        
        # Status label
        self.status_label = tk.Label(
            self,
            text="",
            font=('Segoe UI', 9),
            bg=COLORS['bg'],
            fg=COLORS['text_secondary']
        )
        self.status_label.pack(pady=10)
        
        # Auto-refresh
        self.refresh_models()
    
    def refresh_models(self):
        """Refresh installed models list"""
        self.tree.delete(*self.tree.get_children())
        
        try:
            models = self.manager.list_models()
            
            for model in models:
                self.tree.insert('', tk.END, values=(
                    model['name'],
                    model['size'],
                    model.get('modified', 'N/A')
                ))
            
            self.status_label.config(
                text=f"✅ {len(models)} models installed",
                fg=COLORS['success']
            )
        except Exception as e:
            self.status_label.config(
                text=f"❌ Error: {str(e)}",
                fg=COLORS['error']
            )
    
    def get_selected_model(self):
        """Get selected model name"""
        selection = self.tree.selection()
        if not selection:
            return None
        
        item = self.tree.item(selection[0])
        return item['values'][0]
    
    def run_model(self):
        """Run selected model in terminal"""
        model = self.get_selected_model()
        if not model:
            messagebox.showwarning("No Selection", "Please select a model")
            return
        
        # Check if it's an embedding model
        is_embedding = any(keyword in model.lower() for keyword in ['embed', 'minilm', 'bge', 'e5', 'nomic-embed'])
        
        if is_embedding:
            # Show info message for embedding models
            response = messagebox.askquestion(
                "Embedding Model",
                f"'{model}' is an embedding model and cannot run interactively.\n\n"
                "Embedding models require text input on the command line.\n\n"
                "Example usage:\n"
                f'  ollama run {model} "your text here"\n\n'
                "Would you like to open a terminal where you can type this command manually?",
                icon='info'
            )
            
            if response == 'yes':
                # Open terminal at the project directory
                if os.name == 'nt':  # Windows
                    subprocess.Popen(['start', 'cmd'], shell=True)
                else:  # Unix-like
                    subprocess.Popen(['x-terminal-emulator'])
                
                self.status_label.config(
                    text=f"💡 Terminal opened. Type: ollama run {model} \"your text\"",
                    fg=COLORS['text_secondary']
                )
            return
        
        # Open terminal with ollama run command for chat models
        if os.name == 'nt':  # Windows
            subprocess.Popen(['start', 'cmd', '/k', f'ollama run {model}'], shell=True)
        else:  # Unix-like
            subprocess.Popen(['x-terminal-emulator', '-e', f'ollama run {model}'])
        
        self.status_label.config(text=f"🚀 Launched {model} in terminal")
    
    def delete_model(self):
        """Delete selected model"""
        model = self.get_selected_model()
        if not model:
            messagebox.showwarning("No Selection", "Please select a model")
            return
        
        if messagebox.askyesno(
            "Delete Model",
            f"Delete '{model}'?\n\nThis action cannot be undone."
        ):
            self.app.run_ollama_command(f"ollama rm {model}", f"Deleting {model}...")
            self.after(2000, self.refresh_models)
    
    def show_model_info(self):
        """Show detailed model information"""
        model = self.get_selected_model()
        if not model:
            messagebox.showwarning("No Selection", "Please select a model")
            return
        
        self.app.run_ollama_command(f"ollama show {model}", f"Model Info: {model}")


class TemplateGeneratorTab(ttk.Frame):
    """Tab for generating starter templates"""
    
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.manager = ModelManager()
        
        self.create_widgets()
    
    def create_widgets(self):
        """Create generator interface with scrolling"""
        # Header (fixed, not scrollable)
        header = tk.Label(
            self,
            text="✨ Generate Starter Templates",
            font=('Segoe UI', 18, 'bold'),
            bg=COLORS['bg'],
            fg=COLORS['accent']
        )
        header.pack(pady=15, fill='x')
        
        # Create scrollable canvas
        canvas_container = tk.Frame(self, bg=COLORS['bg'])
        canvas_container.pack(fill='both', expand=True)
        
        canvas = tk.Canvas(
            canvas_container,
            bg=COLORS['bg'],
            highlightthickness=0,
            borderwidth=0
        )
        scrollbar = tk.Scrollbar(canvas_container, orient='vertical', command=canvas.yview)
        
        # Scrollable frame inside canvas
        self.scrollable_frame = tk.Frame(canvas, bg=COLORS['bg'])
        self.scrollable_frame.bind(
            '<Configure>',
            lambda e: canvas.configure(scrollregion=canvas.bbox('all'))
        )
        
        window_id = canvas.create_window((0, 0), window=self.scrollable_frame, anchor='nw')
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Make scrollable frame expand to canvas width
        def _configure_canvas(event):
            canvas.itemconfig(window_id, width=event.width)
        canvas.bind('<Configure>', _configure_canvas)
        
        # Pack canvas and scrollbar
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')
        
        # Enable mouse wheel scrolling
        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        
        # Main container (now inside scrollable frame)
        main_frame = tk.Frame(self.scrollable_frame, bg=COLORS['bg'])
        main_frame.pack(fill='both', expand=True, padx=40, pady=10)
        
        # Configure grid for responsive two-column layout
        main_frame.grid_columnconfigure(0, weight=1, minsize=400)
        main_frame.grid_columnconfigure(1, weight=1, minsize=400)
        
        # Model selection (left column)
        model_frame = tk.LabelFrame(
            main_frame,
            text="Select Model",
            font=('Segoe UI', 11, 'bold'),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent'],
            relief='flat',
            borderwidth=2
        )
        model_frame.grid(row=0, column=0, sticky='nsew', padx=(0, 10), pady=10)
        
        self.model_var = tk.StringVar()
        self.model_combo = ttk.Combobox(
            model_frame,
            textvariable=self.model_var,
            font=('Segoe UI', 11),
            state='readonly',
            height=15
        )
        self.model_combo.pack(padx=25, pady=20, fill='x', ipady=8)
        
        refresh_model_btn = tk.Button(
            model_frame,
            text="🔄 Refresh Models",
            command=self.refresh_models,
            bg=COLORS['bg_hover'],
            fg=COLORS['text'],
            font=('Segoe UI', 9),
            relief='flat',
            cursor='hand2',
            padx=15,
            pady=6,
            borderwidth=0,
            activebackground=COLORS['accent_dim']
        )
        refresh_model_btn.pack(padx=25, pady=(0, 15))
        
        # Template selection (right column)
        template_frame = tk.LabelFrame(
            main_frame,
            text="Select Template Type",
            font=('Segoe UI', 11, 'bold'),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent'],
            relief='flat',
            borderwidth=2
        )
        template_frame.grid(row=0, column=1, sticky='nsew', padx=(10, 0), pady=10)
        
        self.templates = [
            ("Simple Chat", "chat", "Basic conversational interface"),
            ("Custom Model", "custom", "Customizable with hooks"),
            ("Streaming Chat", "streaming", "Real-time responses"),
            ("Experimentation", "experiment", "Test different settings"),
            ("Integration", "integration", "Integrate into your app"),
            ("Tkinter GUI", "tkinter", "🎨 Desktop GUI"),
            ("Tkinter Advanced", "tkinter_advanced", "🎨 Advanced GUI"),
        ]
        
        self.template_var = tk.StringVar(value="chat")
        
        # Add scrollable frame for templates
        canvas_frame = tk.Frame(template_frame, bg=COLORS['bg_secondary'])
        canvas_frame.pack(fill='both', expand=True, padx=25, pady=15)
        
        for name, value, desc in self.templates:
            frame = tk.Frame(canvas_frame, bg=COLORS['bg_secondary'])
            frame.pack(fill='x', pady=3)
            
            rb = tk.Radiobutton(
                frame,
                text=f"{name} - {desc}",
                variable=self.template_var,
                value=value,
                font=('Segoe UI', 10),
                bg=COLORS['bg_secondary'],
                fg=COLORS['text'],
                selectcolor=COLORS['bg'],
                activebackground=COLORS['bg_secondary'],
                activeforeground=COLORS['accent'],
                cursor='hand2',
                padx=5,
                pady=4
            )
            rb.pack(anchor='w', pady=1, padx=5)
        
        # Filename (full width below)
        filename_frame = tk.LabelFrame(
            main_frame,
            text="Output Filename",
            font=('Segoe UI', 11, 'bold'),
            bg=COLORS['bg_secondary'],
            fg=COLORS['accent'],
            relief='flat',
            borderwidth=2
        )
        filename_frame.grid(row=1, column=0, columnspan=2, sticky='ew', pady=15)
        
        fn_inner = tk.Frame(filename_frame, bg=COLORS['bg_secondary'])
        fn_inner.pack(fill='x', padx=25, pady=20)
        
        self.filename_var = tk.StringVar(value="my_otk_app.py")
        filename_entry = tk.Entry(
            fn_inner,
            textvariable=self.filename_var,
            font=('Segoe UI', 11),
            bg=COLORS['bg'],
            fg=COLORS['text'],
            insertbackground=COLORS['accent'],
            relief='flat',
            borderwidth=0,
            highlightthickness=1,
            highlightbackground=COLORS['border'],
            highlightcolor=COLORS['accent']
        )
        filename_entry.pack(side='left', fill='x', expand=True, padx=(0, 15), ipady=8)
        
        browse_btn = tk.Button(
            fn_inner,
            text="📁 Browse",
            command=self.browse_file,
            bg=COLORS['bg_hover'],
            fg=COLORS['text'],
            font=('Segoe UI', 10),
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=10,
            borderwidth=0,
            activebackground=COLORS['accent_dim']
        )
        browse_btn.pack(side='right')
        
        # Generate button - Large and prominent with proper spacing (full width)
        generate_btn_container = tk.Frame(main_frame, bg=COLORS['bg'])
        generate_btn_container.grid(row=2, column=0, columnspan=2, sticky='ew', pady=30)
        
        self.generate_btn = tk.Button(
            generate_btn_container,
            text="🚀  Generate Template",
            command=self.generate_template,
            bg=COLORS['accent'],
            fg=COLORS['text_bright'],
            font=('Segoe UI', 14, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=70,
            pady=20,
            borderwidth=0,
            activebackground=COLORS['accent_hover'],
            activeforeground=COLORS['text_bright'],
            width=25
        )
        self.generate_btn.pack(expand=True)
        
        # Add hover effect
        self.generate_btn.bind('<Enter>', lambda e: self.generate_btn.config(bg=COLORS['accent_hover']))
        self.generate_btn.bind('<Leave>', lambda e: self.generate_btn.config(bg=COLORS['accent']))
        
        # Status label (in scrollable area, full width)
        self.status_label = tk.Label(
            main_frame,
            text="",
            font=('Segoe UI', 10),
            bg=COLORS['bg'],
            fg=COLORS['text_secondary'],
            wraplength=900
        )
        self.status_label.grid(row=3, column=0, columnspan=2, pady=15)
        
        # Add some bottom padding
        bottom_spacer = tk.Frame(main_frame, bg=COLORS['bg'], height=30)
        bottom_spacer.grid(row=4, column=0, columnspan=2)
        
        # Initial refresh
        self.refresh_models()
    
    def refresh_models(self):
        """Refresh available models"""
        try:
            models = self.manager.list_models()
            model_names = [m['name'] for m in models]
            self.model_combo['values'] = model_names
            
            if model_names:
                self.model_combo.current(0)
                self.status_label.config(
                    text=f"✅ {len(model_names)} models available",
                    fg=COLORS['success']
                )
            else:
                self.status_label.config(
                    text="⚠️  No models installed. Go to 'Browse Models' tab to install one.",
                    fg=COLORS['warning']
                )
        except Exception as e:
            self.status_label.config(
                text=f"❌ Error: {str(e)}",
                fg=COLORS['error']
            )
    
    def browse_file(self):
        """Browse for output file location"""
        filename = filedialog.asksaveasfilename(
            defaultextension=".py",
            filetypes=[("Python files", "*.py"), ("All files", "*.*")]
        )
        if filename:
            self.filename_var.set(filename)
    
    def generate_template(self):
        """Generate the selected template"""
        model = self.model_var.get()
        if not model:
            messagebox.showwarning("No Model", "Please select a model")
            return
        
        template_type = self.template_var.get()
        filename = self.filename_var.get()
        
        if not filename:
            messagebox.showwarning("No Filename", "Please enter a filename")
            return
        
        # Check if file exists
        if os.path.exists(filename):
            if not messagebox.askyesno(
                "File Exists",
                f"'{filename}' already exists. Overwrite?"
            ):
                return
        
        try:
            # Import the template generator from create_starter.py
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from create_starter import create_template
            
            # Find template name
            template_name = next(t[0] for t in self.templates if t[1] == template_type)
            
            # Generate
            create_template(model, template_name, template_type, filename)
            
            self.status_label.config(
                text=f"✅ Successfully generated '{filename}' with {template_name} template!",
                fg=COLORS['success']
            )
            
            # Show success dialog
            if messagebox.askyesno(
                "Template Created",
                f"Template created successfully!\n\nFile: {filename}\nModel: {model}\nType: {template_name}\n\nOpen containing folder?"
            ):
                folder = os.path.dirname(os.path.abspath(filename))
                if os.name == 'nt':  # Windows
                    os.startfile(folder)
                else:  # Unix-like
                    subprocess.Popen(['xdg-open', folder])
        
        except Exception as e:
            messagebox.showerror("Generation Error", f"Failed to generate template:\n\n{str(e)}")
            self.status_label.config(
                text=f"❌ Error: {str(e)}",
                fg=COLORS['error']
            )


class OTKGUI:
    """Main application window"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Open OTK - Ollama Toolkit")
        self.root.geometry("1200x820")
        self.root.minsize(900, 650)
        self.root.configure(bg=COLORS['bg'])
        
        # Make window resizable
        self.root.resizable(True, True)
        
        # Start maximized (fullscreen)
        self.root.state('zoomed')
        
        # Set window icon
        try:
            # Try to load icon file from project directory
            icon_path = os.path.join(os.path.dirname(__file__), 'icon.ico')
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
            else:
                # Try PNG format with iconphoto
                icon_png = os.path.join(os.path.dirname(__file__), 'icon.png')
                if os.path.exists(icon_png):
                    icon = tk.PhotoImage(file=icon_png)
                    self.root.iconphoto(True, icon)
        except Exception as e:
            pass
        
        # DPI awareness for Windows (makes GUI sharper)
        try:
            if os.name == 'nt':
                import ctypes
                ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except:
            pass
        
        # Configure style
        self.setup_style()
        
        # Check Ollama
        self.check_ollama()
        
        # Create UI
        self.create_widgets()
        
        # Terminal window
        self.terminal_window = None
    
    def setup_style(self):
        """Setup ttk styles"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure notebook tabs with better styling
        style.configure(
            'TNotebook',
            background=COLORS['bg'],
            borderwidth=0,
            tabmargins=[0, 0, 0, 0]
        )
        style.configure(
            'TNotebook.Tab',
            background=COLORS['bg_secondary'],
            foreground=COLORS['text'],
            padding=[25, 12],
            font=('Segoe UI', 11, 'bold'),
            borderwidth=0
        )
        style.map(
            'TNotebook.Tab',
            background=[('selected', COLORS['accent'])],
            foreground=[('selected', COLORS['text_bright'])],
            expand=[('selected', [1, 1, 1, 0])]
        )
        
        # Configure treeview
        style.configure(
            'Treeview',
            background=COLORS['bg_secondary'],
            foreground=COLORS['text'],
            fieldbackground=COLORS['bg_secondary'],
            borderwidth=0,
            font=('Segoe UI', 10),
            rowheight=30
        )
        style.configure(
            'Treeview.Heading',
            background=COLORS['bg_tertiary'],
            foreground=COLORS['accent'],
            font=('Segoe UI', 11, 'bold'),
            borderwidth=0,
            relief='flat'
        )
        style.map('Treeview',
            background=[('selected', COLORS['accent'])],
            foreground=[('selected', COLORS['text_bright'])]
        )
        
        # All frames
        style.configure('TFrame', background=COLORS['bg'])
        
        # Combobox styling
        style.configure(
            'TCombobox',
            fieldbackground=COLORS['bg_secondary'],
            background=COLORS['bg_secondary'],
            foreground=COLORS['text'],
            arrowcolor=COLORS['accent'],
            borderwidth=1,
            relief='flat'
        )
        style.map('TCombobox',
            fieldbackground=[('readonly', COLORS['bg_secondary'])],
            selectbackground=[('readonly', COLORS['accent'])],
            selectforeground=[('readonly', COLORS['text_bright'])]
        )
    
    def check_ollama(self):
        """Check if Ollama is running"""
        try:
            client = OllamaClient()
            if not client.is_running():
                messagebox.showwarning(
                    "Ollama Not Running",
                    "Ollama is not running!\n\nPlease start Ollama before using this tool.\n\n" +
                    "Download from: https://ollama.ai"
                )
        except Exception as e:
            messagebox.showerror(
                "Connection Error",
                f"Could not connect to Ollama:\n\n{str(e)}"
            )
    
    def create_widgets(self):
        """Create main UI"""
        # Header with gradient effect (simulated with frame)
        header_frame = tk.Frame(self.root, bg=COLORS['bg_tertiary'], height=100)
        header_frame.pack(fill='x', pady=0)
        header_frame.pack_propagate(False)
        
        title = tk.Label(
            header_frame,
            text="Open OTK",
            font=('Segoe UI', 22, 'bold'),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_bright'],
            pady=15
        )
        title.pack(side='top', pady=(20, 5))
        
        subtitle = tk.Label(
            header_frame,
            text="Open Ollama Toolkit • Professional Template Generator",
            font=('Segoe UI', 11),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_secondary'],
            pady=0
        )
        subtitle.pack(side='top', pady=(0, 15))
        
        # Notebook (tabs)
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=0, pady=0)
        
        # Create tabs
        self.browser_tab = ModelBrowserTab(self.notebook, self)
        self.manager_tab = ModelManagerTab(self.notebook, self)
        self.generator_tab = TemplateGeneratorTab(self.notebook, self)
        
        self.notebook.add(self.browser_tab, text="🌐 Browse Models")
        self.notebook.add(self.manager_tab, text="🔧 Manage Models")
        self.notebook.add(self.generator_tab, text="✨ Generate Template")
        
        # Footer with better styling
        footer = tk.Frame(self.root, bg=COLORS['bg_tertiary'], height=40)
        footer.pack(fill='x', side='bottom')
        footer.pack_propagate(False)
        
        # Left side - developer info
        footer_label = tk.Label(
            footer,
            text="Developed by Md. Abid Hasan Rafi • Powered by AI Extension!",
            font=('Segoe UI', 9),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text_secondary']
        )
        footer_label.pack(side='left', padx=20)
        
        # Right side - GitHub link
        github_frame = tk.Frame(footer, bg=COLORS['bg_tertiary'])
        github_frame.pack(side='right', padx=20)
        
        github_label = tk.Label(
            github_frame,
            text="⭐ GitHub",
            font=('Segoe UI', 9, 'bold'),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['accent'],
            cursor='hand2'
        )
        github_label.pack()
        
        def open_github(event):
            webbrowser.open("https://github.com/aiextension/open-otk")
        
        github_label.bind('<Button-1>', open_github)
        github_label.bind('<Enter>', lambda e: github_label.config(fg=COLORS['accent_hover']))
        github_label.bind('<Leave>', lambda e: github_label.config(fg=COLORS['accent']))
    
    def install_model(self, model_name):
        """Install a model"""
        self.run_ollama_command(
            f"ollama pull {model_name}",
            f"Installing {model_name}"
        )
        
        # Refresh manager tab after installation
        self.root.after(3000, self.manager_tab.refresh_models)
        self.root.after(3000, self.generator_tab.refresh_models)
    
    def run_ollama_command(self, command, title="Ollama Command"):
        """Run an Ollama command in a popup terminal"""
        # Create terminal window
        terminal = tk.Toplevel(self.root)
        terminal.title(title)
        terminal.geometry("800x500")
        terminal.configure(bg=COLORS['bg'])
        
        # Header
        header = tk.Label(
            terminal,
            text=f"⚡ {title}",
            font=('Segoe UI', 12, 'bold'),
            bg=COLORS['bg'],
            fg=COLORS['accent']
        )
        header.pack(pady=10)
        
        # Command label
        cmd_label = tk.Label(
            terminal,
            text=f"$ {command}",
            font=('Consolas', 9),
            bg=COLORS['bg_secondary'],
            fg=COLORS['text_secondary'],
            anchor='w'
        )
        cmd_label.pack(fill='x', padx=10, pady=5)
        
        # Output text
        output = scrolledtext.ScrolledText(
            terminal,
            font=('Consolas', 9),
            bg=COLORS['bg_tertiary'],
            fg=COLORS['text'],
            insertbackground=COLORS['accent'],
            relief='flat',
            wrap='word'
        )
        output.pack(fill='both', expand=True, padx=10, pady=10)
        
        # Close button
        close_btn = tk.Button(
            terminal,
            text="✕ Close",
            command=terminal.destroy,
            bg=COLORS['error'],
            fg=COLORS['text_bright'],
            font=('Segoe UI', 9, 'bold'),
            relief='flat',
            cursor='hand2',
            padx=20,
            pady=8,
            borderwidth=0,
            activebackground='#ff6b6b'
        )
        close_btn.pack(pady=10)
        
        # Run command in thread
        def run():
            try:
                process = subprocess.Popen(
                    command,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    bufsize=1
                )
                
                for line in process.stdout:
                    output.insert(tk.END, line)
                    output.see(tk.END)
                    output.update()
                
                process.wait()
                
                if process.returncode == 0:
                    output.insert(tk.END, "\n✅ Command completed successfully!\n")
                    output.tag_config('success', foreground=COLORS['success'])
                    output.insert(tk.END, "\n", 'success')
                else:
                    output.insert(tk.END, f"\n❌ Command failed with code {process.returncode}\n")
                    output.tag_config('error', foreground=COLORS['error'])
                    output.insert(tk.END, "\n", 'error')
                
                output.see(tk.END)
                
            except Exception as e:
                output.insert(tk.END, f"\n❌ Error: {str(e)}\n")
                output.see(tk.END)
        
        threading.Thread(target=run, daemon=True).start()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()


def main():
    """Main entry point"""
    # Check dependencies
    try:
        import requests
        from bs4 import BeautifulSoup
    except ImportError:
        print("❌ Missing dependencies!")
        print("\nPlease install required packages:")
        print("  pip install requests beautifulsoup4")
        sys.exit(1)
    
    # Run GUI
    app = OTKGUI()
    app.run()


if __name__ == "__main__":
    main()
