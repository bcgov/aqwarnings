import datetime
import unittest
import pytz
from unittest.mock import patch

import construct_lists
from construct_lists import select_recent_warnings, extract_header_from_file, get_today_in_bc_timezone


class TestWarningSelectionLogic(unittest.TestCase):
    def test_select_recent_warnings(self):
        """Test the warning selection logic with mock data"""
        # Mock today's date as 2025-06-13
        mock_today = datetime.date(2025, 6, 13)

        # Create some test header entries
        mock_headers = [
            # Same-day wildfire smoke issue (0 days old) - should be included
            {
                'entry': {
                    'path': '/path/to/warning1.md',
                    'title': 'Wildfire Smoke Warning',
                    'type': 'wildfire_smoke',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 13),  # Same day as mock_today
                    'location': 'Interior',
                },
                'raw_header': {
                    'title': 'Wildfire Smoke Warning',
                    'type': 'wildfire_smoke',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 13),  # Same day as mock_today
                    'location': 'Interior',
                },
            },
            # 1-day-old wildfire smoke issue - should be excluded due to special handling (age >= 1)
            {
                'entry': {
                    'path': '/path/to/warning2.md',
                    'title': 'Wildfire Smoke Warning',
                    'type': 'wildfire_smoke',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 12),  # 1 day old
                    'location': 'Interior',
                },
                'raw_header': {
                    'title': 'Wildfire Smoke Warning',
                    'type': 'wildfire_smoke',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 12),  # 1 day old
                    'location': 'Interior',
                },
            },
            # Recent heat warning (3 days old) - should be included
            {
                'entry': {
                    'path': '/path/to/warning3.md',
                    'title': 'Heat Warning',
                    'type': 'heat',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 10),
                    'location': 'Coast',
                },
                'raw_header': {
                    'title': 'Heat Warning',
                    'type': 'heat',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 10),
                    'location': 'Coast',
                },
            },
            # Old warning (6 days old) - should be excluded due to age
            {
                'entry': {
                    'path': '/path/to/warning4.md',
                    'title': 'Air Quality Warning',
                    'type': 'air_quality',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 7),
                    'location': 'North',
                },
                'raw_header': {
                    'title': 'Air Quality Warning',
                    'type': 'air_quality',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 7),
                    'location': 'North',
                },
            },
            # Warning without date - should be excluded
            {
                'entry': {
                    'path': '/path/to/warning5.md',
                    'title': 'Generic Warning',
                    'type': 'other',
                    'ice': 'issue',
                    'date': None,
                    'location': 'Province-wide',
                },
                'raw_header': {
                    'title': 'Generic Warning',
                    'type': 'other',
                    'ice': 'issue',
                    'location': 'Province-wide',
                },
            },
        ]

        # Test with default threshold (5 days)
        recent_warnings = select_recent_warnings(mock_headers, today_date=mock_today)

        # We should have 2 warnings (recent wildfire smoke and heat warning)
        self.assertEqual(len(recent_warnings), 2)

        # Check that the right warnings were selected
        paths = [warning['path'] for warning in recent_warnings]
        self.assertIn('/path/to/warning1.md', paths)  # Recent wildfire smoke
        self.assertIn('/path/to/warning3.md', paths)  # Heat warning

        # Check that excluded warnings are not present
        self.assertNotIn('/path/to/warning2.md', paths)  # Old wildfire smoke
        self.assertNotIn('/path/to/warning4.md', paths)  # Old air quality
        self.assertNotIn('/path/to/warning5.md', paths)  # No date

        # Test with custom threshold (2 days)
        recent_warnings = select_recent_warnings(mock_headers, today_date=mock_today, recent_threshold_days=2)

        # We should have only 1 warning now
        self.assertEqual(len(recent_warnings), 1)
        self.assertEqual(recent_warnings[0]['path'], '/path/to/warning1.md')


class TestTimezoneHandling(unittest.TestCase):
    """Test class for timezone handling in warning selection"""

    def test_get_today_in_bc_timezone(self):
        """Test that get_today_in_bc_timezone returns the correct date in BC timezone"""
        # Mock the datetime to return a fixed UTC time
        mock_utc_datetime = datetime.datetime(2025, 6, 14, 5, 30, 0, tzinfo=pytz.UTC)  # 5:30 AM UTC

        with patch('datetime.datetime') as mock_datetime:
            # Configure the mock to return our fixed UTC time
            mock_datetime.now.return_value = mock_utc_datetime
            mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

            # Get the BC date
            bc_today = get_today_in_bc_timezone()

            # The time in BC should be 10:30 PM on June 13, 2025 (PST = UTC-7 during summer)
            # So the date should be 2025-06-13
            expected_date = datetime.date(2025, 6, 13)
            self.assertEqual(bc_today, expected_date)

    def test_warning_expiry_at_bc_midnight(self):
        """Test that warnings expire at midnight BC time, not UTC"""
        # Create a test warning with date 2025-06-09 (4 days before our test date)
        mock_headers = [
            {
                'entry': {
                    'path': '/path/to/expiring_warning.md',
                    'title': 'Expiring Warning',
                    'type': 'heat',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 9),  # 4 days before 2025-06-13
                    'location': 'Interior',
                },
                'raw_header': {
                    'title': 'Expiring Warning',
                    'type': 'heat',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 9),
                    'location': 'Interior',
                },
            }
        ]

        # Scenario 1: Test with BC time on June 13 (4 days since June 9)
        # The warning should still be included (not expired) as age is less than threshold
        bc_time_day4 = datetime.date(2025, 6, 13)
        warnings = select_recent_warnings(mock_headers, today_date=bc_time_day4)
        self.assertEqual(len(warnings), 1, 'Warning should be included when age < threshold')

        # Scenario 2: Test with BC time on June 14 (5 days since June 9)
        # The warning should be excluded (expired) as age equals threshold
        bc_time_day5 = datetime.date(2025, 6, 14)
        warnings = select_recent_warnings(mock_headers, today_date=bc_time_day5)
        self.assertEqual(len(warnings), 0, 'Warning should expire when age = threshold')

    def test_timezone_edge_case(self):
        """Test warning selection using real timezone handling with mocked time"""
        # Create a warning that's 4 days old (just under the threshold)
        mock_headers = [
            {
                'entry': {
                    'path': '/path/to/edge_case_warning.md',
                    'title': 'Edge Case Warning',
                    'type': 'air_quality',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 9),  # 4 days before 2025-06-13
                    'location': 'Coast',
                },
                'raw_header': {
                    'title': 'Edge Case Warning',
                    'type': 'air_quality',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 9),
                    'location': 'Coast',
                },
            }
        ]

        # Test 1: When BC date is 2025-06-13, warning is 4 days old and should be included
        with patch.object(construct_lists, 'get_today_in_bc_timezone', return_value=datetime.date(2025, 6, 13)):
            warnings = select_recent_warnings(mock_headers)  # No today_date, will use mocked function
            self.assertEqual(len(warnings), 1, 'Warning should be included when age < threshold')

        # Test 2: When BC date is 2025-06-14, warning is 5 days old and should be excluded
        with patch.object(construct_lists, 'get_today_in_bc_timezone', return_value=datetime.date(2025, 6, 14)):
            warnings = select_recent_warnings(mock_headers)  # No today_date, will use mocked function
            self.assertEqual(len(warnings), 0, 'Warning should expire when age = threshold')

    def test_utc_vs_bc_timezone_bug(self):
        """Test specifically for the timezone bug scenario - warnings disappearing too early"""
        # Create a warning dated June 9, 2025
        mock_headers = [
            {
                'entry': {
                    'path': '/path/to/timezone_bug_warning.md',
                    'title': 'Timezone Bug Test Warning',
                    'type': 'heat',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 9),
                    'location': 'Interior',
                },
                'raw_header': {
                    'title': 'Timezone Bug Test Warning',
                    'type': 'heat',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 9),
                    'location': 'Interior',
                },
            }
        ]

        # Scenario: It's still June 13 in BC (late evening), but already June 14 in UTC
        # We want to ensure that warnings don't expire prematurely due to UTC time

        # Mock the datetime to return a fixed UTC time (June 14, 2025 05:00 AM UTC)
        # This corresponds to June 13, 2025 10:00 PM in BC (UTC-7)
        mock_utc_datetime = datetime.datetime(2025, 6, 14, 5, 0, 0, tzinfo=pytz.UTC)

        # This test demonstrates the bug fix:
        # If we use UTC time directly (June 14), the warning would incorrectly expire
        # But using BC timezone (June 13), the warning should still be included

        # Step 1: Without timezone fixing (simulating the bug)
        utc_date = mock_utc_datetime.date()  # This would be June 14 in UTC
        warnings_with_utc = select_recent_warnings(mock_headers, today_date=utc_date)
        self.assertEqual(len(warnings_with_utc), 0, 'Using UTC time directly would incorrectly expire the warning')

        # Step 2: With timezone fixing via get_today_in_bc_timezone
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_utc_datetime
            mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

            # Call the actual function we're testing
            bc_today = get_today_in_bc_timezone()
            warnings_with_bc_timezone = select_recent_warnings(mock_headers, today_date=bc_today)

            self.assertEqual(
                len(warnings_with_bc_timezone), 1, 'Using BC timezone keeps warning active until BC midnight'
            )
            self.assertEqual(bc_today, datetime.date(2025, 6, 13), 'BC date should be June 13 even when UTC is June 14')


if __name__ == '__main__':
    unittest.main()
