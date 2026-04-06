import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from conflict import (
    check_resource_conflict,
    check_capacity_constraint,
    check_quantity_constraint,
    validate_allocation
)

# ─────────────────────────────────────────
# Mock Helpers
# ─────────────────────────────────────────

def make_resource(id, name, rtype, capacity, is_active=True, is_deleted=False):
    return {
        'id': id, 'name': name,
        'resource_type': rtype,
        'capacity': capacity,
        'is_active': is_active,
        'is_deleted': is_deleted
    }

def make_event(id, title, start_offset_h, duration_h):
    base  = datetime(2025, 6, 1, 9, 0)
    start = base + timedelta(hours=start_offset_h)
    end   = start + timedelta(hours=duration_h)
    return {'id': id, 'title': title, 'start_time': start, 'end_time': end}

BASE = datetime(2025, 6, 1, 9, 0)


# ─────────────────────────────────────────
# Test 1: No conflict when no allocations
# ─────────────────────────────────────────
def test_no_conflict_empty():
    room = make_resource(1, 'Room A', 'room', 20)
    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.return_value = room
        cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = cursor

        result = check_resource_conflict(
            1, BASE, BASE + timedelta(hours=2)
        )
        assert result['conflict'] is False


# ─────────────────────────────────────────
# Test 2: Exact time overlap is a conflict
# ─────────────────────────────────────────
def test_exact_overlap_conflict():
    room = make_resource(1, 'Room A', 'room', 20)
    conflict_row = {
        'event_id': 2, 'event_title': 'Existing Event',
        'start_time': BASE, 'end_time': BASE + timedelta(hours=2),
        'quantity_needed': 1
    }
    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.return_value = room
        cursor.fetchall.return_value = [conflict_row]
        mock_conn.return_value.cursor.return_value = cursor

        result = check_resource_conflict(
            1, BASE, BASE + timedelta(hours=2)
        )
        assert result['conflict'] is True
        assert 'Existing Event' in result['message']


# ─────────────────────────────────────────
# Test 3: Partial overlap at start
# ─────────────────────────────────────────
def test_partial_overlap_start():
    room = make_resource(1, 'Room B', 'room', 20)
    conflict_row = {
        'event_id': 2, 'event_title': 'Morning Session',
        'start_time': BASE, 'end_time': BASE + timedelta(hours=3),
        'quantity_needed': 1
    }
    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.return_value = room
        cursor.fetchall.return_value = [conflict_row]
        mock_conn.return_value.cursor.return_value = cursor

        result = check_resource_conflict(
            1,
            BASE - timedelta(hours=1),
            BASE + timedelta(hours=1)
        )
        assert result['conflict'] is True


# ─────────────────────────────────────────
# Test 4: No overlap — events are adjacent
# ─────────────────────────────────────────
def test_no_overlap_adjacent_events():
    room = make_resource(1, 'Room C', 'room', 20)
    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.return_value = room
        cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = cursor

        result = check_resource_conflict(
            1,
            BASE + timedelta(hours=2),
            BASE + timedelta(hours=4)
        )
        assert result['conflict'] is False


# ─────────────────────────────────────────
# Test 5: Inactive resource is a conflict
# ─────────────────────────────────────────
def test_inactive_resource_conflict():
    room = make_resource(1, 'Room D', 'room', 20, is_active=False)
    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.return_value = room
        mock_conn.return_value.cursor.return_value = cursor

        result = check_resource_conflict(
            1, BASE, BASE + timedelta(hours=2)
        )
        assert result['conflict'] is True
        assert 'inactive' in result['message'].lower()


# ─────────────────────────────────────────
# Test 6: Equipment skips time conflict check
# ─────────────────────────────────────────
def test_equipment_skips_conflict_check():
    equipment = make_resource(1, 'Projector', 'equipment', 5)
    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.return_value = equipment
        mock_conn.return_value.cursor.return_value = cursor

        result = check_resource_conflict(
            1, BASE, BASE + timedelta(hours=2)
        )
        assert result['conflict'] is False


# ─────────────────────────────────────────
# Test 7: Room capacity exceeded
# ─────────────────────────────────────────
def test_room_capacity_exceeded():
    room = make_resource(1, 'Small Room', 'room', 5)
    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.return_value = room
        mock_conn.return_value.cursor.return_value = cursor

        result = check_capacity_constraint(1, attendees_count=10)
        assert result['violation'] is True
        assert '5' in result['message']
        assert '10' in result['message']


# ─────────────────────────────────────────
# Test 8: Room capacity within limit
# ─────────────────────────────────────────
def test_room_capacity_ok():
    room = make_resource(1, 'Big Room', 'room', 50)
    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.return_value = room
        mock_conn.return_value.cursor.return_value = cursor

        result = check_capacity_constraint(1, attendees_count=30)
        assert result['violation'] is False


# ─────────────────────────────────────────
# Test 9: Equipment quantity exceeded
# ─────────────────────────────────────────
def test_equipment_quantity_exceeded():
    equipment = make_resource(1, 'Laptop', 'equipment', 5)
    used_result = {'total_used': 4}
    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.side_effect = [equipment, used_result]
        mock_conn.return_value.cursor.return_value = cursor

        result = check_quantity_constraint(
            1, quantity_needed=3,
            start_time=BASE,
            end_time=BASE + timedelta(hours=2)
        )
        assert result['violation'] is True
        assert result['available'] == 1


# ─────────────────────────────────────────
# Test 10: Equipment quantity available
# ─────────────────────────────────────────
def test_equipment_quantity_ok():
    equipment = make_resource(1, 'Laptop', 'equipment', 10)
    used_result = {'total_used': 3}
    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.side_effect = [equipment, used_result]
        mock_conn.return_value.cursor.return_value = cursor

        result = check_quantity_constraint(
            1, quantity_needed=5,
            start_time=BASE,
            end_time=BASE + timedelta(hours=2)
        )
        assert result['violation'] is False
        assert result['available'] == 7


# ─────────────────────────────────────────
# Test 11: Instructor conflict same time
# ─────────────────────────────────────────
def test_instructor_conflict():
    instructor = make_resource(1, 'John Smith', 'instructor', 1)
    conflict_row = {
        'event_id': 2, 'event_title': 'Other Class',
        'start_time': BASE, 'end_time': BASE + timedelta(hours=2),
        'quantity_needed': 1
    }
    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.return_value = instructor
        cursor.fetchall.return_value = [conflict_row]
        mock_conn.return_value.cursor.return_value = cursor

        result = check_resource_conflict(
            1, BASE, BASE + timedelta(hours=2)
        )
        assert result['conflict'] is True
        assert 'Other Class' in result['message']


# ─────────────────────────────────────────
# Test 12: validate_allocation returns
#          empty list when all checks pass
# ─────────────────────────────────────────
def test_validate_allocation_no_errors():
    room  = make_resource(1, 'Room A', 'room', 30)
    event = make_event(1, 'Workshop', 0, 2)

    with patch('conflict.get_connection') as mock_conn:
        cursor = MagicMock()
        cursor.fetchone.side_effect = [event, room, room, room]
        cursor.fetchall.return_value = []
        mock_conn.return_value.cursor.return_value = cursor

        errors = validate_allocation(
            resource_id=1,
            event_id=1,
            attendees_count=20,
            quantity_needed=1
        )
        assert errors == []