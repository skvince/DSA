import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
import os
import sys
import subprocess
from database import Database, hash_password

class MSAPortalApp:
    def __init__(self, root):
        self.root = root
        self.root.title("MSAQC Portal")
        self.root.geometry("1200x700")

        self.db = Database()

        # Track currently selected row primary keys
        self.selected_id = None

        # Base Layout Panels
        self.sidebar = tk.Frame(root, bg="#0B2240", width=220)
        self.sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(root, bg="#F4F7FA")
        self.content.pack(side="right", fill="both", expand=True)

        # Sidebar header with logo and text aligned horizontally
        header_frame = tk.Frame(self.sidebar, bg="#0B2240")
        header_frame.pack(pady=20, padx=10, fill="x")

        # Logo on the left
        try:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            pil_img = Image.open(logo_path)
            pil_img = pil_img.resize((70, 70), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(pil_img)
            logo_label = tk.Label(header_frame, image=self.logo_img, bg="#0B2240")
            logo_label.pack(side="left", padx=(0, 5))
        except Exception:
            pass

        # MSAQC text on the right
        tk.Label(header_frame, text="MSAQC",
                 bg="#0B2240", fg="white",
                 font=("Arial", 16, "bold")).pack(side="left")

        # List of navigation buttons
        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Students", self.show_students),
            ("Teachers", self.show_teachers),
            ("Departments", self.show_departments),
            ("Sections", self.show_sections),
            ("Subjects", self.show_subjects),
            ("Assignments", self.show_assignments),
            ("Grade Deadlines", self.show_deadlines),
            ("Grade Request", self.show_approvals)
        ]

        self.nav_buttons = []
        for text, cmd in buttons:
            btn = tk.Button(self.sidebar, text=text,
                            command=lambda c=cmd, t=text: self._on_nav_click(c, t),
                            bg="#0B2240", fg="white", bd=0,
                            activebackground="#163866",
                            activeforeground="white", cursor="hand2",
                            font=("Arial", 11))
            btn.pack(fill="x", pady=5, padx=20)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#163866"))
            btn.bind("<Leave>", lambda e, b=btn, t=text: self._reset_nav_color(b, t))
            self.nav_buttons.append((btn, text))

        self.sidebar.pack_propagate(False)
        logout_frame = tk.Frame(self.sidebar, bg="#0B2240")
        logout_frame.pack(side="bottom", fill="x", padx=20, pady=20)
        logout_btn = tk.Button(logout_frame, text="Logout",
                               command=self.logout,
                               bg="#dc3545", fg="white", bd=0,
                               activebackground="#a71d2a",
                               activeforeground="white", cursor="hand2",
                               font=("Arial", 11, "bold"))
        logout_btn.pack(fill="x")
        logout_btn.bind("<Enter>", lambda e, b=logout_btn: b.configure(bg="#a71d2a"))
        logout_btn.bind("<Leave>", lambda e, b=logout_btn: b.configure(bg="#dc3545"))

        self.active_nav_text = None
        self.show_dashboard()

    def _set_active_nav(self, text):
        self.active_nav_text = text
        for b, t in self.nav_buttons:
            if t == text:
                b.configure(bg="#1f5f9e")
            else:
                b.configure(bg="#0B2240")

    def _reset_nav_color(self, btn, text):
        if text == self.active_nav_text:
            btn.configure(bg="#1f5f9e")
        else:
            btn.configure(bg="#0B2240")

    def _on_nav_click(self, cmd, text):
        self._set_active_nav(text)
        cmd()

    def _generate_default_password(self, new_id, surname):
        if not isinstance(new_id, int):
            numeric_part_str = str(new_id)
            numeric_part_str = "".join(c for c in numeric_part_str if c.isdigit())
            if not numeric_part_str:
                raise ValueError("Invalid ID format: numeric portion not found.")
            numeric_part = int(numeric_part_str)
        else:
            numeric_part = new_id
        formatted_surname = surname.replace(" ", "_")
        return f"{numeric_part}{formatted_surname}"

    def _add_search_filter(self, parent, table, columns, top_frame=None):
        if top_frame is None:
            search_frame = tk.Frame(parent, bg="#F4F7FA")
            search_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(5, 0))
        else:
            search_frame = top_frame
            search_frame.grid_columnconfigure(0, weight=1)
        
        tk.Label(search_frame, text="Search", bg="#F4F7FA").pack(side="right", padx=(0, 5))
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, width=25)
        search_entry.pack(side="right")
        search_entry.configure(textvariable=search_var)
        
        # Cache to store all original items and their values
        table._search_cache = {}
        
        def filter_table(event=None):
            query = search_var.get().lower().strip()
            
            # First refresh cache with current attached items
            for item in table.get_children():
                if item not in table._search_cache:
                    table._search_cache[item] = table.item(item, 'values')
            
            # If query is empty, restore all cached items
            if query == "":
                for item_id, values in table._search_cache.items():
                    table.reattach(item_id, '', 'end')
                return
            
            # Filter items based on query
            for item in table.get_children():
                values = table.item(item, 'values')
                match = any(str(v).lower().find(query) >= 0 for v in values)
                if not match:
                    table.detach(item)
        
        search_entry.bind("<KeyRelease>", filter_table)
        
        table.grid(row=1, column=0, sticky="nsew", pady=(5, 0))
        for child in parent.winfo_children():
            if isinstance(child, ttk.Scrollbar):
                info = child.grid_info()
                if info.get('row') in (0, 1) and info.get('column') == 1:
                    child.grid(row=1, column=1, sticky="ns")
                elif info.get('row') in (0, 1) and info.get('columnspan') == 2:
                    child.grid(row=2, column=0, columnspan=2, sticky="ew")
        
        parent.grid_rowconfigure(0, weight=0)
        parent.grid_rowconfigure(1, weight=1)
        parent.grid_columnconfigure(0, weight=1)
        
        return search_var, search_entry

    def logout(self):
        confirm = messagebox.askyesno("Logout", "Sigurado ka ba na gusto mong mag-logout?")
        if confirm:
            self.root.destroy()
            current_dir = os.path.dirname(os.path.abspath(__file__))
            login_script = os.path.join(current_dir, "login.py")
            subprocess.run([sys.executable, login_script])

    def clear_content(self):
        self.selected_id = None
        for w in self.content.winfo_children():
            w.destroy()

    # -----------------------------
    # DASHBOARD VIEW
    # -----------------------------
    def show_dashboard(self):
        self.clear_content()

        tk.Label(self.content, text="Dashboard",
                 font=("Arial", 24, "bold"), bg="#F4F7FA").pack(pady=20)

        stats = tk.Frame(self.content, bg="#F4F7FA")
        stats.pack()

        data = [
            ("Students", len(self.db.get_students())),
            ("Teachers", len(self.db.get_teachers())),
            ("Departments", len(self.db.get_departments())),
            ("Sections", len(self.db.get_sections()))
        ]

        for i, (title, value) in enumerate(data):
            card = tk.Frame(stats, bg="white", bd=1, relief="solid", width=180, height=100)
            card.grid(row=0, column=i, padx=10)
            card.pack_propagate(False)

            tk.Label(card, text=title, bg="white", font=("Arial", 11)).pack(pady=10)
            tk.Label(card, text=str(value), bg="white", font=("Arial", 20, "bold")).pack()

        dept_frame = tk.Frame(self.content, bg="#F4F7FA")
        dept_frame.pack(fill="both", expand=True, padx=20, pady=20)

        tk.Label(dept_frame, text="Students & Teachers per Department",
                 font=("Arial", 14, "bold"), bg="#F4F7FA").pack(anchor="w", pady=(0, 10))

        table_frame = tk.Frame(dept_frame, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True)

        table = ttk.Treeview(table_frame, columns=("Department", "Teachers", "Students"), show="headings")
        table.heading("Department", text="Department")
        table.heading("Teachers", text="Teachers")
        table.heading("Students", text="Students")
        table.column("Department", width=300, anchor="center")
        table.column("Teachers", width=150, anchor="center")
        table.column("Students", width=150, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        

        def populate_table():
            table.delete(*table.get_children())
            for row in self.db.get_department_counts():
                table.insert("", "end", values=(row[1], row[2], row[3]))

        populate_table()

    # -----------------------------
    # DEPARTMENTS MANAGEMENT
    # -----------------------------
    def show_departments(self):
        self.clear_content()

        tk.Label(self.content, text="Departments Management", font=("Arial", 20, "bold"), bg="#F4F7FA").pack(pady=(20, 10))

        form_container = tk.Frame(self.content, bg="#F4F7FA")
        form_container.pack(anchor="center")

        form = tk.Frame(form_container, bg="#F4F7FA")
        form.pack(pady=10)
            
        tk.Label(form, text="Department Name", bg="#F4F7FA").grid(row=0, column=0, padx=5, pady=5)
        dept_name_entry = tk.Entry(form, width=30)
        dept_name_entry.grid(row=0, column=1, padx=5, pady=5)
        
        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        table = ttk.Treeview(table_frame, columns=("ID", "NAME"), show="headings")
        table.heading("ID", text="ID")
        table.heading("NAME", text="Department Name")
        table.column("ID", width=50, anchor="center")
        table.column("NAME", width=200, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        def populate_table():
            table.delete(*table.get_children())
            for row in self.db.get_departments():
                table.insert("", "end", values=row)

        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            self.selected_id = values[0]
            dept_name_entry.delete(0, tk.END)
            dept_name_entry.insert(0, values[1])

        table.bind("<<TreeviewSelect>>", on_select)

        def add():
            if dept_name_entry.get().strip():
                self.db.add_department(dept_name_entry.get().strip())
                dept_name_entry.delete(0, tk.END)
                populate_table()
            else:
                messagebox.showwarning("Error", "Field cannot be empty")

        def update():
            if self.selected_id and dept_name_entry.get().strip():
                self.db.update_department(self.selected_id, dept_name_entry.get().strip())
                self.show_departments()
            else:
                messagebox.showwarning("Error", "Select a row first.")

        def delete():
            if self.selected_id:
                if messagebox.askyesno("Confirm", "Deleting this department will delete connected sections/teachers!"):
                    self.db.delete_department(self.selected_id)
                    self.show_departments()
            else:
                messagebox.showwarning("Error", "Select a row first.")

        btn_frame = tk.Frame(self.content, bg="#F4F7FA")
        btn_frame.pack(pady=5, anchor="center")
        tk.Button(btn_frame, text="Add New", command=add, bg="#28a745", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Update Selected", command=update, bg="#ffc107").grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=delete, bg="#dc3545", fg="white").grid(row=0, column=2, padx=5)

        populate_table()
    def show_sections(self):
        self.clear_content()
        tk.Label(self.content, text="Sections Management", font=("Arial", 20, "bold"), bg="#F4F7FA").pack(pady=(20, 10))

        form_container = tk.Frame(self.content, bg="#F4F7FA")
        form_container.pack(anchor="center")

        form = tk.Frame(form_container, bg="#F4F7FA")
        form.pack(pady=10)

        tk.Label(form, text="Section Name", bg="#F4F7FA").grid(row=0, column=0, padx=5, pady=5)
        sec_name_entry = tk.Entry(form, width=25)
        sec_name_entry.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(form, text="Department", bg="#F4F7FA").grid(row=1, column=0, padx=5, pady=5)
        
        dept_list = self.db.get_departments()
        dept_dict = {name: idx for idx, name in dept_list}
        
        dept_combo = ttk.Combobox(form, values=list(dept_dict.keys()), state="readonly", width=22)
        dept_combo.grid(row=1, column=1, padx=5, pady=5)
        
        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Corrected parent context to table_frame
        table = ttk.Treeview(table_frame, columns=("ID", "Section", "Department"), show="headings")
        table.column("ID", width=50, anchor="center")
        table.column("Section", width=180, anchor="center")
        table.column("Department", width=180, anchor="center")

        for c in ("ID", "Section", "Department"): table.heading(c, text=c)
   

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        def populate_table():
            table.delete(*table.get_children())
            for row in self.db.get_sections():
                table.insert("", "end", values=row)

        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            self.selected_id = values[0]
            sec_name_entry.delete(0, tk.END)
            sec_name_entry.insert(0, values[1])
            dept_combo.set(values[2])

        table.bind("<<TreeviewSelect>>", on_select)

        def add():
            dept_id = dept_dict.get(dept_combo.get())
            if sec_name_entry.get().strip() and dept_id:
                self.db.add_section(sec_name_entry.get().strip(), dept_id)
                self.show_sections()
            else:
                messagebox.showwarning("Error", "Please complete the form requirements.")

        def update():
            dept_id = dept_dict.get(dept_combo.get())
            if self.selected_id and sec_name_entry.get().strip() and dept_id:
                self.db.update_section(self.selected_id, sec_name_entry.get().strip(), dept_id)
                self.show_sections()
            else:
                messagebox.showwarning("Error", "Select a row and complete the form entries.")

        def delete():
            if self.selected_id:
                self.db.delete_section(self.selected_id)
                self.show_sections()
            else:
                messagebox.showwarning("Error", "Select a row first.")

        btn_frame = tk.Frame(self.content, bg="#F4F7FA")
        btn_frame.pack(pady=5, anchor="center")
        tk.Button(btn_frame, text="Add New", command=add, bg="#28a745", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Update Selected", command=update, bg="#ffc107").grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=delete, bg="#dc3545", fg="white").grid(row=0, column=2, padx=5)

        populate_table()

    # -----------------------------
    # TEACHERS MANAGEMENT
    # -----------------------------
    def show_teachers(self):
        self.clear_content()
        tk.Label(self.content, text="Teachers Management", font=("Arial", 20, "bold"), bg="#F4F7FA").pack(pady=(20, 10))

        form_container = tk.Frame(self.content, bg="#F4F7FA")
        form_container.pack(anchor="center")

        form = tk.Frame(form_container, bg="#F4F7FA")
        form.pack(pady=10)

        tk.Label(form, text="First Name", bg="#F4F7FA").grid(row=0, column=0, padx=5, pady=2)
        tf = tk.Entry(form); tf.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(form, text="Middle Name", bg="#F4F7FA").grid(row=1, column=0, padx=5, pady=2)
        tm = tk.Entry(form); tm.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(form, text="Last Name", bg="#F4F7FA").grid(row=2, column=0, padx=5, pady=2)
        tl = tk.Entry(form); tl.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(form, text="Department", bg="#F4F7FA").grid(row=3, column=0, padx=5, pady=2)
        dept_list = self.db.get_departments()
        dept_dict = {name: idx for idx, name in dept_list}
        dept_combo = ttk.Combobox(form, values=list(dept_dict.keys()), state="readonly")
        dept_combo.grid(row=3, column=1, padx=5, pady=2)

        generated_password_str = tk.StringVar()

        def auto_generate_password(event=None):
            first = tf.get().strip()
            last = tl.get().strip()
            if first and last:
                generated_password_str.set(first[0] + last)

        tf.bind("<KeyRelease>", auto_generate_password)
        tl.bind("<KeyRelease>", auto_generate_password)

        table_button_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_button_frame.pack(fill="x", padx=20, pady=(5, 0))
        show_pw_teacher = tk.BooleanVar(value=False)
        teacher_passwords = {}

        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        top_filter_frame = tk.Frame(table_frame, bg="#F4F7FA")
        top_filter_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(5, 0))

        tk.Label(top_filter_frame, text="Department", bg="#F4F7FA").pack(side="left", padx=(0, 5))
        dept_list = self.db.get_departments()
        dept_dict = {"All": None}
        dept_dict.update({name: idx for idx, name in dept_list})
        dept_filter_combo = ttk.Combobox(top_filter_frame, values=list(dept_dict.keys()), state="readonly", width=20)
        dept_filter_combo.set("All")
        dept_filter_combo.pack(side="left", padx=5)

        # Corrected parent context to table_frame
        table = ttk.Treeview(table_frame, columns=("ID", "First Name", "Middle Name", "Last Name", "Department", "Password"), show="headings")
        table.column("ID", width=50, anchor="center")
        table.column("First Name", width=120, anchor="center")
        table.column("Middle Name", width=140, anchor="center")
        table.column("Last Name", width=120, anchor="center")
        table.column("Department", width=130, anchor="center")
        table.column("Password", width=130, anchor="center")

        for c in ("ID", "First Name", "Middle Name", "Last Name", "Department", "Password"): table.heading(c, text=c)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self._add_search_filter(table_frame, table, ("ID", "First Name", "Middle Name", "Last Name", "Department", "Password"), top_frame=top_filter_frame)

        def mask_teacher_passwords():
            for item in table.get_children():
                vals = list(table.item(item, 'values'))
                if len(vals) >= 6:
                    pw = teacher_passwords.get(item, str(vals[5]))
                    vals[5] = '*******' if pw else ''
                    table.item(item, values=vals)

        def reveal_teacher_passwords():
            for item in table.get_children():
                values = list(table.item(item, 'values'))
                raw_id = str(values[0])
                t_id = int(raw_id.split('-')[1]) if '-' in raw_id else int(raw_id)
                surname = values[3]
                try:
                    plaintext = self._generate_default_password(t_id, surname)
                except ValueError:
                    plaintext = teacher_passwords.get(item, '')
                values[5] = plaintext
                table.item(item, values=values)


        def toggle_teacher_password():
            if show_pw_teacher.get():
                reveal_teacher_passwords()
            else:
                mask_teacher_passwords()

        tk.Checkbutton(table_button_frame, text="Show Password in Table", variable=show_pw_teacher,
                       command=toggle_teacher_password, bg="#F4F7FA", fg="#333",
                       font=("Arial", 10)).pack(side="right")

        def populate_table():
            table.delete(*table.get_children())
            teacher_passwords.clear()
            selected_dept = dept_filter_combo.get()
            dept_id = dept_dict.get(selected_dept)
            for row in self.db.get_teachers(dept_id=dept_id):
                t_id = row[0]
                display_row = (f"T-{int(t_id):03d}",) + row[1:]
                item_id = table.insert("", "end", values=display_row)
                if len(display_row) >= 6:
                    pw = str(display_row[5])
                    teacher_passwords[item_id] = pw
            toggle_teacher_password()

        def on_filter_change(event=None):
            populate_table()

        dept_filter_combo.bind("<<ComboboxSelected>>", on_filter_change)


        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            raw_id = str(values[0])
            self.selected_id = int(raw_id.split('-')[1]) if '-' in raw_id else int(raw_id)
            tf.delete(0, tk.END); tf.insert(0, values[1])
            tm.delete(0, tk.END); tm.insert(0, values[2])
            tl.delete(0, tk.END); tl.insert(0, values[3])
            dept_combo.set(values[4])
            try:
                generated_password_str.set(self._generate_default_password(self.selected_id, tl.get().strip()))
            except ValueError:
                generated_password_str.set(teacher_passwords.get(selected, values[5]))

        
        table.bind("<<TreeviewSelect>>", on_select)

        def add():
            d_id = dept_dict.get(dept_combo.get())
            if tf.get().strip() and tl.get().strip() and d_id:
                self.db.add_teacher(tf.get().strip(), tm.get().strip(), tl.get().strip(), d_id, "temp", None)
                new_id = self.db.cursor.lastrowid
                if new_id is None:
                    messagebox.showerror("Error", "Failed to create teacher. Please try again.")
                    return
                # Format teacher id as T-000 and generate password using that id.
                formatted_id = f"T-{int(new_id):03d}"  # type: ignore[reportArgumentType]
                try:
                    password = self._generate_default_password(new_id, tl.get().strip())
                except ValueError as e:
                    messagebox.showerror("Error", str(e))
                    return
                self.db.update_password("teachers", new_id, hash_password(password))
                generated_password_str.set(password)
                self.show_teachers()
            else: messagebox.showwarning("Error", "Check data constraints and retry.")

        def update():
            d_id = dept_dict.get(dept_combo.get())
            if self.selected_id and tf.get().strip() and tl.get().strip() and d_id:
                self.db.update_teacher(self.selected_id, tf.get().strip(), tm.get().strip(), tl.get().strip(), d_id)
                self.show_teachers()
            else: messagebox.showwarning("Error", "Ensure an element is selected.")

        def delete():
            if self.selected_id:
                if messagebox.askyesno("Confirm", "Deleting this teacher will delete connected assignments/grades!"):
                    self.db.delete_teacher(self.selected_id)
                    self.show_teachers()
            else: messagebox.showwarning("Error", "Select target profile first.")

        btn_frame = tk.Frame(self.content, bg="#F4F7FA")
        btn_frame.pack(pady=5, anchor="center")
        tk.Button(btn_frame, text="Add New", command=add, bg="#28a745", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Update Selected", command=update, bg="#ffc107").grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=delete, bg="#dc3545", fg="white").grid(row=0, column=2, padx=5)

        populate_table()

    # -----------------------------
    # STUDENTS MANAGEMENT
    # -----------------------------
    def show_students(self):
        self.clear_content()
        tk.Label(self.content, text="Students Management", font=("Arial", 20, "bold"), bg="#F4F7FA").pack(pady=(20, 10))

        form_container = tk.Frame(self.content, bg="#F4F7FA")
        form_container.pack(anchor="center")

        form = tk.Frame(form_container, bg="#F4F7FA")
        form.pack(pady=10)

        tk.Label(form, text="First Name", bg="#F4F7FA").grid(row=0, column=0, padx=5, pady=2)
        sf = tk.Entry(form); sf.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(form, text="Middle Name", bg="#F4F7FA").grid(row=1, column=0, padx=5, pady=2)
        sm = tk.Entry(form); sm.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(form, text="Last Name", bg="#F4F7FA").grid(row=2, column=0, padx=5, pady=2)
        sl = tk.Entry(form); sl.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(form, text="Department", bg="#F4F7FA").grid(row=3, column=0, padx=5, pady=2)
        dept_list_student = self.db.get_departments()
        dept_dict_student = {name: idx for idx, name in dept_list_student}
        dept_combo_student = ttk.Combobox(form, values=list(dept_dict_student.keys()), state="readonly")
        dept_combo_student.grid(row=3, column=1, padx=5, pady=2)

        tk.Label(form, text="Section", bg="#F4F7FA").grid(row=4, column=0, padx=5, pady=2)
        sec_list = self.db.get_sections()
        sec_dict = {row[1]: row[0] for row in sec_list}
        sec_combo = ttk.Combobox(form, values=list(sec_dict.keys()), state="readonly")
        sec_combo.grid(row=4, column=1, padx=5, pady=2)

        generated_password_student = tk.StringVar()

        def auto_generate_password_student(event=None):
            first = sf.get().strip()
            last = sl.get().strip()
            if first and last:
                generated_password_student.set(first[0] + last)

        sf.bind("<KeyRelease>", lambda e: auto_generate_password_student())
        sl.bind("<KeyRelease>", lambda e: auto_generate_password_student())

        table_button_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_button_frame.pack(fill="x", padx=20, pady=(5, 0))
        show_pw_student = tk.BooleanVar(value=False)
        student_passwords = {}

        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        top_filter_frame = tk.Frame(table_frame, bg="#F4F7FA")
        top_filter_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(5, 0))

        tk.Label(top_filter_frame, text="Department", bg="#F4F7FA").pack(side="left", padx=(0, 5))
        dept_list_student = self.db.get_departments()
        dept_dict_student = {"All": None}
        dept_dict_student.update({name: idx for idx, name in dept_list_student})
        dept_filter_combo = ttk.Combobox(top_filter_frame, values=list(dept_dict_student.keys()), state="readonly", width=20)
        dept_filter_combo.set("All")
        dept_filter_combo.pack(side="left", padx=5)

        # Corrected parent context to table_frame
        table = ttk.Treeview(table_frame, columns=("ID", "First Name", "Middle Name", "Last Name", "Department", "Section", "Password"), show="headings")
        table.column("ID", width=50, anchor="center")
        table.column("First Name", width=120, anchor="center")
        table.column("Middle Name", width=140, anchor="center")
        table.column("Last Name", width=120, anchor="center")
        table.column("Department", width=130, anchor="center")
        table.column("Section", width=140, anchor="center")
        table.column("Password", width=130, anchor="center")

        for c in ("ID", "First Name", "Middle Name", "Last Name", "Department", "Section", "Password"):
            table.heading(c, text=c)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self._add_search_filter(table_frame, table, ("ID", "First Name", "Middle Name", "Last Name", "Department", "Section", "Password"), top_frame=top_filter_frame)

        def mask_passwords():
            for item in table.get_children():
                vals = list(table.item(item, 'values'))
                if len(vals) >= 7:
                    pw = student_passwords.get(item, str(vals[6]))
                    vals[6] = '********'if pw else ''
                    table.item(item, values=vals)

        def reveal_passwords():
            for item in table.get_children():
                values = list(table.item(item, 'values'))
                raw_id = str(values[0])
                s_id = int(raw_id.split('-')[1]) if '-' in raw_id else int(raw_id)
                surname = values[3]
                try:
                    plaintext = self._generate_default_password(s_id, surname)
                except ValueError:
                    plaintext = student_passwords.get(item, values[6])
                values[6] = plaintext
                table.item(item, values=values)


        def toggle_password():
            if show_pw_student.get():
                reveal_passwords()
            else:
                mask_passwords()

        tk.Checkbutton(table_button_frame, text="Show Password in Table", variable=show_pw_student,
                       command=toggle_password, bg="#F4F7FA", fg="#333",
                       font=("Arial", 10)).pack(side="right")

        def populate_table():
            table.delete(*table.get_children())
            student_passwords.clear()
            selected_dept = dept_filter_combo.get()
            dept_id = dept_dict_student.get(selected_dept)
            for row in self.db.get_students(dept_id=dept_id):
                s_id = row[0]
                display_row = (f"S-{int(s_id):03d}",) + row[1:]
                item_id = table.insert("", "end", values=display_row)
                if len(display_row) >= 7:
                    pw = str(display_row[6])
                    student_passwords[item_id] = pw
            toggle_password()

        def on_filter_change(event=None):
            populate_table()

        dept_filter_combo.bind("<<ComboboxSelected>>", on_filter_change)

        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            raw_id = str(values[0])
            self.selected_id = int(raw_id.split('-')[1]) if '-' in raw_id else int(raw_id)
            sf.delete(0, tk.END); sf.insert(0, values[1])
            sm.delete(0, tk.END); sm.insert(0, values[2])
            sl.delete(0, tk.END); sl.insert(0, values[3])
            dept_combo_student.set(values[4])
            sec_combo.set(values[5])
            try:
                generated_password_student.set(self._generate_default_password(self.selected_id, sl.get().strip()))
            except ValueError:
                generated_password_student.set(student_passwords.get(selected, values[6]))


        table.bind("<<TreeviewSelect>>", on_select)

        def add():
            s_id = sec_dict.get(sec_combo.get())
            if sf.get().strip() and sl.get().strip() and s_id:
                self.db.add_student(sf.get().strip(), sm.get().strip(), sl.get().strip(), s_id, "temp")
                new_id = self.db.cursor.lastrowid
                if new_id is None:
                    messagebox.showerror("Error", "Failed to create student. Please try again.")
                    return
                # Format student id as S-000 and generate password using that id.
                formatted_id = f"S-{int(new_id):03d}"  # type: ignore[reportArgumentType]
                try:
                    password = self._generate_default_password(new_id, sl.get().strip())
                except ValueError as e:
                    messagebox.showerror("Error", str(e))
                    return
                self.db.update_password("students", new_id, hash_password(password))
                generated_password_student.set(password)
                self.show_students()
            else: messagebox.showwarning("Error", "Fill out all fields.")

        def update():
            s_id = sec_dict.get(sec_combo.get())
            if self.selected_id and sf.get().strip() and sl.get().strip() and s_id:
                self.db.update_student(self.selected_id, sf.get().strip(), sm.get().strip(), sl.get().strip(), s_id)
                self.show_students()
            else: messagebox.showwarning("Error", "Select a valid row entry.")
        def delete():
            if self.selected_id:
                if messagebox.askyesno("Confirm", "Deleting this student will delete connected grades!"):
                    self.db.delete_student(self.selected_id)
                    self.show_students()
            else:
                messagebox.showwarning("Error", "Select a row record.")

        btn_frame = tk.Frame(self.content, bg="#F4F7FA")
        btn_frame.pack(pady=5, anchor="center")
        tk.Button(btn_frame, text="Add New", command=add, bg="#28a745", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Update Selected", command=update, bg="#ffc107").grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=delete, bg="#dc3545", fg="white").grid(row=0, column=2, padx=5)

        populate_table()

    # -----------------------------
    # ASSIGNMENTS MANAGEMENT
    # -----------------------------
    def show_assignments(self):
        self.clear_content()
        tk.Label(self.content, text="Assignments Management", font=("Arial", 20, "bold"), bg="#F4F7FA").pack(pady=(20, 10))

        form_container = tk.Frame(self.content, bg="#F4F7FA")
        form_container.pack(anchor="center")

        form = tk.Frame(form_container, bg="#F4F7FA")
        form.pack(pady=10)

        teacher_list = self.db.get_teachers()
        teacher_dict = {f"{row[1]} {row[2]} {row[3]}".replace("  ", " ").strip(): row[0] for row in teacher_list}

        sec_list = self.db.get_sections()
        sec_dict = {row[1]: row[0] for row in sec_list}

        subject_list = self.db.get_subjects()
        subject_names = sorted({row[2] for row in subject_list})

        tk.Label(form, text="Teacher Name", bg="#F4F7FA").grid(row=0, column=0, padx=5, pady=2)
        teacher_combo = ttk.Combobox(form, values=list(teacher_dict.keys()), state="readonly")
        teacher_combo.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(form, text="Subject", bg="#F4F7FA").grid(row=1, column=0, padx=5, pady=2)
        sub_combo = ttk.Combobox(form, values=subject_names, state="readonly", width=22)
        sub_combo.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(form, text="Section", bg="#F4F7FA").grid(row=2, column=0, padx=5, pady=2)
        sec_combo = ttk.Combobox(form, values=list(sec_dict.keys()), state="readonly")
        sec_combo.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(form, text="Academic Year", bg="#F4F7FA").grid(row=3, column=0, padx=5, pady=2)
        ay_combo = ttk.Combobox(form, values=[f"{y}-{y+1}" for y in range(2024, 2027)], state="readonly", width=22)
        ay_combo.grid(row=3, column=1, padx=5, pady=2)

        tk.Label(form, text="Semester", bg="#F4F7FA").grid(row=4, column=0, padx=5, pady=2)
        sem_combo = ttk.Combobox(form, values=["1st Semester", "2nd Semester", "Summer"], state="readonly")
        sem_combo.grid(row=4, column=1, padx=5, pady=2)

        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Corrected parent context to table_frame
        table = ttk.Treeview(table_frame, columns=("ID", "Teacher", "Subject", "Section", "Academic Year", "Semester"), show="headings")
        for c in ("ID", "Teacher", "Subject", "Section", "Academic Year", "Semester"):
            table.heading(c, text=c)

        # Center all assignment table columns
        table.column("ID", width=50, anchor="center")
        table.column("Teacher", width=180, anchor="center")
        table.column("Subject", width=180, anchor="center")
        table.column("Section", width=180, anchor="center")
        table.column("Academic Year", width=120, anchor="center")
        table.column("Semester", width=130, anchor="center")


        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self._add_search_filter(table_frame, table, ("ID", "Teacher", "Subject", "Section", "Academic Year", "Semester"))

        def populate_table():
            table.delete(*table.get_children())
            for row in self.db.get_assignments(): 
                table.insert("", "end", values=row)

        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            self.selected_id = values[0]
            teacher_combo.set(values[1])
            sub_combo.set(values[2])
            sec_combo.set(values[3])
            ay_combo.set(values[4])
            sem_combo.set(values[5])

        table.bind("<<TreeviewSelect>>", on_select)

        def add():
            t_id = teacher_dict.get(teacher_combo.get())
            s_id = sec_dict.get(sec_combo.get())
            subject = sub_combo.get().strip()
            ay = ay_combo.get().strip()
            sem = sem_combo.get()

            if t_id and s_id and subject and ay and sem:
                self.db.add_assignment(t_id, subject, s_id, ay, sem)
                self.show_assignments()
            else: 
                messagebox.showwarning("Error", "Please complete all Assignment fields.")

        def update():
            t_id = teacher_dict.get(teacher_combo.get())
            s_id = sec_dict.get(sec_combo.get())
            subject = sub_combo.get().strip()
            ay = ay_combo.get().strip()
            sem = sem_combo.get()

            if self.selected_id and t_id and s_id and subject and ay and sem:
                self.db.update_assignment(self.selected_id, t_id, subject, s_id, ay, sem)
                self.show_assignments()
            else: 
                messagebox.showwarning("Error", "Select an active assignment record first.")

        def delete():
            if self.selected_id:
                self.db.delete_assignment(self.selected_id)
                self.show_assignments()
            else: 
                messagebox.showwarning("Error", "Choose an assignment to drop.")

        btn_frame = tk.Frame(self.content, bg="#F4F7FA")
        btn_frame.pack(pady=5, anchor="center")
        tk.Button(btn_frame, text="Add New", command=add, bg="#28a745", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Update Selected", command=update, bg="#ffc107").grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=delete, bg="#dc3545", fg="white").grid(row=0, column=2, padx=5)

        populate_table()

    # -----------------------------
    # SUBJECTS MANAGEMENT
    # -----------------------------
    def show_subjects(self):
        self.clear_content()
        tk.Label(self.content, text="Subjects Management", font=("Arial", 20, "bold"), bg="#F4F7FA").pack(pady=(20, 10))

        filter_frame = tk.Frame(self.content, bg="#F4F7FA")
        filter_frame.pack(pady=5, anchor="center")

        tk.Label(filter_frame, text="School Year", bg="#F4F7FA").grid(row=0, column=0, padx=5, pady=2)
        ay_filter = ttk.Combobox(filter_frame, values=[""] + [f"{y}-{y+1}" for y in range(2024, 2027)], state="readonly", width=15)
        ay_filter.grid(row=0, column=1, padx=5, pady=2)
        ay_filter.set("")

        tk.Label(filter_frame, text="Semester", bg="#F4F7FA").grid(row=0, column=2, padx=5, pady=2)
        sem_filter = ttk.Combobox(filter_frame, values=["", "1st Semester", "2nd Semester", "Summer"], state="readonly", width=15)
        sem_filter.grid(row=0, column=3, padx=5, pady=2)
        sem_filter.set("")

        form_container = tk.Frame(self.content, bg="#F4F7FA")
        form_container.pack(anchor="center")

        form = tk.Frame(form_container, bg="#F4F7FA")
        form.pack(pady=10)

        tk.Label(form, text="Subject Code", bg="#F4F7FA", anchor="w", width=15).grid(row=0, column=0, padx=5, pady=5, sticky="w")
        code_entry = tk.Entry(form, width=30); code_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(form, text="Subject Name", bg="#F4F7FA", anchor="w", width=15).grid(row=1, column=0, padx=5, pady=5, sticky="w")
        name_entry = tk.Entry(form, width=30); name_entry.grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(form, text="School Year", bg="#F4F7FA", anchor="w", width=15).grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ay_combo = ttk.Combobox(form, values=[f"{y}-{y+1}" for y in range(2024, 2027)], state="readonly", width=27)
        ay_combo.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(form, text="Semester", bg="#F4F7FA", anchor="w", width=15).grid(row=3, column=0, padx=5, pady=5, sticky="w")
        sem_combo = ttk.Combobox(form, values=["1st Semester", "2nd Semester", "Summer"], state="readonly", width=27)
        sem_combo.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        tk.Label(form, text="Units", bg="#F4F7FA", anchor="w", width=15).grid(row=4, column=0, padx=5, pady=5, sticky="w")
        units_entry = tk.Entry(form, width=30); units_entry.grid(row=4, column=1, padx=5, pady=5, sticky="ew")

        form.grid_columnconfigure(1, weight=1)

        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        table = ttk.Treeview(table_frame, columns=("ID", "Code", "Name", "School Year", "Semester", "Units"), show="headings")
        for c in ("ID", "Code", "Name", "School Year", "Semester", "Units"):
            table.heading(c, text=c)
        table.column("ID", width=50, anchor="center")
        table.column("Code", width=80, anchor="center")
        table.column("Name", width=180, anchor="center")
        table.column("School Year", width=100, anchor="center")
        table.column("Semester", width=100, anchor="center")
        table.column("Units", width=60, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self._add_search_filter(table_frame, table, ("ID", "Code", "Name", "School Year", "Semester", "Units"))

        def populate_table():
            table.delete(*table.get_children())
            ay = ay_filter.get().strip() or None
            sem = sem_filter.get() or None
            for row in self.db.get_subjects(school_year=ay, semester=sem):
                table.insert("", "end", values=row)

        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            self.selected_id = values[0]
            code_entry.delete(0, tk.END); code_entry.insert(0, values[1])
            name_entry.delete(0, tk.END); name_entry.insert(0, values[2])
            ay_combo.set(values[3])
            sem_combo.set(values[4])
            units_entry.delete(0, tk.END); units_entry.insert(0, values[5])

        table.bind("<<TreeviewSelect>>", on_select)

        def add():
            if code_entry.get().strip() and name_entry.get().strip() and ay_combo.get() and sem_combo.get() and units_entry.get().strip():
                try:
                    units = int(units_entry.get().strip())
                    success = self.db.add_subject(code_entry.get().strip(), name_entry.get().strip(), ay_combo.get(), sem_combo.get(), units)
                    if not success:
                        messagebox.showerror("Error", "Subject code already exists. Please use a unique code.")
                        return
                    self.show_subjects()
                except ValueError:
                    messagebox.showwarning("Error", "Units must be a number.")
            else:
                messagebox.showwarning("Error", "Please complete all fields.")

        def update():
            if self.selected_id and code_entry.get().strip() and name_entry.get().strip() and ay_combo.get() and sem_combo.get() and units_entry.get().strip():
                try:
                    units = int(units_entry.get().strip())
                    self.db.update_subject(self.selected_id, code_entry.get().strip(), name_entry.get().strip(), ay_combo.get(), sem_combo.get(), units)
                    self.show_subjects()
                except ValueError:
                    messagebox.showwarning("Error", "Units must be a number.")
            else:
                messagebox.showwarning("Error", "Select a row and complete the form entries.")

        def delete():
            if self.selected_id:
                if messagebox.askyesno("Confirm", "Deleting this subject will delete connected assignments!"):
                    self.db.delete_subject(self.selected_id)
                    self.show_subjects()
            else:
                messagebox.showwarning("Error", "Select a subject first.")

        def apply_filter(event=None):
            populate_table()

        ay_filter.bind("<<ComboboxSelected>>", apply_filter)
        sem_filter.bind("<<ComboboxSelected>>", apply_filter)

        btn_frame = tk.Frame(self.content, bg="#F4F7FA")
        btn_frame.pack(pady=5, anchor="center")
        tk.Button(btn_frame, text="Add New", command=add, bg="#28a745", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Update Selected", command=update, bg="#ffc107").grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=delete, bg="#dc3545", fg="white").grid(row=0, column=2, padx=5)

        populate_table()

    # -----------------------------
    # GRADE ENCODING DEADLINES MANAGEMENT
    # -----------------------------
    def show_deadlines(self):
        self.clear_content()
        tk.Label(self.content, text="Grade Encoding Deadlines", font=("Arial", 20, "bold"), bg="#F4F7FA").pack(pady=(20, 10))

        form_container = tk.Frame(self.content, bg="#F4F7FA")
        form_container.pack(anchor="center")

        form = tk.Frame(form_container, bg="#F4F7FA")
        form.pack(pady=10)

        tk.Label(form, text="School Year", bg="#F4F7FA").grid(row=0, column=0, padx=5, pady=2)
        ay_combo = ttk.Combobox(form, values=[f"{y}-{y+1}" for y in range(2024, 2027)], state="readonly", width=22)
        ay_combo.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(form, text="Semester", bg="#F4F7FA").grid(row=1, column=0, padx=5, pady=2)
        sem_combo = ttk.Combobox(form, values=["1st Semester", "2nd Semester", "Summer"], state="readonly", width=22)
        sem_combo.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(form, text="Grading Period", bg="#F4F7FA").grid(row=2, column=0, padx=5, pady=2)
        period_combo = ttk.Combobox(form, values=["Prelim", "Midterm", "Final"], state="readonly", width=22)
        period_combo.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(form, text="Start Date (YYYY-MM-DD)", bg="#F4F7FA").grid(row=3, column=0, padx=5, pady=2)
        start_entry = tk.Entry(form, width=23); start_entry.grid(row=3, column=1, padx=5, pady=2)

        tk.Label(form, text="End Date (YYYY-MM-DD)", bg="#F4F7FA").grid(row=4, column=0, padx=5, pady=2)
        end_entry = tk.Entry(form, width=23); end_entry.grid(row=4, column=1, padx=5, pady=2)

        def refresh_open_period():
            ay = ay_combo.get().strip()
            sem = sem_combo.get()
            period = period_combo.get()
            start = start_entry.get().strip()
            end = end_entry.get().strip()
            if ay and sem and period and start and end:
                from datetime import datetime
                today = datetime.now().strftime("%Y-%m-%d")
                if start <= today <= end:
                    self.db.set_open_period(ay, sem, period)
                else:
                    self.db.set_open_period(ay, sem, None)

        sep = tk.Frame(self.content, height=2, bg="#ccc")
        sep.pack(fill="x", padx=20, pady=10)

        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        table = ttk.Treeview(table_frame, columns=("ID", "School Year", "Semester", "Period", "Start", "End", "Status"), show="headings")
        for c in ("ID", "School Year", "Semester", "Period", "Start", "End", "Status"):
            table.heading(c, text=c)
        table.column("ID", width=50, anchor="center")
        table.column("School Year", width=100, anchor="center")
        table.column("Semester", width=100, anchor="center")
        table.column("Period", width=90, anchor="center")
        table.column("Start", width=100, anchor="center")
        table.column("End", width=100, anchor="center")
        table.column("Status", width=80, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        def populate_table():
            table.delete(*table.get_children())
            for row in self.db.get_deadlines():
                table.insert("", "end", values=row)

        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            self.selected_id = values[0]
            ay_combo.set(values[1])
            sem_combo.set(values[2])
            period_combo.set(values[3])
            start_entry.delete(0, tk.END); start_entry.insert(0, values[4])
            end_entry.delete(0, tk.END); end_entry.insert(0, values[5])
            refresh_open_period()

        table.bind("<<TreeviewSelect>>", on_select)

        def add():
            if ay_combo.get() and sem_combo.get() and period_combo.get() and start_entry.get().strip() and end_entry.get().strip():
                ok = self.db.add_deadline(ay_combo.get().strip(), sem_combo.get(), period_combo.get(), start_entry.get().strip(), end_entry.get().strip())
                if not ok:
                    messagebox.showwarning("Error", "An active deadline already exists for this year, semester, and period.")
                else:
                    refresh_open_period()
                    self.show_deadlines()
            else:
                messagebox.showwarning("Error", "Please complete all fields.")

        def update_status():
            if self.selected_id:
                self.db.update_deadline_status(self.selected_id, "Closed")
                refresh_open_period()
                self.show_deadlines()
            else:
                messagebox.showwarning("Error", "Select a deadline first.")

        def delete():
            if self.selected_id:
                if messagebox.askyesno("Confirm", "Delete this deadline?"):
                    self.db.delete_deadline(self.selected_id)
                    refresh_open_period()
                    self.show_deadlines()
            else:
                messagebox.showwarning("Error", "Select a deadline first.")

        def set_open_from_form():
            refresh_open_period()
            messagebox.showinfo("Open Period Updated", "The open grading period has been set based on the selected deadline and current date.")

        btn_frame = tk.Frame(self.content, bg="#F4F7FA")
        btn_frame.pack(pady=5, anchor="center")
        tk.Button(btn_frame, text="Add New", command=add, bg="#28a745", fg="white").grid(row=0, column=0, padx=5)
        tk.Button(btn_frame, text="Close Deadline", command=update_status, bg="#ffc107").grid(row=0, column=1, padx=5)
        tk.Button(btn_frame, text="Delete Selected", command=delete, bg="#dc3545", fg="white").grid(row=0, column=2, padx=5)
        tk.Button(btn_frame, text="Set Open Period", command=set_open_from_form, bg="#0B2240", fg="white").grid(row=0, column=3, padx=5)

        populate_table()

    # -----------------------------
    # EXTENSION REQUESTS / APPROVALS
    # -----------------------------
    def show_approvals(self):
        self.clear_content()
        tk.Label(self.content, text="Teacher Requests Approval", font=("Arial", 20, "bold"), bg="#F4F7FA").pack(pady=(20, 10))

        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        top_filter_frame = tk.Frame(table_frame, bg="#F4F7FA")
        top_filter_frame.grid(row=0, column=0, columnspan=2, sticky="ew", padx=20, pady=(5, 0))

        tk.Label(top_filter_frame, text="Filter by Department:", bg="#F4F7FA").pack(side="left", padx=(0, 5))
        dept_list = self.db.get_departments()
        dept_dict = {"All": None}
        dept_dict.update({name: idx for idx, name in dept_list})
        dept_combo = ttk.Combobox(top_filter_frame, values=list(dept_dict.keys()), state="readonly", width=20)
        dept_combo.set("All")
        dept_combo.pack(side="left", padx=5)

        table = ttk.Treeview(table_frame, columns=("ID", "Teacher", "Department", "Subject", "Section", "School Year", "Semester", "Periods", "Reason", "Status", "Remarks"), show="headings")
        for c in ("ID", "Teacher", "Department", "Subject", "Section", "School Year", "Semester", "Periods", "Reason", "Status", "Remarks"):
            table.heading(c, text=c)
        table.column("ID", width=40, anchor="center")
        table.column("Teacher", width=120, anchor="center")
        table.column("Department", width=100, anchor="center")
        table.column("Subject", width=100, anchor="center")
        table.column("Section", width=80, anchor="center")
        table.column("School Year", width=80, anchor="center")
        table.column("Semester", width=80, anchor="center")
        table.column("Periods", width=100, anchor="center")
        table.column("Reason", width=130, anchor="w")
        table.column("Status", width=70, anchor="center")
        table.column("Remarks", width=130, anchor="w")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=1, column=0, sticky="nsew")
        vsb.grid(row=1, column=1, sticky="ns")
        hsb.grid(row=2, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(1, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        self._add_search_filter(table_frame, table, ("ID", "Teacher", "Department", "Subject", "Section", "School Year", "Semester", "Periods", "Reason", "Status", "Remarks"), top_frame=top_filter_frame)

        def populate_table():
            table.delete(*table.get_children())
            selected_dept = dept_combo.get()
            dept_id = dept_dict.get(selected_dept)
            for row in self.db.get_extension_requests(dept_id=dept_id):
                values = (
                    row[0],      # ID
                    row[2],      # Teacher
                    row[6],      # Department
                    row[3],      # Subject
                    row[5],      # Section
                    row[7],      # School Year
                    row[8],      # Semester
                    row[9],      # Periods
                    row[10],     # Reason
                    row[11],     # Status
                    row[12]      # Remarks
                )
                table.insert("", "end", values=values)

        def on_filter_change(event=None):
            populate_table()

        dept_combo.bind("<<ComboboxSelected>>", on_filter_change)

        def approve():
            selected = table.focus()
            if not selected:
                messagebox.showwarning("Error", "Select a request first.")
                return
            values = table.item(selected, 'values')
            req_id = values[0]
            status = values[9]
            if status != "Pending":
                messagebox.showwarning("Error", "Only pending requests can be approved.")
                return

            request = self.db.get_request_by_id(req_id)
            if not request:
                messagebox.showerror("Error", "Request not found.")
                return

            popup = tk.Toplevel(self.root)
            popup.title("Approve Request")
            popup.geometry("420x220")
            popup.configure(bg="#F4F7FA")
            popup.resizable(False, False)
            popup.transient(self.root)
            popup.grab_set()

            tk.Label(popup, text="Admin Remarks (optional)", bg="#F4F7FA").pack(pady=10)
            remarks_entry = tk.Entry(popup, width=40)
            remarks_entry.pack(pady=5)

            def confirm():
                remarks = remarks_entry.get().strip()
                self.db.update_request_status(req_id, "Approved", remarks)
                grading_periods = [p.strip() for p in request[9].split(",")]
                self.db.unlock_grade_periods(request[3], request[4], request[6], request[7], grading_periods)
                if grading_periods:
                    self.db.set_open_period(request[6], request[7], grading_periods[0])
                self.db.add_notification(
                    user_id=request[1],
                    user_role="Teacher",
                    title="Grade Reopen Request Approved",
                    message=f"Your request to reopen {request[9]} for {request[3]} has been approved."
                )
                popup.destroy()
                self.show_approvals()

            tk.Button(popup, text="Confirm Approval", command=confirm, bg="#28a745", fg="white", width=16).pack(pady=15)

        def reject():
            selected = table.focus()
            if not selected:
                messagebox.showwarning("Error", "Select a request first.")
                return
            values = table.item(selected, 'values')
            req_id = values[0]
            status = values[9]
            if status != "Pending":
                messagebox.showwarning("Error", "Only pending requests can be rejected.")
                return

            request = self.db.get_request_by_id(req_id)
            if not request:
                messagebox.showerror("Error", "Request not found.")
                return

            popup = tk.Toplevel(self.root)
            popup.title("Reject Request")
            popup.geometry("420x220")
            popup.configure(bg="#F4F7FA")
            popup.resizable(False, False)
            popup.transient(self.root)
            popup.grab_set()

            tk.Label(popup, text="Admin Remarks (required)", bg="#F4F7FA").pack(pady=10)
            remarks_entry = tk.Entry(popup, width=40)
            remarks_entry.pack(pady=5)

            def confirm():
                remarks = remarks_entry.get().strip()
                if not remarks:
                    messagebox.showwarning("Error", "Please provide remarks for the rejection.", parent=popup)
                    return
                self.db.update_request_status(req_id, "Rejected", remarks)
                self.db.add_notification(
                    user_id=request[1],
                    user_role="Teacher",
                    title="Grade Reopen Request Rejected",
                    message=f"Your request to reopen {request[9]} for {request[3]} has been rejected. Remarks: {remarks}"
                )
                popup.destroy()
                self.show_approvals()

            tk.Button(popup, text="Confirm Rejection", command=confirm, bg="#dc3545", fg="white", width=16).pack(pady=15)

        action_frame = tk.Frame(self.content, bg="#F4F7FA")
        action_frame.pack(pady=5, anchor="center")
        tk.Button(action_frame, text="Approve Selected", command=approve, bg="#28a745", fg="white").pack(side="left", padx=5)
        tk.Button(action_frame, text="Reject Selected", command=reject, bg="#dc3545", fg="white").pack(side="left", padx=5)

        populate_table()

if __name__ == "__main__":
    root = tk.Tk()
    app = MSAPortalApp(root)
    root.mainloop()