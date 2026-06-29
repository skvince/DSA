import tkinter as tk
from tkinter import font, messagebox
import os
import sys
import subprocess
from PIL import Image, ImageTk
from database import Database, hash_password

def handle_login():
    username = email_input.get().strip()
    password = password_input.get()
    db = Database()
    python_exe = sys.executable
    if username == "admin" and password == "123":
        db.add_audit_log(1, "admin", "Admin", "All", "Login", "Admin logged in")
        root.destroy()
        subprocess.run([python_exe, "admin.py"])
    else:
        raw = username.replace(" ", "")
        role_prefix = None
        if raw.upper().startswith("T-"):
            role_prefix = "T"
            raw = raw[2:]
        elif raw.upper().startswith("S-"):
            role_prefix = "S"
            raw = raw[2:]

        if raw.isdigit():
            uid = int(raw)

            if role_prefix in (None, "T"):
                teacher = db.cursor.execute(
                    "SELECT id, firstname, middlename, lastname, password FROM teachers WHERE id=?",
                    (uid,)
                ).fetchone()
                if teacher and teacher[4] is not None and teacher[4] == hash_password(password):
                    t_name = f"{teacher[1]} {(teacher[2] or '').strip()} {teacher[3]}".replace("  ", " ").strip()
                    dept = db.cursor.execute("SELECT dept_name FROM departments WHERE id=(SELECT dept_id FROM teachers WHERE id=?)", (uid,)).fetchone()
                    dept_name = dept[0] if dept else "Unknown"
                    db.add_audit_log(uid, t_name, "Teacher", dept_name, "Login", "Teacher logged in")
                    root.destroy()
                    subprocess.run([python_exe, "teacher.py", str(teacher[0]), t_name])
                    return

            if role_prefix in (None, "S"):
                student = db.cursor.execute(
                    "SELECT id, firstname, middlename, lastname, password FROM students WHERE id=?",
                    (uid,)
                ).fetchone()
                if student and student[4] is not None and student[4] == hash_password(password):
                    s_name = f"{student[1]} {(student[2] or '').strip()} {student[3]}".replace("  ", " ").strip()
                    db.add_audit_log(uid, s_name, "Student", "N/A", "Login", "Student logged in")
                    root.destroy()
                    subprocess.run([python_exe, "student.py", str(student[0]), s_name])
                    return

            messagebox.showerror("Error", "Invalid ID or Password")

# Initialize main window
root = tk.Tk()
root.title("MSAQC Portal")
root.geometry("1000x600")
root.configure(bg="#f5f5f5")

# Configure grid weights for a 50/50 split screen
root.grid_columnconfigure(0, weight=1, uniform="group1")
root.grid_columnconfigure(1, weight=1, uniform="group1")
root.grid_rowconfigure(0, weight=1)

# Custom Fonts
font_family_sans = "Arial"
font_family_serif = "Georgia"

title_font = font.Font(family=font_family_serif, size=36, weight="bold")
hero_font = font.Font(family=font_family_serif, size=45, weight="bold")
label_font = font.Font(family=font_family_sans, size=12)
input_font = font.Font(family=font_family_sans, size=12)
btn_font = font.Font(family=font_family_sans, size=16, weight="bold")
sub_text_font = font.Font(family=font_family_sans, size=14)


# LEFT SIDE: Login Form
left_frame = tk.Frame(root, bg="#f5f5f5")
left_frame.grid(row=0, column=1, sticky="nsew", padx=40, pady=100)

left_frame.grid_columnconfigure(0, weight=1)
left_frame.grid_rowconfigure(0, weight=1)
left_frame.grid_rowconfigure(2, weight=1)

login_box = tk.Frame(left_frame, bg="#f5f5f5")
login_box.grid(row=1, column=0, sticky="ew", padx=20)

# Header Row 
header_frame = tk.Frame(login_box, bg="#f5f5f5")
header_frame.pack(anchor="w", pady=(0, 30))

try:
    # Open the newly provided logo file using Pillow
    img_path = "logo.png"
    pil_img = Image.open(img_path)
    
    # Resize the logo beautifully to fit the header row profile (120x120 pixels)
    pil_img = pil_img.resize((120, 120), Image.Resampling.LANCZOS)
    logo_photo = ImageTk.PhotoImage(pil_img)
    
    # Render the actual image logo on the left
    logo_label = tk.Label(header_frame, image=logo_photo, bg="#f5f5f5")
    logo_label.image = logo_photo  # type: ignore[attr-defined]
    logo_label.pack(side="left", padx=(0, 15))
except Exception as e:
    # Safe fallback canvas if the file isn't found
    print(f"Could not load logo image: {e}")
    icon_canvas = tk.Canvas(header_frame, width=70, height=70, bg="#f5f5f5", highlightthickness=0)
    icon_canvas.pack(side="left", padx=(0, 15))
    icon_canvas.create_oval(2, 2, 58, 58, fill="#0f4a2f", outline="")
    icon_canvas.create_polygon(15, 30, 30, 20, 45, 30, 30, 40, fill="white")
    icon_canvas.create_rectangle(24, 36, 36, 42, fill="white")
    icon_canvas.create_line(40, 32, 40, 45, fill="white", width=2)

login_title = tk.Label(header_frame, text="Sign In", font=title_font, fg="#0B2240", bg="#f5f5f5")
login_title.pack(side="left")

# Form Fields
email_label = tk.Label(login_box, text="Username / Student or Teacher ID", font=label_font, fg="#0B2240", bg="#f5f5f5")
email_label.pack(anchor="w", pady=(0, 5))

email_input = tk.Entry(login_box, font=input_font, bg="#e9eef7", fg="black", bd=0, insertbackground="black")
email_input.pack(fill="x", ipady=12, pady=(0, 20))

password_label = tk.Label(login_box, text="Password", font=label_font, fg="#0B2240", bg="#f5f5f5")
password_label.pack(anchor="w", pady=(0, 5))

password_input = tk.Entry(login_box, font=input_font, bg="#e9eef7", fg="black", bd=0, show="•", insertbackground="black")
password_input.pack(fill="x", ipady=12, pady=(0, 30))

# Login Button
login_btn = tk.Button(
    login_box, 
    text="Login", 
    font=btn_font, 
    bg="#0B2240", 
    fg="white", 
    activebackground="#1C3B5E", 
    activeforeground="white", 
    bd=0, 
    cursor="hand2",
    command=handle_login
)
login_btn.pack(fill="x", ipady=10)

# RIGHT SIDE: Hero Accent Banner
right_frame = tk.Frame(root, bg="#0B2240")
right_frame.grid(row=0, column=0, sticky="nsew")

right_frame.grid_columnconfigure(0, weight=1)
right_frame.grid_rowconfigure(0, weight=1)
right_frame.grid_rowconfigure(2, weight=1)

right_content = tk.Frame(right_frame, bg="#0B2240")
right_content.grid(row=1, column=0, sticky="ew")

hero_text = tk.Label(
    right_content, 
    text="BE FUTURE\nQUALIFIED\nWITH US", 
    font=hero_font, 
    fg="white", 
    bg="#0B2240", 
    justify="center"
)
hero_text.pack(pady=(0, 20))

sub_text = tk.Label(
    right_content, 
    text="Metanoia School Academy Quezon City.", 
    font=sub_text_font,     
    fg="#d5d5d5", 
    bg="#0B2240"
)
sub_text.pack()



root.update_idletasks()
root.eval('tk::PlaceWindow . center')

root.mainloop()