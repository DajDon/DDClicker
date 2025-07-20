import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import random
import json
import os
from pynput import mouse, keyboard
from pynput.mouse import Button, Listener as MouseListener
from pynput.keyboard import Key, KeyCode, Listener as KeyboardListener

class AdvancedAutoClicker:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DDClicker")
        self.root.geometry("700x900")
        self.root.resizable(False, False)

        

        
        
        # Színpaletta
        self.colors = {
            'bg': '#0d1117', 'surface': '#161b22', 'primary': '#238636', 
            'secondary': '#1f6feb', 'accent': '#f85149', 'text': '#f0f6fc', 
            'text_secondary': '#8b949e', 'border': '#30363d', 'hover': '#21262d',
            'warning': '#f79009', 'success': '#3fb950'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # Állapot változók
        self.is_clicking = False
        self.click_thread = None
        self.mouse_controller = mouse.Controller()
        self.keyboard_listener = None
        self.current_keys_pressed = set()
        
        # Beállítások
        self.cps = tk.DoubleVar(value=10.0)
        self.current_cps = 10.0  # Dinamikus CPS
        self.click_button = tk.StringVar(value="left")
        self.selected_keybind = tk.StringVar(value="F6")
        self.variance_percentage = tk.DoubleVar(value=15.0)
        
        # Auto pause beállítások
        self.auto_pause_enabled = tk.BooleanVar(value=True)
        self.pause_chance = tk.DoubleVar(value=5.0)
        self.pause_min_duration = tk.DoubleVar(value=0.5)
        self.pause_max_duration = tk.DoubleVar(value=2.0)
        
        # CPS változás beállítások
        self.cps_change_chance = 8.0  # % esély CPS változásra
        self.last_cps_change = time.time()
        
        # Statisztikák
        self.total_clicks = 0
        self.session_start_time = None
        
        # Keybind opciók
        self.keybind_options = [
            "F1", "F2", "F3", "F4", "F5", "F6", "F7", "F8", "F9", "F10", "F11", "F12",
            "Ctrl+F1", "Ctrl+F2", "Ctrl+F3", "Ctrl+F4", "Ctrl+F5", "Ctrl+F6",
            "Alt+F1", "Alt+F2", "Alt+F3", "Alt+F4", "Alt+F5", "Alt+F6",
            "Shift+F1", "Shift+F2", "Shift+F3", "Shift+F4", "Shift+F5", "Shift+F6"
        ]
        
        # Mentés könyvtár
        self.config_dir = "autoclicker_configs"
        if not os.path.exists(self.config_dir):
            os.makedirs(self.config_dir)
        
        # Add a scrollable canvas with a scrollbar
        self.canvas = tk.Canvas(self.root, bg=self.colors['bg'])
        self.scrollbar = ttk.Scrollbar(self.root, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=self.colors['bg'])

        # Configure the canvas
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        # Pack the scrollbar and canvas
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        # Add mouse wheel scrolling
        self.canvas.bind("<Enter>", lambda e: self.canvas.bind_all("<MouseWheel>", self.on_mousewheel))
        self.canvas.bind("<Leave>", lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.setup_ui()
        self.setup_keyboard_listener()
        self.update_stats()
        
    def setup_ui(self):
        style = ttk.Style()
        style.theme_use('clam')
        
        main_frame = tk.Frame(self.scrollable_frame, bg=self.colors['bg'])
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # Header
        header_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        header_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(header_frame, text="⚡ DDClicker", font=('Segoe UI', 24, 'bold'),
                fg=self.colors['secondary'], bg=self.colors['bg']).pack()
        tk.Label(header_frame, text="Professzionális kattintási automatizálás", font=('Segoe UI', 11),
                fg=self.colors['text_secondary'], bg=self.colors['bg']).pack(pady=(5, 0))
        
        # Recommendations panel
        self.create_recommendations_section(main_frame)
        
        # Status panel
        status_frame = tk.Frame(main_frame, bg=self.colors['surface'], relief='solid', bd=1)
        status_frame.pack(fill='x', pady=(0, 15))
        inner_status = tk.Frame(status_frame, bg=self.colors['surface'])
        inner_status.pack(fill='x', padx=15, pady=15)
        
        self.status_label = tk.Label(inner_status, text="🔴 Leállítva", font=('Segoe UI', 14, 'bold'),
                                   fg=self.colors['accent'], bg=self.colors['surface'])
        self.status_label.pack()
        self.status_detail = tk.Label(inner_status, text="Nyomd meg a kiválasztott billentyűt az indításhoz",
                                    font=('Segoe UI', 10), fg=self.colors['text_secondary'], bg=self.colors['surface'])
        self.status_detail.pack(pady=(5, 0))
        
        # Click settings
        click_frame = self.create_section_frame(main_frame, "🖱️ Kattintási beállítások")
        
        cps_frame = tk.Frame(click_frame, bg=self.colors['surface'])
        cps_frame.pack(fill='x', pady=10)
        
        cps_label_frame = tk.Frame(cps_frame, bg=self.colors['surface'])
        cps_label_frame.pack(fill='x')
        tk.Label(cps_label_frame, text="Kattintási sebesség (CPS):", font=('Segoe UI', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['surface']).pack(side='left')
        self.cps_value_label = tk.Label(cps_label_frame, text="10.0", font=('Segoe UI', 10, 'bold'),
                                      fg=self.colors['secondary'], bg=self.colors['surface'])
        self.cps_value_label.pack(side='right')
        
        self.cps_scale = tk.Scale(cps_frame, from_=1.0, to=100.0, resolution=0.1, orient='horizontal',
                                variable=self.cps, bg=self.colors['surface'], fg=self.colors['text'],
                                activebackground=self.colors['secondary'], highlightthickness=0, bd=0,
                                length=400, command=self.update_cps_label)
        self.cps_scale.pack(fill='x')
        
        # Mouse button selection
        button_frame = tk.Frame(click_frame, bg=self.colors['surface'])
        button_frame.pack(fill='x', pady=10)
        tk.Label(button_frame, text="Egérgomb:", font=('Segoe UI', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['surface']).pack(anchor='w')
        
        button_options = tk.Frame(button_frame, bg=self.colors['surface'])
        button_options.pack(fill='x', pady=(5, 0))
        tk.Radiobutton(button_options, text="🖱️ Bal gomb", variable=self.click_button, value="left",
                      font=('Segoe UI', 9), fg=self.colors['text'], bg=self.colors['surface'],
                      selectcolor=self.colors['hover']).pack(side='left')
        tk.Radiobutton(button_options, text="🖱️ Jobb gomb", variable=self.click_button, value="right",
                      font=('Segoe UI', 9), fg=self.colors['text'], bg=self.colors['surface'],
                      selectcolor=self.colors['hover']).pack(side='left', padx=(20, 0))
        
        # Keybind settings
        keybind_frame = self.create_section_frame(main_frame, "⌨️ Billentyű beállítások")
        
        kb_frame = tk.Frame(keybind_frame, bg=self.colors['surface'])
        kb_frame.pack(fill='x', pady=10)
        tk.Label(kb_frame, text="Gyorsbillentyű:", font=('Segoe UI', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['surface']).pack(anchor='w')
        
        combo_frame = tk.Frame(kb_frame, bg=self.colors['surface'])
        combo_frame.pack(fill='x', pady=(5, 0))
        self.keybind_combo = ttk.Combobox(combo_frame, textvariable=self.selected_keybind,
                                        values=self.keybind_options, state='readonly',
                                        font=('Segoe UI', 10), width=15)
        self.keybind_combo.pack(side='left')
        
        current_key_label = tk.Label(combo_frame, text=f"Aktív: {self.selected_keybind.get()}",
                                   font=('Segoe UI', 10), fg=self.colors['secondary'], bg=self.colors['surface'])
        current_key_label.pack(side='right')
        self.selected_keybind.trace('w', lambda *args: current_key_label.config(text=f"Aktív: {self.selected_keybind.get()}"))
        
        # Advanced settings
        adv_frame = self.create_section_frame(main_frame, "⚙️ Speciális beállítások")
        
        # Variance
        variance_frame = tk.Frame(adv_frame, bg=self.colors['surface'])
        variance_frame.pack(fill='x', pady=10)
        
        var_label_frame = tk.Frame(variance_frame, bg=self.colors['surface'])
        var_label_frame.pack(fill='x')
        tk.Label(var_label_frame, text="Természetes variáció (%):", font=('Segoe UI', 10, 'bold'),
                fg=self.colors['text'], bg=self.colors['surface']).pack(side='left')
        self.variance_value_label = tk.Label(var_label_frame, text="15%", font=('Segoe UI', 10, 'bold'),
                                           fg=self.colors['secondary'], bg=self.colors['surface'])
        self.variance_value_label.pack(side='right')
        
        self.variance_scale = tk.Scale(variance_frame, from_=0, to=50, resolution=1, orient='horizontal',
                                     variable=self.variance_percentage, bg=self.colors['surface'],
                                     fg=self.colors['text'], activebackground=self.colors['secondary'],
                                     highlightthickness=0, bd=0, command=self.update_variance_label)
        self.variance_scale.pack(fill='x', pady=(5, 0))
        
        # Auto pause
        pause_frame = tk.Frame(adv_frame, bg=self.colors['surface'])
        pause_frame.pack(fill='x', pady=10)
        tk.Checkbutton(pause_frame, text="🔄 Automatikus véletlenszerű szünet", variable=self.auto_pause_enabled,
                      font=('Segoe UI', 10, 'bold'), fg=self.colors['text'], bg=self.colors['surface'],
                      selectcolor=self.colors['hover']).pack(anchor='w')
        
        pause_settings = tk.Frame(pause_frame, bg=self.colors['surface'])
        pause_settings.pack(fill='x', pady=(10, 0))
        
        chance_frame = tk.Frame(pause_settings, bg=self.colors['surface'])
        chance_frame.pack(fill='x', pady=5)
        tk.Label(chance_frame, text="Szünet esélye (%):", font=('Segoe UI', 9),
                fg=self.colors['text'], bg=self.colors['surface']).pack(side='left')
        tk.Spinbox(chance_frame, from_=0.1, to=20, increment=0.1, textvariable=self.pause_chance,
                  width=8, font=('Segoe UI', 9), bg=self.colors['hover'], fg=self.colors['text']).pack(side='right')
        
        duration_frame = tk.Frame(pause_settings, bg=self.colors['surface'])
        duration_frame.pack(fill='x', pady=5)
        tk.Label(duration_frame, text="Szünet időtartam (s):", font=('Segoe UI', 9),
                fg=self.colors['text'], bg=self.colors['surface']).pack(anchor='w')
        
        dur_inner = tk.Frame(duration_frame, bg=self.colors['surface'])
        dur_inner.pack(fill='x', pady=(5, 0))
        tk.Label(dur_inner, text="Min:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['surface']).pack(side='left')
        tk.Spinbox(dur_inner, from_=0.1, to=5, increment=0.1, textvariable=self.pause_min_duration,
                  width=6, font=('Segoe UI', 8), bg=self.colors['hover'], fg=self.colors['text']).pack(side='left', padx=(5, 15))
        tk.Label(dur_inner, text="Max:", font=('Segoe UI', 8),
                fg=self.colors['text'], bg=self.colors['surface']).pack(side='left')
        tk.Spinbox(dur_inner, from_=0.1, to=10, increment=0.1, textvariable=self.pause_max_duration,
                  width=6, font=('Segoe UI', 8), bg=self.colors['hover'], fg=self.colors['text']).pack(side='left', padx=(5, 0))
        
        # Save/Load section
        self.create_save_load_section(main_frame)
        
        # Control panel
        control_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        control_frame.pack(fill='x', pady=20)
        
        self.toggle_button = tk.Button(control_frame, text="🚀 INDÍTÁS", font=('Segoe UI', 14, 'bold'),
                                     bg=self.colors['primary'], fg='white', activebackground='#2ea043',
                                     width=20, height=2, bd=0, command=self.toggle_clicking)
        self.toggle_button.pack()
        
        info_frame = tk.Frame(control_frame, bg=self.colors['bg'])
        info_frame.pack(pady=(10, 0))
        self.keybind_info = tk.Label(info_frame, text=f"Gyorsbillentyű: {self.selected_keybind.get()}",
                                   font=('Segoe UI', 11), fg=self.colors['text_secondary'], bg=self.colors['bg'])
        self.keybind_info.pack()
        self.selected_keybind.trace('w', lambda *args: self.keybind_info.config(text=f"Gyorsbillentyű: {self.selected_keybind.get()}"))
        
        # Stats panel
        stats_frame = self.create_section_frame(main_frame, "📊 Statisztikák")
        
        stats_grid = tk.Frame(stats_frame, bg=self.colors['surface'])
        stats_grid.pack(fill='x', pady=10)
        
        self.total_clicks_label = tk.Label(stats_grid, text="Összes kattintás: 0", font=('Segoe UI', 10),
                                         fg=self.colors['text'], bg=self.colors['surface'])
        self.total_clicks_label.pack(anchor='w')
        
        self.actual_cps_label = tk.Label(stats_grid, text="Tényleges CPS: 0.0", font=('Segoe UI', 10),
                                       fg=self.colors['text'], bg=self.colors['surface'])
        self.actual_cps_label.pack(anchor='w', pady=(5, 0))
        
        self.session_time_label = tk.Label(stats_grid, text="Munkamenet: 00:00:00", font=('Segoe UI', 10),
                                         fg=self.colors['text'], bg=self.colors['surface'])
        self.session_time_label.pack(anchor='w', pady=(5, 0))
        
        # CPS változások mutatása
        self.dynamic_cps_label = tk.Label(stats_grid, text="Dinamikus CPS: 10.0", font=('Segoe UI', 10),
                                        fg=self.colors['secondary'], bg=self.colors['surface'])
        self.dynamic_cps_label.pack(anchor='w', pady=(5, 0))
        
        tk.Button(stats_grid, text="🔄 Statisztikák törlése", font=('Segoe UI', 9),
                 bg=self.colors['accent'], fg='white', bd=0, command=self.reset_stats).pack(anchor='e', pady=(10, 0))
    
    def create_recommendations_section(self, parent):
        rec_frame = self.create_section_frame(parent, "💡 Ajánlott beállítások")
        
        rec_text = tk.Label(rec_frame, text="Optimális beállítások a legtöbb játékhoz:", 
                          font=('Segoe UI', 10, 'bold'), fg=self.colors['text'], bg=self.colors['surface'])
        rec_text.pack(anchor='w', pady=(0, 10))
        
        # Recommendation buttons
        rec_buttons_frame = tk.Frame(rec_frame, bg=self.colors['surface'])
        rec_buttons_frame.pack(fill='x', pady=5)
        
        # Gaming recommendation
        game_btn = tk.Button(rec_buttons_frame, text="🎮 Játék (CPS: 25, Variáció: 2%)", 
                           font=('Segoe UI', 9, 'bold'), bg=self.colors['warning'], fg='white',
                           bd=0, command=self.apply_gaming_preset)
        game_btn.pack(side='left', padx=(0, 10))
        
        # PvP recommendation
        pvp_btn = tk.Button(rec_buttons_frame, text="⚔️ PvP (CPS: 15, Variáció: 5%)", 
                          font=('Segoe UI', 9, 'bold'), bg=self.colors['accent'], fg='white',
                          bd=0, command=self.apply_pvp_preset)
        pvp_btn.pack(side='left', padx=(0, 10))
        
        # Safe recommendation
        safe_btn = tk.Button(rec_buttons_frame, text="🛡️ Biztonságos (CPS: 8, Variáció: 10%)", 
                           font=('Segoe UI', 9, 'bold'), bg=self.colors['success'], fg='white',
                           bd=0, command=self.apply_safe_preset)
        safe_btn.pack(side='left')
    
    def create_save_load_section(self, parent):
        save_frame = self.create_section_frame(parent, "💾 Mentés és betöltés")
        
        # Save section
        save_section = tk.Frame(save_frame, bg=self.colors['surface'])
        save_section.pack(fill='x', pady=(0, 10))
        
        save_label = tk.Label(save_section, text="Konfiguráció mentése:", font=('Segoe UI', 10, 'bold'),
                            fg=self.colors['text'], bg=self.colors['surface'])
        save_label.pack(anchor='w', pady=(0, 5))
        
        save_input_frame = tk.Frame(save_section, bg=self.colors['surface'])
        save_input_frame.pack(fill='x')
        
        self.config_name_var = tk.StringVar(value="Alap konfiguráció")
        config_entry = tk.Entry(save_input_frame, textvariable=self.config_name_var, 
                              font=('Segoe UI', 10), bg=self.colors['hover'], fg=self.colors['text'],
                              width=30)
        config_entry.pack(side='left', padx=(0, 10))
        
        save_btn = tk.Button(save_input_frame, text="💾 Mentés", font=('Segoe UI', 9, 'bold'),
                           bg=self.colors['primary'], fg='white', bd=0, command=self.save_config)
        save_btn.pack(side='left')
        
        # Load section
        load_section = tk.Frame(save_frame, bg=self.colors['surface'])
        load_section.pack(fill='x')
        
        load_label = tk.Label(load_section, text="Mentett konfigurációk:", font=('Segoe UI', 10, 'bold'),
                            fg=self.colors['text'], bg=self.colors['surface'])
        load_label.pack(anchor='w', pady=(0, 5))
        
        load_buttons_frame = tk.Frame(load_section, bg=self.colors['surface'])
        load_buttons_frame.pack(fill='x')
        
        refresh_btn = tk.Button(load_buttons_frame, text="🔄 Frissítés", font=('Segoe UI', 9),
                              bg=self.colors['secondary'], fg='white', bd=0, 
                              command=self.refresh_saved_configs)
        refresh_btn.pack(side='left', padx=(0, 10))
        
        # Scrollable frame for saved configs
        self.saved_configs_frame = tk.Frame(load_section, bg=self.colors['surface'])
        self.saved_configs_frame.pack(fill='x', pady=(10, 0))
        
        self.refresh_saved_configs()
    
    def apply_gaming_preset(self):
        self.cps.set(25.0)
        self.variance_percentage.set(2.0)
        self.auto_pause_enabled.set(True)
        self.pause_chance.set(3.0)
        messagebox.showinfo("Preset alkalmazva", "Játék preset beállítva!\nCPS: 25, Variáció: 2%")
    
    def apply_pvp_preset(self):
        self.cps.set(15.0)
        self.variance_percentage.set(5.0)
        self.auto_pause_enabled.set(True)
        self.pause_chance.set(7.0)
        messagebox.showinfo("Preset alkalmazva", "PvP preset beállítva!\nCPS: 15, Variáció: 5%")
    
    def apply_safe_preset(self):
        self.cps.set(8.0)
        self.variance_percentage.set(10.0)
        self.auto_pause_enabled.set(True)
        self.pause_chance.set(12.0)
        messagebox.showinfo("Preset alkalmazva", "Biztonságos preset beállítva!\nCPS: 8, Variáció: 10%")
    
    def save_config(self):
        config_name = self.config_name_var.get().strip()
        if not config_name:
            messagebox.showerror("Hiba", "Kérlek adj meg egy nevet a konfigurációnak!")
            return
        
        config = {
            'cps': self.cps.get(),
            'variance_percentage': self.variance_percentage.get(),
            'click_button': self.click_button.get(),
            'selected_keybind': self.selected_keybind.get(),
            'auto_pause_enabled': self.auto_pause_enabled.get(),
            'pause_chance': self.pause_chance.get(),
            'pause_min_duration': self.pause_min_duration.get(),
            'pause_max_duration': self.pause_max_duration.get(),
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
        }
        
        filename = f"{config_name.replace(' ', '_').replace('/', '_')}.json"
        filepath = os.path.join(self.config_dir, filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Siker", f"Konfiguráció mentve: {config_name}")
            self.refresh_saved_configs()
        except Exception as e:
            messagebox.showerror("Hiba", f"Mentés sikertelen: {str(e)}")
    
    def load_config(self, filename):
        filepath = os.path.join(self.config_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            self.cps.set(config.get('cps', 10.0))
            self.variance_percentage.set(config.get('variance_percentage', 15.0))
            self.click_button.set(config.get('click_button', 'left'))
            self.selected_keybind.set(config.get('selected_keybind', 'F6'))
            self.auto_pause_enabled.set(config.get('auto_pause_enabled', True))
            self.pause_chance.set(config.get('pause_chance', 5.0))
            self.pause_min_duration.set(config.get('pause_min_duration', 0.5))
            self.pause_max_duration.set(config.get('pause_max_duration', 2.0))
            
            config_name = filename.replace('.json', '').replace('_', ' ')
            messagebox.showinfo("Siker", f"Konfiguráció betöltve: {config_name}")
        except Exception as e:
            messagebox.showerror("Hiba", f"Betöltés sikertelen: {str(e)}")
    
    def delete_config(self, filename):
        if messagebox.askyesno("Megerősítés", f"Biztosan törölni szeretnéd ezt a konfigurációt?\n{filename.replace('.json', '').replace('_', ' ')}"):
            filepath = os.path.join(self.config_dir, filename)
            try:
                os.remove(filepath)
                messagebox.showinfo("Siker", "Konfiguráció törölve!")
                self.refresh_saved_configs()
            except Exception as e:
                messagebox.showerror("Hiba", f"Törlés sikertelen: {str(e)}")
    
    def refresh_saved_configs(self):
        # Clear existing config buttons
        for widget in self.saved_configs_frame.winfo_children():
            widget.destroy()
        
        if not os.path.exists(self.config_dir):
            return
        
        config_files = [f for f in os.listdir(self.config_dir) if f.endswith('.json')]
        
        if not config_files:
            no_configs = tk.Label(self.saved_configs_frame, text="Még nincsenek mentett konfigurációk",
                                font=('Segoe UI', 9), fg=self.colors['text_secondary'], bg=self.colors['surface'])
            no_configs.pack(anchor='w')
            return
        
        for filename in sorted(config_files):
            config_name = filename.replace('.json', '').replace('_', ' ')
            
            config_row = tk.Frame(self.saved_configs_frame, bg=self.colors['surface'])
            config_row.pack(fill='x', pady=2)
            
            name_label = tk.Label(config_row, text=config_name, font=('Segoe UI', 9),
                                fg=self.colors['text'], bg=self.colors['surface'])
            name_label.pack(side='left')
            
            delete_btn = tk.Button(config_row, text="🗑️", font=('Segoe UI', 8),
                                 bg=self.colors['accent'], fg='white', bd=0, width=3,
                                 command=lambda f=filename: self.delete_config(f))
            delete_btn.pack(side='right', padx=(5, 0))
            
            load_btn = tk.Button(config_row, text="📂 Betöltés", font=('Segoe UI', 8),
                               bg=self.colors['secondary'], fg='white', bd=0,
                               command=lambda f=filename: self.load_config(f))
            load_btn.pack(side='right')
    
    def create_section_frame(self, parent, title):
        container = tk.Frame(parent, bg=self.colors['bg'])
        container.pack(fill='x', pady=(0, 15))
        tk.Label(container, text=title, font=('Segoe UI', 12, 'bold'),
                fg=self.colors['secondary'], bg=self.colors['bg']).pack(anchor='w', pady=(0, 8))
        frame = tk.Frame(container, bg=self.colors['surface'], relief='solid', bd=1)
        frame.pack(fill='x')
        inner_frame = tk.Frame(frame, bg=self.colors['surface'])
        inner_frame.pack(fill='both', expand=True, padx=15, pady=15)
        return inner_frame
    
    def update_cps_label(self, value):
        self.cps_value_label.config(text=f"{float(value):.1f}")
        
    def update_variance_label(self, value):
        self.variance_value_label.config(text=f"{int(float(value))}%")
    
    def setup_keyboard_listener(self):
        def on_press(key):
            self.current_keys_pressed.add(key)
            if self.check_keybind_pressed():
                self.root.after(0, self.toggle_clicking)
        def on_release(key):
            self.current_keys_pressed.discard(key)
        
        self.keyboard_listener = KeyboardListener(on_press=on_press, on_release=on_release)
        self.keyboard_listener.start()
    
    def check_keybind_pressed(self):
        keybind = self.selected_keybind.get()
        
        if keybind.startswith('F') and not '+' in keybind:
            try:
                f_num = int(keybind[1:])
                f_key = getattr(Key, f'f{f_num}', None)
                return f_key in self.current_keys_pressed
            except:
                return False
        
        if '+' in keybind:
            parts = keybind.split('+')
            modifier = parts[0].lower()
            key_part = parts[1]
            
            modifier_pressed = False
            if modifier == 'ctrl':
                modifier_pressed = Key.ctrl_l in self.current_keys_pressed or Key.ctrl_r in self.current_keys_pressed
            elif modifier == 'alt':
                modifier_pressed = Key.alt_l in self.current_keys_pressed or Key.alt_r in self.current_keys_pressed
            elif modifier == 'shift':
                modifier_pressed = Key.shift_l in self.current_keys_pressed or Key.shift_r in self.current_keys_pressed
            
            if modifier_pressed and key_part.startswith('F'):
                try:
                    f_num = int(key_part[1:])
                    f_key = getattr(Key, f'f{f_num}', None)
                    return f_key in self.current_keys_pressed
                except:
                    return False
        return False
    
    def toggle_clicking(self):
        if self.is_clicking:
            self.stop_clicking()
        else:
            self.start_clicking()
    
    def start_clicking(self):
        if not self.is_clicking:
            self.is_clicking = True
            self.current_cps = self.cps.get()
            self.session_start_time = time.time()
            self.last_cps_change = time.time()
            
            self.status_label.config(text="🟢 Aktív", fg=self.colors['primary'])
            self.status_detail.config(text="Kattintás folyamatban...")
            self.toggle_button.config(text="⏹️ MEGÁLLÍTÁS", bg=self.colors['accent'])
            
            self.click_thread = threading.Thread(target=self.clicking_loop, daemon=True)
            self.click_thread.start()
    
    def stop_clicking(self):
        self.is_clicking = False
        self.status_label.config(text="🔴 Leállítva", fg=self.colors['accent'])
        self.status_detail.config(text="Nyomd meg a kiválasztott billentyűt az indításhoz")
        self.toggle_button.config(text="🚀 INDÍTÁS", bg=self.colors['primary'])
    
    def clicking_loop(self):
        last_click_times = []
        clicks_since_last_change = 0
        
        while self.is_clicking:
            try:
                # Dinamikus CPS változtatás
                current_time = time.time()
                if random.random() * 100 < self.cps_change_chance and clicks_since_last_change > 10:
                    # Kihagyás (0 CPS rövid időre)
                    if random.random() < 0.3:  # 30% esély kihagyásra
                        skip_duration = random.uniform(0.1, 0.8)
                        self.root.after(0, lambda: self.status_detail.config(text="Kihagyás..."))
                        time.sleep(skip_duration)
                        if self.is_clicking:
                            self.root.after(0, lambda: self.status_detail.config(text="Kattintás folyamatban..."))
                        clicks_since_last_change = 0
                        continue
                    
                    # CPS csökkentés vagy növelés
                    base_cps = self.cps.get()
                    if random.random() < 0.5:
                        # Csökkentés 5-tel
                        self.current_cps = max(1.0, base_cps - 5)
                    else:
                        # Növelés 5-tel
                        self.current_cps = min(100.0, base_cps + 5)
                    
                    self.last_cps_change = current_time
                    clicks_since_last_change = 0
                    
                    # UI frissítés
                    self.root.after(0, lambda: self.dynamic_cps_label.config(
                        text=f"Dinamikus CPS: {self.current_cps:.1f}"))
                
                # Kattintás végrehajtása
                click_button = Button.left if self.click_button.get() == "left" else Button.right
                self.mouse_controller.click(click_button)
                
                self.total_clicks += 1
                clicks_since_last_change += 1
                last_click_times.append(current_time)
                
                if len(last_click_times) > 10:
                    last_click_times.pop(0)
                
                # Delay számítása aktuális CPS alapján
                base_delay = 1.0 / self.current_cps
                
                # Természetes variáció
                variance = self.variance_percentage.get() / 100.0
                variation = random.uniform(-variance, variance)
                delay = base_delay * (1 + variation)
                delay = max(0.001, delay)
                
                # Automatikus szünet
                if self.auto_pause_enabled.get() and random.random() * 100 < self.pause_chance.get():
                    pause_duration = random.uniform(self.pause_min_duration.get(), self.pause_max_duration.get())
                    self.root.after(0, lambda d=pause_duration: self.status_detail.config(text=f"Szünet... ({d:.1f}s)"))
                    time.sleep(pause_duration)
                    if self.is_clicking:
                        self.root.after(0, lambda: self.status_detail.config(text="Kattintás folyamatban..."))
                
                time.sleep(delay)
                
            except Exception as e:
                print(f"Hiba: {e}")
                break
    
    def update_stats(self):
        if self.is_clicking and self.session_start_time:
            current_time = time.time()
            
            # Tényleges CPS számítása
            if hasattr(self, 'recent_click_times'):
                recent_clicks = sum(1 for t in self.recent_click_times if current_time - t <= 5.0)
                actual_cps = recent_clicks / 5.0
            else:
                actual_cps = 0.0
            
            self.actual_cps_label.config(text=f"Tényleges CPS: {actual_cps:.1f}")
            
            # Munkamenet idő
            session_duration = current_time - self.session_start_time
            hours = int(session_duration // 3600)
            minutes = int((session_duration % 3600) // 60)
            seconds = int(session_duration % 60)
            self.session_time_label.config(text=f"Munkamenet: {hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Dinamikus CPS mutatása
            if hasattr(self, 'current_cps'):
                self.dynamic_cps_label.config(text=f"Dinamikus CPS: {self.current_cps:.1f}")
        
        self.total_clicks_label.config(text=f"Összes kattintás: {self.total_clicks:,}")
        self.root.after(100, self.update_stats)
    
    def reset_stats(self):
        self.total_clicks = 0
        self.session_start_time = time.time() if self.is_clicking else None
        
    def run(self):
        try:
            self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
            self.root.mainloop()
        except KeyboardInterrupt:
            self.on_closing()
    
    def on_closing(self):
        self.is_clicking = False
        if self.keyboard_listener:
            self.keyboard_listener.stop()
        self.root.destroy()

    def on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

if __name__ == "__main__":
    try:
        import pynput
    except ImportError:
        print("A program futtatásához szükséges a pynput modul.")
        print("Telepítés: pip install pynput")
        exit(1)
    
    app = AdvancedAutoClicker()
    app.run()

