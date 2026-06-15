import sqlite3

class Database:
    def __init__(self):
        self.conn = sqlite3.connect("msaqc_portal.db")
        self.cursor = self.conn.cursor()
        # Enable Foreign Key enforcement in SQLite
        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.create_tables()

    def create_tables(self):
        # 1. Departments
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS departments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dept_name TEXT UNIQUE NOT NULL
        )
        """)

        # 2. Sections (Linked to Departments)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS sections(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            section_name TEXT UNIQUE NOT NULL,
            dept_id INTEGER NOT NULL,
            FOREIGN KEY (dept_id) REFERENCES departments(id) ON DELETE CASCADE
        )
        """)

        # 3. Teachers (Linked to Departments)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS teachers(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT NOT NULL,
            middlename TEXT,
            lastname TEXT NOT NULL,
            dept_id INTEGER NOT NULL,
            password TEXT,
            FOREIGN KEY (dept_id) REFERENCES departments(id) ON DELETE CASCADE
        )
        """)

        # 4. Students (Linked to Sections)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS students(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            firstname TEXT NOT NULL,
            middlename TEXT,
            lastname TEXT NOT NULL,
            section_id INTEGER NOT NULL,
            password TEXT,
            FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
        )
        """)

        # 5. Assignments (Linked to Teachers and Sections)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS assignments(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            section_id INTEGER NOT NULL,
            academic_year TEXT NOT NULL,
            semester TEXT NOT NULL,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
            FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
        )
        """)
        self.conn.commit()

        # Migration: Add middlename to teachers if missing
        self.cursor.execute("PRAGMA table_info(teachers)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if "middlename" not in columns:
            self.cursor.execute("ALTER TABLE teachers ADD COLUMN middlename TEXT")
            self.conn.commit()

        # Migration: Add middlename to students if missing
        self.cursor.execute("PRAGMA table_info(students)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if "middlename" not in columns:
            self.cursor.execute("ALTER TABLE students ADD COLUMN middlename TEXT")
            self.conn.commit()

        # Migration: Add email to teachers if missing
        self.cursor.execute("PRAGMA table_info(teachers)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if "email" not in columns:
            self.cursor.execute("ALTER TABLE teachers ADD COLUMN email TEXT")
            self.conn.commit()

        # 6. Grades (Linked to Teachers, Sections, Students)
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS grades(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            section_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            subject TEXT NOT NULL,
            academic_year TEXT NOT NULL,
            semester TEXT NOT NULL,
            prelim REAL NOT NULL DEFAULT 0,
            midterm REAL NOT NULL DEFAULT 0,
            final REAL NOT NULL DEFAULT 0,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
            FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
        """)
        self.conn.commit()

    # -----------------------------
    # DEPARTMENTS
    # -----------------------------
    def add_department(self, dept_name):
        self.cursor.execute("INSERT INTO departments(dept_name) VALUES(?)", (dept_name,))
        self.conn.commit()

    def get_departments(self):
        self.cursor.execute("SELECT id, dept_name FROM departments")
        return self.cursor.fetchall()

    def update_department(self, dept_id, dept_name):
        self.cursor.execute("UPDATE departments SET dept_name=? WHERE id=?", (dept_name, dept_id))
        self.conn.commit()

    def delete_department(self, dept_id):
        self.cursor.execute("DELETE FROM departments WHERE id=?", (dept_id,))
        self.conn.commit()

    # -----------------------------
    # SECTIONS
    # -----------------------------
    def add_section(self, section_name, dept_id):
        self.cursor.execute("INSERT INTO sections(section_name, dept_id) VALUES (?, ?)", (section_name, dept_id))
        self.conn.commit()

    def get_sections(self):
        self.cursor.execute("""
            SELECT sections.id, sections.section_name, departments.dept_name 
            FROM sections 
            JOIN departments ON sections.dept_id = departments.id
        """)
        return self.cursor.fetchall()

    def update_section(self, sec_id, section_name, dept_id):
        self.cursor.execute("UPDATE sections SET section_name=?, dept_id=? WHERE id=?", (section_name, dept_id, sec_id))
        self.conn.commit()

    def delete_section(self, sec_id):
        self.cursor.execute("DELETE FROM sections WHERE id=?", (sec_id,))
        self.conn.commit()

    # -----------------------------
    # TEACHERS
    # -----------------------------
    def add_teacher(self, firstname, middlename, lastname, dept_id, password, email=None):
        self.cursor.execute("""
            INSERT INTO teachers (firstname, middlename, lastname, dept_id, password, email) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (firstname, middlename, lastname, dept_id, password, email))
        self.conn.commit()

    def get_teachers(self):
        self.cursor.execute("""
            SELECT teachers.id, teachers.firstname, teachers.lastname, departments.dept_name, teachers.password, teachers.email 
            FROM teachers 
            JOIN departments ON teachers.dept_id = departments.id
        """)
        return self.cursor.fetchall()

    def get_teacher_by_email(self, email):
        self.cursor.execute("SELECT id, firstname, lastname, dept_id, password, email FROM teachers WHERE email=?", (email,))
        return self.cursor.fetchone()

    def update_teacher(self, tid, firstname, middlename, lastname, dept_id, email=None):
        self.cursor.execute("""
            UPDATE teachers 
            SET firstname=?, middlename=?, lastname=?, dept_id=?, email=? 
            WHERE id=?
        """, (firstname, middlename, lastname, dept_id, email, tid))
        self.conn.commit()

    def update_password(self, table, row_id, password):
        self.cursor.execute(f"UPDATE {table} SET password=? WHERE id=?", (password, row_id))
        self.conn.commit()

    # -----------------------------
    # GRADES
    # -----------------------------
    def add_grade(self, teacher_id, section_id, student_id, subject, academic_year, semester, prelim, midterm, final):
        self.cursor.execute("""
            INSERT INTO grades (teacher_id, section_id, student_id, subject, academic_year, semester, prelim, midterm, final)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (teacher_id, section_id, student_id, subject, academic_year, semester, prelim, midterm, final))
        self.conn.commit()

    def get_grades(self, teacher_id=None, academic_year=None, semester=None):
        query = """
            SELECT 
                grades.id,
                students.firstname || ' ' || students.lastname AS student_name,
                sections.section_name,
                grades.subject,
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
            JOIN students ON grades.student_id = students.id
            JOIN sections ON grades.section_id = sections.id
            WHERE 1=1
        """
        params = []
        if teacher_id:
            query += " AND grades.teacher_id=?"
            params.append(teacher_id)
        if academic_year:
            query += " AND grades.academic_year=?"
            params.append(academic_year)
        if semester:
            query += " AND grades.semester=?"
            params.append(semester)
        query += " ORDER BY grades.academic_year DESC, grades.semester, sections.section_name, students.lastname"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def update_grade(self, grade_id, prelim, midterm, final):
        self.cursor.execute("UPDATE grades SET prelim=?, midterm=?, final=? WHERE id=?", (prelim, midterm, final, grade_id))
        self.conn.commit()

    def delete_grade(self, grade_id):
        self.cursor.execute("DELETE FROM grades WHERE id=?", (grade_id,))
        self.conn.commit()

    def get_available_sections(self, teacher_id):
        self.cursor.execute("""
            SELECT DISTINCT sections.id, sections.section_name, departments.dept_name
            FROM assignments
            JOIN sections ON assignments.section_id = sections.id
            JOIN departments ON sections.dept_id = departments.id
            WHERE assignments.teacher_id=?
        """, (teacher_id,))
        return self.cursor.fetchall()

    def get_available_subjects(self, teacher_id):
        self.cursor.execute("SELECT DISTINCT subject FROM assignments WHERE teacher_id=?", (teacher_id,))
        return [row[0] for row in self.cursor.fetchall()]

    def assignment_exists(self, teacher_id, section_id, subject, academic_year, semester):
        self.cursor.execute("""
            SELECT id FROM assignments 
            WHERE teacher_id=? AND section_id=? AND subject=? AND academic_year=? AND semester=?
        """, (teacher_id, section_id, subject, academic_year, semester))
        return self.cursor.fetchone() is not None

    def get_section_students(self, section_id):
        self.cursor.execute("""
            SELECT students.id, students.firstname, COALESCE(students.middlename, ''), students.lastname, sections.section_name
            FROM students

            JOIN sections ON students.section_id = sections.id
            WHERE students.section_id=?
            ORDER BY students.lastname, students.firstname
        """, (section_id,))
        return self.cursor.fetchall()

    # -----------------------------
    # STUDENTS
    # -----------------------------
    def add_student(self, firstname, middlename, lastname, section_id, password):
        self.cursor.execute("""
            INSERT INTO students (firstname, middlename, lastname, section_id, password) 
            VALUES (?, ?, ?, ?, ?)
        """, (firstname, middlename, lastname, section_id, password))
        self.conn.commit()

    def get_students(self):
        self.cursor.execute("""
            SELECT students.id, students.firstname, students.lastname, sections.section_name, students.password 
            FROM students 
            JOIN sections ON students.section_id = sections.id
        """)
        return self.cursor.fetchall()

    def update_student(self, sid, firstname, middlename, lastname, section_id):
        self.cursor.execute("""
            UPDATE students 
            SET firstname=?, middlename=?, lastname=?, section_id=? 
            WHERE id=?
        """, (firstname, middlename, lastname, section_id, sid))
        self.conn.commit()

    def delete_student(self, sid):
        self.cursor.execute("DELETE FROM students WHERE id=?", (sid,))
        self.conn.commit()

    # -----------------------------
    # ASSIGNMENTS
    # -----------------------------
    def add_assignment(self, teacher_id, subject, section_id, academic_year, semester):
        self.cursor.execute("""
            INSERT INTO assignments (teacher_id, subject, section_id, academic_year, semester)
            VALUES (?, ?, ?, ?, ?)
        """, (teacher_id, subject, section_id, academic_year, semester))
        self.conn.commit()

    def get_assignments(self):
        self.cursor.execute("""
            SELECT 
                assignments.id, 
                (teachers.firstname || ' ' || teachers.lastname) AS teacher_name, 
                assignments.subject, 
                sections.section_name, 
                assignments.academic_year, 
                assignments.semester
            FROM assignments
            JOIN teachers ON assignments.teacher_id = teachers.id
            JOIN sections ON assignments.section_id = sections.id
        """)
        return self.cursor.fetchall()

    def update_assignment(self, assign_id, teacher_id, subject, section_id, academic_year, semester):
        self.cursor.execute("""
            UPDATE assignments 
            SET teacher_id=?, subject=?, section_id=?, academic_year=?, semester=? 
            WHERE id=?
        """, (teacher_id, subject, section_id, academic_year, semester, assign_id))
        self.conn.commit()

    def delete_assignment(self, assign_id):
        self.cursor.execute("DELETE FROM assignments WHERE id=?", (assign_id,))
        self.conn.commit()

    