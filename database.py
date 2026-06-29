import sqlite3
import hashlib
from datetime import datetime

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

class Database:
    def __init__(self):
        # Single shared connection for the app lifetime.
        # WAL + busy_timeout improves responsiveness under concurrent writes.
        self.conn = sqlite3.connect("msaqc_portal.db")
        self.cursor = self.conn.cursor()

        self.cursor.execute("PRAGMA foreign_keys = ON;")
        self.cursor.execute("PRAGMA journal_mode = WAL;")
        self.cursor.execute("PRAGMA busy_timeout = 5000;")
        self.cursor.execute("PRAGMA synchronous = NORMAL;")

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

        # Prevent duplicates at the DB level
        self.cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_assignments_teacher_subject_section_year_sem
            ON assignments(teacher_id, subject, section_id, academic_year, semester)
        """)
        self.conn.commit()


        # 5b. Subjects
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS subjects(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject_code TEXT UNIQUE NOT NULL,
            subject_name TEXT NOT NULL,
            school_year TEXT NOT NULL,
            semester TEXT NOT NULL,
            units INTEGER NOT NULL
        )
        """)
        self.conn.commit()

        # 6. Grade Encoding Deadlines
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS grade_encoding_deadlines(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_year TEXT NOT NULL,
            semester TEXT NOT NULL,
            grading_period TEXT NOT NULL,
            start_date TEXT NOT NULL,
            end_date TEXT NOT NULL,
            status TEXT DEFAULT 'Open'
        )
        """)
        self.conn.commit()

        # 7. Extension Requests
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS extension_requests(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            teacher_id INTEGER NOT NULL,
            teacher_name TEXT,
            subject TEXT,
            section_id INTEGER,
            section_name TEXT,
            dept_id INTEGER,
            school_year TEXT,
            semester TEXT,
            grading_period TEXT,
            reason TEXT,
            status TEXT DEFAULT 'Pending',
            admin_remarks TEXT,
            created_at TEXT,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
            FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE
        )
        """)
        self.conn.commit()

        # Migration: Add missing columns to extension_requests if needed
        self.cursor.execute("PRAGMA table_info(extension_requests)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if "teacher_name" not in columns:
            self.cursor.execute("ALTER TABLE extension_requests ADD COLUMN teacher_name TEXT")
            self.conn.commit()
        if "section_id" not in columns:
            self.cursor.execute("ALTER TABLE extension_requests ADD COLUMN section_id INTEGER")
            self.conn.commit()
        if "section_name" not in columns:
            self.cursor.execute("ALTER TABLE extension_requests ADD COLUMN section_name TEXT")
            self.conn.commit()
        if "admin_remarks" not in columns:
            self.cursor.execute("ALTER TABLE extension_requests ADD COLUMN admin_remarks TEXT")
            self.conn.commit()

        # 8. Grade Locks
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS grade_locks(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            section_id INTEGER NOT NULL,
            school_year TEXT NOT NULL,
            semester TEXT NOT NULL,
            grading_period TEXT NOT NULL,
            locked INTEGER DEFAULT 1,
            locked_at TEXT,
            UNIQUE(subject, section_id, school_year, semester, grading_period)
        )
        """)
        self.conn.commit()

        # Migration: Add missing columns to grade_locks if needed (for existing DBs)
        self.cursor.execute("PRAGMA table_info(grade_locks)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if "section_id" not in columns:
            self.cursor.execute("ALTER TABLE grade_locks ADD COLUMN section_id INTEGER")
            self.conn.commit()

        # 8b. Open Grading Periods
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS open_grading_periods(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            school_year TEXT NOT NULL,
            semester TEXT NOT NULL,
            grading_period TEXT NOT NULL,
            updated_at TEXT,
            UNIQUE(school_year, semester)
        )
        """)
        self.conn.commit()

        # Migration: Add updated_at if missing
        self.cursor.execute("PRAGMA table_info(open_grading_periods)")
        columns = [row[1] for row in self.cursor.fetchall()]
        if "updated_at" not in columns:
            self.cursor.execute("ALTER TABLE open_grading_periods ADD COLUMN updated_at TEXT")
            self.conn.commit()

        # 9. Notifications
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_role TEXT,
            title TEXT,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT
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
            prelim REAL,
            midterm REAL,
            final REAL,
            FOREIGN KEY (teacher_id) REFERENCES teachers(id) ON DELETE CASCADE,
            FOREIGN KEY (section_id) REFERENCES sections(id) ON DELETE CASCADE,
            FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE
        )
        """)
        self.conn.commit()

        # Enforce uniqueness to prevent duplicate grade rows for the same student/subject/year/semester.
        # If the table already exists, adding the index is safe.
        self.cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_grades_student_subject_year_sem
            ON grades(student_id, subject, academic_year, semester)
        """)
        self.conn.commit()

        # 7. Notifications
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS notifications(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_role TEXT,
            title TEXT,
            message TEXT,
            is_read INTEGER DEFAULT 0,
            created_at TEXT
        )
        """)
        self.conn.commit()

        # 8. Audit Logs
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            user_name TEXT,
            role TEXT,
            department TEXT,
            action TEXT NOT NULL,
            description TEXT,
            created_at TEXT NOT NULL
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

    def get_department_counts(self):
        self.cursor.execute("""
            SELECT 
                d.id,
                d.dept_name,
                COUNT(DISTINCT t.id) as teacher_count,
                COUNT(DISTINCT s.id) as student_count
            FROM departments d
            LEFT JOIN teachers t ON d.id = t.dept_id AND t.status != 'Archived'
            LEFT JOIN sections sec ON sec.dept_id = d.id
            LEFT JOIN students s ON s.section_id = sec.id AND s.status != 'Archived'
            GROUP BY d.id, d.dept_name
            ORDER BY d.dept_name
        """)
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
        self.cursor.execute("SELECT id FROM students WHERE section_id=?", (sec_id,))
        if self.cursor.fetchone():
            return "students"
        self.cursor.execute("SELECT id FROM assignments WHERE section_id=?", (sec_id,))
        if self.cursor.fetchone():
            return "assignments"
        self.cursor.execute("DELETE FROM sections WHERE id=?", (sec_id,))
        self.conn.commit()
        return None

    # -----------------------------
    # TEACHERS
    # -----------------------------
    def add_teacher(self, firstname, middlename, lastname, dept_id, password, email=None):
        self.cursor.execute("""
            INSERT INTO teachers (firstname, middlename, lastname, dept_id, password, email) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (firstname, middlename, lastname, dept_id, password, email))
        self.conn.commit()

    def get_teachers(self, dept_id=None):
        query = """
            SELECT 
                teachers.id,
                teachers.firstname,
                COALESCE(teachers.middlename, ''),
                teachers.lastname,
                departments.dept_name,
                teachers.password
            FROM teachers 
            JOIN departments ON teachers.dept_id = departments.id
        """
        params = []
        if dept_id:
            query += " WHERE teachers.dept_id = ?"
            params.append(dept_id)
        query += " ORDER BY teachers.lastname, teachers.firstname"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()


    def get_teacher_by_email(self, email):
        self.cursor.execute("SELECT id, firstname, lastname, dept_id, password, email FROM teachers WHERE email=?", (email,))
        return self.cursor.fetchone()

    def get_teacher_by_id(self, teacher_id):
        self.cursor.execute("SELECT id, firstname, middlename, lastname, dept_id, password, email FROM teachers WHERE id=?", (teacher_id,))
        row = self.cursor.fetchone()
        if row:
            # Return as id, firstname, middlename, lastname, dept_id, password, email
            return (row[0], row[1], row[2], row[3], row[4], row[5], row[6])
        return row

    def update_teacher(self, tid, firstname, middlename, lastname, dept_id, email=None):
        self.cursor.execute("""
            UPDATE teachers 
            SET firstname=?, middlename=?, lastname=?, dept_id=?, email=? 
            WHERE id=?
        """, (firstname, middlename, lastname, dept_id, email, tid))
        self.conn.commit()

    def delete_teacher(self, tid):
        self.cursor.execute("SELECT id FROM assignments WHERE teacher_id=?", (tid,))
        if self.cursor.fetchone():
            return "assignments"
        self.cursor.execute("DELETE FROM teachers WHERE id=?", (tid,))
        self.conn.commit()
        return None

    def update_password(self, table, row_id, password):
        self.cursor.execute(f"UPDATE {table} SET password=? WHERE id=?", (password, row_id))
        self.conn.commit()

    def verify_password(self, table, row_id, password):
        self.cursor.execute(f"SELECT password FROM {table} WHERE id=?", (row_id,))
        result = self.cursor.fetchone()
        return result is not None and result[0] == password

    # -----------------------------
    # GRADES
    # -----------------------------
    def insert_grade(self, teacher_id, section_id, student_id, subject, academic_year, semester, prelim, midterm, final):
        def to_val(v):
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                return None
        p = to_val(prelim)
        m = to_val(midterm)
        f = to_val(final)
        self.cursor.execute(
            "INSERT INTO grades (teacher_id, section_id, student_id, subject, academic_year, semester, prelim, midterm, final) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (teacher_id, section_id, student_id, subject, academic_year, semester, p, m, f)
        )
        self.conn.commit()

    def add_grade(self, teacher_id, section_id, student_id, subject, academic_year, semester, prelim, midterm, final):
        def to_float_or_zero(v):
            if v is None:
                return 0.0
            s = str(v).strip()
            if s == "":
                return 0.0
            try:
                return float(s)
            except ValueError:
                return 0.0

        p = to_float_or_zero(prelim)
        m = to_float_or_zero(midterm)
        f = to_float_or_zero(final)

        self.cursor.execute("""
            INSERT INTO grades (teacher_id, section_id, student_id, subject, academic_year, semester, prelim, midterm, final)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (teacher_id, section_id, student_id, subject, academic_year, semester, p, m, f))
        self.conn.commit()

    def get_grades(self, teacher_id=None, academic_year=None, semester=None):
        query = """
            SELECT 
                grades.id,
                (students.firstname || ' ' || COALESCE(students.middlename,'') || ' ' || students.lastname) AS student_name,
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

    def update_grade_column(self, grade_id, column, value):
        def to_val(v):
            if v is None or v == "":
                return None
            try:
                return float(v)
            except (ValueError, TypeError):
                return None
        self.cursor.execute(f"UPDATE grades SET {column}=? WHERE id=?", (to_val(value), grade_id))
        self.conn.commit()

    def update_grade(self, grade_id, prelim, midterm, final):
        
        def to_float_or_zero(v):
            if v is None:
                return 0.0
            s = str(v).strip()
            if s == "":
                return 0.0
            try:
                return float(s)
            except ValueError:
                return 0.0

        p = to_float_or_zero(prelim)
        m = to_float_or_zero(midterm)
        f = to_float_or_zero(final)

        self.cursor.execute(
            "UPDATE grades SET prelim=?, midterm=?, final=? WHERE id=?",
            (p, m, f, grade_id)
        )
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

    def get_available_subjects_with_ids(self, teacher_id):
        self.cursor.execute("""
            SELECT DISTINCT subjects.id, subjects.subject_name
            FROM assignments
            JOIN subjects ON assignments.subject = subjects.subject_name
            WHERE assignments.teacher_id=?
        """, (teacher_id,))
        return self.cursor.fetchall()

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

    def get_students(self, dept_id=None):
        query = """
            SELECT 
                students.id,
                students.firstname,
                COALESCE(students.middlename, ''),
                students.lastname,
                departments.dept_name,
                sections.section_name,
                students.password
            FROM students 
            JOIN sections ON students.section_id = sections.id
            JOIN departments ON sections.dept_id = departments.id
        """
        params = []
        if dept_id:
            query += " WHERE departments.id = ?"
            params.append(dept_id)
        query += " ORDER BY students.lastname, students.firstname"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()


    def update_student(self, sid, firstname, middlename, lastname, section_id):
        self.cursor.execute("""
            UPDATE students 
            SET firstname=?, middlename=?, lastname=?, section_id=? 
            WHERE id=?
        """, (firstname, middlename, lastname, section_id, sid))
        self.conn.commit()

    def delete_student(self, sid):
        self.cursor.execute("SELECT id FROM grades WHERE student_id=?", (sid,))
        if self.cursor.fetchone():
            return "grades"
        self.cursor.execute("DELETE FROM students WHERE id=?", (sid,))
        self.conn.commit()
        return None

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
                (teachers.firstname || ' ' || COALESCE(teachers.middlename,'') || ' ' || teachers.lastname) AS teacher_name, 
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
        self.cursor.execute("SELECT subject, section_id FROM assignments WHERE id=?", (assign_id,))
        row = self.cursor.fetchone()
        if row:
            subject = row[0]
            section_id = row[1]
            self.cursor.execute("SELECT id FROM grades WHERE subject=? AND section_id=?", (subject, section_id))
            if self.cursor.fetchone():
                return "grades"
        self.cursor.execute("DELETE FROM assignments WHERE id=?", (assign_id,))
        self.conn.commit()
        return None

    def get_student_by_id(self, student_id):
        self.cursor.execute("SELECT id, firstname, middlename, lastname, section_id, password FROM students WHERE id=?", (student_id,))
        return self.cursor.fetchone()

    def get_grades_by_student(self, student_id, academic_year=None, semester=None):
        query = """
            SELECT 
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
            WHERE grades.student_id=?
        """
        params = [student_id]
        if academic_year:
            query += " AND grades.academic_year=?"
            params.append(academic_year)
        if semester:
            query += " AND grades.semester=?"
            params.append(semester)
        query += " ORDER BY grades.academic_year DESC, grades.semester, grades.subject"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_subjects(self, dept_id=None, school_year=None, semester=None):
        query = """
            SELECT subjects.id, subjects.subject_code, subjects.subject_name, 
                   subjects.school_year, subjects.semester, subjects.units
            FROM subjects
        """
        params = []
        if school_year:
            query += " WHERE subjects.school_year = ?"
            params.append(school_year)
        if semester:
            if school_year:
                query += " AND subjects.semester = ?"
            else:
                query += " WHERE subjects.semester = ?"
            params.append(semester)
        query += " ORDER BY subjects.subject_code"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def add_subject(self, subject_code, subject_name, school_year, semester, units):
        try:
            self.cursor.execute(
                "INSERT INTO subjects (subject_code, subject_name, school_year, semester, units) VALUES (?, ?, ?, ?, ?)",
                (subject_code, subject_name, school_year, semester, units)
            )
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def update_subject(self, subj_id, subject_code, subject_name, school_year, semester, units):
        self.cursor.execute(
            "UPDATE subjects SET subject_code=?, subject_name=?, school_year=?, semester=?, units=? WHERE id=?",
            (subject_code, subject_name, school_year, semester, units, subj_id)
        )
        self.conn.commit()

    def delete_subject(self, subj_id):
        self.cursor.execute("SELECT subject_name FROM subjects WHERE id=?", (subj_id,))
        row = self.cursor.fetchone()
        if row:
            subject_name = row[0]
            self.cursor.execute("SELECT id FROM grades WHERE subject=?", (subject_name,))
            if self.cursor.fetchone():
                return "grades"
            self.cursor.execute("SELECT id FROM assignments WHERE subject=?", (subject_name,))
            if self.cursor.fetchone():
                return "assignments"
        self.cursor.execute("DELETE FROM subjects WHERE id=?", (subj_id,))
        self.conn.commit()
        return None

    def get_subject_by_name(self, subject_name):
        self.cursor.execute("SELECT id FROM subjects WHERE subject_name=?", (subject_name,))
        return self.cursor.fetchone()

    def get_deadlines(self):
        self.cursor.execute("""
            SELECT gd.id, gd.school_year, gd.semester, gd.grading_period, gd.start_date, gd.end_date, gd.status
            FROM grade_encoding_deadlines gd
            ORDER BY gd.school_year DESC, gd.semester
        """)
        return self.cursor.fetchall()

    def add_deadline(self, school_year, semester, grading_period, start_date, end_date):
        self.cursor.execute(
            "SELECT id FROM grade_encoding_deadlines WHERE school_year=? AND semester=? AND grading_period=? AND status='Open'",
            (school_year, semester, grading_period)
        )
        if self.cursor.fetchone():
            return False
        self.cursor.execute(
            "INSERT INTO grade_encoding_deadlines (school_year, semester, grading_period, start_date, end_date, status) VALUES (?, ?, ?, ?, ?, 'Open')",
            (school_year, semester, grading_period, start_date, end_date)
        )
        self.conn.commit()
        return True

    def update_deadline_status(self, deadline_id, status):
        self.cursor.execute("UPDATE grade_encoding_deadlines SET status=? WHERE id=?", (status, deadline_id))
        self.conn.commit()

    def delete_deadline(self, deadline_id):
        self.cursor.execute("DELETE FROM grade_encoding_deadlines WHERE id=?", (deadline_id,))
        self.conn.commit()

    def is_period_locked(self, subject, section_id, school_year, semester, grading_period):
        self.cursor.execute(
            "SELECT locked FROM grade_locks WHERE subject=? AND section_id=? AND school_year=? AND semester=? AND grading_period=?",
            (subject, section_id, school_year, semester, grading_period)
        )
        row = self.cursor.fetchone()
        return bool(row[0]) if row else False

    def set_open_period(self, school_year, semester, grading_period):
        self.cursor.execute("DELETE FROM open_grading_periods WHERE school_year=? AND semester=?", (school_year, semester))
        if grading_period:
            self.cursor.execute(
                "INSERT INTO open_grading_periods (school_year, semester, grading_period) VALUES (?, ?, ?)",
                (school_year, semester, grading_period)
            )
        self.conn.commit()

    def get_open_period(self, school_year, semester):
        self.cursor.execute(
            "SELECT grading_period FROM open_grading_periods WHERE school_year=? AND semester=?",
            (school_year, semester)
        )
        row = self.cursor.fetchone()
        return row[0] if row else None

    def lock_grade_period(self, subject, section_id, school_year, semester, grading_period):
        self.cursor.execute(
            """INSERT INTO grade_locks (subject, section_id, school_year, semester, grading_period, locked, locked_at)
               VALUES (?, ?, ?, ?, ?, 1, ?)
               ON CONFLICT(subject, section_id, school_year, semester, grading_period)
               DO UPDATE SET locked=1, locked_at=excluded.locked_at""",
            (subject, section_id, school_year, semester, grading_period, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.conn.commit()

    def unlock_grade_periods(self, subject, section_id, school_year, semester, grading_periods):
        for period in grading_periods:
            self.cursor.execute(
                """INSERT INTO grade_locks (subject, section_id, school_year, semester, grading_period, locked, locked_at)
                   VALUES (?, ?, ?, ?, ?, 0, ?)
                   ON CONFLICT(subject, section_id, school_year, semester, grading_period)
                   DO UPDATE SET locked=0, locked_at=excluded.locked_at""",
                (subject, section_id, school_year, semester, period, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
        self.conn.commit()

    def get_locked_periods(self, subject, section_id, school_year, semester):
        self.cursor.execute(
            "SELECT grading_period FROM grade_locks WHERE subject=? AND section_id=? AND school_year=? AND semester=? AND locked=1",
            (subject, section_id, school_year, semester)
        )
        return [row[0] for row in self.cursor.fetchall()]

    def add_grade_with_period(self, teacher_id, section_id, student_id, subject, academic_year, semester, prelim, midterm, final):
        def to_float_or_zero(v):
            if v is None:
                return 0.0
            s = str(v).strip()
            if s == "":
                return 0.0
            try:
                return float(s)
            except ValueError:
                return 0.0

        p = to_float_or_zero(prelim)
        m = to_float_or_zero(midterm)
        f = to_float_or_zero(final)

        self.cursor.execute("""
            INSERT INTO grades (teacher_id, section_id, student_id, subject, academic_year, semester, prelim, midterm, final)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (teacher_id, section_id, student_id, subject, academic_year, semester, p, m, f))
        self.conn.commit()

    def grade_row_exists(self, teacher_id, section_id, student_id, subject, academic_year, semester):
        self.cursor.execute(
            "SELECT id FROM grades WHERE teacher_id=? AND section_id=? AND student_id=? AND subject=? AND academic_year=? AND semester=?",
            (teacher_id, section_id, student_id, subject, academic_year, semester)
        )
        return self.cursor.fetchone() is not None

    def is_within_deadline(self, school_year, semester, grading_period):
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        if grading_period == "All":
            self.cursor.execute(
                "SELECT start_date, end_date, status FROM grade_encoding_deadlines WHERE school_year=? AND semester=? AND status='Open'",
                (school_year, semester)
            )
        else:
            self.cursor.execute(
                "SELECT start_date, end_date, status FROM grade_encoding_deadlines WHERE school_year=? AND semester=? AND grading_period=? AND status='Open'",
                (school_year, semester, grading_period)
            )
        deadlines = self.cursor.fetchall()
        for deadline in deadlines:
            if deadline[2] == 'Open' and deadline[0] <= today <= deadline[1]:
                return True
        return False

    def add_extension_request(self, teacher_id, teacher_name, subject, section_id, section_name, school_year, semester, grading_period, reason):
        self.cursor.execute(
            "SELECT id FROM extension_requests WHERE teacher_id=? AND subject=? AND section_id=? AND school_year=? AND semester=? AND status='Pending'",
            (teacher_id, subject, section_id, school_year, semester)
        )
        if self.cursor.fetchone():
            return False
        self.cursor.execute(
            "INSERT INTO extension_requests (teacher_id, teacher_name, subject, section_id, section_name, school_year, semester, grading_period, reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (teacher_id, teacher_name, subject, section_id, section_name, school_year, semester, grading_period, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.conn.commit()
        return True

    def add_reopen_request(self, teacher_id, teacher_name, subject, section_id, section_name, dept_id, school_year, semester, grading_periods, reason):
        grading_period_str = ", ".join(grading_periods)
        self.cursor.execute(
            "SELECT id FROM extension_requests WHERE teacher_id=? AND subject=? AND section_id=? AND school_year=? AND semester=? AND status='Pending'",
            (teacher_id, subject, section_id, school_year, semester)
        )
        if self.cursor.fetchone():
            return False
        self.cursor.execute(
            "INSERT INTO extension_requests (teacher_id, teacher_name, subject, section_id, section_name, dept_id, school_year, semester, grading_period, reason, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (teacher_id, teacher_name, subject, section_id, section_name, dept_id, school_year, semester, grading_period_str, reason, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.conn.commit()
        return True

    def get_extension_requests(self, dept_id=None, teacher_id=None):
        query = """
            SELECT er.id, er.teacher_id, er.teacher_name, er.subject, er.section_id, er.section_name,
                   d.dept_name, er.school_year, er.semester, er.grading_period, er.reason, er.status, er.admin_remarks, er.created_at
            FROM extension_requests er
            LEFT JOIN teachers t ON er.teacher_id = t.id
            LEFT JOIN departments d ON t.dept_id = d.id
        """
        params = []
        if dept_id:
            query += " WHERE d.id = ?"
            params.append(dept_id)
        if teacher_id:
            query += " WHERE er.teacher_id = ?" if not dept_id else " AND er.teacher_id = ?"
            params.append(teacher_id)
        query += " ORDER BY er.id DESC"
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def get_request_by_id(self, request_id):
        self.cursor.execute(
            "SELECT id, teacher_id, teacher_name, subject, section_id, section_name, school_year, semester, grading_period, reason, status, admin_remarks FROM extension_requests WHERE id=?",
            (request_id,)
        )
        return self.cursor.fetchone()

    def update_request_status(self, request_id, status, admin_remarks):
        self.cursor.execute(
            "UPDATE extension_requests SET status=?, admin_remarks=? WHERE id=?",
            (status, admin_remarks, request_id)
        )
        self.conn.commit()

    def approve_extension_request(self, request_id, start_date, end_date):
        self.cursor.execute("UPDATE extension_requests SET status='Approved', start_date=?, end_date=? WHERE id=?", (start_date, end_date, request_id))
        self.conn.commit()

    def reject_extension_request(self, request_id):
        self.cursor.execute("UPDATE extension_requests SET status='Rejected' WHERE id=?", (request_id,))
        self.conn.commit()

    def add_notification(self, user_id, user_role, title, message):
        from datetime import datetime
        self.cursor.execute(
            "INSERT INTO notifications (user_id, user_role, title, message, created_at) VALUES (?, ?, ?, ?, ?)",
            (user_id, user_role, title, message, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.conn.commit()

    def add_audit_log(self, user_id, user_name, role, department, action, description):
        from datetime import datetime
        self.cursor.execute(
            "INSERT INTO audit_logs (user_id, user_name, role, department, action, description, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, user_name, role, department, action, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        self.conn.commit()

    