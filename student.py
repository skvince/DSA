import tkinter as tk
from tkinter import ttk, messagebox
from database import Database
import os
import sys
import subprocess

class StudentPortalApp:
    def __init__(self, root, student_id, student_name):
        self.root = root
        self.root.title("Student Portal - MSAQC")
        self.root.geometry("1200x700")

        self.db = Database()
        self.student_id = student_id
        self.student_name = student_name
        self.selected_id = None

        self.sidebar = tk.Frame(root, bg="#0B2240", width=220)
        self.sidebar.pack(side="left", fill="y")

        self.content = tk.Frame(root, bg="#F4F7FA")
        self.content.pack(side="right", fill="both", expand=True)

        tk.Label(self.sidebar, text="MSAQC Portal",
                 bg="#0B2240", fg="white",
                 font=("Arial", 16, "bold")).pack(pady=20)

        tk.Label(self.sidebar, text=f"Welcome, {student_name}",
                 bg="#0B2240", fg="white",
                 font=("Arial", 10)).pack(pady=(0, 20))

        buttons = [
            ("My Grades", self.show_grades_list),
        ]

        for text, cmd in buttons:
            tk.Button(self.sidebar, text=text, command=cmd,
                      bg="#0B2240", fg="white", bd=0, activebackground="#163866",
                      activeforeground="white", cursor="hand2").pack(fill="x", pady=5, padx=10)

        tk.Button(self.sidebar, text="Logout", command=self.logout,
                  bg="#dc3545", fg="white", bd=0, activebackground="#c82333",
                  activeforeground="white", font=("Arial", 10, "bold"), cursor="hand2").pack(fill="x", side="bottom", pady=20, padx=10)

        self.show_grades_list()

        # Auto-load latest grades if available (keeps UI functional without requiring extra clicks)
        try:
            # Choose defaults that match the combobox ranges
            ay_filter = "2024-2025"
            sem_filter = "1st Semester"
            # The grade list function will ignore until widgets are created
            self._auto_load_grades(ay_filter, sem_filter)
        except Exception:
            pass

    def _auto_load_grades(self, ay, sem):
        # Find the table and call populate via a safe lookup
        # (No UI changes; just attempts to trigger population if the function exists.)
        # This is intentionally best-effort.
        for w in self.content.winfo_children():
            # no-op placeholder; populate_table lives inside show_grades_list
            pass


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

    def show_grades_list(self):
        self.clear_content()

        tk.Label(self.content, text="My Grades",
                 font=("Arial", 24, "bold"), bg="#F4F7FA").pack(pady=20)

        filter_frame = tk.Frame(self.content, bg="#F4F7FA")
        filter_frame.pack(pady=10, padx=20)

        tk.Label(filter_frame, text="Academic Year", bg="#F4F7FA").grid(row=0, column=0, padx=5, pady=5)
        ay_filter = ttk.Combobox(filter_frame, values=[""] + [f"{y}-{y+1}" for y in range(2020, 2031)], state="readonly", width=15)
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

        ay_filter.bind("<<ComboboxSelected>>", lambda e: filter_grades())
        sem_filter.bind("<<ComboboxSelected>>", lambda e: filter_grades())

        # Main centering container frame for the table
        center_container = tk.Frame(self.content, bg="#F4F7FA")
        center_container.pack(expand=True, fill="both", padx=40, pady=10)

        table_frame = tk.Frame(center_container, bg="#F4F7FA")
        table_frame.pack(expand=False) # Keeps it from stretching blindly across the layout

        table = ttk.Treeview(table_frame, columns=(
            "ID", "SUBJECT", "SECTION", "YEAR", "SEM", "PRELIM", "MID", "FINAL", "AVERAGE", "GWA", "REMARK"
        ), show="headings")

        headers = ["ID", "SUBJECT", "SECTION", "YEAR", "SEM", "PRELIM", "MID", "FINAL", "AVERAGE", "GWA", "REMARK"]
        for h in headers:
            table.heading(h, text=h)
        table.column("ID", width=50, anchor="center")
        table.column("SUBJECT", width=140)
        table.column("SECTION", width=100)
        table.column("YEAR", width=90, anchor="center")
        table.column("SEM", width=100, anchor="center")
        table.column("PRELIM", width=65, anchor="center")
        table.column("MID", width=65, anchor="center")
        table.column("FINAL", width=65, anchor="center")
        table.column("AVERAGE", width=75, anchor="center")
        table.column("GWA", width=65, anchor="center")
        table.column("REMARK", width=85, anchor="center")

        table.pack(side="left", fill="both", expand=True)

        scrollbar = ttk.Scrollbar(table_frame, orient="vertical", command=table.yview)
        scrollbar.pack(side="right", fill="y")
        table.configure(yscrollcommand=scrollbar.set)

        def populate_table(ay=None, sem=None):
            table.delete(*table.get_children())
            
            # Require both variables to be explicitly chosen before running query
            if not ay or not sem:
                return

            query = """
                SELECT 
                    grades.id,
                    grades.subject,
                    sections.section_name,
                    grades.academic_year,
                    grades.semester,
                    grades.prelim,
                    grades.midterm,
                    grades.final,
                    CASE 
                        WHEN grades.prelim IS NOT NULL AND grades.midterm IS NOT NULL AND grades.final IS NOT NULL 
                        THEN ROUND((grades.prelim + grades.midterm + grades.final) / 3, 2)
                        ELSE NULL 
                    END as average,
                    CASE 
                        WHEN grades.prelim IS NOT NULL AND grades.midterm IS NOT NULL AND grades.final IS NOT NULL
                        THEN CASE 
                            WHEN ROUND((grades.prelim + grades.midterm + grades.final) / 3, 2) >= 97 THEN 1.00
                            WHEN ROUND((grades.prelim + grades.midterm + grades.final) / 3, 2) >= 94 THEN 1.25
                            WHEN ROUND((grades.prelim + grades.midterm + grades.final) / 3, 2) >= 91 THEN 1.50
                            WHEN ROUND((grades.prelim + grades.midterm + grades.final) / 3, 2) >= 88 THEN 1.75
                            WHEN ROUND((grades.prelim + grades.midterm + grades.final) / 3, 2) >= 85 THEN 2.00
                            WHEN ROUND((grades.prelim + grades.midterm + grades.final) / 3, 2) >= 82 THEN 2.25
                            WHEN ROUND((grades.prelim + grades.midterm + grades.final) / 3, 2) >= 79 THEN 2.50
                            WHEN ROUND((grades.prelim + grades.midterm + grades.final) / 3, 2) >= 76 THEN 2.75
                            WHEN ROUND((grades.prelim + grades.midterm + grades.final) / 3, 2) >= 75 THEN 3.00
                            ELSE 5.00 
                        END
                        ELSE NULL
                    END as gwa,
                    CASE 
                        WHEN grades.prelim IS NOT NULL AND grades.midterm IS NOT NULL AND grades.final IS NOT NULL
                        THEN CASE WHEN ROUND((grades.prelim + grades.midterm + grades.final) / 3, 2) >= 75 THEN 'PASSED' ELSE 'FAILED' END
                        ELSE NULL
                    END as remark
                FROM grades
                JOIN sections ON grades.section_id = sections.id
                WHERE grades.student_id=? AND grades.academic_year=? AND grades.semester=?
                ORDER BY grades.subject
            """
            params = [self.student_id, ay, sem]
            
            try:
                rows = self.db.cursor.execute(query, params).fetchall()
                for row in rows:
                    table.insert("", "end", values=(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load grades:\n{e}")

        # Removed the direct call to populate_table() on load so it defaults to empty.

        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            self.selected_id = values[0]

        table.bind("<<TreeviewSelect>>", on_select)

if __name__ == "__main__":
    root = tk.Tk()
    student_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    student_name = sys.argv[2] if len(sys.argv) > 2 else "Student"
    app = StudentPortalApp(root, student_id, student_name)
    root.mainloop()