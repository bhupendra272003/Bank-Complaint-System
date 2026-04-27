from flask import Flask, request, render_template, jsonify, send_file, redirect, url_for, flash
from flask_login import login_required, current_user
import pickle
import pandas as pd
import hashlib
from datetime import datetime
import os
import database as db
from auth import auth_bp, login_manager
from notification import notify_admin_and_customer

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "your-secret-key-here-change-it-2026")

login_manager.init_app(app)
app.register_blueprint(auth_bp, url_prefix='/auth')

# Load model
model = pickle.load(open("model.pkl", "rb"))
vectorizer = pickle.load(open("vectorizer.pkl", "rb"))

priority_map = {
    "fraud": ("🔴 HIGH", "priority-high"),
    "transfer": ("🟡 MEDIUM", "priority-medium"),
    "atm": ("🟡 MEDIUM", "priority-medium"),
    "billing": ("🟢 LOW", "priority-low"),
    "loan": ("🟢 LOW", "priority-low")
}

def generate_complaint_id(customer_name, mobile):
    unique_string = f"{customer_name}{mobile}{datetime.now().timestamp()}"
    return hashlib.md5(unique_string.encode()).hexdigest()[:8].upper()

# ========== CUSTOMER PAGES (No Login Required) ==========

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit_complaint", methods=["POST"])
def submit_complaint():
    try:
        customer_name = request.form.get("customer_name", "").strip()
        mobile = request.form.get("mobile", "").strip()
        id_number = request.form.get("id_number", "").strip()
        email = request.form.get("email", "").strip()
        complaint_text = request.form.get("complaint", "").strip()
        
        if not all([customer_name, mobile, id_number, complaint_text]):
            return jsonify({"error": "Please fill all required fields"}), 400
        
        if len(mobile) != 10 or not mobile.isdigit():
            return jsonify({"error": "Mobile number must be 10 digits"}), 400
        
        complaint_vec = vectorizer.transform([complaint_text])
        cat = model.predict(complaint_vec)[0]
        priority, priority_class = priority_map.get(cat, ("🟡 MEDIUM", "priority-medium"))
        
        complaint_id = generate_complaint_id(customer_name, mobile)
        
        complaint_data = {
            "complaint_id": complaint_id,
            "customer_name": customer_name,
            "mobile": mobile,
            "id_number": id_number,
            "email": email,
            "complaint_text": complaint_text,
            "category": cat.upper(),
            "priority": priority,
            "priority_class": priority_class,
            "status": "Registered",
            "created_by": None,
            "assigned_to": None
        }
        
        db.save_complaint(complaint_data)
        
        # Send notifications
        notify_admin_and_customer(complaint_id, customer_name, email, mobile, complaint_text, cat.upper(), priority)
        
        return jsonify({
            "success": True,
            "complaint_id": complaint_id,
            "category": cat.upper(),
            "priority": priority,
            "priority_class": priority_class,
            "customer_name": customer_name,
            "mobile": mobile,
            "id_number": id_number
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/track", methods=["GET", "POST"])
def track_complaint():
    complaint = None
    error = None
    
    if request.method == "POST":
        complaint_id = request.form.get("complaint_id", "").strip()
        if complaint_id:
            complaint = db.get_complaint_by_id(complaint_id)
            if not complaint:
                error = "Complaint ID not found"
    
    return render_template("track_complaint.html", complaint=complaint, error=error)

# ========== PROFILE PAGE ==========

@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    user = db.get_user_by_id(current_user.id)
    stats = db.get_user_stats(current_user.id)
    
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        department = request.form.get("department")
        
        db.update_own_profile(current_user.id, full_name, email, mobile, department)
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('profile'))
    
    return render_template("profile.html", user=user, stats=stats, current_user=current_user)

# ========== PASSWORD CHANGE ==========

@app.route("/change_password", methods=["GET", "POST"])
@login_required
def change_password():
    if request.method == "POST":
        current_password = request.form.get("current_password")
        new_password = request.form.get("new_password")
        
        user = db.get_user_by_id(current_user.id)
        
        if db.bcrypt.check_password_hash(user['password'], current_password):
            db.update_user_password(current_user.id, new_password)
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Current password is incorrect"}), 400
    
    return render_template("change_password.html", user=current_user)

# ========== CLERK PAGES ==========

@app.route("/clerk")
@login_required
def clerk_dashboard():
    if current_user.role not in ['admin', 'clerk']:
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    complaints = db.get_complaints_by_user(current_user.id)
    stats = db.get_statistics()
    
    return render_template("clerk_dashboard.html", 
                         complaints=complaints, 
                         stats=stats,
                         user=current_user)

@app.route("/clerk/submit", methods=["GET", "POST"])
@login_required
def clerk_submit_complaint():
    if current_user.role not in ['admin', 'clerk']:
        if request.method == "POST":
            return jsonify({"error": "Access denied"}), 403
        flash('Access denied', 'error')
        return redirect(url_for('index'))
    
    if request.method == "POST":
        try:
            customer_name = request.form.get("customer_name", "").strip()
            mobile = request.form.get("mobile", "").strip()
            id_number = request.form.get("id_number", "").strip()
            email = request.form.get("email", "").strip()
            complaint_text = request.form.get("complaint", "").strip()
            
            if not all([customer_name, mobile, id_number, complaint_text]):
                return jsonify({"error": "Please fill all required fields"}), 400
            
            if len(mobile) != 10 or not mobile.isdigit():
                return jsonify({"error": "Mobile number must be 10 digits"}), 400
            
            complaint_vec = vectorizer.transform([complaint_text])
            cat = model.predict(complaint_vec)[0]
            priority, priority_class = priority_map.get(cat, ("🟡 MEDIUM", "priority-medium"))
            
            complaint_id = generate_complaint_id(customer_name, mobile)
            
            complaint_data = {
                "complaint_id": complaint_id,
                "customer_name": customer_name,
                "mobile": mobile,
                "id_number": id_number,
                "email": email,
                "complaint_text": complaint_text,
                "category": cat.upper(),
                "priority": priority,
                "priority_class": priority_class,
                "status": "Registered",
                "created_by": current_user.id,
                "assigned_to": current_user.id
            }
            
            db.save_complaint(complaint_data)
            
            # Send notifications
            notify_admin_and_customer(complaint_id, customer_name, email, mobile, complaint_text, cat.upper(), priority)
            
            return jsonify({
                "success": True,
                "complaint_id": complaint_id,
                "category": cat.upper(),
                "priority": priority,
                "priority_class": priority_class
            })
            
        except Exception as e:
            return jsonify({"error": str(e)}), 500
    
    return render_template("clerk_submit.html", user=current_user)

# ========== ADMIN PAGES ==========

@app.route("/admin")
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('index'))
    
    complaints = db.get_all_complaints()
    stats = db.get_statistics()
    users = db.get_all_users()
    
    return render_template("admin_dashboard.html", 
                         complaints=complaints, 
                         stats=stats, 
                         users=users,
                         user=current_user)

@app.route("/admin/add_employee", methods=["POST"])
@login_required
def add_employee():
    if current_user.role != 'admin':
        return jsonify({"error": "Access denied"}), 403
    
    username = request.form.get("username")
    email = request.form.get("email")
    password = request.form.get("password")
    mobile = request.form.get("mobile")
    full_name = request.form.get("full_name")
    department = request.form.get("department")
    role = request.form.get("role")
    
    if db.create_user(username, email, password, mobile, role, full_name, department):
        return jsonify({"success": True})
    else:
        return jsonify({"error": "Username or email already exists"}), 400

@app.route("/admin/edit_employee/<int:user_id>", methods=["GET", "POST"])
@login_required
def edit_employee(user_id):
    if current_user.role != 'admin':
        flash('Access denied. Admin only.', 'error')
        return redirect(url_for('index'))
    
    user = db.get_user_by_id(user_id)
    if not user:
        flash('User not found', 'error')
        return redirect(url_for('admin_dashboard'))
    
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        department = request.form.get("department")
        role = request.form.get("role")
        
        if db.update_user_info(user_id, full_name, email, mobile, department, role):
            flash('Employee information updated successfully!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Failed to update employee information', 'error')
    
    return render_template("edit_employee.html", employee=user, user=current_user)

@app.route("/admin/reset_password/<int:user_id>", methods=["POST"])
@login_required
def reset_user_password(user_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Access denied"}), 403
    
    data = request.get_json()
    new_password = data.get("new_password")
    
    if not new_password or len(new_password) < 6:
        return jsonify({"error": "Password must be at least 6 characters"}), 400
    
    db.reset_user_password(user_id, new_password)
    return jsonify({"success": True})

@app.route("/admin/delete_employee/<int:user_id>", methods=["DELETE"])
@login_required
def delete_employee(user_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Access denied"}), 403
    
    if db.delete_user(user_id):
        return jsonify({"success": True})
    return jsonify({"error": "Cannot delete admin or user not found"}), 404

@app.route("/admin/delete_complaint/<complaint_id>", methods=["DELETE"])
@login_required
def delete_complaint(complaint_id):
    if current_user.role != 'admin':
        return jsonify({"error": "Access denied"}), 403
    
    if db.delete_complaint(complaint_id):
        return jsonify({"success": True})
    return jsonify({"error": "Complaint not found"}), 404

# ========== COMMON APIs ==========

@app.route("/get_complaints")
@login_required
def get_complaints():
    if current_user.role == 'admin':
        complaints = db.get_all_complaints()
    else:
        complaints = db.get_complaints_by_user(current_user.id)
    
    complaints_list = []
    for c in complaints:
        complaints_list.append({
            "id": c["complaint_id"],
            "name": c["customer_name"],
            "mobile": c["mobile"],
            "category": c["category"],
            "priority": c["priority"],
            "status": c["status"],
            "date": c["created_at"]
        })
    
    return jsonify(complaints_list)

@app.route("/get_statistics")
@login_required
def get_statistics():
    stats = db.get_statistics()
    return jsonify({
        "total_complaints": stats['total'],
        "categories": [{"name": s['category'], "count": s['count']} for s in stats['category_stats']],
        "priorities": [{"name": s['priority'], "count": s['count']} for s in stats['priority_stats']],
        "statuses": [{"name": s['status'], "count": s['count']} for s in stats['status_stats']]
    })

@app.route("/update_status", methods=["POST"])
@login_required
def update_status():
    data = request.get_json()
    complaint_id = data.get("complaint_id")
    status = data.get("status")
    
    if db.update_complaint_status(complaint_id, status):
        return jsonify({"success": True})
    return jsonify({"error": "Complaint not found"}), 404

@app.route("/download_report")
@login_required
def download_report():
    if current_user.role == 'admin':
        complaints = db.get_all_complaints()
    else:
        complaints = db.get_complaints_by_user(current_user.id)
    
    if not complaints:
        return "No complaints to report", 404
    
    data = []
    for c in complaints:
        data.append({
            "Complaint ID": c["complaint_id"],
            "Date": c["created_at"],
            "Customer Name": c["customer_name"],
            "Mobile": c["mobile"],
            "ID Proof": c["id_number"],
            "Email": c["email"],
            "Complaint": c["complaint_text"],
            "Category": c["category"],
            "Priority": c["priority"],
            "Status": c["status"]
        })
    
    df = pd.DataFrame(data)
    df.to_excel("bank_complaints_report.xlsx", index=False)
    return send_file("bank_complaints_report.xlsx", as_attachment=True)

# ========== PRODUCTION SERVER ==========
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)