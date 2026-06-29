import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
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

        # Sidebar header with logo and text aligned horizontally
        header_frame = tk.Frame(self.sidebar, bg="#0B2240")
        header_frame.pack(pady=20, padx=10, fill="x")

        # Logo on the left
        try:
            logo_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logo.png")
            pil_img = Image.open(logo_path)
            pil_img = pil_img.resize((70,70), Image.Resampling.LANCZOS)
            self.logo_img = ImageTk.PhotoImage(pil_img)
            logo_label = tk.Label(header_frame, image=self.logo_img, bg="#0B2240")
            logo_label.pack(side="left", padx=(0, 5))
        except Exception:
            pass

        # MSAQC text on the right
        tk.Label(header_frame, text="MSAQC",
                 bg="#0B2240", fg="white",
                 font=("Arial", 16, "bold")).pack(side="left")

        tk.Label(self.sidebar, text=f"Welcome, {student_name}",
                 bg="#0B2240", fg="white",
                 font=("Arial", 10)).pack(pady=(0, 20))

        buttons = [
            ("My Grades", self.show_grades_list),
            ("Change Password", self.show_change_password),
        ]

        for text, cmd in buttons:
            tk.Button(self.sidebar, text=text, command=cmd,
                    bg="#0B2240", fg="white", bd=0,
                    activebackground="#163866",
                    activeforeground="white", cursor="hand2").pack(fill="x", pady=5, padx=10)

        tk.Button(self.sidebar, text="Logout", command=self.logout,
                  bg="#dc3545", fg="white", bd=0, activebackground="#c82333",
                  activeforeground="white", font=("Arial", 10, "bold"), cursor="hand2").pack(fill="x", side="bottom", pady=20, padx=10)

        self.show_grades_list()

    def logout(self):
        confirm = messagebox.askyesno("Logout", "Sigurado ka ba na gusto mong mag-logout?")
        if confirm:
            self.clear_content()
            self.db.add_audit_log(self.student_id, self.student_name, "Student", "N/A", "Logout", "Student logged out")
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
        ay_filter.set("2024-2025")

        tk.Label(filter_frame, text="Semester", bg="#F4F7FA").grid(row=0, column=2, padx=5, pady=5)
        sem_filter = ttk.Combobox(filter_frame, values=["", "1st Semester", "2nd Semester", "Summer"], state="readonly", width=15)
        sem_filter.grid(row=0, column=3, padx=5, pady=5)
        sem_filter.set("1st Semester")

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
            "CODE", "SUBJECT", "SECTION", "PRELIM", "MID", "FINAL", "AVERAGE", "GWA", "REMARK"
        ), show="headings")

        headers = ["CODE", "SUBJECT", "SECTION", "PRELIM", "MID", "FINAL", "AVERAGE", "GWA", "REMARK"]
        for h in headers:
            table.heading(h, text=h)
        table.column("CODE", width=70, anchor="center")
        table.column("SUBJECT", width=140)
        table.column("SECTION", width=100)
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
            if not ay or not sem:
                return

            query = """
                SELECT 
                    COALESCE(g.id, -1) as id,
                    a.subject,
                    s.section_name,
                    sub.subject_code,
                    g.prelim,
                    g.midterm,
                    g.final,
                    CASE 
                        WHEN g.prelim > 0 AND g.midterm > 0 AND g.final > 0
                        THEN ROUND((g.prelim + g.midterm + g.final) / 3, 2)
                        ELSE NULL
                    END as average,
                    CASE 
                        WHEN g.prelim > 0 AND g.midterm > 0 AND g.final > 0
                        THEN CASE 
                            WHEN ROUND((g.prelim + g.midterm + g.final) / 3, 2) >= 97 THEN 1.00
                            WHEN ROUND((g.prelim + g.midterm + g.final) / 3, 2) >= 94 THEN 1.25
                            WHEN ROUND((g.prelim + g.midterm + g.final) / 3, 2) >= 91 THEN 1.50
                            WHEN ROUND((g.prelim + g.midterm + g.final) / 3, 2) >= 88 THEN 1.75
                            WHEN ROUND((g.prelim + g.midterm + g.final) / 3, 2) >= 85 THEN 2.00
                            WHEN ROUND((g.prelim + g.midterm + g.final) / 3, 2) >= 82 THEN 2.25
                            WHEN ROUND((g.prelim + g.midterm + g.final) / 3, 2) >= 79 THEN 2.50
                            WHEN ROUND((g.prelim + g.midterm + g.final) / 3, 2) >= 76 THEN 2.75
                            WHEN ROUND((g.prelim + g.midterm + g.final) / 3, 2) >= 75 THEN 3.00
                            ELSE 5.00 
                        END
                        ELSE NULL
                    END as gwa,
                    CASE 
                        WHEN g.prelim > 0 AND g.midterm > 0 AND g.final > 0
                        THEN CASE WHEN ROUND((g.prelim + g.midterm + g.final) / 3, 2) >= 75 THEN 'PASSED' ELSE 'FAILED' END
                        ELSE NULL
                    END as remark

                FROM assignments a
                JOIN sections s ON s.id = a.section_id
                JOIN students st ON st.section_id = a.section_id
                JOIN subjects sub ON sub.subject_name = a.subject
                LEFT JOIN grades g ON g.student_id = st.id 
                    AND g.subject = a.subject 
                    AND g.academic_year = a.academic_year 
                    AND g.semester = a.semester
                WHERE st.id=? AND a.academic_year=? AND a.semester=?
                ORDER BY a.subject
            """
            params = [self.student_id, ay, sem]
            
            try:
                rows = self.db.cursor.execute(query, params).fetchall()
                for row in rows:
                    table.insert("", "end", values=(row[3], row[1], row[2], row[4] if row[4] is not None else "", row[5] if row[5] is not None else "", row[6] if row[6] is not None else "", row[7] if row[7] is not None else "", row[8] if row[8] is not None else "", row[9] if row[9] is not None else ""))
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load grades:\n{e}")

        def on_select(event):
            selected = table.focus()
            if not selected: return
            values = table.item(selected, 'values')
            self.selected_id = values[0]

        table.bind("<<TreeviewSelect>>", on_select)

        populate_table(ay_filter.get().strip() or None, sem_filter.get() or None)

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
            if not self.db.verify_password("students", self.student_id, current_pw.get()):
                messagebox.showerror("Error", "Current password is incorrect.", parent=popup)
                return
            if new_pw.get() != confirm_pw.get():
                messagebox.showerror("Error", "New passwords do not match.", parent=popup)
                return
            if len(new_pw.get()) < 4:
                messagebox.showwarning("Error", "Password must be at least 4 characters.", parent=popup)
                return
            self.db.update_password("students", self.student_id, new_pw.get())
            self.db.add_audit_log(self.student_id, self.student_name, "Student", "N/A", "Password Change", "Password changed successfully")
            self.db.add_notification(self.student_id, "Student", "Password Changed", "Your password has been changed. Please login again.")
            messagebox.showinfo("Success", "Password changed successfully. Please login again.", parent=popup)
            popup.destroy()
            self.logout()

        tk.Button(popup, text="Change Password", command=change, bg="#0B2240", fg="white", font=("Arial", 10), width=18).pack(pady=10)


if __name__ == "__main__":
    root = tk.Tk()
    student_id = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    student_name = sys.argv[2] if len(sys.argv) > 2 else "Student"
    app = StudentPortalApp(root, student_id, student_name)
    root.mainloop()