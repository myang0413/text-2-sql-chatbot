-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create sample Spider dataset tables
CREATE TABLE IF NOT EXISTS departments (
    department_id SERIAL PRIMARY KEY,
    department_name VARCHAR(100) NOT NULL,
    budget DECIMAL(12,2),
    head_id INTEGER
);

CREATE TABLE IF NOT EXISTS employees (
    employee_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    department_id INTEGER REFERENCES departments(department_id),
    salary DECIMAL(10,2),
    hire_date DATE,
    position VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS projects (
    project_id SERIAL PRIMARY KEY,
    project_name VARCHAR(200) NOT NULL,
    department_id INTEGER REFERENCES departments(department_id),
    start_date DATE,
    end_date DATE,
    budget DECIMAL(12,2)
);

CREATE TABLE IF NOT EXISTS student (
    student_id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    age INTEGER,
    major VARCHAR(50),
    gpa DECIMAL(3,2)
);

CREATE TABLE IF NOT EXISTS course (
    course_id SERIAL PRIMARY KEY,
    course_name VARCHAR(100) NOT NULL,
    credits INTEGER,
    department VARCHAR(50)
);

CREATE TABLE IF NOT EXISTS enrollment (
    enrollment_id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES student(student_id),
    course_id INTEGER REFERENCES course(course_id),
    grade VARCHAR(2),
    semester VARCHAR(20)
);

-- Insert sample data
INSERT INTO departments (department_name, budget, head_id) VALUES
('Computer Science', 500000.00, 1),
('Mathematics', 300000.00, 2),
('Physics', 400000.00, 3),
('Chemistry', 350000.00, 4);

INSERT INTO employees (name, department_id, salary, hire_date, position) VALUES
('John Smith', 1, 75000.00, '2020-01-15', 'Professor'),
('Jane Doe', 1, 65000.00, '2019-08-20', 'Associate Professor'),
('Bob Johnson', 2, 70000.00, '2018-03-10', 'Professor'),
('Alice Brown', 3, 68000.00, '2021-09-01', 'Assistant Professor');

INSERT INTO projects (project_name, department_id, start_date, end_date, budget) VALUES
('AI Research Project', 1, '2023-01-01', '2024-12-31', 100000.00),
('Quantum Computing Study', 3, '2023-06-01', '2025-05-31', 150000.00),
('Data Analysis Framework', 1, '2023-03-15', '2024-03-14', 80000.00);

INSERT INTO student (name, age, major, gpa) VALUES
('Michael Chen', 20, 'Computer Science', 3.8),
('Sarah Wilson', 19, 'Mathematics', 3.9),
('David Lee', 21, 'Physics', 3.6),
('Emma Davis', 20, 'Chemistry', 3.7),
('James Miller', 22, 'Computer Science', 3.5);

INSERT INTO course (course_name, credits, department) VALUES
('Introduction to Programming', 3, 'Computer Science'),
('Data Structures', 4, 'Computer Science'),
('Calculus I', 4, 'Mathematics'),
('Linear Algebra', 3, 'Mathematics'),
('General Physics', 4, 'Physics'),
('Organic Chemistry', 4, 'Chemistry');

INSERT INTO enrollment (student_id, course_id, grade, semester) VALUES
(1, 1, 'A', 'Fall 2023'),
(1, 2, 'B+', 'Spring 2024'),
(2, 3, 'A-', 'Fall 2023'),
(3, 5, 'B', 'Fall 2023'),
(4, 6, 'A', 'Spring 2024'),
(5, 1, 'B-', 'Fall 2023');
