# app.py
# Desktop Image Editor (Tkinter + OpenCV)
# Features:
# - File menu: Open, Save, Save As, Exit
# - Edit menu: Undo, Redo
# - Collapsible Tools Sidebar: "◀ Hide Tools" / "▶ Show Tools"
# - Image display area
# - Tools:
#   * Grayscale
#   * Blur (+ / -)
#   * Edge Detection 
#   * Brightness (+ / -)  
#   * Contrast (+ / -)    
#   * Scale (+ / -)       
#   * Rotate 90/180/270
#   * Flip Horizontal/Vertical



import os
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

import cv2
import numpy as np
from PIL import Image, ImageTk

from image_model import ImageModel
from history_manager import HistoryManager


class ImageEditorApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Image Editor - Tkinter + OpenCV")
        self.root.geometry("1100x700")

        # Model + history (class interaction)
        self.model = ImageModel()
        self.history = HistoryManager()

        # Tk requires keeping a reference to PhotoImage
        self._current_photo = None

        # Sidebar toggle state
        self.tools_visible = True

        # Blur state
        self.blur_level = 0
        self.blur_base = None

        # Brightness/Contrast (buttons) state 
        
        self.brightness_level = 0
        self.contrast_level = 0
        self.bc_base = None

        # Scale (buttons) state -
        
        self.scale_level = 0
        self.scale_base = None

        # Edge state 
        self.edge_applied = False

        self._build_menu()
        self._build_layout()
        self._update_ui_state()

    # ---------------- MENU ----------------
    def _build_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_image)
        file_menu.add_command(label="Save As", command=self.save_as_image)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_app)
        menubar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo_action)
        edit_menu.add_command(label="Redo", command=self.redo_action)
        menubar.add_cascade(label="Edit", menu=edit_menu)

        self.root.config(menu=menubar)

    # ---------------- LAYOUT ----------------
    def _build_layout(self):
        self.main_frame = ttk.Frame(self.root)
        self.main_frame.pack(fill=tk.BOTH, expand=True)

        # Sidebar
        self.left_panel = ttk.Frame(self.main_frame, padding=10)
        self.left_panel.pack(side=tk.LEFT, fill=tk.Y)

        # Toggle button stays always visible
        self.toggle_btn = ttk.Button(self.left_panel, text="◀ Hide Tools", command=self.toggle_tools)
        self.toggle_btn.pack(fill=tk.X, pady=(0, 10))

        # Container that holds ALL tools 
        self.tools_container = ttk.Frame(self.left_panel)
        self.tools_container.pack(fill=tk.Y, expand=True)

        # Main image area
        self.right_panel = ttk.Frame(self.main_frame, padding=10)
        self.right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        # Image display
        self.image_label = ttk.Label(self.right_panel, text="Open an image to start", anchor="center")
        self.image_label.pack(fill=tk.BOTH, expand=True)

        # Status bar
        self.status_var = tk.StringVar(value="No image loaded")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor="w")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # -------- Tools UI (inside tools_container) --------
        ttk.Label(self.tools_container, text="Effects / Tools", font=("Segoe UI", 12, "bold")).pack(pady=(0, 10))

        ttk.Button(self.tools_container, text="Grayscale", command=self.apply_grayscale).pack(fill=tk.X, pady=4)
        ttk.Button(self.tools_container, text="Edge Detection", command=self.apply_edges_once).pack(fill=tk.X, pady=4)

        # Blur buttons
        ttk.Label(self.tools_container, text="Blur Intensity").pack(pady=(12, 0))
        blur_frame = ttk.Frame(self.tools_container)
        blur_frame.pack(fill=tk.X, pady=4)
        ttk.Button(blur_frame, text="-", command=self.decrease_blur).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(blur_frame, text="+", command=self.increase_blur).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Brightness buttons
        ttk.Label(self.tools_container, text="Brightness").pack(pady=(12, 0))
        b_frame = ttk.Frame(self.tools_container)
        b_frame.pack(fill=tk.X, pady=4)
        ttk.Button(b_frame, text="-", command=self.decrease_brightness).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(b_frame, text="+", command=self.increase_brightness).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Contrast buttons
        ttk.Label(self.tools_container, text="Contrast").pack(pady=(12, 0))
        c_frame = ttk.Frame(self.tools_container)
        c_frame.pack(fill=tk.X, pady=4)
        ttk.Button(c_frame, text="-", command=self.decrease_contrast).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(c_frame, text="+", command=self.increase_contrast).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Scale buttons
        ttk.Label(self.tools_container, text="Image Scale").pack(pady=(12, 0))
        s_frame = ttk.Frame(self.tools_container)
        s_frame.pack(fill=tk.X, pady=4)
        ttk.Button(s_frame, text="-", command=self.decrease_scale).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(s_frame, text="+", command=self.increase_scale).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Rotate
        ttk.Label(self.tools_container, text="Rotate").pack(pady=(12, 0))
        rot = ttk.Frame(self.tools_container)
        rot.pack(fill=tk.X, pady=4)
        ttk.Button(rot, text="90°", command=lambda: self.apply_rotate(90)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(rot, text="180°", command=lambda: self.apply_rotate(180)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(rot, text="270°", command=lambda: self.apply_rotate(270)).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        # Flip
        ttk.Label(self.tools_container, text="Flip").pack(pady=(12, 0))
        flp = ttk.Frame(self.tools_container)
        flp.pack(fill=tk.X, pady=4)
        ttk.Button(flp, text="Horizontal", command=lambda: self.apply_flip("horizontal")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)
        ttk.Button(flp, text="Vertical", command=lambda: self.apply_flip("vertical")).pack(side=tk.LEFT, expand=True, fill=tk.X, padx=2)

        ttk.Button(self.tools_container, text="Reset to Original", command=self.reset_image).pack(fill=tk.X, pady=(14, 4))

    # ---------------- Sidebar Toggle ----------------
    def toggle_tools(self):
        
        if self.tools_visible:
            self.tools_container.pack_forget()
            self.toggle_btn.config(text="▶ Show Tools")
            self.tools_visible = False
        else:
            self.tools_container.pack(fill=tk.Y, expand=True)
            self.toggle_btn.config(text="◀ Hide Tools")
            self.tools_visible = True

  
    def _update_ui_state(self):
        has_img = self.model.has_image()
        state = "normal" if has_img else "disabled"

       
        for child in self.tools_container.winfo_children():
            if isinstance(child, ttk.Button) or isinstance(child, ttk.Scale):
                child.configure(state=state)
            if isinstance(child, ttk.Frame):
                for sub in child.winfo_children():
                    if isinstance(sub, ttk.Button):
                        sub.configure(state=state)

        if not has_img:
            self.image_label.config(text="Open an image to start", image="")
            self.status_var.set("No image loaded")

    def _update_status(self):
        if not self.model.has_image():
            self.status_var.set("No image loaded")
            return

        w, h = self.model.get_dimensions()
        name = os.path.basename(self.model.get_filepath()) if self.model.get_filepath() else "Untitled"
        self.status_var.set(f"File: {name} | Size: {w}x{h}")

    def _show_image(self, img_bgr):
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        pil_img = Image.fromarray(img_rgb)

        lw = self.image_label.winfo_width()
        lh = self.image_label.winfo_height()
        if lw > 50 and lh > 50:
            pil_img.thumbnail((lw, lh), Image.Resampling.LANCZOS)

        self._current_photo = ImageTk.PhotoImage(pil_img)
        self.image_label.config(image=self._current_photo, text="")
        self._update_status()

    def _apply_and_show(self, new_img):
        self.history.push(self.model.get_current())
        self.model.set_current(new_img)
        self._show_image(self.model.get_current())

    def _reset_blur_state(self):
        self.blur_level = 0
        self.blur_base = None

    def _reset_bc_state(self):
        self.brightness_level = 0
        self.contrast_level = 0
        self.bc_base = None

    def _reset_scale_state(self):
        self.scale_level = 0
        self.scale_base = None

    def _reset_edge_state(self):
        self.edge_applied = False

    def _reset_all_tool_states(self):
        self._reset_blur_state()
        self._reset_bc_state()
        self._reset_scale_state()
        self._reset_edge_state()

    def _cancel_other_sessions_for(self, tool_name: str):
        
        if tool_name != "blur":
            self._reset_blur_state()
        if tool_name != "bc":
            self._reset_bc_state()
        if tool_name != "scale":
            self._reset_scale_state()
        if tool_name != "edge":
            self._reset_edge_state()
    
    # ---------------- FILE MENU ----------------
    def open_image(self):
        path = filedialog.askopenfilename(
            title="Open Image",
            filetypes=[("Image Files", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not path:
            return
        try:
                        self.model.load(path)
            self.history.clear()
            self._reset_all_tool_states()
            self._show_image(self.model.get_current())
            self._update_ui_state()
        except Exception as e:
            messagebox.showerror("Open Error", str(e))

        def save_image(self):
        if not self.model.has_image():
            messagebox.showwarning("No Image", "Please open an image first.")
            return

        if not self.model.get_filepath():
            self.save_as_image()
            return
        
                ok = cv2.imwrite(self.model.get_filepath(), self.model.get_current())
        if ok:
            messagebox.showinfo("Saved", "Image saved successfully.")
        else:
            messagebox.showerror("Save Error", "Failed to save the image.")

    def save_as_image(self):
        if not self.model.has_image():
            messagebox.showwarning("No Image", "Please open an image first.")
            return

        path = filedialog.asksaveasfilename(
            title="Save Image As",
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg *.jpeg"), ("BMP", "*.bmp")]
        )
        if not path:
            return

        ok = cv2.imwrite(path, self.model.get_current())
        if ok:
            self.model.set_filepath(path)
            messagebox.showinfo("Saved", "Image saved successfully.")
            self._update_status()
        else:
        
                    messagebox.showerror("Save Error", "Failed to save the image.")

    def exit_app(self):
        if messagebox.askyesno("Exit", "Are you sure you want to exit?"):
            self.root.destroy()

    # ---------------- EDIT MENU ----------------
    def undo_action(self):
        if not self.model.has_image() or not self.history.can_undo():
            messagebox.showinfo("Undo", "Nothing to undo.")
            return

        prev_img = self.history.undo(self.model.get_current())
        if prev_img is not None:
            self.model.set_current(prev_img)
            self._show_image(prev_img)

        self._reset_all_tool_states()

    def redo_action(self):
        if not self.model.has_image() or not self.history.can_redo():
            messagebox.showinfo("Redo", "Nothing to redo.")
            return

        next_img = self.history.redo(self.model.get_current())
        if next_img is not None:
                      self.model.set_current(next_img)
            self._show_image(next_img)

        self._reset_all_tool_states()

    # ---------------- TOOLS ----------------
    def apply_grayscale(self):
        if not self.model.has_image():
            return
        self._apply_and_show(self.model.to_grayscale())
        self._reset_all_tool_states()

    def apply_edges_once(self):
        if not self.model.has_image():
            return
        if self.edge_applied:
            return
        self._apply_and_show(self.model.edge_detect())
        self.edge_applied = True
        self._cancel_other_sessions_for("edge")

    # ---- Blur (+ / -) ----
    def increase_blur(self):
        if not self.model.has_image():
            return
        if self.blur_level == 0:
                       self.blur_base = self.model.get_current().copy()
            self.history.push(self.model.get_current())

        self.blur_level += 1
        k = 2 * self.blur_level + 1  
        blurred = cv2.GaussianBlur(self.blur_base, (k, k), 0)

        self.model.set_current(blurred)
        self._show_image(blurred)
        self._cancel_other_sessions_for("blur")

    def decrease_blur(self):
        if not self.model.has_image():
            return
        if self.blur_level == 0:
            return

        self.blur_level -= 1
        if self.blur_level == 0:
            self.model.set_current(self.blur_base)
            self._show_image(self.blur_base)
            self.blur_base = None
            return

        k = 2 * self.blur_level + 1
        blurred = cv2.GaussianBlur(self.blur_base, (k, k), 0)
        
                self.model.set_current(blurred)
        self._show_image(blurred)
        self._cancel_other_sessions_for("blur")

    # ---- Brightness / Contrast (Buttons) ----
    def _ensure_bc_session(self):
        if self.bc_base is None:
            self.bc_base = self.model.get_current().copy()
            self.history.push(self.model.get_current())
        self._cancel_other_sessions_for("bc")

    def _apply_brightness_contrast(self):
        if self.bc_base is None:
            return

        # Extended ranges:
        brightness = self.brightness_level * 12  
        contrast = 1.0 + (self.contrast_level * 0.08)  
        contrast = max(0.2, min(4.0, contrast))

        img = self.bc_base.astype(np.float32)
        img = (img - 128.0) * contrast + 128.0 + brightness
        img = np.clip(img, 0, 255).astype(np.uint8)

        self.model.set_current(img)
