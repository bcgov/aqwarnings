import datetime
import unittest
import pytz
from unittest.mock import patch

import construct_lists
from construct_lists import select_recent_warnings, extract_header_from_file, get_today_in_bc_timezone


class TestWarningSelectionLogic(unittest.TestCase):
    def test_select_recent_warnings_basic_logic(self):
        """Test the basic warning selection logic with mock data"""
        # Mock today's date as 2025-06-13
        mock_today = datetime.date(2025, 6, 13)

        # Create some test header entries
        mock_headers = [
            # Newest wildfire smoke warning - should be included
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
            # Older wildfire smoke warning - should be excluded as only newest is kept
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
            # Heat warning for Coast - should be included as newest for this community
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
            # Air quality warning for North - should be included as newest for this community
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
                    'ice': 'Issue',
                    'date': None,
                    'location': 'Province-wide',
                },
                'raw_header': {
                    'title': 'Generic Warning',
                    'type': 'other',
                    'ice': 'Issue',
                    'location': 'Province-wide',
                },
            },
        ]

        # Test with default settings
        recent_warnings = select_recent_warnings(mock_headers, today_date=mock_today)

        # We should have 3 warnings (newest wildfire + one for each community)
        self.assertEqual(len(recent_warnings), 3)

        # Check that the right warnings were selected
        paths = [warning['path'] for warning in recent_warnings]
        self.assertIn('/path/to/warning1.md', paths)  # Newest wildfire smoke
        self.assertIn('/path/to/warning3.md', paths)  # Heat warning for Coast
        self.assertIn('/path/to/warning4.md', paths)  # Air quality for North

        # Check that excluded warnings are not present
        self.assertNotIn('/path/to/warning2.md', paths)  # Older wildfire smoke
        self.assertNotIn('/path/to/warning5.md', paths)  # No date

    def test_end_status_warnings(self):
        """Test handling of warnings with 'end' status"""
        # Mock today's date as 2025-06-13
        mock_today = datetime.date(2025, 6, 13)

        mock_headers = [
            # Recent "end" status warning (1 day old) - should be included
            {
                'entry': {
                    'path': '/path/to/end_warning1.md',
                    'title': 'Ending Heat Warning',
                    'type': 'heat',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 12),  # 1 day old
                    'location': 'Interior',
                },
                'raw_header': {
                    'title': 'Ending Heat Warning',
                    'type': 'heat',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 12),
                    'location': 'Interior',
                },
            },
            # Older "end" status warning (4 days old) - should be excluded
            {
                'entry': {
                    'path': '/path/to/end_warning2.md',
                    'title': 'Ending Wildfire Smoke Warning',
                    'type': 'wildfire_smoke',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 9),  # 4 days old
                    'location': 'Coast',
                },
                'raw_header': {
                    'title': 'Ending Wildfire Smoke Warning',
                    'type': 'wildfire_smoke',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 9),
                    'location': 'Coast',
                },
            },
        ]

        recent_warnings = select_recent_warnings(mock_headers, today_date=mock_today)

        # Only the 1-day old "end" status warning should be included
        self.assertEqual(len(recent_warnings), 1)
        self.assertEqual(recent_warnings[0]['path'], '/path/to/end_warning1.md')

        # Test with custom threshold (0 days) - no "end" status warnings should be included
        recent_warnings = select_recent_warnings(mock_headers, today_date=mock_today, end_status_threshold_days=0)
        self.assertEqual(len(recent_warnings), 0)

    def test_metro_vancouver_handling(self):
        """Test special handling for Metro Vancouver file"""
        # Mock today's date as 2025-06-13
        mock_today = datetime.date(2025, 6, 13)

        # Test case 1: Metro Vancouver without End status
        mock_headers = [
            # Metro Vancouver special file - should be included
            {
                'entry': {
                    'path': 'https://metrovancouver.org/air-quality',
                    'title': 'Metro Vancouver Air Quality',
                    'type': 'redirect',
                    'ice': 'Issue',
                },
                'raw_header': {
                    'title': 'Metro Vancouver Air Quality',
                    'type': 'redirect',
                    'ice': 'Issue',
                    'path': 'https://metrovancouver.org/air-quality',
                },
            },
            # Regular warning
            {
                'entry': {
                    'path': '/path/to/regular_warning.md',
                    'title': 'Regular Warning',
                    'type': 'heat',
                    'date': datetime.date(2025, 6, 12),
                    'location': 'Interior',
                    'ice': 'Issue',
                },
                'raw_header': {
                    'title': 'Regular Warning',
                    'type': 'heat',
                    'date': datetime.date(2025, 6, 12),
                    'location': 'Interior',
                    'ice': 'Issue',
                },
            },
        ]

        recent_warnings = select_recent_warnings(mock_headers, today_date=mock_today)

        # Both warnings should be included
        self.assertEqual(len(recent_warnings), 2)
        paths = [warning['path'] for warning in recent_warnings]
        self.assertIn('https://metrovancouver.org/air-quality', paths)
        self.assertIn('/path/to/regular_warning.md', paths)

        # Test case 2: Metro Vancouver with End status but recent (within threshold)
        mock_headers = [
            {
                'entry': {
                    'path': 'https://metrovancouver.org/air-quality',
                    'title': 'Metro Vancouver Air Quality',
                    'type': 'redirect',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 12),  # 1 day old
                },
                'raw_header': {
                    'title': 'Metro Vancouver Air Quality',
                    'type': 'redirect',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 12),
                    'path': 'https://metrovancouver.org/air-quality',
                },
            }
        ]

        recent_warnings = select_recent_warnings(mock_headers, today_date=mock_today)

        # Metro Vancouver warning should be included (only 1 day old)
        self.assertEqual(len(recent_warnings), 1)
        self.assertEqual(recent_warnings[0]['path'], 'https://metrovancouver.org/air-quality')

        # Test case 3: Metro Vancouver with End status and old (beyond threshold)
        mock_headers = [
            {
                'entry': {
                    'path': 'https://metrovancouver.org/air-quality',
                    'title': 'Metro Vancouver Air Quality',
                    'type': 'redirect',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 9),  # 4 days old
                },
                'raw_header': {
                    'title': 'Metro Vancouver Air Quality',
                    'type': 'redirect',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 9),
                    'path': 'https://metrovancouver.org/air-quality',
                },
            }
        ]

        recent_warnings = select_recent_warnings(mock_headers, today_date=mock_today)

        # Metro Vancouver warning should be excluded (4 days old with End status)
        self.assertEqual(len(recent_warnings), 0)

    def test_newest_per_community(self):
        """Test that we only keep the newest warning per community"""
        # Mock today's date as 2025-06-13
        mock_today = datetime.date(2025, 6, 13)

        mock_headers = [
            # Newest warning for Interior
            {
                'entry': {
                    'path': '/path/to/interior_newest.md',
                    'title': 'Newest Interior Warning',
                    'type': 'heat',
                    'date': datetime.date(2025, 6, 12),  # 1 day old
                    'location': 'Interior',
                    'ice': 'Issue',
                },
                'raw_header': {
                    'title': 'Newest Interior Warning',
                    'type': 'heat',
                    'date': datetime.date(2025, 6, 12),
                    'location': 'Interior',
                    'ice': 'Issue',
                },
            },
            # Older warning for Interior - should be excluded
            {
                'entry': {
                    'path': '/path/to/interior_older.md',
                    'title': 'Older Interior Warning',
                    'type': 'heat',
                    'date': datetime.date(2025, 6, 10),  # 3 days old
                    'location': 'Interior',
                    'ice': 'Issue',
                },
                'raw_header': {
                    'title': 'Older Interior Warning',
                    'type': 'heat',
                    'date': datetime.date(2025, 6, 10),
                    'location': 'Interior',
                    'ice': 'Issue',
                },
            },
            # Newest warning for Coast
            {
                'entry': {
                    'path': '/path/to/coast_newest.md',
                    'title': 'Newest Coast Warning',
                    'type': 'air_quality',
                    'date': datetime.date(2025, 6, 11),  # 2 days old
                    'location': 'Coast',
                    'ice': 'Issue',
                },
                'raw_header': {
                    'title': 'Newest Coast Warning',
                    'type': 'air_quality',
                    'date': datetime.date(2025, 6, 11),
                    'location': 'Coast',
                    'ice': 'Issue',
                },
            },
            # Older warning for Coast - should be excluded
            {
                'entry': {
                    'path': '/path/to/coast_older.md',
                    'title': 'Older Coast Warning',
                    'type': 'air_quality',
                    'date': datetime.date(2025, 6, 9),  # 4 days old
                    'location': 'Coast',
                    'ice': 'Issue',
                },
                'raw_header': {
                    'title': 'Older Coast Warning',
                    'type': 'air_quality',
                    'date': datetime.date(2025, 6, 9),
                    'location': 'Coast',
                    'ice': 'Issue',
                },
            },
        ]

        recent_warnings = select_recent_warnings(mock_headers, today_date=mock_today)

        # We should have exactly 2 warnings - the newest for each community
        self.assertEqual(len(recent_warnings), 2)

        paths = [warning['path'] for warning in recent_warnings]
        self.assertIn('/path/to/interior_newest.md', paths)
        self.assertIn('/path/to/coast_newest.md', paths)

        # Check that older warnings are not included
        self.assertNotIn('/path/to/interior_older.md', paths)
        self.assertNotIn('/path/to/coast_older.md', paths)

    def test_wildfire_warning_selection(self):
        """Test that only the most recent wildfire smoke warning is kept, regardless of location"""
        # Mock today's date as 2025-06-13
        mock_today = datetime.date(2025, 6, 13)

        mock_headers = [
            # Newest wildfire warning
            {
                'entry': {
                    'path': '/path/to/wildfire_newest.md',
                    'title': 'Newest Wildfire Warning',
                    'type': 'wildfire_smoke',
                    'date': datetime.date(2025, 6, 13),  # Today
                    'location': 'Interior',
                },
                'raw_header': {
                    'title': 'Newest Wildfire Warning',
                    'type': 'wildfire_smoke',
                    'date': datetime.date(2025, 6, 13),
                    'location': 'Interior',
                },
            },
            # Older wildfire warning from same location - should be excluded
            {
                'entry': {
                    'path': '/path/to/wildfire_older_same_loc.md',
                    'title': 'Older Wildfire Warning',
                    'type': 'wildfire_smoke',
                    'date': datetime.date(2025, 6, 12),  # 1 day old
                    'location': 'Interior',
                },
                'raw_header': {
                    'title': 'Older Wildfire Warning',
                    'type': 'wildfire_smoke',
                    'date': datetime.date(2025, 6, 12),
                    'location': 'Interior',
                },
            },
            # Older wildfire warning from different location - should still be excluded
            {
                'entry': {
                    'path': '/path/to/wildfire_older_diff_loc.md',
                    'title': 'Older Wildfire Warning Different Location',
                    'type': 'wildfire_smoke',
                    'date': datetime.date(2025, 6, 11),  # 2 days old
                    'location': 'Coast',
                },
                'raw_header': {
                    'title': 'Older Wildfire Warning Different Location',
                    'type': 'wildfire_smoke',
                    'date': datetime.date(2025, 6, 11),
                    'location': 'Coast',
                },
            },
        ]

        recent_warnings = select_recent_warnings(mock_headers, today_date=mock_today)

        # We should have exactly 1 warning - only the newest wildfire warning
        self.assertEqual(len(recent_warnings), 1)
        self.assertEqual(recent_warnings[0]['path'], '/path/to/wildfire_newest.md')


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
        """Test that end status warnings expire at the right time"""
        # Create a test warning with date 2025-06-10 (3 days before our test date)
        mock_headers = [
            {
                'entry': {
                    'path': '/path/to/expiring_warning.md',
                    'title': 'Expiring Warning',
                    'type': 'heat',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 10),  # 3 days before 2025-06-13
                    'location': 'Interior',
                },
                'raw_header': {
                    'title': 'Expiring Warning',
                    'type': 'heat',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 10),
                    'location': 'Interior',
                },
            }
        ]

        # Scenario 1: Test with BC time on June 13 (3 days since June 10)
        # The warning should be excluded as age = threshold
        bc_time_day3 = datetime.date(2025, 6, 13)
        warnings = select_recent_warnings(mock_headers, today_date=bc_time_day3)
        self.assertEqual(len(warnings), 0, 'Warning should be excluded when age = threshold')

        # Scenario 2: Test with BC time on June 12 (2 days since June 10)
        # The warning should be included as age < threshold
        bc_time_day2 = datetime.date(2025, 6, 12)
        warnings = select_recent_warnings(mock_headers, today_date=bc_time_day2)
        self.assertEqual(len(warnings), 1, 'Warning should be included when age < threshold')

    def test_timezone_edge_case(self):
        """Test warning selection using real timezone handling with mocked time"""
        # Create a warning that's the newest for its community
        mock_headers = [
            {
                'entry': {
                    'path': '/path/to/edge_case_warning.md',
                    'title': 'Edge Case Warning',
                    'type': 'air_quality',
                    'date': datetime.date(2025, 6, 9),  # From Coast community
                    'location': 'Coast',
                    'ice': 'Issue',
                },
                'raw_header': {
                    'title': 'Edge Case Warning',
                    'type': 'air_quality',
                    'date': datetime.date(2025, 6, 9),
                    'location': 'Coast',
                    'ice': 'Issue',
                },
            }
        ]

        # Test with BC date - warning should be included as it's the newest for its community
        with patch.object(construct_lists, 'get_today_in_bc_timezone', return_value=datetime.date(2025, 6, 13)):
            warnings = select_recent_warnings(mock_headers)  # No today_date, will use mocked function
            self.assertEqual(len(warnings), 1, 'Warning should be included as newest for community')

    def test_utc_vs_bc_timezone_bug(self):
        """Test specifically for the timezone bug scenario - warnings using correct timezone"""
        # Create a warning with status=end that's 3 days old
        mock_headers = [
            {
                'entry': {
                    'path': '/path/to/timezone_bug_warning.md',
                    'title': 'Timezone Bug Test Warning',
                    'type': 'heat',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 10),  # 3 days before June 13
                    'location': 'Interior',
                },
                'raw_header': {
                    'title': 'Timezone Bug Test Warning',
                    'type': 'heat',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 10),
                    'location': 'Interior',
                },
            }
        ]

        # Scenario: It's still June 12 in BC (late evening), but already June 13 in UTC
        # We want to ensure that we're using BC timezone for date calculations

        # Mock the datetime to return a fixed UTC time (June 13, 2025 05:00 AM UTC)
        # This corresponds to June 12, 2025 10:00 PM in BC (UTC-7)
        mock_utc_datetime = datetime.datetime(2025, 6, 13, 5, 0, 0, tzinfo=pytz.UTC)

        # Step 1: Using BC timezone via get_today_in_bc_timezone
        with patch('datetime.datetime') as mock_datetime:
            mock_datetime.now.return_value = mock_utc_datetime
            mock_datetime.side_effect = lambda *args, **kw: datetime.datetime(*args, **kw)

            # Call the actual function we're testing
            bc_today = get_today_in_bc_timezone()
            warnings = select_recent_warnings(mock_headers, today_date=bc_today)

            self.assertEqual(bc_today, datetime.date(2025, 6, 12), 'BC date should be June 12 even when UTC is June 13')

            # With BC date of June 12, the warning is 2 days old and should be included (age < threshold)
            self.assertEqual(
                len(warnings), 1, 'End status warning should be included when age < threshold in BC timezone'
            )


if __name__ == '__main__':
    unittest.main()
