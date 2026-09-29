import sys
import os
import json
import tkinter as tk
from tkinter import messagebox, filedialog
import pymupdf as fitz
from PIL import Image, ImageTk

# Koyu Tema Renk Paleti & Modern Tasarım Sabitleri
BG_DARK = "#18181b"       # Derin Koyu Gri Arka Plan
BG_SIDEBAR = "#202024"    # Sol Panel Arka Planı
BG_PANEL = "#27272a"      # Kontrol Paneli Arka Planı
BG_WIDGET = "#3f3f46"     # Buton Arka Planı
FG_COLOR = "#f4f4f5"      # Ana Metin Rengi
BTN_ACTIVE = "#52525b"    # Buton Aktif Rengi
PEN_ACTIVE_BG = "#e11d48" # Kalem Açıkken Kırmızı Vurgu
ACCENT_COLOR = "#3b82f6"  # Odak Vurgu Rengi
RECENTS_FILE = os.path.expanduser("~/.parsbelge_recents.json")

class ParsBelgeApp:
    def __init__(self, root, pdf_path=None):
        self.root = root
        self.root.title("Parsbelge - Akıllı Tahta PDF Okuyucu")
        self.root.geometry("1100x750")
        self.root.configure(bg=BG_DARK)

        # Görselleri ve pencere ikonunu yükle
        self.load_custom_icons()

        self.is_drawing_mode = False
        self.page_drawings = {}  # Her sayfanın çizim koordinatları
        self.last_canvas_x = 0
        self.last_canvas_y = 0

        if pdf_path:
            self.add_recent_file(pdf_path)
            self.load_pdf(pdf_path)
        else:
            self.show_welcome_screen()

    def load_custom_icons(self):
        try:
            if os.path.exists("solustsimge.jpeg"):
                ico = Image.open("solustsimge.jpeg")
                self.window_icon = ImageTk.PhotoImage(ico)
                self.root.iconphoto(True, self.window_icon)

            if os.path.exists("uygulama.jpeg"):
                img = Image.open("uygulama.jpeg").resize((90, 90), Image.Resampling.LANCZOS)
                self.logo_img = ImageTk.PhotoImage(img)
            else:
                self.logo_img = None

            if os.path.exists("folder_icon.png"):
                img = Image.open("folder_icon.png").resize((32, 32), Image.Resampling.LANCZOS)
                self.folder_icon = ImageTk.PhotoImage(img)
            else:
                self.folder_icon = None
        except Exception:
            pass

    def load_recents(self):
        if os.path.exists(RECENTS_FILE):
            try:
                with open(RECENTS_FILE, "r", encoding="utf-8") as f:
                    files = json.load(f)
                    return [f for f in files if os.path.exists(f)]
            except Exception:
                return []
        return []

    def add_recent_file(self, path):
        recents = self.load_recents()
        abs_path = os.path.abspath(path)
        if abs_path in recents:
            recents.remove(abs_path)
        recents.insert(0, abs_path)
        recents = recents[:5]
        try:
            with open(RECENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(recents, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    def show_welcome_screen(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        self.welcome_frame = tk.Frame(self.root, bg=BG_DARK)
        self.welcome_frame.pack(fill=tk.BOTH, expand=True)

        if hasattr(self, 'logo_img') and self.logo_img:
            logo_label = tk.Label(self.welcome_frame, image=self.logo_img, bg=BG_DARK)
            logo_label.pack(pady=(80, 10))
        else:
            logo_canvas = tk.Canvas(self.welcome_frame, width=90, height=90, bg=BG_DARK, highlightthickness=0)
            logo_canvas.pack(pady=(80, 10))
            logo_canvas.create_rectangle(15, 5, 75, 85, fill=ACCENT_COLOR, outline="")
            logo_canvas.create_text(45, 45, text="PDF", fill="#ffffff", font=("Arial", 14, "bold"))

        title_label = tk.Label(self.welcome_frame, text="PARSBELGE", bg=BG_DARK, fg=FG_COLOR, font=("Arial", 28, "bold"))
        title_label.pack(pady=(5, 5))

        sub_label = tk.Label(self.welcome_frame, text="Akıllı Tahta İçin Optimize Edilmiş PDF Okuyucu", bg=BG_DARK, fg="#a1a1aa", font=("Arial", 11))
        sub_label.pack(pady=(0, 25))

        btn_kwargs = {
            "command": self.open_file_dialog,
            "bg": ACCENT_COLOR, 
            "activebackground": "#2563eb", 
            "relief": tk.FLAT, 
            "padx": 16, 
            "pady": 16, 
            "cursor": "hand2"
        }
        if hasattr(self, 'folder_icon') and self.folder_icon:
            btn_kwargs["image"] = self.folder_icon
        else:
            btn_kwargs["text"] = "📁 Dosya Seç"
            btn_kwargs["fg"] = "#ffffff"
            btn_kwargs["font"] = ("Arial", 12, "bold")

        select_btn = tk.Button(self.welcome_frame, **btn_kwargs)
        select_btn.pack(pady=(0, 20))

        recents = self.load_recents()
        if recents:
            recent_title = tk.Label(self.welcome_frame, text="📌 Son Kullanılan Belgeler", bg=BG_DARK, fg="#71717a", font=("Arial", 10, "bold"))
            recent_title.pack(pady=(15, 10))

            recent_frame = tk.Frame(self.welcome_frame, bg=BG_DARK)
            recent_frame.pack()

            for path in recents:
                filename = os.path.basename(path)
                btn = tk.Button(recent_frame, text=f"📄  {filename}", command=lambda p=path: self.open_recent_file(p),
                                bg=BG_PANEL, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=FG_COLOR,
                                font=("Arial", 10), relief=tk.FLAT, width=50, anchor="w", padx=15, pady=8, cursor="hand2")
                btn.pack(pady=4)

    def open_recent_file(self, path):
        if os.path.exists(path):
            self.welcome_frame.destroy()
            self.add_recent_file(path)
            self.load_pdf(path)
        else:
            messagebox.showerror("Hata", "Seçilen dosya bulunamadı veya taşınmış.")
            recents = [r for r in self.load_recents() if r != path]
            with open(RECENTS_FILE, "w", encoding="utf-8") as f:
                json.dump(recents, f, ensure_ascii=False, indent=2)
            self.show_welcome_screen()

    def open_file_dialog(self):
        pdf_path = filedialog.askopenfilename(
            title="Bir PDF Dosyası Seçin",
            filetypes=[("PDF Dosyaları", "*.pdf"), ("Tüm Dosyalar", "*.*")]
        )
        if pdf_path:
            if hasattr(self, 'welcome_frame') and self.welcome_frame.winfo_exists():
                self.welcome_frame.destroy()
            for widget in self.root.winfo_children():
                widget.destroy()
            self.add_recent_file(pdf_path)
            self.load_pdf(pdf_path)

    def return_to_main_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()
        self.show_welcome_screen()

    def load_pdf(self, pdf_path):
        try:
            self.doc = fitz.open(pdf_path)
        except Exception as e:
            messagebox.showerror("Hata", f"PDF dosyası açılamadı: {e}")
            self.show_welcome_screen()
            return

        self.current_page = 0
        self.total_pages = len(self.doc)
        self.zoom_factor = 1.0

        for widget in self.root.winfo_children():
            widget.destroy()

        # --- ANA PENCERE YERLEŞİMİ ---
        
        # 1. SOL KENAR ÇUĞUĞU (Sidebar)
        self.sidebar_frame = tk.Frame(self.root, bg=BG_SIDEBAR, width=220)
        self.sidebar_frame.pack(side=tk.LEFT, fill=tk.Y)
        self.sidebar_frame.pack_propagate(False)

        # Üst 2x2 Araç Kutusu Matrisi
        tools_frame = tk.Frame(self.sidebar_frame, bg=BG_SIDEBAR)
        tools_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # 1. Buton: Kalem (Çizim Modu)
        self.btn_pen = tk.Button(tools_frame, text="✏️️ Kalem", command=self.toggle_pen,
                                 bg=BG_WIDGET, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=FG_COLOR,
                                 relief=tk.FLAT, font=("Arial", 9, "bold"), width=9, height=2, cursor="hand2")
        self.btn_pen.grid(row=0, column=0, padx=4, pady=4)

        # 2. Buton: Sayfayı Temizle
        self.btn_clear = tk.Button(tools_frame, text="🗑️ Temizle", command=self.clear_current_page_drawings,
                                   bg=BG_WIDGET, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=FG_COLOR,
                                   relief=tk.FLAT, font=("Arial", 9, "bold"), width=9, height=2, cursor="hand2")
        self.btn_clear.grid(row=0, column=1, padx=4, pady=4)

        # 3. Buton: Ana Menüye Dön
        self.btn_home = tk.Button(tools_frame, text="🏠 Ana Menü", command=self.return_to_main_menu,
                                  bg=BG_WIDGET, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=FG_COLOR,
                                  relief=tk.FLAT, font=("Arial", 9, "bold"), width=9, height=2, cursor="hand2")
        self.btn_home.grid(row=1, column=0, padx=4, pady=4)

        # 4. Buton: Yakınlaşma Sıfırla (%100)
        self.btn_zoom_reset = tk.Button(tools_frame, text="🔍 %100", command=self.reset_zoom,
                                       bg=BG_WIDGET, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=FG_COLOR,
                                       relief=tk.FLAT, font=("Arial", 9, "bold"), width=9, height=2, cursor="hand2")
        self.btn_zoom_reset.grid(row=1, column=1, padx=4, pady=4)

        # Ayırıcı Çizgi
        sep = tk.Frame(self.sidebar_frame, bg="#3f3f46", height=2)
        sep.pack(fill=tk.X, padx=10, pady=5)

        # Sayfa Listesi Başlığı
        thumb_label = tk.Label(self.sidebar_frame, text="📄 Sayfalar", bg=BG_SIDEBAR, fg="#a1a1aa", font=("Arial", 9, "bold"))
        thumb_label.pack(anchor="w", padx=15, pady=(5, 5))

        # Kaydırılabilir Sayfa Listesi Alanı (Tamamen Çubuksuz ve Çerçevesiz)
        thumb_container = tk.Frame(self.sidebar_frame, bg=BG_SIDEBAR)
        thumb_container.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=(0, 10))

        self.thumb_canvas = tk.Canvas(thumb_container, bg=BG_SIDEBAR, highlightthickness=0, bd=0)
        self.thumb_inner_frame = tk.Frame(self.thumb_canvas, bg=BG_SIDEBAR)

        self.thumb_inner_frame.bind(
            "<Configure>",
            lambda e: self.thumb_canvas.configure(scrollregion=self.thumb_canvas.bbox("all"))
        )
        self.thumb_canvas.create_window((0, 0), window=self.thumb_inner_frame, anchor="nw")
        self.thumb_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Farenin tekerleğiyle sayfa listesini kaydırma desteği (Linux için MouseWheel olayları)
        def _on_mousewheel(event):
            if event.num == 4 or event.delta > 0:
                self.thumb_canvas.yview_scroll(-1, "units")
            elif event.num == 5 or event.delta < 0:
                self.thumb_canvas.yview_scroll(1, "units")

        # Fare tekerleği bağlamaları
        self.thumb_canvas.bind("<MouseWheel>", _on_mousewheel)
        self.thumb_inner_frame.bind("<MouseWheel>", _on_mousewheel)
        self.thumb_canvas.bind("<Button-4>", _on_mousewheel)
        self.thumb_canvas.bind("<Button-5>", _on_mousewheel)
        self.thumb_inner_frame.bind("<Button-4>", _on_mousewheel)
        self.thumb_inner_frame.bind("<Button-5>", _on_mousewheel)

        # Sayfa Numarası Butonları Listesi
        self.page_buttons = []
        for i in range(self.total_pages):
            p_btn = tk.Button(self.thumb_inner_frame, text=f"Sayfa {i+1}", 
                              command=lambda page_idx=i: self.go_to_page(page_idx),
                              bg=BG_PANEL, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=FG_COLOR,
                              relief=tk.FLAT, font=("Arial", 10, "bold"), width=16, anchor="w", padx=12, pady=8, cursor="hand2")
            p_btn.pack(pady=3)
            p_btn.bind("<MouseWheel>", _on_mousewheel)
            p_btn.bind("<Button-4>", _on_mousewheel)
            p_btn.bind("<Button-5>", _on_mousewheel)
            self.page_buttons.append(p_btn)

        # 2. SAĞ ANA ALAN (PDF Görüntüleme ve Üst Kontroller)
        right_container = tk.Frame(self.root, bg=BG_DARK)
        right_container.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        top_bar = tk.Frame(right_container, bg=BG_PANEL, height=40)
        top_bar.pack(side=tk.TOP, fill=tk.X)

        self.btn_prev = tk.Button(top_bar, text="◀ Önceki", command=self.prev_page, 
                                  bg=BG_WIDGET, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=FG_COLOR, relief=tk.FLAT, padx=8, font=("Arial", 9), cursor="hand2")
        self.btn_prev.pack(side=tk.LEFT, padx=10, pady=6)

        self.page_info_label = tk.Label(top_bar, text=f"Sayfa 1 / {self.total_pages}", bg=BG_PANEL, fg=FG_COLOR, font=("Arial", 9, "bold"))
        self.page_info_label.pack(side=tk.LEFT, padx=10)

        self.btn_next = tk.Button(top_bar, text="Sonraki ▶", command=self.next_page, 
                                  bg=BG_WIDGET, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=FG_COLOR, relief=tk.FLAT, padx=8, font=("Arial", 9), cursor="hand2")
        self.btn_next.pack(side=tk.LEFT, padx=2, pady=6)

        self.btn_zoom_in = tk.Button(top_bar, text=" + ", command=self.zoom_in, 
                                     bg=BG_WIDGET, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=FG_COLOR, relief=tk.FLAT, font=("Arial", 9, "bold"), padx=6, cursor="hand2")
        self.btn_zoom_in.pack(side=tk.RIGHT, padx=10, pady=6)

        self.zoom_label = tk.Label(top_bar, text="%100", bg=BG_PANEL, fg=FG_COLOR, font=("Arial", 9))
        self.zoom_label.pack(side=tk.RIGHT, padx=2)

        self.btn_zoom_out = tk.Button(top_bar, text=" - ", command=self.zoom_out, 
                                      bg=BG_WIDGET, fg=FG_COLOR, activebackground=BTN_ACTIVE, activeforeground=FG_COLOR, relief=tk.FLAT, font=("Arial", 9, "bold", "bold"), padx=6, cursor="hand2")
        self.btn_zoom_out.pack(side=tk.RIGHT, padx=2, pady=6)

        # PDF Tuvali (Canvas) - Sağ tarafın kaydırma çubukları duruyor (istendiği gibi)
        self.canvas_frame = tk.Frame(right_container, bg=BG_DARK)
        self.canvas_frame.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#121214", highlightthickness=0, cursor="fleur")
        self.v_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.h_scrollbar = tk.Scrollbar(self.canvas_frame, orient=tk.HORIZONTAL, command=self.canvas.xview)
        
        self.canvas.configure(yscrollcommand=self.v_scrollbar.set, xscrollcommand=self.h_scrollbar.set)

        self.v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.canvas.bind("<Button-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<Configure>", lambda e: self.render_page())

        self.render_page()

    def toggle_pen(self):
        self.is_drawing_mode = not self.is_drawing_mode
        if self.is_drawing_mode:
            self.btn_pen.config(text="✏️ Kalem (Açık)", bg=PEN_ACTIVE_BG)
            self.canvas.config(cursor="cross")
        else:
            self.btn_pen.config(text="✏️ Kalem", bg=BG_WIDGET)
            self.canvas.config(cursor="fleur")

    def clear_current_page_drawings(self):
        if self.current_page in self.page_drawings:
            self.page_drawings[self.current_page] = []
            self.render_page()

    def go_to_page(self, page_idx):
        if 0 <= page_idx < self.total_pages:
            self.current_page = page_idx
            self.render_page()

    def on_press(self, event):
        if self.is_drawing_mode:
            self.last_canvas_x = self.canvas.canvasx(event.x)
            self.last_canvas_y = self.canvas.canvasy(event.y)
        else:
            self.canvas.scan_mark(event.x, event.y)

    def on_drag(self, event):
        if self.is_drawing_mode:
            if hasattr(self, 'img_x') and hasattr(self, 'img_y'):
                canvas_x = self.canvas.canvasx(event.x)
                canvas_y = self.canvas.canvasy(event.y)
                
                pdf_x1 = (self.last_canvas_x - self.img_x) / self.zoom_factor
                pdf_y1 = (self.last_canvas_y - self.img_y) / self.zoom_factor
                pdf_x2 = (canvas_x - self.img_x) / self.zoom_factor
                pdf_y2 = (canvas_y - self.img_y) / self.zoom_factor
                
                if self.current_page not in self.page_drawings:
                    self.page_drawings[self.current_page] = []
                self.page_drawings[self.current_page].append((pdf_x1, pdf_y1, pdf_x2, pdf_y2))
                
                self.canvas.create_line(
                    self.last_canvas_x, self.last_canvas_y, canvas_x, canvas_y,
                    fill="#f43f5e", width=max(2, int(3 * self.zoom_factor)), capstyle=tk.ROUND, smooth=True
                )
                
                self.last_canvas_x = canvas_x
                self.last_canvas_y = canvas_y
        else:
            self.canvas.scan_dragto(event.x, event.y, gain=1)

    def render_page(self):
        if hasattr(self, 'doc') and 0 <= self.current_page < self.total_pages:
            page = self.doc[self.current_page]
            
            mat = fitz.Matrix(self.zoom_factor, self.zoom_factor)
            pix = page.get_pixmap(matrix=mat)
            
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            self.tk_img = ImageTk.PhotoImage(img)
            
            self.canvas.update_idletasks()
            c_width = self.canvas.winfo_width()
            c_height = self.canvas.winfo_height()
            
            self.img_x = max(0, (c_width - pix.width) // 2)
            self.img_y = max(0, (c_height - pix.height) // 2)
            
            self.canvas.delete("all")
            self.canvas.create_image(self.img_x, self.img_y, anchor=tk.NW, image=self.tk_img)
            
            if self.current_page in self.page_drawings:
                for (p1_x, p1_y, p2_x, p2_y) in self.page_drawings[self.current_page]:
                    cx1 = self.img_x + p1_x * self.zoom_factor
                    cy1 = self.img_y + p1_y * self.zoom_factor
                    cx2 = self.img_x + p2_x * self.zoom_factor
                    cy2 = self.img_y + p2_y * self.zoom_factor
                    self.canvas.create_line(
                        cx1, cy1, cx2, cy2,
                        fill="#f43f5e", width=max(2, int(3 * self.zoom_factor)), capstyle=tk.ROUND, smooth=True
                    )
            
            self.canvas.config(scrollregion=(0, 0, max(c_width, pix.width), max(c_height, pix.height)))
            
            if hasattr(self, 'page_info_label'):
                self.page_info_label.config(text=f"Sayfa {self.current_page + 1} / {self.total_pages}")
                self.zoom_label.config(text=f"%{int(self.zoom_factor * 100)}")

                for idx, btn in enumerate(self.page_buttons):
                    if idx == self.current_page:
                        btn.config(bg=ACCENT_COLOR, fg="#ffffff")
                    else:
                        btn.config(bg=BG_PANEL, fg=FG_COLOR)

    def zoom_in(self):
        if hasattr(self, 'zoom_factor') and self.zoom_factor < 3.0:
            self.zoom_factor += 0.2
            self.render_page()

    def zoom_out(self):
        if hasattr(self, 'zoom_factor') and self.zoom_factor > 0.4:
            self.zoom_factor -= 0.2
            self.render_page()

    def reset_zoom(self):
        if hasattr(self, 'zoom_factor'):
            self.zoom_factor = 1.0
            self.render_page()

    def next_page(self):
        if hasattr(self, 'doc') and self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.render_page()

    def prev_page(self):
        if hasattr(self, 'doc') and self.current_page > 0:
            self.current_page -= 1
            self.render_page()

if __name__ == "__main__":
    root = tk.Tk()
    
    pdf_arg = sys.argv[1] if len(sys.argv) > 1 else None
    app = ParsBelgeApp(root, pdf_arg)
    
    root.mainloop()