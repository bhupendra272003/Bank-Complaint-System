import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask_bcrypt import Bcrypt
from datetime import datetime

bcrypt = Bcrypt()

# Get database URL from environment (Render automatically provides this)
DATABASE_URL = os.environ.get('DATABASE_URL')

def get_db_connection():
    """Get database connection - works on Render PostgreSQL and local SQLite"""
    if DATABASE_URL:
        # Production: PostgreSQL on Render
        conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    else:
        # Local development: SQLite fallback
        import sqlite3
        conn = sqlite3.connect('complaints.db')
        conn.row_factory = sqlite3.Row
    return conn

def create_tables():
    """Create all tables if they don't exist"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        # PostgreSQL syntax
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id SERIAL PRIMARY KEY,
                complaint_id TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                id_number TEXT NOT NULL,
                email TEXT,
                complaint_text TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                priority_class TEXT,
                status TEXT DEFAULT 'Registered',
                created_by INTEGER,
                assigned_to INTEGER,
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                mobile TEXT,
                full_name TEXT,
                department TEXT,
                role TEXT DEFAULT 'clerk',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_password_change TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id SERIAL PRIMARY KEY,
                complaint_id TEXT,
                notification_type TEXT,
                recipient TEXT,
                status TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset (
                id SERIAL PRIMARY KEY,
                user_id INTEGER,
                token TEXT UNIQUE,
                expires_at TIMESTAMP,
                used INTEGER DEFAULT 0
            )
        ''')
    else:
        # SQLite syntax for local development
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS complaints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id TEXT UNIQUE NOT NULL,
                customer_name TEXT NOT NULL,
                mobile TEXT NOT NULL,
                id_number TEXT NOT NULL,
                email TEXT,
                complaint_text TEXT NOT NULL,
                category TEXT NOT NULL,
                priority TEXT NOT NULL,
                priority_class TEXT,
                status TEXT DEFAULT 'Registered',
                created_by INTEGER,
                assigned_to INTEGER,
                resolution_notes TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT,
                password TEXT NOT NULL,
                mobile TEXT,
                full_name TEXT,
                department TEXT,
                role TEXT DEFAULT 'clerk',
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_password_change TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                complaint_id TEXT,
                notification_type TEXT,
                recipient TEXT,
                status TEXT,
                sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS password_reset (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                token TEXT UNIQUE,
                expires_at TIMESTAMP,
                used INTEGER DEFAULT 0
            )
        ''')
    
    conn.commit()
    
    # Insert default admin (Manager)
    default_password = bcrypt.generate_password_hash("admin123").decode('utf-8')
    
    if DATABASE_URL:
        cursor.execute("SELECT * FROM users WHERE username = 'manager'")
    else:
        cursor.execute("SELECT * FROM users WHERE username = 'manager'")
    
    admin_exists = cursor.fetchone()
    
    if not admin_exists:
        if DATABASE_URL:
            cursor.execute('''
                INSERT INTO users (username, email, password, role, full_name, department)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', ('manager', 'manager@bank.com', default_password, 'admin', 'Admin Manager', 'Management'))
        else:
            cursor.execute('''
                INSERT INTO users (username, email, password, role, full_name, department)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('manager', 'manager@bank.com', default_password, 'admin', 'Admin Manager', 'Management'))
        print("✅ Manager user created (username: manager, password: admin123)")
    
    # Insert demo clerk
    clerk_password = bcrypt.generate_password_hash("clerk123").decode('utf-8')
    
    if DATABASE_URL:
        cursor.execute("SELECT * FROM users WHERE username = 'clerk1'")
    else:
        cursor.execute("SELECT * FROM users WHERE username = 'clerk1'")
    
    clerk_exists = cursor.fetchone()
    
    if not clerk_exists:
        if DATABASE_URL:
            cursor.execute('''
                INSERT INTO users (username, email, password, role, full_name, department)
                VALUES (%s, %s, %s, %s, %s, %s)
            ''', ('clerk1', 'clerk@bank.com', clerk_password, 'clerk', 'John Clerk', 'Customer Service'))
        else:
            cursor.execute('''
                INSERT INTO users (username, email, password, role, full_name, department)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', ('clerk1', 'clerk@bank.com', clerk_password, 'clerk', 'John Clerk', 'Customer Service'))
        print("✅ Clerk user created (username: clerk1, password: clerk123)")
    
    conn.commit()
    conn.close()
    print("✅ Database tables created successfully!")

# ========== USER MANAGEMENT ==========

def get_user_by_username(username):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    else:
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    else:
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    else:
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
    
    user = cursor.fetchone()
    conn.close()
    return user

def create_user(username, email, password, mobile=None, role='clerk', full_name=None, department=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed = bcrypt.generate_password_hash(password).decode('utf-8')
    
    try:
        if DATABASE_URL:
            cursor.execute('''
                INSERT INTO users (username, email, password, mobile, role, full_name, department)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            ''', (username, email, hashed, mobile, role, full_name, department))
        else:
            cursor.execute('''
                INSERT INTO users (username, email, password, mobile, role, full_name, department)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (username, email, hashed, mobile, role, full_name, department))
        conn.commit()
        return True
    except Exception as e:
        print(f"Error creating user: {e}")
        return False
    finally:
        conn.close()

def update_user_info(user_id, full_name, email, mobile, department, role):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            UPDATE users 
            SET full_name = %s, email = %s, mobile = %s, department = %s, role = %s
            WHERE id = %s AND role != 'admin'
        ''', (full_name, email, mobile, department, role, user_id))
    else:
        cursor.execute('''
            UPDATE users 
            SET full_name = ?, email = ?, mobile = ?, department = ?, role = ?
            WHERE id = ? AND role != 'admin'
        ''', (full_name, email, mobile, department, role, user_id))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def update_own_profile(user_id, full_name, email, mobile, department):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            UPDATE users 
            SET full_name = %s, email = %s, mobile = %s, department = %s
            WHERE id = %s
        ''', (full_name, email, mobile, department, user_id))
    else:
        cursor.execute('''
            UPDATE users 
            SET full_name = ?, email = ?, mobile = ?, department = ?
            WHERE id = ?
        ''', (full_name, email, mobile, department, user_id))
    
    conn.commit()
    conn.close()
    return True

def update_user_password(user_id, new_password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed = bcrypt.generate_password_hash(new_password).decode('utf-8')
    
    if DATABASE_URL:
        cursor.execute('''
            UPDATE users 
            SET password = %s, last_password_change = CURRENT_TIMESTAMP
            WHERE id = %s
        ''', (hashed, user_id))
    else:
        cursor.execute('''
            UPDATE users 
            SET password = ?, last_password_change = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (hashed, user_id))
    
    conn.commit()
    conn.close()
    return True

def reset_user_password(user_id, new_password):
    return update_user_password(user_id, new_password)

def get_all_users(limit=100):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            SELECT id, username, email, mobile, full_name, department, role, is_active, created_at 
            FROM users 
            ORDER BY created_at DESC
            LIMIT %s
        ''', (limit,))
    else:
        cursor.execute('''
            SELECT id, username, email, mobile, full_name, department, role, is_active, created_at 
            FROM users 
            ORDER BY created_at DESC
            LIMIT ?
        ''', (limit,))
    
    users = cursor.fetchall()
    conn.close()
    return users

def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('DELETE FROM users WHERE id = %s AND role != "admin"', (user_id,))
    else:
        cursor.execute('DELETE FROM users WHERE id = ? AND role != "admin"', (user_id,))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def get_user_stats(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('SELECT COUNT(*) as count FROM complaints WHERE created_by = %s', (user_id,))
    else:
        cursor.execute('SELECT COUNT(*) as count FROM complaints WHERE created_by = ?', (user_id,))
    
    result = cursor.fetchone()
    total = result['count'] if result else 0
    
    if DATABASE_URL:
        cursor.execute('SELECT COUNT(*) as count FROM complaints WHERE created_by = %s AND status = %s', (user_id, 'Resolved'))
    else:
        cursor.execute('SELECT COUNT(*) as count FROM complaints WHERE created_by = ? AND status = ?', (user_id, 'Resolved'))
    
    result = cursor.fetchone()
    resolved = result['count'] if result else 0
    
    if DATABASE_URL:
        cursor.execute('SELECT COUNT(*) as count FROM complaints WHERE created_by = %s AND status IN (%s, %s)', (user_id, 'Registered', 'In Progress'))
    else:
        cursor.execute('SELECT COUNT(*) as count FROM complaints WHERE created_by = ? AND status IN (?, ?)', (user_id, 'Registered', 'In Progress'))
    
    result = cursor.fetchone()
    pending = result['count'] if result else 0
    
    if DATABASE_URL:
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM complaints 
            WHERE created_by = %s 
            GROUP BY category
        ''', (user_id,))
    else:
        cursor.execute('''
            SELECT category, COUNT(*) as count 
            FROM complaints 
            WHERE created_by = ? 
            GROUP BY category
        ''', (user_id,))
    
    categories = cursor.fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'resolved': resolved,
        'pending': pending,
        'categories': categories
    }

# ========== COMPLAINT MANAGEMENT ==========

def save_complaint(complaint_data):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            INSERT INTO complaints (
                complaint_id, customer_name, mobile, id_number, email,
                complaint_text, category, priority, priority_class, status, created_by, assigned_to
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', (
            complaint_data['complaint_id'],
            complaint_data['customer_name'],
            complaint_data['mobile'],
            complaint_data['id_number'],
            complaint_data['email'],
            complaint_data['complaint_text'],
            complaint_data['category'],
            complaint_data['priority'],
            complaint_data['priority_class'],
            complaint_data['status'],
            complaint_data.get('created_by'),
            complaint_data.get('assigned_to')
        ))
    else:
        cursor.execute('''
            INSERT INTO complaints (
                complaint_id, customer_name, mobile, id_number, email,
                complaint_text, category, priority, priority_class, status, created_by, assigned_to
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            complaint_data['complaint_id'],
            complaint_data['customer_name'],
            complaint_data['mobile'],
            complaint_data['id_number'],
            complaint_data['email'],
            complaint_data['complaint_text'],
            complaint_data['category'],
            complaint_data['priority'],
            complaint_data['priority_class'],
            complaint_data['status'],
            complaint_data.get('created_by'),
            complaint_data.get('assigned_to')
        ))
    
    conn.commit()
    conn.close()
    return True

def get_all_complaints(limit=100):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            SELECT c.*, u.full_name as created_by_name
            FROM complaints c
            LEFT JOIN users u ON c.created_by = u.id
            ORDER BY c.created_at DESC 
            LIMIT %s
        ''', (limit,))
    else:
        cursor.execute('''
            SELECT c.*, u.full_name as created_by_name
            FROM complaints c
            LEFT JOIN users u ON c.created_by = u.id
            ORDER BY c.created_at DESC 
            LIMIT ?
        ''', (limit,))
    
    complaints = cursor.fetchall()
    conn.close()
    return complaints

def get_complaints_by_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            SELECT * FROM complaints 
            WHERE created_by = %s
            ORDER BY created_at DESC
        ''', (user_id,))
    else:
        cursor.execute('''
            SELECT * FROM complaints 
            WHERE created_by = ?
            ORDER BY created_at DESC
        ''', (user_id,))
    
    complaints = cursor.fetchall()
    conn.close()
    return complaints

def get_complaint_by_id(complaint_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            SELECT c.*, u.full_name as created_by_name
            FROM complaints c
            LEFT JOIN users u ON c.created_by = u.id
            WHERE c.complaint_id = %s
        ''', (complaint_id,))
    else:
        cursor.execute('''
            SELECT c.*, u.full_name as created_by_name
            FROM complaints c
            LEFT JOIN users u ON c.created_by = u.id
            WHERE c.complaint_id = ?
        ''', (complaint_id,))
    
    complaint = cursor.fetchone()
    conn.close()
    return complaint

def update_complaint_status(complaint_id, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            UPDATE complaints 
            SET status = %s 
            WHERE complaint_id = %s
        ''', (status, complaint_id))
    else:
        cursor.execute('''
            UPDATE complaints 
            SET status = ? 
            WHERE complaint_id = ?
        ''', (status, complaint_id))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def get_complaints_by_category(category):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            SELECT * FROM complaints 
            WHERE category = %s 
            ORDER BY created_at DESC
        ''', (category,))
    else:
        cursor.execute('''
            SELECT * FROM complaints 
            WHERE category = ? 
            ORDER BY created_at DESC
        ''', (category,))
    
    complaints = cursor.fetchall()
    conn.close()
    return complaints

def delete_complaint(complaint_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('DELETE FROM complaints WHERE complaint_id = %s', (complaint_id,))
    else:
        cursor.execute('DELETE FROM complaints WHERE complaint_id = ?', (complaint_id,))
    
    conn.commit()
    affected = cursor.rowcount
    conn.close()
    return affected > 0

def search_complaints(search_term):
    conn = get_db_connection()
    cursor = conn.cursor()
    search_pattern = f"%{search_term}%"
    
    if DATABASE_URL:
        cursor.execute('''
            SELECT * FROM complaints 
            WHERE customer_name LIKE %s 
               OR mobile LIKE %s 
               OR complaint_id LIKE %s
            ORDER BY created_at DESC
        ''', (search_pattern, search_pattern, search_pattern))
    else:
        cursor.execute('''
            SELECT * FROM complaints 
            WHERE customer_name LIKE ? 
               OR mobile LIKE ? 
               OR complaint_id LIKE ?
            ORDER BY created_at DESC
        ''', (search_pattern, search_pattern, search_pattern))
    
    complaints = cursor.fetchall()
    conn.close()
    return complaints

# ========== NOTIFICATION MANAGEMENT ==========

def save_notification(complaint_id, notification_type, recipient, status):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('''
            INSERT INTO notifications (complaint_id, notification_type, recipient, status)
            VALUES (%s, %s, %s, %s)
        ''', (complaint_id, notification_type, recipient, status))
    else:
        cursor.execute('''
            INSERT INTO notifications (complaint_id, notification_type, recipient, status)
            VALUES (?, ?, ?, ?)
        ''', (complaint_id, notification_type, recipient, status))
    
    conn.commit()
    conn.close()

# ========== STATISTICS ==========

def get_statistics():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if DATABASE_URL:
        cursor.execute('SELECT COUNT(*) as count FROM complaints')
    else:
        cursor.execute('SELECT COUNT(*) as count FROM complaints')
    
    result = cursor.fetchone()
    total = result['count'] if result else 0
    
    if DATABASE_URL:
        cursor.execute('SELECT category, COUNT(*) as count FROM complaints GROUP BY category')
    else:
        cursor.execute('SELECT category, COUNT(*) as count FROM complaints GROUP BY category')
    
    category_stats = cursor.fetchall()
    
    if DATABASE_URL:
        cursor.execute('SELECT priority, COUNT(*) as count FROM complaints GROUP BY priority')
    else:
        cursor.execute('SELECT priority, COUNT(*) as count FROM complaints GROUP BY priority')
    
    priority_stats = cursor.fetchall()
    
    if DATABASE_URL:
        cursor.execute('SELECT status, COUNT(*) as count FROM complaints GROUP BY status')
    else:
        cursor.execute('SELECT status, COUNT(*) as count FROM complaints GROUP BY status')
    
    status_stats = cursor.fetchall()
    
    if DATABASE_URL:
        cursor.execute('SELECT COUNT(*) as count FROM users')
    else:
        cursor.execute('SELECT COUNT(*) as count FROM users')
    
    result = cursor.fetchone()
    total_users = result['count'] if result else 0
    
    if DATABASE_URL:
        cursor.execute('SELECT role, COUNT(*) as count FROM users GROUP BY role')
    else:
        cursor.execute('SELECT role, COUNT(*) as count FROM users GROUP BY role')
    
    role_stats = cursor.fetchall()
    
    conn.close()
    
    return {
        'total': total,
        'category_stats': category_stats,
        'priority_stats': priority_stats,
        'status_stats': status_stats,
        'total_users': total_users,
        'role_stats': role_stats
    }

# Create tables when module loads
create_tables()