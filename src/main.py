import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import threading
from database import LocalDatabase
from api_client import GLM53FlashClient

class GLMFlashDesktopApp:
    """
    Main Application UI built with Tkinter.
    Provides dark-themed IDE-like interface for GLM-5.3-Flash model interactions.
    """
    def __init__(self, root):
        self.root = root
        self.root.title("GLM-5.3-Flash — Stealth Model '0x Alpha' Desktop Client")
        self.root.geometry("1100x700")

        # Initialize Backend Components
        self.db = LocalDatabase()
        self.api_client = GLM53FlashClient()

        # State tracking
        self.current_project_id = None
        self.current_session_id = None
        self.attached_files = []
        self.attached_images = []

        self._apply_theme()
        self._build_layout()
        self._load_initial_data()

    def _apply_theme(self):
        """Configure dark theme parameters."""
        self.bg_color = "#1e1e1e"
        self.sidebar_color = "#252526"
        self.text_color = "#d4d4d4"
        self.accent_color = "#10b981" # Green highlight

        self.root.configure(bg=self.bg_color)
        
        style = ttk.Style()
        style.theme_use('default')
        style.configure(".", background=self.bg_color, foreground=self.text_color)
        style.configure("Sidebar.TFrame", background=self.sidebar_color)
        style.configure("TButton", background="#333333", foreground="#ffffff", borderwidth=0)
        style.map("TButton", background=[("active", "#444444")])

    def _build_layout(self):
        """Construct side panel and main chat canvas."""
        # Main Grid Layout
        self.root.columnconfigure(1, weight=1)
        self.root.rowconfigure(0, weight=1)

        # ------------------ LEFT SIDEBAR ------------------
        sidebar = ttk.Frame(self.root, style="Sidebar.TFrame", width=260)
        sidebar.grid(row=0, column=0, sticky="nsew", padx=2, pady=2)
        sidebar.pack_propagate(False)

        # Header Title
        lbl_brand = tk.Label(sidebar, text="⚡ GLM-5.3-Flash", bg=self.sidebar_color, fg=self.accent_color, font=("Consolas", 14, "bold"))
        lbl_brand.pack(anchor="w", padx=10, pady=10)

        # Projects Section
        lbl_proj = tk.Label(sidebar, text="PROJECT LIBRARY", bg=self.sidebar_color, fg="#888888", font=("Segoe UI", 8, "bold"))
        lbl_proj.pack(anchor="w", padx=10, pady=(10, 2))

        btn_new_proj = tk.Button(sidebar, text="+ New Project", bg="#333333", fg="white", bd=0, command=self._add_project_dialog)
        btn_new_proj.pack(fill="x", padx=10, pady=2)

        self.lst_projects = tk.Listbox(sidebar, bg="#2d2d2d", fg="white", bd=0, highlightthickness=0, height=5)
        self.lst_projects.pack(fill="x", padx=10, pady=5)
        self.lst_projects.bind("<<ListboxSelect>>", self._on_project_select)

        # Chat Sessions Section
        lbl_sess = tk.Label(sidebar, text="SESSIONS", bg=self.sidebar_color, fg="#888888", font=("Segoe UI", 8, "bold"))
        lbl_sess.pack(anchor="w", padx=10, pady=(10, 2))

        btn_new_chat = tk.Button(sidebar, text="+ New Chat", bg="#333333", fg="white", bd=0, command=self._add_session)
        btn_new_chat.pack(fill="x", padx=10, pady=2)

        self.lst_sessions = tk.Listbox(sidebar, bg="#2d2d2d", fg="white", bd=0, highlightthickness=0)
        self.lst_sessions.pack(fill="both", expand=True, padx=10, pady=5)
        self.lst_sessions.bind("<<ListboxSelect>>", self._on_session_select)

        # ------------------ MAIN CONTENT AREA ------------------
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.grid(row=0, column=1, sticky="nsew", padx=5, pady=5)
        main_frame.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)

        # Chat Window
        self.txt_chat = tk.Text(main_frame, bg="#121212", fg="#e0e0e0", font=("Consolas", 10), wrap="word", bd=0, highlightthickness=0)
        self.txt_chat.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        
        # Context/Attachments Status Bar
        self.lbl_attachments = tk.Label(main_frame, text="Attachments: None", bg=self.bg_color, fg="#a0a0a0", anchor="w")
        self.lbl_attachments.grid(row=1, column=0, sticky="ew", padx=5)

        # Bottom Input Controls
        input_frame = tk.Frame(main_frame, bg=self.bg_color)
        input_frame.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        input_frame.columnconfigure(0, weight=1)

        self.txt_input = tk.Text(input_frame, bg="#2d2d2d", fg="white", height=3, font=("Segoe UI", 10), bd=0)
        self.txt_input.grid(row=0, column=0, sticky="ew", padx=(0, 5))

        # Action Buttons Box
        btn_box = tk.Frame(input_frame, bg=self.bg_color)
        btn_box.grid(row=0, column=1, sticky="nsew")

        btn_attach_code = tk.Button(btn_box, text="📄 Code", bg="#3c3c3c", fg="white", bd=0, width=8, command=self._attach_code_file)
        btn_attach_code.pack(fill="x", pady=1)

        btn_attach_img = tk.Button(btn_box, text="🖼 Image", bg="#3c3c3c", fg="white", bd=0, width=8, command=self._attach_image_file)
        btn_attach_img.pack(fill="x", pady=1)

        btn_send = tk.Button(btn_box, text="Send ⚡", bg=self.accent_color, fg="black", font=("Segoe UI", 9, "bold"), bd=0, command=self._send_message)
        btn_send.pack(fill="x", pady=(2, 0))

    def _load_initial_data(self):
        """Initial database sync with UI components."""
        projects = self.db.get_projects()
        if not projects:
            p_id = self.db.create_project("Default Workspace")
            projects = self.db.get_projects()

        for p in projects:
            self.lst_projects.insert(tk.END, f"📁 {p[1]}")
        
        self.lst_projects.select_set(0)
        self._on_project_select(None)

    def _add_project_dialog(self):
        """Dialog window to create a project category."""
        def save():
            name = entry.get().strip()
            if name:
                p_id = self.db.create_project(name)
                self.lst_projects.insert(0, f"📁 {name}")
                top.destroy()

        top = tk.Toplevel(self.root)
        top.title("New Project")
        top.geometry("300x100")
        top.configure(bg=self.bg_color)
        
        tk.Label(top, text="Project Name:", bg=self.bg_color, fg="white").pack(pady=5)
        entry = tk.Entry(top, bg="#2d2d2d", fg="white")
        entry.pack(pady=5, padx=10, fill="x")
        tk.Button(top, text="Create", bg=self.accent_color, command=save).pack(pady=5)

    def _on_project_select(self, event):
        """Load chat sessions belonging to selected project."""
        idx = self.lst_projects.curselection()
        if not idx:
            return
        projects = self.db.get_projects()
        self.current_project_id = projects[idx[0]][0]

        self.lst_sessions.delete(0, tk.END)
        sessions = self.db.get_sessions(self.current_project_id)
        
        for s in sessions:
            self.lst_sessions.insert(tk.END, f"💬 {s[1]}")

        if sessions:
            self.lst_sessions.select_set(0)
            self._on_session_select(None)
        else:
            self._add_session()

    def _add_session(self):
        """Create new conversation session."""
        if not self.current_project_id:
            return
        s_id = self.db.create_session(self.current_project_id, "New Coding Session")
        self.lst_sessions.insert(0, "💬 New Coding Session")
        self.lst_sessions.select_clear(0, tk.END)
        self.lst_sessions.select_set(0)
        self._on_session_select(None)

    def _on_session_select(self, event):
        """Load messages from session into chat view."""
        idx = self.lst_sessions.curselection()
        if not idx:
            return
        sessions = self.db.get_sessions(self.current_project_id)
        self.current_session_id = sessions[idx[0]][0]

        self.txt_chat.delete("1.0", tk.END)
        messages = self.db.get_messages(self.current_session_id)
        
        for role, content, att, ts in messages:
            prefix = "User: " if role == "user" else "GLM-5.3-Flash: "
            self.txt_chat.insert(tk.END, f"{prefix}\n{content}\n\n" + "-"*50 + "\n\n")

    def _attach_code_file(self):
        """File picker for codebase context."""
        files = filedialog.askopenfilenames(title="Attach Code Files to 1M Context Window")
        if files:
            self.attached_files.extend(files)
            self._update_attachments_label()

    def _attach_image_file(self):
        """File picker for vision processing."""
        files = filedialog.askopenfilenames(title="Attach Screenshots or Diagrams", filetypes=[("Images", "*.png *.jpg *.jpeg")])
        if files:
            self.attached_images.extend(files)
            self._update_attachments_label()

    def _update_attachments_label(self):
        """Update context info bar text."""
        txt = f"Context Files: {len(self.attached_files)} | Images: {len(self.attached_images)}"
        self.lbl_attachments.config(text=txt)

    def _send_message(self):
        """Processes message input, manages threads and handles API stream."""
        user_text = self.txt_input.get("1.0", tk.END).strip()
        if not user_text and not self.attached_files and not self.attached_images:
            return

        # Render message on UI
        self.txt_chat.insert(tk.END, f"User:\n{user_text}\n\n")
        self.txt_input.delete("1.0", tk.END)

        # Save to Local DB
        attachments_meta = {"files": self.attached_files, "images": self.attached_images}
        self.db.add_message(self.current_session_id, "user", user_text, attachments_meta)

        # Build payload for API
        formatted_msg = self.api_client.build_multimodal_message(
            text=user_text,
            code_files=self.attached_files,
            image_paths=self.attached_images
        )

        # Clear active attachments after queueing
        self.attached_files = []
        self.attached_images = []
        self._update_attachments_label()

        # Start non-blocking stream thread
        self.txt_chat.insert(tk.END, "GLM-5.3-Flash:\n")
        threading.Thread(target=self._stream_response_worker, args=([formatted_msg],), daemon=True).start()

    def _stream_response_worker(self, messages_payload):
        """Background thread worker to handle server-sent event stream."""
        full_response = ""
        for token in self.api_client.generate_stream(messages_payload):
            full_response += token
            # Update GUI text dynamically
            self.root.after(10, self._append_token, token)

        self.root.after(10, self._finalize_stream, full_response)

    def _append_token(self, token: str):
        self.txt_chat.insert(tk.END, token)
        self.txt_chat.see(tk.END)

    def _finalize_stream(self, full_response: str):
        self.txt_chat.insert(tk.END, "\n\n" + "="*50 + "\n\n")
        self.txt_chat.see(tk.END)
        # Save response to SQLite
        self.db.add_message(self.current_session_id, "assistant", full_response)


if __name__ == "__main__":
    root = tk.Tk()
    app = GLMFlashDesktopApp(root)
    root.mainloop()
