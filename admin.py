import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys
import subprocess
from database import Database

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
        self.sidebar.pack_propagate(False) # Prevents the sidebar from shrinking

        self.content = tk.Frame(root, bg="#F4F7FA")
        self.content.pack(side="right", fill="both", expand=True)

        tk.Label(self.sidebar, text="MSAQC Portal",
                 bg="#0B2240", fg="white",
                 font=("Arial", 16, "bold")).pack(pady=20)

        # List of navigation buttons
        buttons = [
            ("Dashboard", self.show_dashboard),
            ("Students", self.show_students),
            ("Teachers", self.show_teachers),
            ("Departments", self.show_departments),
            ("Sections", self.show_sections),
            ("Assignments", self.show_assignments)
        ]

        for text, cmd in buttons:
            tk.Button(self.sidebar, text=text, command=cmd,
                      bg="#0B2240", fg="white", bd=0, activebackground="#163866",
                      activeforeground="white", cursor="hand2", font=("Arial", 11)).pack(fill="x", pady=5, padx=20)

        # LOGOUT BUTTON
        tk.Button(self.sidebar, text="Logout", command=self.logout,
                  bg="#dc3545", fg="white", bd=0, activebackground="#c82333",
                  activeforeground="white", font=("Arial", 10, "bold"), cursor="hand2").pack(fill="x", side="bottom", pady=20, padx=20)

        self.show_dashboard()

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

    # -----------------------------
    # SECTIONS MANAGEMENT
    # -----------------------------
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
        table = ttk.Treeview(table_frame, columns=("ID", "SEC", "DEPT"), show="headings")
        table.column("ID", width=50, anchor="center")
        table.column("SEC", width=180, anchor="center")
        table.column("DEPT", width=180, anchor="center")

        for c in ("ID", "SEC", "DEPT"): table.heading(c, text=c)

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

        # Corrected parent context to table_frame
        table = ttk.Treeview(table_frame, columns=("ID", "FN", "LN", "DEPT", "PASSWORD"), show="headings")
        table.column("ID", width=50, anchor="center")
        table.column("FN", width=140, anchor="center")
        table.column("LN", width=140, anchor="center")
        table.column("DEPT", width=130, anchor="center")
        table.column("PASSWORD", width=130, anchor="center")

        for c in ("ID", "FN", "LN", "DEPT", "PASSWORD"): table.heading(c, text=c)

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        def mask_teacher_passwords():
            for item in table.get_children():
                vals = list(table.item(item, 'values'))
                if len(vals) >= 5:
                    pw = teacher_passwords.get(item, str(vals[4]))
                    vals[4] = '*' * len(pw) if pw else ''
                    table.item(item, values=vals)

        def reveal_teacher_passwords():
            for item in table.get_children():
                vals = list(table.item(item, 'values'))
                if len(vals) >= 5:
                    raw_pw = teacher_passwords.get(item, str(vals[4]))
                    vals[4] = raw_pw if raw_pw else ''
                    table.item(item, values=vals)

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
            for row in self.db.get_teachers():
                item_id = table.insert("", "end", values=row)
                if len(row) >= 5:
                    pw = str(row[4])
                    teacher_passwords[item_id] = pw
            toggle_teacher_password()

        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            self.selected_id = values[0]
            tf.delete(0, tk.END); tf.insert(0, values[1])
            tm.delete(0, tk.END)
            tl.delete(0, tk.END); tl.insert(0, values[2])
            dept_combo.set(values[3])
            actual_pw = teacher_passwords.get(selected, values[4])
            generated_password_str.set(actual_pw)
        
        table.bind("<<TreeviewSelect>>", on_select)

        def add():
            d_id = dept_dict.get(dept_combo.get())
            if tf.get().strip() and tl.get().strip() and d_id:
                self.db.add_teacher(tf.get().strip(), tm.get().strip(), tl.get().strip(), d_id, "temp")
                new_id = self.db.cursor.lastrowid
                password = f"{new_id}{tl.get().strip()}"
                self.db.update_password("teachers", new_id, password)
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

        tk.Label(form, text="Section", bg="#F4F7FA").grid(row=3, column=0, padx=5, pady=2)
        sec_list = self.db.get_sections()
        sec_dict = {row[1]: row[0] for row in sec_list}
        sec_combo = ttk.Combobox(form, values=list(sec_dict.keys()), state="readonly")
        sec_combo.grid(row=3, column=1, padx=5, pady=2)

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
        show_pw = tk.BooleanVar(value=False)
        student_passwords = {}

        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Corrected parent context to table_frame
        table = ttk.Treeview(table_frame, columns=("ID", "First Name", "Last Name", "Section", "PASSWORD"), show="headings")
        table.column("ID", width=50, anchor="center")
        table.column("First Name", width=140, anchor="center")
        table.column("Last Name", width=140, anchor="center")
        table.column("Section", width=140, anchor="center")
        table.column("PASSWORD", width=130, anchor="center")

        for c in ("ID", "First Name", "Last Name", "Section", "PASSWORD"):
            table.heading(c, text=c)


        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        def mask_passwords():
            for item in table.get_children():
                vals = list(table.item(item, 'values'))
                if len(vals) >= 5:
                    pw = student_passwords.get(item, str(vals[4]))
                    vals[4] = '*' * len(pw) if pw else ''
                    table.item(item, values=vals)

        def reveal_passwords():
            for item in table.get_children():
                vals = list(table.item(item, 'values'))
                if len(vals) >= 5:
                    raw_pw = student_passwords.get(item, '')
                    vals[4] = raw_pw
                    table.item(item, values=vals)

        def toggle_password():
            if show_pw.get():
                reveal_passwords()
            else:
                mask_passwords()

        tk.Checkbutton(table_button_frame, text="Show Password in Table", variable=show_pw,
                       command=toggle_password, bg="#F4F7FA", fg="#333",
                       font=("Arial", 10)).pack(side="right")
        
        def populate_table():
            table.delete(*table.get_children())
            student_passwords.clear()
            for row in self.db.get_students():
                item_id = table.insert("", "end", values=row)
                if len(row) >= 5:
                    pw = str(row[4])
                    student_passwords[item_id] = pw
            toggle_password()

        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            self.selected_id = values[0]
            sf.delete(0, tk.END); sf.insert(0, values[1])
            sm.delete(0, tk.END)
            sl.delete(0, tk.END); sl.insert(0, values[2])
            sec_combo.set(values[3])
            actual_pw = student_passwords.get(selected, values[4])
            generated_password_student.set(actual_pw)

        table.bind("<<TreeviewSelect>>", on_select)

        def add():
            s_id = sec_dict.get(sec_combo.get())
            if sf.get().strip() and sl.get().strip() and s_id:
                self.db.add_student(sf.get().strip(), sm.get().strip(), sl.get().strip(), s_id, "temp")
                new_id = self.db.cursor.lastrowid
                password = f"{new_id}{sf.get().strip()}"
                self.db.update_password("students", new_id, password)
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
                self.db.delete_student(self.selected_id)
                self.show_students()
            else: messagebox.showwarning("Error", "Select a row record.")

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
        teacher_dict = {f"{row[1]} {row[2]}": row[0] for row in teacher_list}
        
        sec_list = self.db.get_sections()
        sec_dict = {row[1]: row[0] for row in sec_list}

        tk.Label(form, text="Teacher Name", bg="#F4F7FA").grid(row=0, column=0, padx=5, pady=2)
        teacher_combo = ttk.Combobox(form, values=list(teacher_dict.keys()), state="readonly")
        teacher_combo.grid(row=0, column=1, padx=5, pady=2)

        tk.Label(form, text="Subject", bg="#F4F7FA").grid(row=1, column=0, padx=5, pady=2)
        # CHANGED: Swapped broken/empty sub_combo to a standard input entry field
        sub_entry = tk.Entry(form, width=23)
        sub_entry.grid(row=1, column=1, padx=5, pady=2)

        tk.Label(form, text="Section", bg="#F4F7FA").grid(row=2, column=0, padx=5, pady=2)
        sec_combo = ttk.Combobox(form, values=list(sec_dict.keys()), state="readonly")
        sec_combo.grid(row=2, column=1, padx=5, pady=2)

        tk.Label(form, text="Academic Year", bg="#F4F7FA").grid(row=3, column=0, padx=5, pady=2)
        ay_combo = ttk.Combobox(form, values=[f"{y}-{y+1}" for y in range(2020, 2031)], state="readonly", width=22)
        ay_combo.grid(row=3, column=1, padx=5, pady=2)

        tk.Label(form, text="Semester", bg="#F4F7FA").grid(row=4, column=0, padx=5, pady=2)
        sem_combo = ttk.Combobox(form, values=["1st Semester", "2nd Semester", "Summer"], state="readonly")
        sem_combo.grid(row=4, column=1, padx=5, pady=2)

        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        # Corrected parent context to table_frame
        table = ttk.Treeview(table_frame, columns=("ID", "TEACHER", "SUBJECT", "SECTION", "A_YEAR", "SEMESTER"), show="headings")
        for c in ("ID", "TEACHER", "SUBJECT", "SECTION", "A_YEAR", "SEMESTER"):
            table.heading(c, text=c)

        # Center all assignment table columns
        table.column("ID", width=50, anchor="center")
        table.column("TEACHER", width=180, anchor="center")
        table.column("SUBJECT", width=180, anchor="center")
        table.column("SECTION", width=180, anchor="center")
        table.column("A_YEAR", width=120, anchor="center")
        table.column("SEMESTER", width=130, anchor="center")


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
            for row in self.db.get_assignments(): 
                table.insert("", "end", values=row)

        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            self.selected_id = values[0]
            teacher_combo.set(values[1])
            sub_entry.delete(0, tk.END)
            sub_entry.insert(0, values[2])
            sec_combo.set(values[3])
            ay_combo.set(values[4])
            sem_combo.set(values[5])

        table.bind("<<TreeviewSelect>>", on_select)

        def add():
            t_id = teacher_dict.get(teacher_combo.get())
            s_id = sec_dict.get(sec_combo.get())
            subject = sub_entry.get().strip()
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
            subject = sub_entry.get().strip()
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

if __name__ == "__main__":
    root = tk.Tk()
    app = MSAPortalApp(root)
    root.mainloop()