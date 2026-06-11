from flask import render_template, url_for, flash, redirect, request, abort

from todo_project import app, db, bcrypt, security_logger

# Import the forms
from todo_project.forms import (LoginForm, RegistrationForm, UpdateUserInfoForm,
                                UpdateUserPassword, TaskForm, UpdateTaskForm)

# Import the Models
from todo_project.models import User, Task

# Import
from flask_login import login_required, current_user, login_user, logout_user


@app.errorhandler(404)
def error_404(error):
    return (render_template('errors/404.html'), 404)


@app.errorhandler(403)
def error_403(error):
    return (render_template('errors/403.html'), 403)


@app.errorhandler(500)
def error_500(error):
    return (render_template('errors/500.html'), 500)


@app.route("/")
@app.route("/about")
def about():
    return render_template('about.html', title='About')


@app.route("/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('all_tasks'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user)
            security_logger.info(
                f"AUTH_SUCCESS username={user.username} ip={request.remote_addr}"
            )
            flash('Login Successfull', 'success')
            return redirect(url_for('all_tasks'))

        security_logger.warning(
            f"AUTH_FAILURE username={form.username.data} ip={request.remote_addr}"
        )
        flash('Login Unsuccessful. Please check Username Or Password', 'danger')

    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    username = current_user.username if current_user.is_authenticated else "anonymous"
    security_logger.info(
        f"AUTH_LOGOUT username={username} ip={request.remote_addr}"
    )
    logout_user()
    return redirect(url_for('login'))


@app.route("/register", methods=['POST', 'GET'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('all_tasks'))

    form = RegistrationForm()

    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()

        security_logger.info(
            f"USER_REGISTERED username={form.username.data} ip={request.remote_addr}"
        )

        flash(f'Account Created For {form.username.data}', 'success')
        return redirect(url_for('login'))

    return render_template('register.html', title='Register', form=form)


@app.route("/all_tasks")
@login_required
def all_tasks():
    tasks = User.query.filter_by(username=current_user.username).first().tasks
    return render_template('all_tasks.html', title='All Tasks', tasks=tasks)


@app.route("/add_task", methods=['POST', 'GET'])
@login_required
def add_task():
    form = TaskForm()

    if form.validate_on_submit():
        task = Task(content=form.task_name.data, author=current_user)
        db.session.add(task)
        db.session.commit()

        security_logger.info(
            f"TASK_CREATED task_id={task.id} username={current_user.username} ip={request.remote_addr}"
        )

        flash('Task Created', 'success')
        return redirect(url_for('add_task'))

    return render_template('add_task.html', form=form, title='Add Task')


@app.route("/all_tasks/<int:task_id>/update_task", methods=['GET', 'POST'])
@login_required
def update_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.author != current_user:
        security_logger.warning(
            f"BROKEN_ACCESS_BLOCKED action=update_task task_id={task_id} username={current_user.username} ip={request.remote_addr}"
        )
        abort(403)

    form = UpdateTaskForm()

    if form.validate_on_submit():
        if form.task_name.data != task.content:
            task.content = form.task_name.data
            db.session.commit()

            security_logger.info(
                f"TASK_UPDATED task_id={task.id} username={current_user.username} ip={request.remote_addr}"
            )

            flash('Task Updated', 'success')
            return redirect(url_for('all_tasks'))

        flash('No Changes Made', 'warning')
        return redirect(url_for('all_tasks'))

    elif request.method == 'GET':
        form.task_name.data = task.content

    return render_template('add_task.html', title='Update Task', form=form)


@app.route("/all_tasks/<int:task_id>/delete_task")
@login_required
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)

    if task.author != current_user:
        security_logger.warning(
            f"BROKEN_ACCESS_BLOCKED action=delete_task task_id={task_id} username={current_user.username} ip={request.remote_addr}"
        )
        abort(403)

    db.session.delete(task)
    db.session.commit()

    security_logger.info(
        f"TASK_DELETED task_id={task_id} username={current_user.username} ip={request.remote_addr}"
    )

    flash('Task Deleted', 'info')
    return redirect(url_for('all_tasks'))


@app.route("/account", methods=['POST', 'GET'])
@login_required
def account():
    form = UpdateUserInfoForm()

    if form.validate_on_submit():
        if form.username.data != current_user.username:
            old_username = current_user.username
            current_user.username = form.username.data
            db.session.commit()

            security_logger.info(
                f"ACCOUNT_USERNAME_UPDATED old_username={old_username} new_username={current_user.username} ip={request.remote_addr}"
            )

            flash('Username Updated Successfully', 'success')
            return redirect(url_for('account'))

    elif request.method == 'GET':
        form.username.data = current_user.username

    return render_template('account.html', title='Account Settings', form=form)


@app.route("/account/change_password", methods=['POST', 'GET'])
@login_required
def change_password():
    form = UpdateUserPassword()

    if form.validate_on_submit():
        if bcrypt.check_password_hash(current_user.password, form.old_password.data):
            current_user.password = bcrypt.generate_password_hash(form.new_password.data).decode('utf-8')
            db.session.commit()

            security_logger.info(
                f"PASSWORD_CHANGED username={current_user.username} ip={request.remote_addr}"
            )

            flash('Password Changed Successfully', 'success')
            return redirect(url_for('account'))

        security_logger.warning(
            f"PASSWORD_CHANGE_FAILURE username={current_user.username} ip={request.remote_addr}"
        )
        flash('Please Enter Correct Password', 'danger')

    return render_template('change_password.html', title='Change Password', form=form)
