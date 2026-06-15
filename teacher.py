import tkinter as tk
from tkinter import ttk, messagebox
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

        self.sidebar = tk.Frame(root, bg="#0B2240", width=220)
        self.sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(root, bg="#F4F7FA")
        self.content.pack(side="right", fill="both", expand=True)

        tk.Label(self.sidebar, text="MSAQC Portal",
                 bg="#0B2240", fg="white",
                 font=("Arial", 16, "bold")).pack(pady=20)

        tk.Label(self.sidebar, text=f"Welcome, {teacher_name}",
                 bg="#0B2240", fg="white",
                 font=("Arial", 10)).pack(pady=(0, 20))

        buttons = [
            ("Grade Entry", self.show_grade_entry),
        ]

        for text, cmd in buttons:
            tk.Button(self.sidebar, text=text, command=cmd,
                      bg="#0B2240", fg="white", bd=0, activebackground="#163866",
                      activeforeground="white", cursor="hand2").pack(fill="x", pady=5, padx=10)

        tk.Button(self.sidebar, text="Logout", command=self.logout,
                  bg="#dc3545", fg="white", bd=0, activebackground="#c82333",
                  activeforeground="white", font=("Arial", 10, "bold"), cursor="hand2").pack(fill="x", side="bottom", pady=20, padx=10)

        self.show_grade_entry()

    def logout(self):
        confirm = messagebox.askyesno("Logout", "Sigurado ka ba na gusto mong mag-logout?")
        if confirm:
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
                  bg="#0B2240", fg="white").grid(row=1, column=0, columnspan=8, pady=5)

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
            except ValueError:
                return "", "", ""

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
            students = self.db.get_section_students(sec_id)
            all_grades = self.db.get_grades(teacher_id=self.teacher_id, academic_year=year, semester=sem)
            grade_map = {g[1]: g for g in all_grades if g[3] == subject}
            for s in students:
                middle = (s[2] or "").strip()
                last = (s[3] or "").strip()
                first = (s[1] or "").strip()
                name = f"{first} {middle} {last}".replace("  ", " ").strip()

                existing = grade_map.get(name)
                p = existing[6] if existing else ""
                m = existing[7] if existing else ""
                f = existing[8] if existing else ""
                avg, gwa, remark = compute_grade(p, m, f)
                item_id = table.insert("", "end", values=(s[0], name, p, m, f, avg, gwa, remark))
                students_data.append({
                    "id": s[0],
                    "name": name,
                    "sec_id": sec_id,
                    "tbl_id": item_id,
                    "existing": existing
                })

        def on_cell_double_click(event):
            region = table.identify("region", event.x, event.y)
            if region != "cell":
                return
            column = table.identify_column(event.x)
            if column not in ("#3", "#4", "#5"):
                return
            row = table.identify_row(event.y)
            if not row:
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
            sec_name = sec_combo.get().split(" (")[0]
            sec_id = None
            for row in sections:
                if row[1] == sec_name:
                    sec_id = row[0]
                    break
            if sec_id is None:
                return
            subject = sub_combo.get()
            year = ay_entry.get().strip()
            sem = sem_combo.get()
            saved = 0
            for item in students_data:
                tbl_id = item["tbl_id"]
                prelim = table.set(tbl_id, "PRELIM")
                midterm = table.set(tbl_id, "MID")
                final = table.set(tbl_id, "FINAL")
                try:
                    p = float(prelim) if prelim != "" else 0
                    m = float(midterm) if midterm != "" else 0
                    f = float(final) if final != "" else 0
                except ValueError:
                    continue
                if item["existing"]:
                    self.db.update_grade(item["existing"][0], p, m, f)
                    item["existing"] = (item["existing"][0], item["existing"][1], item["existing"][2], item["existing"][3], item["existing"][4], item["existing"][5], p, m, f)
                else:
                    self.db.add_grade(self.teacher_id, sec_id, item["id"], subject, year, sem, p, m, f)
                    new_grade = self.db.cursor.execute("SELECT last_insert_rowid()").fetchone()[0]
                    item["existing"] = (new_grade, item["name"], sub_combo.get(), subject, year, sem, p, m, f)
                saved += 1
            if saved > 0:
                messagebox.showinfo("Success", f"{saved} grade(s) saved successfully!")
            else:
                messagebox.showwarning("Notice", "No changes to save.")

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


if __name__ == "__main__":
    root = tk.Tk()
    teacher_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    teacher_name = sys.argv[2] if len(sys.argv) > 2 else "Teacher"
    app = TeacherPortalApp(root, teacher_id, teacher_name)
    root.mainloop()
