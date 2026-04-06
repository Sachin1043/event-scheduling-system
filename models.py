from database import get_connection


# ─────────────────────────────────────────
# USER QUERIES
# ─────────────────────────────────────────

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def get_user_by_email(email):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user


def get_all_users():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users ORDER BY created_at DESC")
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return users


def create_user(username, email, password_hash, role='viewer'):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, role)
        VALUES (%s, %s, %s, %s)
    """, (username, email, password_hash, role))
    conn.commit()
    user_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return user_id


def update_user(user_id, username, email, role):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET username = %s,
            email    = %s,
            role     = %s
        WHERE id = %s
    """, (username, email, role, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def update_profile(user_id, username, email):
    """Update username and email only."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET username = %s,
            email    = %s
        WHERE id = %s
    """, (username, email, user_id))
    conn.commit()
    cursor.close()
    conn.close()
 
 
def update_password(user_id, new_password_hash):
    """Update password hash for a user."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET password_hash = %s
        WHERE id = %s
    """, (new_password_hash, user_id))
    conn.commit()
    cursor.close()
    conn.close()

def toggle_user_active(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE users
        SET is_active = NOT is_active
        WHERE id = %s
    """, (user_id,))
    conn.commit()
    cursor.close()
    conn.close()


# ─────────────────────────────────────────
# EVENT QUERIES
# ─────────────────────────────────────────

def get_all_events(search=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    if search:
        cursor.execute("""
            SELECT e.*, u.username AS creator_name
            FROM events e
            JOIN users u ON e.created_by = u.id
            WHERE e.is_deleted = 0
            AND (
                e.title       LIKE %s
                OR e.description LIKE %s
            )
            ORDER BY e.start_time ASC
        """, (f'%{search}%', f'%{search}%'))
    else:
        cursor.execute("""
            SELECT e.*, u.username AS creator_name
            FROM events e
            JOIN users u ON e.created_by = u.id
            WHERE e.is_deleted = 0
            ORDER BY e.start_time ASC
        """)
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    return events


def get_event_by_id(event_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*, u.username AS creator_name
        FROM events e
        JOIN users u ON e.created_by = u.id
        WHERE e.id = %s AND e.is_deleted = 0
    """, (event_id,))
    event = cursor.fetchone()
    cursor.close()
    conn.close()
    return event


def create_event(title, description, start_time, end_time, timezone, created_by):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO events
            (title, description, start_time, end_time, timezone, created_by)
        VALUES
            (%s, %s, %s, %s, %s, %s)
    """, (title, description, start_time, end_time, timezone, created_by))
    conn.commit()
    event_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return event_id


def update_event(event_id, title, description, start_time, end_time, timezone):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE events
        SET title       = %s,
            description = %s,
            start_time  = %s,
            end_time    = %s,
            timezone    = %s
        WHERE id = %s AND is_deleted = 0
    """, (title, description, start_time, end_time, timezone, event_id))
    conn.commit()
    cursor.close()
    conn.close()


def delete_event(event_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE events
        SET is_deleted = 1
        WHERE id = %s
    """, (event_id,))
    conn.commit()
    cursor.close()
    conn.close()


def get_upcoming_events(limit=5):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*, u.username AS creator_name
        FROM events e
        JOIN users u ON e.created_by = u.id
        WHERE e.is_deleted = 0
        AND e.start_time >= NOW()
        ORDER BY e.start_time ASC
        LIMIT %s
    """, (limit,))
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    return events


def get_events_for_week(week_start, week_end):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT e.*, u.username AS creator_name
        FROM events e
        JOIN users u ON e.created_by = u.id
        WHERE e.is_deleted = 0
        AND e.start_time >= %s
        AND e.start_time <  %s
        ORDER BY e.start_time ASC
    """, (week_start, week_end))
    events = cursor.fetchall()
    cursor.close()
    conn.close()
    return events


# ─────────────────────────────────────────
# RESOURCE QUERIES
# ─────────────────────────────────────────

def get_all_resources_with_allocation(rtype=None):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    base_query = """
        SELECT
            r.*,
            COALESCE(SUM(a.quantity_needed), 0)               AS allocated,
            r.capacity - COALESCE(SUM(a.quantity_needed), 0)  AS available
        FROM resources r
        LEFT JOIN allocations a ON a.resource_id = r.id
        LEFT JOIN events e      ON a.event_id    = e.id
                                AND e.is_deleted  = 0
        WHERE r.is_deleted = 0
        {type_filter}
        GROUP BY r.id
        ORDER BY r.name ASC
    """
    if rtype:
        cursor.execute(base_query.format(type_filter="AND r.resource_type = %s"), (rtype,))
    else:
        cursor.execute(base_query.format(type_filter=""))
    resources = cursor.fetchall()
    cursor.close()
    conn.close()
    return resources


def get_all_resources(rtype=None, include_deleted=False):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if include_deleted:
        if rtype:
            cursor.execute("""
                SELECT * FROM resources
                WHERE resource_type = %s
                ORDER BY name ASC
            """, (rtype,))
        else:
            cursor.execute("""
                SELECT * FROM resources
                ORDER BY name ASC
            """)
    else:
        if rtype:
            cursor.execute("""
                SELECT * FROM resources
                WHERE is_deleted = 0
                AND resource_type = %s
                ORDER BY name ASC
            """, (rtype,))
        else:
            cursor.execute("""
                SELECT * FROM resources
                WHERE is_deleted = 0
                ORDER BY name ASC
            """)

    resources = cursor.fetchall()
    cursor.close()
    conn.close()
    return resources


def get_resource_by_id(resource_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM resources
        WHERE id = %s AND is_deleted = 0
    """, (resource_id,))
    resource = cursor.fetchone()
    cursor.close()
    conn.close()
    return resource


def get_deleted_resources():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT * FROM resources
        WHERE is_deleted = 1
        ORDER BY name ASC
    """)
    resources = cursor.fetchall()
    cursor.close()
    conn.close()
    return resources


def create_resource(name, resource_type, capacity, description, location):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO resources
            (name, resource_type, capacity, description, location)
        VALUES
            (%s, %s, %s, %s, %s)
    """, (name, resource_type, capacity, description, location))
    conn.commit()
    resource_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return resource_id


def update_resource(resource_id, name, resource_type, capacity, description, location):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE resources
        SET name          = %s,
            resource_type = %s,
            capacity      = %s,
            description   = %s,
            location      = %s
        WHERE id = %s AND is_deleted = 0
    """, (name, resource_type, capacity, description, location, resource_id))
    conn.commit()
    cursor.close()
    conn.close()


def delete_resource(resource_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE resources
        SET is_deleted = 1,
            is_active  = 0
        WHERE id = %s
    """, (resource_id,))
    conn.commit()
    cursor.close()
    conn.close()


def restore_resource(resource_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE resources
        SET is_deleted = 0,
            is_active  = 1
        WHERE id = %s
    """, (resource_id,))
    conn.commit()
    cursor.close()
    conn.close()


def toggle_resource_active(resource_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE resources
        SET is_active = NOT is_active
        WHERE id = %s AND is_deleted = 0
    """, (resource_id,))
    conn.commit()
    cursor.close()
    conn.close()


# ─────────────────────────────────────────
# ALLOCATION QUERIES
# ─────────────────────────────────────────

def get_all_allocations():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            a.*,
            e.title          AS event_title,
            e.start_time     AS event_start,
            e.end_time       AS event_end,
            r.name           AS resource_name,
            r.resource_type  AS resource_type,
            u.username       AS allocated_by_name
        FROM allocations a
        JOIN events    e ON a.event_id    = e.id
        JOIN resources r ON a.resource_id = r.id
        LEFT JOIN users u ON a.allocated_by = u.id
        WHERE e.is_deleted = 0
        ORDER BY e.start_time ASC
    """)
    allocations = cursor.fetchall()
    cursor.close()
    conn.close()
    return allocations


def get_allocations_by_event(event_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            a.*,
            r.name          AS resource_name,
            r.resource_type AS resource_type,
            r.capacity      AS resource_capacity,
            u.username      AS allocated_by_name
        FROM allocations a
        JOIN resources r ON a.resource_id = r.id
        LEFT JOIN users u ON a.allocated_by = u.id
        WHERE a.event_id = %s
        ORDER BY r.name ASC
    """, (event_id,))
    allocations = cursor.fetchall()
    cursor.close()
    conn.close()
    return allocations


def create_allocation(event_id, resource_id, quantity_needed, attendees_count, notes, allocated_by):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO allocations
            (event_id, resource_id, quantity_needed, attendees_count, notes, allocated_by)
        VALUES
            (%s, %s, %s, %s, %s, %s)
    """, (event_id, resource_id, quantity_needed, attendees_count, notes, allocated_by))
    conn.commit()
    alloc_id = cursor.lastrowid
    cursor.close()
    conn.close()
    return alloc_id


def delete_allocation(alloc_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM allocations WHERE id = %s", (alloc_id,))
    conn.commit()
    cursor.close()
    conn.close()


def allocation_exists(event_id, resource_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT id FROM allocations
        WHERE event_id = %s AND resource_id = %s
    """, (event_id, resource_id))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None


# ─────────────────────────────────────────
# REPORT QUERIES
# ─────────────────────────────────────────

def get_utilisation_report(start_date, end_date):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    # Append time so end_date is inclusive for the full day
    end_date_full = end_date + ' 23:59:59'
    cursor.execute("""
        SELECT
            r.id,
            r.name,
            r.resource_type,
            r.capacity,
            COUNT(a.id)                             AS event_count,
            COALESCE(SUM(
                TIMESTAMPDIFF(HOUR, e.start_time, e.end_time)
            ), 0)                                   AS total_hours
        FROM resources r
        JOIN allocations a ON r.id = a.resource_id
        JOIN events e
            ON  a.event_id   = e.id
            AND e.is_deleted = 0
            AND e.start_time >= %s
            AND e.start_time <= %s
        WHERE r.is_deleted = 0
        GROUP BY r.id, r.name, r.resource_type, r.capacity
        ORDER BY total_hours DESC
    """, (start_date, end_date_full))
    report = cursor.fetchall()
    cursor.close()
    conn.close()
    return report


def get_dashboard_stats():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM events WHERE is_deleted = 0")
    total_events = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM resources WHERE is_deleted = 0")
    total_resources = cursor.fetchone()['total']

    cursor.execute("SELECT COUNT(*) AS total FROM allocations")
    total_allocations = cursor.fetchone()['total']

    cursor.execute("""
        SELECT COUNT(*) AS total FROM events
        WHERE is_deleted = 0 AND start_time >= NOW()
    """)
    upcoming_events = cursor.fetchone()['total']

    cursor.close()
    conn.close()

    return {
        'total_events':      total_events,
        'total_resources':   total_resources,
        'total_allocations': total_allocations,
        'upcoming_events':   upcoming_events
    }


# ─────────────────────────────────────────
# AUDIT LOG QUERIES
# ─────────────────────────────────────────

def log_action(user_id, action, entity_type, entity_id, details=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO audit_logs
            (user_id, action, entity_type, entity_id, details)
        VALUES
            (%s, %s, %s, %s, %s)
    """, (user_id, action, entity_type, entity_id, details))
    conn.commit()
    cursor.close()
    conn.close()


def get_audit_logs():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT
            al.*,
            u.username AS username
        FROM audit_logs al
        LEFT JOIN users u ON al.user_id = u.id
        ORDER BY al.created_at DESC
        LIMIT 200
    """)
    logs = cursor.fetchall()
    cursor.close()
    conn.close()
    return logs