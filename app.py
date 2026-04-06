from flask import Flask, render_template, redirect, url_for, flash, request, session, jsonify, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
from functools import wraps
from datetime import datetime, timedelta
import os
import csv
import io
import json, os

from models import (
    get_user_by_id, get_user_by_email, get_user_by_username,
    get_all_users, create_user, update_user, toggle_user_active,
    get_all_events, get_event_by_id, create_event, update_event,
    delete_event, get_upcoming_events, get_events_for_week,
    get_all_resources, get_all_resources_with_allocation, get_resource_by_id, get_deleted_resources,
    create_resource, update_resource, delete_resource,
    restore_resource, toggle_resource_active,
    get_all_allocations, get_allocations_by_event,
    create_allocation, delete_allocation, allocation_exists,
    update_profile, update_password,
    get_utilisation_report, get_dashboard_stats, log_action,
    get_audit_logs
)
from conflict import validate_allocation

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'fallback-secret-key')


# ─────────────────────────────────────────
# AUTH HELPERS
# ─────────────────────────────────────────

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def organizer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') not in ('admin', 'organizer'):
            flash('Organizer or Admin role required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            flash('Please log in to continue.', 'warning')
            return redirect(url_for('login'))
        if session.get('role') != 'admin':
            flash('Admin role required.', 'danger')
            return redirect(url_for('dashboard'))
        return f(*args, **kwargs)
    return decorated


def current_user():
    if 'user_id' in session:
        return get_user_by_id(session['user_id'])
    return None


app.jinja_env.globals['current_user'] = current_user


# ─────────────────────────────────────────
# AUTH ROUTES
# ─────────────────────────────────────────

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        user = get_user_by_email(email)
        if user and check_password_hash(user['password_hash'], password):
            if not user['is_active']:
                flash('Your account has been deactivated.', 'danger')
                return redirect(url_for('login'))
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['role']     = user['role']
            flash(f'Welcome back, {user["username"]}!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm', '')

        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters.')
        if not email:
            errors.append('Email is required.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if get_user_by_email(email):
            errors.append('Email already registered.')
        if get_user_by_username(username):
            errors.append('Username already taken.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('register.html')

        create_user(username, email, generate_password_hash(password))
        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')


# ─────────────────────────────────────────
# DASHBOARD
# ─────────────────────────────────────────

@app.route('/dashboard')
@login_required
def dashboard():
    stats          = get_dashboard_stats()
    upcoming       = get_upcoming_events(limit=5)
    return render_template('index.html', stats=stats, upcoming=upcoming)


# ─────────────────────────────────────────
# USER MANAGEMENT ROUTES (Admin only)
# ─────────────────────────────────────────

@app.route('/users')
@admin_required
def users():
    all_users = get_all_users()
    return render_template('users.html', users=all_users)


@app.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_user(user_id):
    user = get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('users'))
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email    = request.form.get('email', '').strip()
        role     = request.form.get('role', 'viewer')
        update_user(user_id, username, email, role)
        log_action(session['user_id'], 'update', 'user', user_id,
                   f'Updated user {username} role to {role}')
        flash('User updated successfully.', 'success')
        return redirect(url_for('users'))
    return render_template('users.html',
                           users=get_all_users(),
                           edit_user=user)


@app.route('/users/<int:user_id>/toggle', methods=['POST'])
@admin_required
def toggle_user(user_id):
    if user_id == session['user_id']:
        flash('You cannot deactivate yourself.', 'warning')
        return redirect(url_for('users'))
    toggle_user_active(user_id)
    log_action(session['user_id'], 'toggle', 'user', user_id, 'Toggled user active status')
    flash('User status updated.', 'success')
    return redirect(url_for('users'))


# ─────────────────────────────────────────
# EVENT ROUTES
# ─────────────────────────────────────────

@app.route('/events')
@login_required
def events():
    search = request.args.get('q', '').strip()
    all_events = get_all_events(search=search if search else None)
    return render_template('events.html', events=all_events, search=search)


@app.route('/events/<int:event_id>')
@login_required
def event_detail(event_id):
    event = get_event_by_id(event_id)
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('events'))
    allocations = get_allocations_by_event(event_id)
    resources   = get_all_resources()
    return render_template('event_detail.html',
                           event=event,
                           allocations=allocations,
                           resources=resources)


@app.route('/events/create', methods=['GET', 'POST'])
@organizer_required
def create_event_route():
    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        start_time  = request.form.get('start_time', '')
        end_time    = request.form.get('end_time', '')
        timezone    = request.form.get('timezone', 'UTC')

        errors = []
        if not title:
            errors.append('Title is required.')
        if not start_time or not end_time:
            errors.append('Start and end times are required.')
        else:
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
                end_dt   = datetime.strptime(end_time,   '%Y-%m-%dT%H:%M')
                if end_dt <= start_dt:
                    errors.append('End time must be after start time.')
            except ValueError:
                errors.append('Invalid date format.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            # Pass submitted values back so fields are not wiped
            form_data = {
                'title':       title,
                'description': description,
                'start_time':  start_time,
                'end_time':    end_time,
                'timezone':    timezone,
            }
            return render_template('event_form.html', action='Create', form_data=form_data)

        event_id = create_event(
            title, description, start_time, end_time,
            timezone, session['user_id']
        )
        log_action(session['user_id'], 'create', 'event', event_id,
                   f'Created event: {title}')
        flash('Event created successfully.', 'success')
        return redirect(url_for('event_detail', event_id=event_id))

    return render_template('event_form.html', action='Create')


@app.route('/events/<int:event_id>/edit', methods=['GET', 'POST'])
@organizer_required
def edit_event(event_id):
    event = get_event_by_id(event_id)
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('events'))

    if request.method == 'POST':
        title       = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        start_time  = request.form.get('start_time', '')
        end_time    = request.form.get('end_time', '')
        timezone    = request.form.get('timezone', 'UTC')

        errors = []
        if not title:
            errors.append('Title is required.')
        if not start_time or not end_time:
            errors.append('Start and end times are required.')
        else:
            try:
                start_dt = datetime.strptime(start_time, '%Y-%m-%dT%H:%M')
                end_dt   = datetime.strptime(end_time,   '%Y-%m-%dT%H:%M')
                if end_dt <= start_dt:
                    errors.append('End time must be after start time.')
            except ValueError:
                errors.append('Invalid date format.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            form_data = {
                'title':       title,
                'description': description,
                'start_time':  start_time,
                'end_time':    end_time,
                'timezone':    timezone,
            }
            return render_template('event_form.html', action='Edit', event=event, form_data=form_data)

        update_event(event_id, title, description, start_time, end_time, timezone)
        log_action(session['user_id'], 'update', 'event', event_id,
                   f'Updated event: {title}')
        flash('Event updated successfully.', 'success')
        return redirect(url_for('event_detail', event_id=event_id))

    return render_template('event_form.html', action='Edit', event=event)


@app.route('/events/<int:event_id>/delete', methods=['POST'])
@admin_required
def delete_event_route(event_id):
    event = get_event_by_id(event_id)
    if not event:
        flash('Event not found.', 'danger')
        return redirect(url_for('events'))
    delete_event(event_id)
    log_action(session['user_id'], 'delete', 'event', event_id,
               f'Deleted event: {event["title"]}')
    flash('Event deleted successfully.', 'success')
    return redirect(url_for('events'))


# ─────────────────────────────────────────
# RESOURCE ROUTES
# ─────────────────────────────────────────

@app.route('/resources')
@login_required
def resources():
    rtype      = request.args.get('type', '').strip()
    all_resources = get_all_resources_with_allocation(rtype=rtype if rtype else None)
    return render_template('resources.html',
                           resources=all_resources,
                           rtype=rtype)


@app.route('/resources/deleted')
@admin_required
def deleted_resources():
    resources = get_deleted_resources()
    return render_template('deleted_resources.html', resources=resources)


@app.route('/resources/create', methods=['GET', 'POST'])
@organizer_required
def create_resource_route():
    if request.method == 'POST':
        name          = request.form.get('name', '').strip()
        resource_type = request.form.get('resource_type', '')
        capacity      = request.form.get('capacity', 1)
        description   = request.form.get('description', '').strip()
        location      = request.form.get('location', '').strip()

        errors = []
        if not name:
            errors.append('Name is required.')
        if resource_type not in ('room', 'instructor', 'equipment'):
            errors.append('Invalid resource type.')
        try:
            capacity = int(capacity)
            if capacity < 1:
                errors.append('Capacity must be at least 1.')
        except ValueError:
            errors.append('Capacity must be a number.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('resources_form.html', action='Create')

        resource_id = create_resource(
            name, resource_type, capacity, description, location
        )
        log_action(session['user_id'], 'create', 'resource', resource_id,
                   f'Created resource: {name}')
        flash('Resource created successfully.', 'success')
        return redirect(url_for('resources'))

    return render_template('resources_form.html', action='Create')


@app.route('/resources/<int:resource_id>/edit', methods=['GET', 'POST'])
@organizer_required
def edit_resource(resource_id):
    resource = get_resource_by_id(resource_id)
    if not resource:
        flash('Resource not found.', 'danger')
        return redirect(url_for('resources'))

    if request.method == 'POST':
        name          = request.form.get('name', '').strip()
        resource_type = request.form.get('resource_type', '')
        capacity      = request.form.get('capacity', 1)
        description   = request.form.get('description', '').strip()
        location      = request.form.get('location', '').strip()

        errors = []
        if not name:
            errors.append('Name is required.')
        if resource_type not in ('room', 'instructor', 'equipment'):
            errors.append('Invalid resource type.')
        try:
            capacity = int(capacity)
            if capacity < 1:
                errors.append('Capacity must be at least 1.')
        except ValueError:
            errors.append('Capacity must be a number.')

        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('resources_form.html',
                                   action='Edit', resource=resource)

        update_resource(resource_id, name, resource_type,
                        capacity, description, location)
        log_action(session['user_id'], 'update', 'resource', resource_id,
                   f'Updated resource: {name}')
        flash('Resource updated successfully.', 'success')
        return redirect(url_for('resources'))

    return render_template('resources_form.html', action='Edit', resource=resource)


@app.route('/resources/<int:resource_id>/delete', methods=['POST'])
@admin_required
def delete_resource_route(resource_id):
    resource = get_resource_by_id(resource_id)
    if not resource:
        flash('Resource not found.', 'danger')
        return redirect(url_for('resources'))
    delete_resource(resource_id)
    log_action(session['user_id'], 'delete', 'resource', resource_id,
               f'Deleted resource: {resource["name"]}')
    flash('Resource deleted. It can be restored from Deleted Resources.', 'success')
    return redirect(url_for('resources'))


@app.route('/resources/<int:resource_id>/restore', methods=['POST'])
@admin_required
def restore_resource_route(resource_id):
    restore_resource(resource_id)
    log_action(session['user_id'], 'restore', 'resource', resource_id,
               'Restored resource')
    flash('Resource restored successfully.', 'success')
    return redirect(url_for('deleted_resources'))


@app.route('/resources/<int:resource_id>/toggle', methods=['POST'])
@organizer_required
def toggle_resource(resource_id):
    toggle_resource_active(resource_id)
    log_action(session['user_id'], 'toggle', 'resource', resource_id,
               'Toggled resource active status')
    flash('Resource status updated.', 'success')
    return redirect(url_for('resources'))


# ─────────────────────────────────────────
# ALLOCATION ROUTES
# ─────────────────────────────────────────

@app.route('/allocations')
@login_required
def allocations():
    all_allocations = get_all_allocations()
    return render_template('allocations.html', allocations=all_allocations)


@app.route('/allocations/create', methods=['POST'])
@organizer_required
def create_allocation_route():
    event_id        = request.form.get('event_id', type=int)
    resource_id     = request.form.get('resource_id', type=int)
    quantity_needed = request.form.get('quantity_needed', 1, type=int)
    attendees_count = request.form.get('attendees_count', 1, type=int)
    notes           = request.form.get('notes', '').strip()

    if not event_id or not resource_id:
        flash('Event and resource are required.', 'danger')
        return redirect(url_for('event_detail', event_id=event_id))

    if allocation_exists(event_id, resource_id):
        flash('This resource is already allocated to this event.', 'warning')
        return redirect(url_for('event_detail', event_id=event_id))

    errors = validate_allocation(
        resource_id, event_id, attendees_count, quantity_needed
    )
    if errors:
        for e in errors:
            flash(e, 'danger')
        return redirect(url_for('event_detail', event_id=event_id))

    alloc_id = create_allocation(
        event_id, resource_id, quantity_needed,
        attendees_count, notes, session['user_id']
    )
    log_action(session['user_id'], 'create', 'allocation', alloc_id,
               f'Allocated resource {resource_id} to event {event_id}')
    flash('Resource allocated successfully.', 'success')
    return redirect(url_for('event_detail', event_id=event_id))


@app.route('/allocations/<int:alloc_id>/delete', methods=['POST'])
@organizer_required
def delete_allocation_route(alloc_id):
    event_id = request.form.get('event_id', type=int)
    delete_allocation(alloc_id)
    log_action(session['user_id'], 'delete', 'allocation', alloc_id,
               'Removed allocation')
    flash('Allocation removed successfully.', 'success')
    return redirect(url_for('event_detail', event_id=event_id))


# ─────────────────────────────────────────
# REPORT ROUTES
# ─────────────────────────────────────────

@app.route('/report')
@login_required
def report():
    start_date = request.args.get('start_date', '')
    end_date   = request.args.get('end_date', '')

    if not start_date:
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    report_data = get_utilisation_report(start_date, end_date)

    total_window_hours = 0
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt   = datetime.strptime(end_date,   '%Y-%m-%d')
        total_window_hours = max((end_dt - start_dt).days * 24, 1)
    except ValueError:
        total_window_hours = 1

    for row in report_data:
        row['utilisation_pct'] = round(
            (row['total_hours'] / total_window_hours) * 100, 1
        )

    return render_template('report.html',
                           report=report_data,
                           start_date=start_date,
                           end_date=end_date)


@app.route('/report/export')
@organizer_required
def export_csv():
    start_date = request.args.get('start_date', '')
    end_date   = request.args.get('end_date', '')

    if not start_date:
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    report_data = get_utilisation_report(start_date, end_date)

    total_window_hours = 1
    try:
        start_dt = datetime.strptime(start_date, '%Y-%m-%d')
        end_dt   = datetime.strptime(end_date,   '%Y-%m-%d')
        total_window_hours = max((end_dt - start_dt).days * 24, 1)
    except ValueError:
        pass

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        'Resource', 'Type', 'Capacity',
        'Events Count', 'Total Hours', 'Utilisation %'
    ])
    for row in report_data:
        pct = round((row['total_hours'] / total_window_hours) * 100, 1)
        writer.writerow([
            row['name'],
            row['resource_type'],
            row['capacity'],
            row['event_count'],
            row['total_hours'],
            pct
        ])

    response = make_response(output.getvalue())
    response.headers['Content-Type'] = 'text/csv'
    response.headers['Content-Disposition'] = (
        f'attachment; filename=utilisation_{start_date}_to_{end_date}.csv'
    )
    return response


# ─────────────────────────────────────────
# CALENDAR ROUTE
# ─────────────────────────────────────────

@app.route('/calendar')
@login_required
def calendar():
    week_offset = request.args.get('week', 0, type=int)
    today       = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    week_start  = today - timedelta(days=today.weekday()) + timedelta(weeks=week_offset)
    week_end    = week_start + timedelta(days=7)

    events = get_events_for_week(week_start, week_end)

    week_days = [week_start + timedelta(days=i) for i in range(7)]

    return render_template('calendar.html',
                           events=events,
                           week_days=week_days,
                           week_start=week_start,
                           week_end=week_end,
                           week_offset=week_offset,
                           today=today)


# ─────────────────────────────────────────
# AUDIT LOG ROUTE (Admin only)
# ─────────────────────────────────────────

@app.route('/audit')
@admin_required
def audit():
    logs = get_audit_logs()
    return render_template('audit.html', logs=logs)


# ─────────────────────────────────────────
# REST API ROUTES
# ─────────────────────────────────────────

def api_login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    return decorated


def api_organizer_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        if session.get('role') not in ('admin', 'organizer'):
            return jsonify({'error': 'Organizer role required'}), 403
        return f(*args, **kwargs)
    return decorated


def api_admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Authentication required'}), 401
        if session.get('role') != 'admin':
            return jsonify({'error': 'Admin role required'}), 403
        return f(*args, **kwargs)
    return decorated


# ── API Events ───────────────────────────

@app.route('/api/events', methods=['GET'])
@api_login_required
def api_list_events():
    events = get_all_events()
    result = []
    for e in events:
        result.append({
            'id':          e['id'],
            'title':       e['title'],
            'description': e['description'],
            'start_time':  str(e['start_time']),
            'end_time':    str(e['end_time']),
            'timezone':    e['timezone'],
            'created_by':  e['creator_name'],
        })
    return jsonify(result)


@app.route('/api/events/<int:event_id>', methods=['GET'])
@api_login_required
def api_get_event(event_id):
    event = get_event_by_id(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    return jsonify({
        'id':          event['id'],
        'title':       event['title'],
        'description': event['description'],
        'start_time':  str(event['start_time']),
        'end_time':    str(event['end_time']),
        'timezone':    event['timezone'],
        'created_by':  event['creator_name'],
    })


@app.route('/api/events', methods=['POST'])
@api_organizer_required
def api_create_event():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    title      = data.get('title', '').strip()
    start_time = data.get('start_time', '')
    end_time   = data.get('end_time', '')
    if not title:
        return jsonify({'error': 'title is required'}), 400
    if not start_time or not end_time:
        return jsonify({'error': 'start_time and end_time are required'}), 400
    try:
        start_dt = datetime.fromisoformat(start_time)
        end_dt   = datetime.fromisoformat(end_time)
        if end_dt <= start_dt:
            return jsonify({'error': 'end_time must be after start_time'}), 400
    except ValueError:
        return jsonify({'error': 'Invalid datetime format'}), 400

    event_id = create_event(
        title,
        data.get('description', ''),
        start_time,
        end_time,
        data.get('timezone', 'UTC'),
        session['user_id']
    )
    log_action(session['user_id'], 'api_create', 'event', event_id, f'API created: {title}')
    return jsonify({'id': event_id, 'message': 'Event created'}), 201


@app.route('/api/events/<int:event_id>', methods=['PUT'])
@api_organizer_required
def api_update_event(event_id):
    event = get_event_by_id(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    title      = data.get('title',       event['title'])
    description= data.get('description', event['description'])
    start_time = data.get('start_time',  str(event['start_time']))
    end_time   = data.get('end_time',    str(event['end_time']))
    timezone   = data.get('timezone',    event['timezone'])
    update_event(event_id, title, description, start_time, end_time, timezone)
    log_action(session['user_id'], 'api_update', 'event', event_id, f'API updated: {title}')
    return jsonify({'message': 'Event updated'})


@app.route('/api/events/<int:event_id>', methods=['DELETE'])
@api_admin_required
def api_delete_event(event_id):
    event = get_event_by_id(event_id)
    if not event:
        return jsonify({'error': 'Event not found'}), 404
    delete_event(event_id)
    log_action(session['user_id'], 'api_delete', 'event', event_id, f'API deleted event')
    return jsonify({'message': 'Event deleted'})


# ── API Resources ────────────────────────

@app.route('/api/resources', methods=['GET'])
@api_login_required
def api_list_resources():
    rtype     = request.args.get('type', '')
    resources = get_all_resources(rtype=rtype if rtype else None)
    return jsonify(list(resources))


@app.route('/api/resources/<int:resource_id>', methods=['GET'])
@api_login_required
def api_get_resource(resource_id):
    resource = get_resource_by_id(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    return jsonify(dict(resource))


@app.route('/api/resources', methods=['POST'])
@api_organizer_required
def api_create_resource():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    name          = data.get('name', '').strip()
    resource_type = data.get('resource_type', '')
    capacity      = data.get('capacity', 1)
    if not name:
        return jsonify({'error': 'name is required'}), 400
    if resource_type not in ('room', 'instructor', 'equipment'):
        return jsonify({'error': 'Invalid resource_type'}), 400
    resource_id = create_resource(
        name, resource_type, capacity,
        data.get('description', ''),
        data.get('location', '')
    )
    log_action(session['user_id'], 'api_create', 'resource', resource_id, f'API created: {name}')
    return jsonify({'id': resource_id, 'message': 'Resource created'}), 201


@app.route('/api/resources/<int:resource_id>', methods=['PUT'])
@api_organizer_required
def api_update_resource(resource_id):
    resource = get_resource_by_id(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    update_resource(
        resource_id,
        data.get('name',          resource['name']),
        data.get('resource_type', resource['resource_type']),
        data.get('capacity',      resource['capacity']),
        data.get('description',   resource['description']),
        data.get('location',      resource['location'])
    )
    log_action(session['user_id'], 'api_update', 'resource', resource_id, 'API updated resource')
    return jsonify({'message': 'Resource updated'})


@app.route('/api/resources/<int:resource_id>', methods=['DELETE'])
@api_admin_required
def api_delete_resource(resource_id):
    resource = get_resource_by_id(resource_id)
    if not resource:
        return jsonify({'error': 'Resource not found'}), 404
    delete_resource(resource_id)
    log_action(session['user_id'], 'api_delete', 'resource', resource_id, 'API deleted resource')
    return jsonify({'message': 'Resource deleted'})


# ── API Allocations ──────────────────────

@app.route('/api/allocations', methods=['GET'])
@api_login_required
def api_list_allocations():
    allocations = get_all_allocations()
    result = []
    for a in allocations:
        result.append({
            'id':             a['id'],
            'event_id':       a['event_id'],
            'event_title':    a['event_title'],
            'resource_id':    a['resource_id'],
            'resource_name':  a['resource_name'],
            'resource_type':  a['resource_type'],
            'quantity_needed':a['quantity_needed'],
            'attendees_count':a['attendees_count'],
            'notes':          a['notes'],
        })
    return jsonify(result)


@app.route('/api/allocations', methods=['POST'])
@api_organizer_required
def api_create_allocation():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    event_id        = data.get('event_id')
    resource_id     = data.get('resource_id')
    quantity_needed = data.get('quantity_needed', 1)
    attendees_count = data.get('attendees_count', 1)
    if not event_id or not resource_id:
        return jsonify({'error': 'event_id and resource_id are required'}), 400
    if allocation_exists(event_id, resource_id):
        return jsonify({'error': 'Resource already allocated to this event'}), 409
    errors = validate_allocation(resource_id, event_id, attendees_count, quantity_needed)
    if errors:
        return jsonify({'error': 'Conflict detected', 'details': errors}), 409
    alloc_id = create_allocation(
        event_id, resource_id, quantity_needed,
        attendees_count, data.get('notes', ''), session['user_id']
    )
    log_action(session['user_id'], 'api_create', 'allocation', alloc_id, 'API created allocation')
    return jsonify({'id': alloc_id, 'message': 'Allocation created'}), 201


@app.route('/api/allocations/<int:alloc_id>', methods=['DELETE'])
@api_organizer_required
def api_delete_allocation(alloc_id):
    delete_allocation(alloc_id)
    log_action(session['user_id'], 'api_delete', 'allocation', alloc_id, 'API deleted allocation')
    return jsonify({'message': 'Allocation removed'})


# ─────────────────────────────────────────
# ERROR HANDLERS
# ─────────────────────────────────────────

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(403)
def forbidden(e):
    return render_template('404.html'), 403

# Path to store admin preferences as a JSON file
PREFS_FILE = os.path.join(os.path.dirname(__file__), 'preferences.json')
 
def load_prefs():
    """Load app preferences from file."""
    if os.path.exists(PREFS_FILE):
        with open(PREFS_FILE, 'r') as f:
            return json.load(f)
    return {'timezone': 'UTC', 'date_format': 'YYYY-MM-DD', 'time_format': '24hr'}
 
def save_prefs(prefs):
    """Save app preferences to file."""
    with open(PREFS_FILE, 'w') as f:
        json.dump(prefs, f, indent=2)
 
 
# ─────────────────────────────────────────
# SETTINGS ROUTE
# ─────────────────────────────────────────
 
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    user  = get_user_by_id(session['user_id'])
    prefs = load_prefs()
 
    if request.method == 'POST':
        form_type = request.form.get('form_type')
 
        # ── Profile update ──────────────────────────
        if form_type == 'profile':
            username         = request.form.get('username', '').strip()
            email            = request.form.get('email', '').strip()
            current_password = request.form.get('current_password', '')
            new_password     = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')
 
            errors = []
 
            # Check username/email conflicts (skip own record)
            existing_username = get_user_by_username(username)
            if existing_username and existing_username['id'] != session['user_id']:
                errors.append('Username is already taken.')
 
            existing_email = get_user_by_email(email)
            if existing_email and existing_email['id'] != session['user_id']:
                errors.append('Email is already registered.')
 
            # Password change validation
            change_password = bool(current_password or new_password or confirm_password)
            if change_password:
                if not check_password_hash(user['password_hash'], current_password):
                    errors.append('Current password is incorrect.')
                if len(new_password) < 6:
                    errors.append('New password must be at least 6 characters.')
                if new_password != confirm_password:
                    errors.append('New passwords do not match.')
 
            if errors:
                for e in errors:
                    flash(e, 'danger')
                return redirect(url_for('settings'))
 
            # Save profile
            update_profile(session['user_id'], username, email)
            session['username'] = username  # keep session in sync
 
            # Save password if changed
            if change_password:
                update_password(session['user_id'],
                                generate_password_hash(new_password))
                flash('Password updated successfully.', 'success')
 
            log_action(session['user_id'], 'update', 'user',
                       session['user_id'], 'Updated own profile from Settings')
            flash('Profile saved successfully.', 'success')
            return redirect(url_for('settings'))
 
        # ── App Preferences (admin only) ────────────
        if form_type == 'preferences' and session.get('role') == 'admin':
            prefs['timezone']    = request.form.get('default_timezone', 'UTC')
            prefs['date_format'] = request.form.get('date_format', 'YYYY-MM-DD')
            prefs['time_format'] = request.form.get('time_format', '24hr')
            save_prefs(prefs)
            log_action(session['user_id'], 'update', 'preferences',
                       None, 'Updated app preferences from Settings')
            flash('Preferences saved successfully.', 'success')
            return redirect(url_for('settings'))
 
    return render_template('settings.html', prefs=prefs)
# ─────────────────────────────────────────
# RUN
# ─────────────────────────────────────────

if __name__ == '__main__':
    app.run(
        debug=os.getenv('FLASK_DEBUG', '1') == '1',
        host='0.0.0.0',
        port=5000
    )