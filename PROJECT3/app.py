from flask import Flask, render_template, redirect, request, flash, url_for
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Task
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from datetime import datetime

app = Flask(__name__)

# Cấu hình cơ sở dữ liệu PostgreSQL
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:1@localhost:5432/dbweb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # tắt tính năng theo dõi các thay đổi trong SQLAlchemy giúp giảm tải hiệu suất không cần thiết
app.secret_key = 'your_secret_key' 

# Khởi tạo các thành phần của ứng dụng
db.init_app(app) # Khởi tạo cơ sở dữ liệu với ứng dụng Flask.
migrate = Migrate(app, db) # Khởi tạo Flask-Migrate để hỗ trợ di chuyển cơ sở dữ liệu.
login_manager = LoginManager(app)  #Khởi tạo trình quản lý đăng nhập.
login_manager.login_view = 'login' #Đặt route mặc định khi người dùng chưa đăng nhập.

@login_manager.user_loader   # Định nghĩa cách Flask-Login tải thông tin người dùng từ ID.
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')  
def home():
    return render_template('login.html')

#Route cho trang đăng nhập
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('task_list'))
        else:
            flash('*Tên đăng nhập hoặc mật khẩu không đúng.')
            return render_template('login.html')

    return render_template('login.html')

# Route cho trang đăng ký
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash('*Mật khẩu và mật khẩu xác nhận không khớp.')
            return render_template('register.html')

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('*Tài khoản đã tồn tại.')
            return render_template('register.html')

        new_user = User(username=username, password=generate_password_hash(password))
        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')

# Route cho danh sách công việc
@app.route('/tasks')
@login_required
def task_list():
    tasks = Task.query.filter_by(user_id=current_user.id).all()
    return render_template('tasks.html', tasks=tasks)

# Route để thêm công việc mới
@app.route('/add_task', methods=['GET', 'POST'])
@login_required
def add_task():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form.get('description')
        due_date = request.form.get('due_date')

        new_task = Task(
            title=title,
            description=description,
            due_date=datetime.strptime(due_date, '%Y-%m-%d') if due_date else None,
            user_id=current_user.id
        )

        db.session.add(new_task)
        db.session.commit()
        return redirect(url_for('task_list'))

    return render_template('add_task.html')

# Route để đánh dấu công việc đã hoàn thành
@app.route('/tasks/complete/<int:task_id>', methods=['POST'])
@login_required
def complete_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == current_user.id:
        task.is_completed = True
        db.session.commit()
        flash('Nhiệm vụ đã được đánh dấu là hoàn thành.', 'success')
    else:
        flash('Bạn không có quyền thực hiện thao tác này.', 'error')
    return redirect(url_for('task_list'))

# Route để xóa công việc
@app.route('/tasks/delete/<int:task_id>', methods=['POST'])
@login_required
def delete_task(task_id):
    task = Task.query.get(task_id)
    if task and task.user_id == current_user.id:
        db.session.delete(task)
        db.session.commit()
        flash('Nhiệm vụ đã được xóa.', 'success')
    else:
        flash('Bạn không có quyền xóa nhiệm vụ này.', 'error')
    return redirect(url_for('task_list'))
from flask_login import login_required, logout_user, current_user

@app.route('/logout')
@login_required  # Đảm bảo rằng chỉ người dùng đã đăng nhập mới có thể logout
def logout():
    logout_user()  # Đăng xuất người dùng hiện tại
    flash('Đăng xuất thành công.', 'success')  # Hiển thị thông báo
    return redirect(url_for('login'))  # Quay lại trang đăng nhập

@app.route('/edit_task/<int:task_id>', methods=['GET', 'POST'])
@login_required
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    
    if task.user_id != current_user.id:
        flash("Bạn không thể sửa nhiệm vụ này.", "danger")
        return redirect(url_for('task_list'))
    
    if request.method == 'POST':
        task.title = request.form['title']
        task.description = request.form['description']
        task.due_date = request.form.get('due_date') if request.form.get('due_date') else None
        task.is_completed = 'is_completed' in request.form
    
        db.session.commit()
        flash("Cập nhật nhiệm vụ thành công.", "success")
        return redirect(url_for('task_list'))
    
    return render_template('edit_task.html', task=task)





if __name__ == '__main__':
    app.run(debug=True)
