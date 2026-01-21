import datetime
import unittest
import pytz
from unittest.mock import patch

from construct_lists import select_recent_warnings, get_today_in_bc_timezone, process_warning_entries


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
            # PM2.5 warning for Coast - should be included as newest for this community
            {
                'entry': {
                    'path': '/path/to/warning3.md',
                    'title': 'PM2.5 Warning',
                    'type': 'fine_pm',
                    'ice': 'issue',
                    'date': datetime.date(2025, 6, 10),
                    'location': 'Coast',
                },
                'raw_header': {
                    'title': 'PM2.5 Warning',
                    'type': 'fine_pm',
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
        recent_warnings = select_recent_warnings(mock_headers, mock_today)

        # We should have 3 warnings (newest wildfire + one for each community)
        self.assertEqual(len(recent_warnings), 3)

        # Check that the right warnings were selected
        paths = [warning['path'] for warning in recent_warnings]
        self.assertIn('/path/to/warning1.md', paths)  # Newest wildfire smoke
        self.assertIn('/path/to/warning3.md', paths)  # PM2.5 warning for Coast
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
                    'title': 'Ending PM2.5 Warning',
                    'type': 'fine_pm',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 12),  # 1 day old
                    'location': 'Interior',
                },
                'raw_header': {
                    'title': 'Ending PM2.5 Warning',
                    'type': 'fine_pm',
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

        recent_warnings = select_recent_warnings(mock_headers, mock_today)

        # Only the 1-day old "end" status warning should be included
        self.assertEqual(len(recent_warnings), 1)
        self.assertEqual(recent_warnings[0]['path'], '/path/to/end_warning1.md')

        # Test with custom threshold (0 days) - no "end" status warnings should be included
        recent_warnings = select_recent_warnings(mock_headers, mock_today, end_status_threshold_days=0)
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
                    'type': 'fine_pm',
                    'date': datetime.date(2025, 6, 12),
                    'location': 'Interior',
                    'ice': 'Issue',
                },
                'raw_header': {
                    'title': 'Regular Warning',
                    'type': 'fine_pm',
                    'date': datetime.date(2025, 6, 12),
                    'location': 'Interior',
                    'ice': 'Issue',
                },
            },
        ]

        recent_warnings = select_recent_warnings(mock_headers, mock_today)

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

        recent_warnings = select_recent_warnings(mock_headers, mock_today)

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

        recent_warnings = select_recent_warnings(mock_headers, mock_today)

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
                    'type': 'fine_pm',
                    'date': datetime.date(2025, 6, 12),  # 1 day old
                    'location': 'Interior',
                    'ice': 'Issue',
                },
                'raw_header': {
                    'title': 'Newest Interior Warning',
                    'type': 'fine_pm',
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
                    'type': 'fine_pm',
                    'date': datetime.date(2025, 6, 10),  # 3 days old
                    'location': 'Interior',
                    'ice': 'Issue',
                },
                'raw_header': {
                    'title': 'Older Interior Warning',
                    'type': 'fine_pm',
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

        recent_warnings = select_recent_warnings(mock_headers, mock_today)

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

        recent_warnings = select_recent_warnings(mock_headers, mock_today)

        # We should have exactly 1 warning - only the newest wildfire warning
        self.assertEqual(len(recent_warnings), 1)
        self.assertEqual(recent_warnings[0]['path'], '/path/to/wildfire_newest.md')

    def test_warning_expiry_at_bc_midnight(self):
        """Test that end status warnings expire at the right time"""
        # Create a test warning with date 2025-06-10 (3 days before our test date)
        mock_headers = [
            {
                'entry': {
                    'path': '/path/to/expiring_warning.md',
                    'title': 'Expiring Warning',
                    'type': 'fine_pm',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 10),  # 3 days before 2025-06-13
                    'location': 'Interior',
                },
                'raw_header': {
                    'title': 'Expiring Warning',
                    'type': 'fine_pm',
                    'ice': 'End',
                    'date': datetime.date(2025, 6, 10),
                    'location': 'Interior',
                },
            }
        ]

        # Scenario 1: Test with BC time on June 13 (3 days since June 10)
        # The warning should be excluded as age = threshold
        bc_time_day3 = datetime.date(2025, 6, 13)
        warnings = select_recent_warnings(mock_headers, bc_time_day3)
        self.assertEqual(len(warnings), 0, 'Warning should be excluded when age = threshold')

        # Scenario 2: Test with BC time on June 12 (2 days since June 10)
        # The warning should be included as age < threshold
        bc_time_day2 = datetime.date(2025, 6, 12)
        warnings = select_recent_warnings(mock_headers, bc_time_day2)
        self.assertEqual(len(warnings), 1, 'Warning should be included when age < threshold')


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


class TestProcessWarningEntries(unittest.TestCase):
    """Tests the value selection logic for final rendering."""

    def test_type_passthrough(self):
        """Test output values that are passed through from the original warning entry."""
        test_date = datetime.date(2025, 12, 11)
        input_warnings = [
            {
                'type': 'wildfire_smoke',
                'path': 'N/A',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'An air quality warning',
                'override_title': False,
                'pollutant': 'N/A',
                'burn_restrictions': 0,
                'bylaw': False,
            }
        ]
        expected_processed_warnings = [
            {'type': 'wildfire_smoke', 'path': 'N/A', 'location': 'My City', 'status': 'ISSUE', 'date': test_date}
        ]

        actual_processed_warnings = process_warning_entries(input_warnings)

        self.assertEqual(expected_processed_warnings[0]['type'], actual_processed_warnings[0]['type'])
        self.assertEqual(expected_processed_warnings[0]['path'], actual_processed_warnings[0]['path'])
        self.assertEqual(expected_processed_warnings[0]['location'], actual_processed_warnings[0]['location'])
        self.assertEqual(expected_processed_warnings[0]['status'], actual_processed_warnings[0]['status'])
        self.assertEqual(expected_processed_warnings[0]['date'], actual_processed_warnings[0]['date'])

    def test_derived_title(self):
        """Tests that the title responds correctly to the various inputs."""
        test_date = datetime.date(2025, 12, 11)
        input_warnings = [
            {
                # Overridden title
                'type': 'wildfire_smoke',
                'path': 'N/A',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'overridden title',
                'override_title': True,
                'pollutant': 'N/A',
                'burn_restrictions': 0,
                'bylaw': False,
            },
            {
                # Not overridden title
                'type': 'wildfire_smoke',
                'path': 'N/A',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'overridden title',
                'override_title': False,
                'pollutant': 'N/A',
                'burn_restrictions': 0,
                'bylaw': False,
            },
            {
                # Metro Vancouver case
                'type': 'redirect',
                'path': 'vancouver dot ca',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'An air quality warning',
                'pollutant': 'N/A',
                'burn_restrictions': 0,
                'bylaw': False,
            },
            {
                # Wildfire smoke case
                'type': 'wildfire_smoke',
                'path': 'N/A',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'An air quality warning',
                'pollutant': 'N/A',
                'burn_restrictions': 0,
                'bylaw': False,
            },
            {
                # Pollution prevention case
                'type': 'pollution_prevention',
                'path': 'N/A',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'An air quality warning',
                'pollutant': 'N/A',
                'burn_restrictions': 0,
                'bylaw': False,
            },
            {
                # PM25 case
                'type': 'local_emissions',
                'path': 'N/A',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'An air quality warning',
                'pollutant': 'PM25',
                'burn_restrictions': 0,
                'bylaw': False,
            },
            {
                # O3 case
                'type': 'local_emissions',
                'path': 'N/A',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'An air quality warning',
                'pollutant': 'O3',
                'burn_restrictions': 0,
                'bylaw': False,
            },
            {
                # PM10 case
                'type': 'local_emissions',
                'path': 'N/A',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'An air quality warning',
                'pollutant': 'PM10',
                'burn_restrictions': 0,
                'bylaw': False,
            },
            {
                # PM25 & PM10 case
                'type': 'local_emissions',
                'path': 'N/A',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'An air quality warning',
                'pollutant': 'PM25 & PM10',
                'burn_restrictions': 0,
                'bylaw': False,
            },
            {
                # Invalid Type
                'type': 'invalid',
                'path': 'N/A',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'An air quality warning',
                'override_title': False,
                'pollutant': 'PM25 & PM10',
                'burn_restrictions': 0,
                'bylaw': False,
            },
            {
                # Invalid Pollutant
                'type': 'local_emissions',
                'path': 'N/A',
                'location': 'My City',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'An air quality warning',
                'pollutant': 'invalid',
                'burn_restrictions': 0,
                'bylaw': False,
            },
        ]
        expected_titles = [
            'overridden title',  # Overridden title
            'Wildfire Smoke',  # Not overridden title
            'Air Quality Warning',  # Metro Vancouver case
            'Wildfire Smoke',  # Wildfire smoke case
            'Pollution Prevention Notice',  # Pollution prevention case
            'Fine particulate matter',  # PM25 case
            'Ground level ozone',  # O3 case
            'Dust',  # PM10 case
            'Fine particulate matter and Dust',  # PM25 & PM10 case
            'N/A',  # Invalid Type
            'N/A',  # Invalid Pollutant
        ]

        actual_processed_warnings = process_warning_entries(input_warnings)

        self.assertEqual(expected_titles[0], actual_processed_warnings[0]['title'])  # Overridden title
        self.assertEqual(expected_titles[1], actual_processed_warnings[1]['title'])  # Not overridden title
        self.assertEqual(expected_titles[2], actual_processed_warnings[2]['title'])  # Metro Vancouver case
        self.assertEqual(expected_titles[3], actual_processed_warnings[3]['title'])  # PM25 case
        self.assertEqual(expected_titles[4], actual_processed_warnings[4]['title'])  # Pollution prevention case
        self.assertEqual(expected_titles[5], actual_processed_warnings[5]['title'])  # O3 case
        self.assertEqual(expected_titles[6], actual_processed_warnings[6]['title'])  # PM10 case
        self.assertEqual(expected_titles[7], actual_processed_warnings[7]['title'])  # PM25 & PM10 case
        self.assertEqual(expected_titles[8], actual_processed_warnings[8]['title'])  # Invalid Type
        self.assertEqual(expected_titles[9], actual_processed_warnings[9]['title'])  # Invalid Pollutant

    def test_mandatory_action(self):
        test_date = datetime.date(2025, 12, 11)
        input_warnings = [
            {
                # Burn restrictions overrides bylaw
                'type': 'wildfire_smoke',
                'path': 'N/A',
                'location': 'Burnaby',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'burn restrictions',
                'override_title': False,
                'pollutant': 'N/A',
                'burn_restrictions': 1,
                'bylaw': False,
            },
            {
                # Bylaw overrides location negatively
                'type': 'wildfire_smoke',
                'path': 'N/A',
                'location': 'Duncan',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'burn restrictions',
                'override_title': False,
                'pollutant': 'N/A',
                'burn_restrictions': 0,
                'bylaw': False,
            },
            {
                # Bylaw overrides location postively
                'type': 'wildfire_smoke',
                'path': 'N/A',
                'location': 'Vernon',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'burn restrictions',
                'override_title': False,
                'pollutant': 'N/A',
                'burn_restrictions': 0,
                'bylaw': True,
            },
            {
                # Location has bylaw, and it is not overridden
                'type': 'wildfire_smoke',
                'path': 'N/A',
                'location': 'Duncan',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'burn restrictions',
                'override_title': False,
                'pollutant': 'N/A',
                'burn_restrictions': 0,
                # 'bylaw': True,  I left this here for illustrative purposes.
            },
            {
                # Location does not have bylaw, and it is not overridden
                'type': 'wildfire_smoke',
                'path': 'N/A',
                'location': 'Vernon',
                'ice': 'ISSUE',
                'date': test_date,
                'title': 'burn restrictions',
                'override_title': False,
                'pollutant': 'N/A',
                'burn_restrictions': 0,
                # 'bylaw': False,  I left this here for illustrative purposes.
            },
        ]
        expected_mandatory_actions = [
            'Yes',  # Burn restrictions overrides bylaw
            'No',  # Bylaw overrides location negatively
            'Yes',  # Bylaw overrides location postively
            'Yes',  # Location has bylaw, and it is not overridden
            'No',  # Location does not have bylaw, and it is not overridden
        ]

        actual_processed_warnings = process_warning_entries(input_warnings)

        # Burn restrictions overrides bylaw
        self.assertEqual(expected_mandatory_actions[0], actual_processed_warnings[0]['mandatoryAction'])
        # Bylaw overrides location negatively
        self.assertEqual(expected_mandatory_actions[1], actual_processed_warnings[1]['mandatoryAction'])
        # Bylaw overrides location postively
        self.assertEqual(expected_mandatory_actions[2], actual_processed_warnings[2]['mandatoryAction'])
        # Location has bylaw, and it is not overridden
        self.assertEqual(expected_mandatory_actions[3], actual_processed_warnings[3]['mandatoryAction'])
        # Location does not have bylaw, and it is not overridden
        self.assertEqual(expected_mandatory_actions[4], actual_processed_warnings[4]['mandatoryAction'])

    def test_empty_collection(self):
        input_warnings = []

        actual_processed_warning = process_warning_entries(input_warnings)

        self.assertIsInstance(actual_processed_warning, list)
        self.assertEqual(len(actual_processed_warning), 0)


if __name__ == '__main__':
    unittest.main()
