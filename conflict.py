from database import get_connection



def check_resource_conflict(resource_id, start_time, end_time, exclude_event_id=None):
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM resources
        WHERE id = %s AND is_deleted = 0
    """, (resource_id,))
    resource = cursor.fetchone()

    if not resource:
        cursor.close()
        conn.close()
        return {
            'conflict': True,
            'message': 'Resource not found.',
            'conflicting_events': []
        }

    if not resource['is_active']:
        cursor.close()
        conn.close()
        return {
            'conflict': True,
            'message': f'Resource "{resource["name"]}" is inactive.',
            'conflicting_events': []
        }
        
    if resource['resource_type'] == 'equipment':
        cursor.close()
        conn.close()
        return {
            'conflict': False,
            'message': 'No conflict.',
            'conflicting_events': []
        }

    
    query = """
        SELECT
            e.id        AS event_id,
            e.title     AS event_title,
            e.start_time,
            e.end_time,
            a.quantity_needed
        FROM allocations a
        JOIN events e ON a.event_id = e.id
        WHERE
            a.resource_id = %s
            AND e.is_deleted = 0
            AND e.start_time < %s
            AND e.end_time   > %s
    """
    params = [resource_id, end_time, start_time]

    
    if exclude_event_id:
        query += " AND e.id != %s"
        params.append(exclude_event_id)

    cursor.execute(query, params)
    conflicting = cursor.fetchall()

    cursor.close()
    conn.close()

    if not conflicting:
        return {
            'conflict': False,
            'message': 'No conflict.',
            'conflicting_events': []
        }

    names = ', '.join(c['event_title'] for c in conflicting)
    message = (
        f'Resource "{resource["name"]}" is already booked '
        f'during this time. Conflicts with: {names}.'
    )

    return {
        'conflict': True,
        'message': message,
        'conflicting_events': list(conflicting)
    }


def check_capacity_constraint(resource_id, attendees_count):
    
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM resources
        WHERE id = %s AND is_deleted = 0
    """, (resource_id,))
    resource = cursor.fetchone()

    cursor.close()
    conn.close()

    if not resource:
        return {
            'violation': True,
            'message': 'Resource not found.'
        }

    if resource['resource_type'] != 'room':
        return {
            'violation': False,
            'message': 'Not a room. Capacity check skipped.'
        }

    if attendees_count > resource['capacity']:
        return {
            'violation': True,
            'message': (
                f'Room "{resource["name"]}" has a capacity of '
                f'{resource["capacity"]} but {attendees_count} '
                f'attendees were requested.'
            )
        }

    return {
        'violation': False,
        'message': 'Capacity OK.'
    }


def check_quantity_constraint(resource_id, quantity_needed, start_time, end_time, exclude_event_id=None):
   
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM resources
        WHERE id = %s AND is_deleted = 0
    """, (resource_id,))
    resource = cursor.fetchone()

    if not resource:
        cursor.close()
        conn.close()
        return {
            'violation': True,
            'message': 'Resource not found.',
            'available': 0
        }

    if resource['resource_type'] != 'equipment':
        cursor.close()
        conn.close()
        return {
            'violation': False,
            'message': 'Not equipment. Quantity check skipped.',
            'available': resource['capacity']
        }

    query = """
        SELECT COALESCE(SUM(a.quantity_needed), 0) AS total_used
        FROM allocations a
        JOIN events e ON a.event_id = e.id
        WHERE
            a.resource_id = %s
            AND e.is_deleted = 0
            AND e.start_time < %s
            AND e.end_time   > %s
    """
    params = [resource_id, end_time, start_time]

    if exclude_event_id:
        query += " AND e.id != %s"
        params.append(exclude_event_id)

    cursor.execute(query, params)
    result = cursor.fetchone()

    cursor.close()
    conn.close()

    total_used = result['total_used'] if result else 0
    available  = resource['capacity'] - total_used

    if quantity_needed > available:
        return {
            'violation': True,
            'message': (
                f'Only {available} unit(s) of "{resource["name"]}" '
                f'available (total: {resource["capacity"]}, '
                f'already booked: {total_used}, '
                f'requested: {quantity_needed}).'
            ),
            'available': available
        }

    return {
        'violation': False,
        'message': 'Quantity OK.',
        'available': available
    }



def validate_allocation(resource_id, event_id, attendees_count=1, quantity_needed=1, exclude_event_id=None):
    
    errors = []

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT * FROM events
        WHERE id = %s AND is_deleted = 0
    """, (event_id,))
    event = cursor.fetchone()

    cursor.close()
    conn.close()

    if not event:
        return ['Event not found.']

    start_time = event['start_time']
    end_time   = event['end_time']

    # 1. Time overlap check for rooms and instructors
    conflict = check_resource_conflict(
        resource_id,
        start_time,
        end_time,
        exclude_event_id=exclude_event_id
    )
    if conflict['conflict']:
        errors.append(conflict['message'])

    # 2. Room capacity check
    capacity = check_capacity_constraint(
        resource_id,
        attendees_count
    )
    if capacity['violation']:
        errors.append(capacity['message'])

    # 3. Equipment quantity check
    quantity = check_quantity_constraint(
        resource_id,
        quantity_needed,
        start_time,
        end_time,
        exclude_event_id=exclude_event_id
    )
    if quantity['violation']:
        errors.append(quantity['message'])

    return errors