import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from database import Database
import os
import sys
import subprocess


class TeacherPortalApp:
    def __init__(self, root, teacher_id, teacher_name):
        self.root = root
        self.root.title("MSAQC Portal")
        self.root.geometry("1200x700")

        self.db = Database()
        self.teacher_id = teacher_id
        self.teacher_name = teacher_name
        self.selected_id = None

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

        tk.Label(self.sidebar, text=f"Welcome, {teacher_name}",
                 bg="#0B2240", fg="white",
                 font=("Arial", 10)).pack(pady=(0, 20))

        buttons = [
            ("Grade Entry", self.show_grade_entry),
            ("My Request", self.show_extension_request),
            ("Change Password", self.show_change_password),
        ]

        self.nav_buttons = []
        self.active_nav_text = None

        for text, cmd in buttons:
            btn = tk.Button(self.sidebar, text=text,
                          command=lambda c=cmd, t=text: self._on_nav_click(c, t),
                          bg="#0B2240", fg="white", bd=0, activebackground="#163866",
                          activeforeground="white", cursor="hand2")
            btn.pack(fill="x", pady=5, padx=10)
            btn.bind("<Enter>", lambda e, b=btn: b.configure(bg="#163866"))
            btn.bind("<Leave>", lambda e, b=btn, t=text: self._reset_nav_color(b, t))
            self.nav_buttons.append((btn, text))

        self._set_active_nav("Grade Entry")  # Set initial active button

        tk.Button(self.sidebar, text="Logout", command=self.logout,
                  bg="#dc3545", fg="white", bd=0, activebackground="#c82333",
                  activeforeground="white", font=("Arial", 10, "bold"), cursor="hand2").pack(fill="x", side="bottom", pady=20, padx=10)

        self.show_grade_entry()

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

    def logout(self):
        confirm = messagebox.askyesno("Logout", "Sigurado ka ba na gusto mong mag-logout?")
        if confirm:
            self.clear_content()
            self.db.add_audit_log(self.teacher_id, self.teacher_name, "Teacher", "", "Logout", "Teacher logged out")
            self.root.destroy()
            current_dir = os.path.dirname(os.path.abspath(__file__))
            login_script = os.path.join(current_dir, "login.py")
            subprocess.run([sys.executable, login_script])

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    def show_grade_entry(self):
        self.clear_content()
        tk.Label(self.content, text="Grade Entry",
                 font=("Arial", 24, "bold"), bg="#F4F7FA").pack(pady=20)

        filter_frame = tk.Frame(self.content, bg="#F4F7FA")
        filter_frame.pack(pady=10, padx=20, fill="x")

        tk.Label(filter_frame, text="Section", bg="#F4F7FA").grid(row=0, column=0, padx=5, pady=5)
        sections = self.db.get_available_sections(self.teacher_id)
        sec_names = [f"{row[1]} ({row[2]})" for row in sections]
        sec_combo = ttk.Combobox(filter_frame, values=sec_names, state="readonly", width=25)
        sec_combo.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(filter_frame, text="Subject", bg="#F4F7FA").grid(row=0, column=2, padx=5, pady=5)
        subjects = self.db.get_available_subjects(self.teacher_id)
        sub_combo = ttk.Combobox(filter_frame, values=subjects, state="readonly", width=25)
        sub_combo.grid(row=0, column=3, padx=5, pady=5)

        tk.Label(filter_frame, text="Academic Year", bg="#F4F7FA").grid(row=0, column=4, padx=5, pady=5)
        ay_entry = ttk.Combobox(filter_frame, values=[""] + [f"{y}-{y+1}" for y in range(2020, 2031)], state="readonly", width=18)
        ay_entry.set("2024-2025")
        ay_entry.grid(row=0, column=5, padx=5, pady=5)

        tk.Label(filter_frame, text="Semester", bg="#F4F7FA").grid(row=0, column=6, padx=5, pady=5)
        sem_combo = ttk.Combobox(filter_frame, values=["1st Semester", "2nd Semester", "Summer"], state="readonly", width=15)
        sem_combo.grid(row=0, column=7, padx=5, pady=5)

        tk.Button(filter_frame, text="Load Students", command=lambda: load_students(),
                  bg="#0B2240", fg="white").grid(row=1, column=0, columnspan=9, pady=5)

        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)

        table = ttk.Treeview(table_frame, columns=("ID", "STUDENT", "PRELIM", "MID", "FINAL", "AVERAGE", "GWA", "REMARK"), show="headings")
        table.heading("ID", text="ID")
        table.heading("STUDENT", text="Student Name (First Middle Last)")

        table.heading("PRELIM", text="Prelim")
        table.heading("MID", text="Midterm")
        table.heading("FINAL", text="Final")
        table.heading("AVERAGE", text="Average")
        table.heading("GWA", text="GWA")
        table.heading("REMARK", text="Remark")
        table.column("ID", width=50, anchor="center")
        table.column("STUDENT", width=180, anchor="center")
        table.column("PRELIM", width=80, anchor="center")
        table.column("MID", width=80, anchor="center")
        table.column("FINAL", width=80, anchor="center")
        table.column("AVERAGE", width=80, anchor="center")
        table.column("GWA", width=80, anchor="center")
        table.column("REMARK", width=80, anchor="center")

        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=table.xview)
        table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        table_frame.grid_rowconfigure(0, weight=1)
        table_frame.grid_columnconfigure(0, weight=1)

        students_data = []

        def compute_grade(prelim, midterm, final):
            if prelim == "" or midterm == "" or final == "":
                return "", "", ""
            try:
                p = float(prelim)
                m = float(midterm)
                f = float(final)
            except ValueError:
                return "", "", ""

            avg = round((p + m + f) / 3, 2)
            if avg >= 97:
                gwa = 1.00
            elif avg >= 94:
                gwa = 1.25
            elif avg >= 91:
                gwa = 1.50
            elif avg >= 88:
                gwa = 1.75
            elif avg >= 85:
                gwa = 2.00
            elif avg >= 82:
                gwa = 2.25
            elif avg >= 79:
                gwa = 2.50
            elif avg >= 76:
                gwa = 2.75
            elif avg >= 75:
                gwa = 3.00
            else:
                gwa = 5.00

            remark = "PASSED" if avg >= 75 else "FAILED"
            return f"{avg:.2f}", f"{gwa:.2f}", remark

        def load_students():
            students_data.clear()
            table.delete(*table.get_children())
            if not sec_combo.get() or not sub_combo.get():
                messagebox.showwarning("Error", "Please fill all filter fields.")
                return
            sec_name = sec_combo.get().split(" (")[0]
            sec_id = None
            for row in sections:
                if row[1] == sec_name:
                    sec_id = row[0]
                    break
            if sec_id is None:
                return
            year = ay_entry.get().strip()
            sem = sem_combo.get()
            if not year or not sem:
                messagebox.showwarning("Error", "Fill Academic Year and Semester.")
                return
            subject = sub_combo.get()
            if not self.db.assignment_exists(self.teacher_id, sec_id, subject, year, sem):
                messagebox.showerror("Access Denied", "You are not assigned to this section/subject for the selected year and semester.")
                return
            open_period = self.db.get_open_period(year, sem)
            is_locked = self.db.is_period_locked(subject, sec_id, year, sem, open_period) if open_period else True
            students = self.db.get_section_students(sec_id)
            all_grades = self.db.get_grades(teacher_id=self.teacher_id, academic_year=year, semester=sem)
            grade_map = {g[1]: g for g in all_grades if g[3] == subject}
            for s in students:
                middle = (s[2] or "").strip()
                last = (s[3] or "").strip()
                first = (s[1] or "").strip()
                name = f"{first} {middle} {last}".replace("  ", " ").strip()

                existing = grade_map.get(name)
                p = existing[6] if existing and existing[6] not in (None, 0) else ""
                m = existing[7] if existing and existing[7] not in (None, 0) else ""
                f = existing[8] if existing and existing[8] not in (None, 0) else ""

                avg, gwa, remark = compute_grade(p, m, f)
                item_id = table.insert("", "end", values=(s[0], name, p, m, f, avg, gwa, remark))
                students_data.append({
                    "id": s[0],
                    "name": name,
                    "sec_id": sec_id,
                    "tbl_id": item_id,
                    "existing": existing
                })
                if existing:
                    students_data[-1]["db_grades"] = {
                        "prelim": existing[6],
                        "midterm": existing[7],
                        "final": existing[8]
                    }
            if not open_period or is_locked:
                for item in table.get_children():
                    table.item(item, tags=("locked",))
                table.tag_configure("locked", foreground="gray")
                table.unbind("<Double-1>")
            else:
                table.bind("<Double-1>", on_cell_double_click)

        def on_cell_double_click(event):
            year = ay_entry.get().strip()
            sem = sem_combo.get()
            open_period = self.db.get_open_period(year, sem) if year and sem else None
            if not open_period:
                messagebox.showwarning("Closed", "No grading period is currently open. Contact admin.")
                return
            region = table.identify("region", event.x, event.y)
            if region != "cell":
                return
            column = table.identify_column(event.x)
            allowed_cols = {"Prelim": "#3", "Midterm": "#4", "Final": "#5"}
            target_col = allowed_cols.get(open_period)
            if column != target_col:
                messagebox.showwarning("Locked", f"Only {open_period} grades can be edited right now.")
                return
            row = table.identify_row(event.y)
            if not row:
                return
            sec_name = sec_combo.get().split(" (")[0]
            sec_id = None
            for r in sections:
                if r[1] == sec_name:
                    sec_id = r[0]
                    break
            if not sec_id:
                return
            subject = sub_combo.get()
            if self.db.is_period_locked(subject, sec_id, year, sem, open_period):
                messagebox.showwarning("Locked", f"The {open_period} grading period is locked. Please submit a reopen request.")
                return
            x, y, width, height = table.bbox(row, column)
            value = table.set(row, column)
            entry = tk.Entry(table)
            entry.place(x=x, y=y, width=width, height=height)
            entry.insert(0, value)
            entry.focus_set()

            def finish_edit(event=None):
                new_value = entry.get()
                table.set(row, column, new_value)
                prelim = table.set(row, "PRELIM")
                midterm = table.set(row, "MID")
                final = table.set(row, "FINAL")
                avg, gwa, remark = compute_grade(prelim, midterm, final)
                table.set(row, "AVERAGE", avg)
                table.set(row, "GWA", gwa)
                table.set(row, "REMARK", remark)
                entry.destroy()

            entry.bind("<Return>", finish_edit)
            entry.bind("<FocusOut>", lambda e: finish_edit())


        table.bind("<Double-1>", on_cell_double_click)

        def save_all_grades():
            if not sec_combo.get() or not sub_combo.get() or not ay_entry.get().strip() or not sem_combo.get():
                messagebox.showwarning("Error", "Fill Section, Subject, Year, and Semester first.")
                return
            year = ay_entry.get().strip()
            sem = sem_combo.get()
            open_period = self.db.get_open_period(year, sem)
            if not open_period:
                messagebox.showwarning("Closed", "No grading period is currently open. Contact admin.")
                return
            sec_name = sec_combo.get().split(" (")[0]
            sec_id = None
            for row in sections:
                if row[1] == sec_name:
                    sec_id = row[0]
                    break
            if sec_id is None:
                return
            subject = sub_combo.get()
            if self.db.is_period_locked(subject, sec_id, year, sem, open_period):
                messagebox.showwarning("Locked", f"The {open_period} grading period is already locked. Please submit a reopen request if you need to edit.")
                return
            confirm = messagebox.askyesno("Confirm Submission", f"Are you sure you want to submit {open_period} grades? This will lock the grading period after submission.")
            if not confirm:
                return
            saved = 0
            inserted = 0
            updated = 0
            for item in students_data:
                tbl_id = item["tbl_id"]
                prelim = table.set(tbl_id, "PRELIM")
                midterm = table.set(tbl_id, "MID")
                final = table.set(tbl_id, "FINAL")

                def to_float_or_zero(val):
                    if val is None:
                        return 0.0
                    s = str(val).strip()
                    if s == "":
                        return 0.0
                    try:
                        return float(s)
                    except ValueError:
                        return 0.0

                p = to_float_or_zero(prelim)
                m = to_float_or_zero(midterm)
                f = to_float_or_zero(final)

                existing = item.get("existing")
                db_grades = item.get("db_grades", {})
                if existing:
                    grade_row_id = existing[0]
                    if open_period == "Prelim":
                        self.db.update_grade_column(grade_row_id, "prelim", p)
                    elif open_period == "Midterm":
                        self.db.update_grade_column(grade_row_id, "midterm", m)
                    else:
                        self.db.update_grade_column(grade_row_id, "final", f)
                    updated += 1
                else:
                    if open_period == "Prelim":
                        self.db.add_grade(self.teacher_id, sec_id, item["id"], subject, year, sem, p, 0.0, 0.0)
                    elif open_period == "Midterm":
                        self.db.add_grade(self.teacher_id, sec_id, item["id"], subject, year, sem, 0.0, m, 0.0)
                    else:
                        self.db.add_grade(self.teacher_id, sec_id, item["id"], subject, year, sem, 0.0, 0.0, f)
                    inserted += 1

                saved += 1

            self.db.lock_grade_period(subject, sec_id, year, sem, open_period)
            self.db.add_audit_log(self.teacher_id, self.teacher_name, "Teacher", "", "Grade Encoding", f"Submitted {open_period} grades for {subject}")
            messagebox.showinfo(
                "Submission Successful",
                f"{saved} grade row(s) processed for {open_period}. Inserted: {inserted}, Updated: {updated}.\nThe {open_period} grading period has been locked."
            )
            load_students()

        btn_frame = tk.Frame(self.content, bg="#F4F7FA")
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Save Grades", command=save_all_grades, bg="#28a745", fg="white").pack()

    def show_grades_list(self):
        self.clear_content()
        tk.Label(self.content, text="My Grades",
                 font=("Arial", 24, "bold"), bg="#F4F7FA").pack(pady=20)

        filter_frame = tk.Frame(self.content, bg="#F4F7FA")
        filter_frame.pack(pady=10, padx=20, fill="x")

        tk.Label(filter_frame, text="Academic Year", bg="#F4F7FA").grid(row=0, column=0, padx=5, pady=5)
        ay_filter = tk.Entry(filter_frame, width=15)
        ay_filter.grid(row=0, column=1, padx=5, pady=5)

        tk.Label(filter_frame, text="Semester", bg="#F4F7FA").grid(row=0, column=2, padx=5, pady=5)
        sem_filter = ttk.Combobox(filter_frame, values=["", "1st Semester", "2nd Semester", "Summer"], state="readonly", width=15)
        sem_filter.grid(row=0, column=3, padx=5, pady=5)

        def filter_grades():
            ay = ay_filter.get().strip() or None
            sem = sem_filter.get() or None
            populate_table(ay, sem)

        tk.Button(filter_frame, text="Apply Filter", command=filter_grades,
                  bg="#0B2240", fg="white").grid(row=0, column=4, padx=10, pady=5)

        table = ttk.Treeview(self.content, columns=(
            "ID", "STUDENT", "SECTION", "SUBJECT", "YEAR", "SEM", "PRELIM", "MID", "FINAL", "AVERAGE", "GWA", "REMARK"
        ), show="headings")
        headers = ["ID", "STUDENT", "SECTION", "SUBJECT", "YEAR", "SEM", "PRELIM", "MID", "FINAL", "AVERAGE", "GWA", "REMARK"]
        for h in headers:
            table.heading(h, text=h)
        table.column("ID", width=50, anchor="center")
        table.column("STUDENT", width=180)
        table.column("SECTION", width=100)
        table.column("SUBJECT", width=120)
        table.column("YEAR", width=80, anchor="center")
        table.column("SEM", width=80, anchor="center")
        table.column("PRELIM", width=60, anchor="center")
        table.column("MID", width=60, anchor="center")
        table.column("FINAL", width=60, anchor="center")
        table.column("AVERAGE", width=70, anchor="center")
        table.column("GWA", width=70, anchor="center")
        table.column("REMARK", width=70, anchor="center")

        table_frame = tk.Frame(self.content, bg="#F4F7FA")
        table_frame.pack(fill="both", expand=True, padx=20, pady=10)
        table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        scrollbar.pack(side="right", fill="y")
        table.configure(yscrollcommand=scrollbar.set)

        def populate_table(ay=None, sem=None):
            table.delete(*table.get_children())
            grades = self.db.get_grades(teacher_id=self.teacher_id, academic_year=ay, semester=sem)
            for row in grades:
                table.insert("", "end", values=row)

        populate_table()

        def on_select(event):
            selected = table.focus()
            if not selected:
                return
            values = table.item(selected, 'values')
            self.selected_id = values[0]

        table.bind("<<TreeviewSelect>>", on_select)

        def delete_selected():
            if not self.selected_id:
                messagebox.showwarning("Error", "Select a row first.")
                return
            if messagebox.askyesno("Confirm", "Delete this grade record?"):
                self.db.delete_grade(self.selected_id)
                self.show_grades_list()

        btn_frame = tk.Frame(self.content, bg="#F4F7FA")
        btn_frame.pack(pady=5)
        tk.Button(btn_frame, text="Delete Selected", command=delete_selected, bg="#dc3545", fg="white").pack()

    # -----------------------------
    # MY REQUEST
    # -----------------------------
    def show_extension_request(self):
        self.clear_content()

        main_container = tk.Frame(self.content, bg="#F4F7FA")
        main_container.pack(fill="both", expand=True, padx=30, pady=20)

        tk.Label(main_container, text="My Request", font=("Arial", 22, "bold"), bg="#F4F7FA", fg="#0B2240").pack(pady=(0, 20), anchor="w")

        form_card = tk.Frame(main_container, bg="white", bd=1, relief="solid")
        form_card.pack(fill="x", pady=(0, 20))

        form_inner = tk.Frame(form_card, bg="white")
        form_inner.pack(padx=25, pady=20, fill="x")

        header_frame = tk.Frame(form_inner, bg="white")
        header_frame.grid(row=0, column=0, columnspan=4, sticky="w", pady=(0, 15))

        tk.Label(header_frame, text="Request Information", font=("Arial", 13, "bold"), bg="white", fg="#0B2240").pack(side="left")

        info_frame = tk.Frame(form_inner, bg="white")
        info_frame.grid(row=1, column=0, columnspan=4, sticky="w", pady=(0, 15))

        teacher = self.db.get_teacher_by_id(self.teacher_id)
        teacher_dept = teacher[4] if teacher else None
        teacher_name = self.teacher_name

        tk.Label(info_frame, text="Teacher ID:", bg="white", font=("Arial", 9)).grid(row=0, column=0, padx=(0, 5), pady=2, sticky="e")
        tk.Label(info_frame, text=str(self.teacher_id), bg="white", font=("Arial", 9, "bold"), fg="#333").grid(row=0, column=1, padx=(0, 20), pady=2, sticky="w")

        tk.Label(info_frame, text="Name:", bg="white", font=("Arial", 9)).grid(row=0, column=2, padx=(0, 5), pady=2, sticky="e")
        tk.Label(info_frame, text=teacher_name, bg="white", font=("Arial", 9, "bold"), fg="#333").grid(row=0, column=3, padx=(0, 0), pady=2, sticky="w")

        dept_name = self.db.cursor.execute("SELECT dept_name FROM departments WHERE id=?", (teacher_dept,)).fetchone()
        tk.Label(info_frame, text="Department:", bg="white", font=("Arial", 9)).grid(row=1, column=0, padx=(0, 5), pady=2, sticky="e")
        tk.Label(info_frame, text=dept_name[0] if dept_name else "N/A", bg="white", font=("Arial", 9, "bold"), fg="#333").grid(row=1, column=1, padx=(0, 20), pady=2, sticky="w")

        tk.Label(info_frame, text="Section:", bg="white", font=("Arial", 9)).grid(row=1, column=2, padx=(0, 5), pady=2, sticky="e")
        sections = self.db.get_available_sections(self.teacher_id)
        sec_names = [f"{row[1]} ({row[2]})" for row in sections]
        sec_combo = ttk.Combobox(info_frame, values=sec_names, state="readonly", width=22, font=("Arial", 9))
        sec_combo.grid(row=1, column=3, padx=(0, 0), pady=2, sticky="w")

        form_grid = tk.Frame(form_inner, bg="white")
        form_grid.grid(row=2, column=0, columnspan=4, sticky="ew", pady=(10, 0))

        tk.Label(form_grid, text="Subject", bg="white", font=("Arial", 9)).grid(row=0, column=0, padx=(0, 8), pady=6, sticky="e")
        subjects = self.db.get_available_subjects_with_ids(self.teacher_id)
        subj_dict = {f"{row[1]} - {row[0]}": row[0] for row in subjects}
        subj_combo = ttk.Combobox(form_grid, values=list(subj_dict.keys()) if subj_dict else ["No subjects assigned"], state="readonly", width=28, font=("Arial", 9))
        subj_combo.grid(row=0, column=1, padx=(0, 15), pady=6, sticky="w")

        tk.Label(form_grid, text="School Year", bg="white", font=("Arial", 9)).grid(row=0, column=2, padx=(0, 8), pady=6, sticky="e")
        ay_req = ttk.Combobox(form_grid, values=[f"{y}-{y+1}" for y in range(2024, 2027)], state="readonly", width=15, font=("Arial", 9))
        ay_req.grid(row=0, column=3, padx=(0, 0), pady=6, sticky="w")

        tk.Label(form_grid, text="Semester", bg="white", font=("Arial", 9)).grid(row=1, column=0, padx=(0, 8), pady=6, sticky="e")
        sem_req = ttk.Combobox(form_grid, values=["1st Semester", "2nd Semester", "Summer"], state="readonly", width=15, font=("Arial", 9))
        sem_req.grid(row=1, column=1, padx=(0, 15), pady=6, sticky="w")

        tk.Label(form_grid, text="Grading Period(s)", bg="white", font=("Arial", 9)).grid(row=1, column=2, padx=(0, 8), pady=6, sticky="e")
        gp_frame = tk.Frame(form_grid, bg="white")
        gp_frame.grid(row=1, column=3, padx=(0, 0), pady=6, sticky="w")
        gp_prelim = tk.BooleanVar()
        gp_midterm = tk.BooleanVar()
        gp_final = tk.BooleanVar()
        tk.Checkbutton(gp_frame, text="Prelim", variable=gp_prelim, bg="white", font=("Arial", 9)).pack(side="left", padx=(0, 8))
        tk.Checkbutton(gp_frame, text="Midterm", variable=gp_midterm, bg="white", font=("Arial", 9)).pack(side="left", padx=(0, 8))
        tk.Checkbutton(gp_frame, text="Finals", variable=gp_final, bg="white", font=("Arial", 9)).pack(side="left", padx=(0, 0))

        tk.Label(form_grid, text="Reason", bg="white", font=("Arial", 9)).grid(row=2, column=0, padx=(0, 8), pady=6, sticky="ne")
        reason_text = tk.Text(form_grid, width=40, height=4, font=("Arial", 9), bd=1, relief="solid", bg="#fafafa")
        reason_text.grid(row=2, column=1, columnspan=3, padx=(0, 0), pady=6, sticky="w")

        def submit_request():
            if not subj_combo.get() or not ay_req.get() or not sem_req.get() or not sec_combo.get():
                messagebox.showwarning("Error", "Please complete all required fields.")
                return
            selected_periods = []
            if gp_prelim.get():
                selected_periods.append("Prelim")
            if gp_midterm.get():
                selected_periods.append("Midterm")
            if gp_final.get():
                selected_periods.append("Final")
            if not selected_periods:
                messagebox.showwarning("Error", "Please select at least one grading period.")
                return
            subj_id = subj_dict.get(subj_combo.get())
            subject_name = subj_combo.get().split(" - ")[0] if " - " in subj_combo.get() else subj_combo.get()
            sec_name = sec_combo.get().split(" (")[0]
            sec_id = None
            for r in sections:
                if r[1] == sec_name:
                    sec_id = r[0]
                    break
            if sec_id is None:
                messagebox.showwarning("Error", "Invalid section selected.")
                return
            reason = reason_text.get("1.0", tk.END).strip()
            if not reason:
                messagebox.showwarning("Error", "Please provide a reason for the request.")
                return
            if self.db.add_reopen_request(self.teacher_id, teacher_name, subject_name, sec_id, sec_name, teacher_dept, ay_req.get(), sem_req.get(), selected_periods, reason):
                dept_name_str = dept_name[0] if dept_name else ""
                self.db.add_audit_log(self.teacher_id, teacher_name, "Teacher", dept_name_str, "Reopen Request", f"Requested reopen for {subject_name} - {', '.join(selected_periods)}")
                messagebox.showinfo("Success", "Request submitted successfully.")
                gp_prelim.set(False)
                gp_midterm.set(False)
                gp_final.set(False)
                reason_text.delete("1.0", tk.END)
                populate_requests()
            else:
                messagebox.showwarning("Error", "A pending request already exists for this selection.")

        btn_frame = tk.Frame(form_inner, bg="white")
        btn_frame.grid(row=3, column=0, columnspan=4, pady=(15, 0), sticky="w")
        tk.Button(btn_frame, text="Submit Request", command=submit_request, bg="#28a745", fg="white",
                  font=("Arial", 9, "bold"), width=14, cursor="hand2").pack(side="left", padx=(0, 10))
        tk.Button(btn_frame, text="Clear Form", command=lambda: [
            subj_combo.set(''), ay_req.set(''), sem_req.set(''), sec_combo.set(''),
            gp_prelim.set(False), gp_midterm.set(False), gp_final.set(False),
            reason_text.delete("1.0", tk.END)
        ], bg="#6c757d", fg="white", font=("Arial", 9), width=12, cursor="hand2").pack(side="left")

        tk.Label(main_container, text="My Requests", font=("Arial", 16, "bold"), bg="#F4F7FA", fg="#0B2240").pack(pady=(10, 10), anchor="w")

        table_card = tk.Frame(main_container, bg="white", bd=1, relief="solid")
        table_card.pack(fill="both", expand=True)

        table_inner = tk.Frame(table_card, bg="white")
        table_inner.pack(padx=15, pady=15, fill="both", expand=True)

        req_table = ttk.Treeview(table_inner, columns=("ID", "Date", "Department", "Subject", "Section", "School Year", "Semester", "Periods", "Reason", "Status", "Remarks"), show="headings")
        for c in ("ID", "Date", "Department", "Subject", "Section", "School Year", "Semester", "Periods", "Reason", "Status", "Remarks"):
            req_table.heading(c, text=c)
        req_table.column("ID", width=40, anchor="center")
        req_table.column("Date", width=90, anchor="center")
        req_table.column("Department", width=100, anchor="center")
        req_table.column("Subject", width=100, anchor="center")
        req_table.column("Section", width=80, anchor="center")
        req_table.column("School Year", width=80, anchor="center")
        req_table.column("Semester", width=80, anchor="center")
        req_table.column("Periods", width=100, anchor="center")
        req_table.column("Reason", width=130, anchor="w")
        req_table.column("Status", width=70, anchor="center")
        req_table.column("Remarks", width=130, anchor="w")

        req_table.tag_configure("Pending", foreground="#d68c00", font=("Arial", 9))
        req_table.tag_configure("Approved", foreground="#28a745", font=("Arial", 9))
        req_table.tag_configure("Rejected", foreground="#dc3545", font=("Arial", 9))

        vsb = ttk.Scrollbar(table_inner, orient="vertical", command=req_table.yview)
        hsb = ttk.Scrollbar(table_inner, orient="horizontal", command=req_table.xview)
        req_table.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        req_table.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, columnspan=2, sticky="ew")

        table_inner.grid_rowconfigure(0, weight=1)
        table_inner.grid_columnconfigure(0, weight=1)

        def populate_requests():
            req_table.delete(*req_table.get_children())
            for row in self.db.get_extension_requests(teacher_id=self.teacher_id):
                date_str = row[13][:10] if row[13] else ""
                values = (row[0], date_str, row[6], row[3], row[5], row[7], row[8], row[9], row[10], row[11], row[12])
                status = row[11]
                req_table.insert("", "end", values=values, tags=(status,))

        populate_requests()

    # -----------------------------
    # CHANGE PASSWORD
    # -----------------------------
    def show_change_password(self):
        popup = tk.Toplevel(self.root)
        popup.title("Change Password")
        popup.geometry("420x240")
        popup.configure(bg="#fff3cd")
        popup.resizable(False, False)
        popup.transient(self.root)
        popup.grab_set()

        tk.Label(popup, text="Change Password", font=("Arial", 14, "bold"), bg="#fff3cd").pack(pady=15)

        form = tk.Frame(popup, bg="#fff3cd")
        form.pack(pady=5)

        tk.Label(form, text="Current Password", bg="#fff3cd").grid(row=0, column=0, padx=10, pady=8, sticky="e")
        current_pw = tk.Entry(form, show="*", width=25)
        current_pw.grid(row=0, column=1, padx=10, pady=8)

        tk.Label(form, text="New Password", bg="#fff3cd").grid(row=1, column=0, padx=10, pady=8, sticky="e")
        new_pw = tk.Entry(form, show="*", width=25)
        new_pw.grid(row=1, column=1, padx=10, pady=8)

        tk.Label(form, text="Confirm New Password", bg="#fff3cd").grid(row=2, column=0, padx=10, pady=8, sticky="e")
        confirm_pw = tk.Entry(form, show="*", width=25)
        confirm_pw.grid(row=2, column=1, padx=10, pady=8)

        def change():
            if not self.db.verify_password("teachers", self.teacher_id, current_pw.get()):
                messagebox.showerror("Error", "Current password is incorrect.", parent=popup)
                return
            if new_pw.get() != confirm_pw.get():
                messagebox.showerror("Error", "New passwords do not match.", parent=popup)
                return
            if len(new_pw.get()) < 4:
                messagebox.showwarning("Error", "Password must be at least 4 characters.", parent=popup)
                return
            self.db.update_password("teachers", self.teacher_id, new_pw.get())
            self.db.add_audit_log(self.teacher_id, self.teacher_name, "Teacher", "", "Password Change", "Password changed successfully")
            self.db.add_notification(self.teacher_id, "Teacher", "Password Changed", "Your password has been changed. Please login again.")
            messagebox.showinfo("Success", "Password changed successfully. Please login again.", parent=popup)
            popup.destroy()
            self.logout()

        tk.Button(popup, text="Change Password", command=change, bg="#0B2240", fg="white", font=("Arial", 10), width=18).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    teacher_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    teacher_name = sys.argv[2] if len(sys.argv) > 2 else "Teacher"
    app = TeacherPortalApp(root, teacher_id, teacher_name)
    root.mainloop()
