from flask import Flask, render_template, request, redirect, url_for, flash, session
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-this'

# Khởi tạo database
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Bảng users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            email TEXT NOT NULL
        )
    ''')
    
    # Bảng products (để demo CRUD)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            user_id INTEGER,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    conn.commit()
    conn.close()

# Route trang chủ
@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

# Route đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        
        # LỖ HỔNG 1: SQL INJECTION
        # Sử dụng string formatting thay vì parameterized query
        query = f"SELECT * FROM users WHERE username = '{username}' AND password = '{password}'"
        print(f"Executing query: {query}")  # Debug - không nên làm trong production
        cursor.execute(query)
        user = cursor.fetchone()
        conn.close()
        
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Đăng nhập thành công!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Tên đăng nhập hoặc mật khẩu không đúng!', 'danger')
    
    return render_template('login.html')

# Route đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        # LỖ HỔNG 2: WEAK PASSWORD POLICY & PLAIN TEXT STORAGE
        # Không kiểm tra độ mạnh mật khẩu và lưu plain text
        if len(password) < 3:  # Yêu cầu mật khẩu quá yếu
            flash('Mật khẩu phải có ít nhất 3 ký tự!', 'danger')
            return render_template('register.html')
        
        # Lưu mật khẩu dưới dạng plain text thay vì hash
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute('INSERT INTO users (username, password, email) VALUES (?, ?, ?)',
                         (username, password, email))  # Plain text password!
            conn.commit()
            conn.close()
            flash('Đăng ký thành công! Hãy đăng nhập.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Tên đăng nhập đã tồn tại!', 'danger')
    
    return render_template('register.html')

# Route dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    # LỖ HỔNG 3: INSECURE DIRECT OBJECT REFERENCE (IDOR)
    # Không kiểm tra quyền sở hữu, cho phép xem sản phẩm của user khác
    user_filter = request.args.get('user_id', session['user_id'])
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM products WHERE user_id = ?', (user_filter,))
    products = cursor.fetchall()
    
    # Lấy thông tin user để hiển thị
    cursor.execute('SELECT username FROM users WHERE id = ?', (user_filter,))
    viewed_user = cursor.fetchone()
    conn.close()
    
    return render_template('dashboard.html', products=products, 
                         viewed_user=viewed_user[0] if viewed_user else 'Unknown')

# Route thêm sản phẩm
@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('INSERT INTO products (name, price, description, user_id) VALUES (?, ?, ?, ?)',
                     (name, price, description, session['user_id']))
        conn.commit()
        conn.close()
        
        flash('Thêm sản phẩm thành công!', 'success')
        return redirect(url_for('dashboard'))
    
    return render_template('add_product.html')

# Route sửa sản phẩm - cũng có lỗ hổng IDOR
@app.route('/edit_product/<int:product_id>', methods=['GET', 'POST'])
def edit_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']
        
        # Không kiểm tra user_id - có thể sửa sản phẩm của người khác!
        cursor.execute('UPDATE products SET name=?, price=?, description=? WHERE id=?',
                     (name, price, description, product_id))
        conn.commit()
        conn.close()
        
        flash('Cập nhật sản phẩm thành công!', 'success')
        return redirect(url_for('dashboard'))
    
    # Không kiểm tra quyền sở hữu khi lấy dữ liệu
    cursor.execute('SELECT * FROM products WHERE id=?', (product_id,))
    product = cursor.fetchone()
    conn.close()
    
    if not product:
        flash('Không tìm thấy sản phẩm!', 'danger')
        return redirect(url_for('dashboard'))
    
    return render_template('edit_product.html', product=product)

# Route xóa sản phẩm - cũng có lỗ hổng IDOR
@app.route('/delete_product/<int:product_id>')
def delete_product(product_id):
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    # Không kiểm tra user_id - có thể xóa sản phẩm của người khác!
    cursor.execute('DELETE FROM products WHERE id=?', (product_id,))
    conn.commit()
    conn.close()
    
    flash('Xóa sản phẩm thành công!', 'success')
    return redirect(url_for('dashboard'))

# Route đăng xuất
@app.route('/logout')
def logout():
    session.clear()
    flash('Đã đăng xuất thành công!', 'success')
    return redirect(url_for('login'))

# Route để xem database (chỉ để test lỗ hổng)
@app.route('/debug/users')
def debug_users():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, username, password, email FROM users')
    users = cursor.fetchall()
    conn.close()
    
    html = "<h2>Debug: All Users</h2><table border='1'><tr><th>ID</th><th>Username</th><th>Password</th><th>Email</th></tr>"
    for user in users:
        html += f"<tr><td>{user[0]}</td><td>{user[1]}</td><td>{user[2]}</td><td>{user[3]}</td></tr>"
    html += "</table><br><a href='/dashboard'>Back to Dashboard</a>"
    return html

if __name__ == '__main__':
    init_db()
    app.run(debug=True)
