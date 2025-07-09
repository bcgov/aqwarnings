import datetime
import pytz
import os
import re
from typing import List, Dict, Any, Optional

import yaml

"""
This script generates a file as part of the pre-render process for quarto site generation

RECENTS_FILE_NAME will contain a yaml list of files with a date attribute newer than RECENT_THRESHOLD_DAYS

This is then used in custom listings within the qmd markup
"""

# editable -- consider posts less than RECENT_THRESHOLD_DAYS days old to be "recent"
# Hardcoded below to 1 day for smoky skies bulletins with ice = Issue metadata
RECENT_THRESHOLD_DAYS = 5
RECENTS_FILE_NAME = '_recent_warnings.yaml'

# globals. do not modify.
_quarto_input_files = os.getenv('QUARTO_PROJECT_INPUT_FILES')
INPUT_FILES = _quarto_input_files.split('\n') if _quarto_input_files is not None else []
HEADER_REGEX = re.compile('^---\n((.*\n)+)---\n', re.MULTILINE)


def get_today_in_bc_timezone():
    """Get the current date in British Columbia timezone (Pacific Time)"""
    bc_tz = pytz.timezone('America/Vancouver')
    now_in_bc = datetime.datetime.now(pytz.utc).astimezone(bc_tz)
    return now_in_bc.date()


def extract_header_from_file(file_path: str) -> Optional[Dict[str, Any]]:
    """
    Extract YAML header from a file and return entry with metadata.

    Args:
        file_path: Path to the file to parse

    Returns:
        Dictionary with metadata or None if no header found
    """
    try:
        with open(file_path, 'r') as file:
            contents = file.read()
            match = HEADER_REGEX.search(contents)
            if match:
                doc_preamble = match.group(1)
                parsed_header = yaml.safe_load(doc_preamble)
                # Prepare entry from header
                entry_from_header = {
                    'path': file_path,
                    'title': parsed_header.get('title', 'No Title'),
                    'type': parsed_header.get('type', 'N/A'),
                    'ice': parsed_header.get('ice', 'N/A'),
                    'date': parsed_header.get('date'),
                    'location': parsed_header.get('location'),
                }

                return {'entry': entry_from_header, 'raw_header': parsed_header}
    except Exception as e:
        print(f'Error processing file {file_path}: {e}')

    return None


def select_recent_warnings(
    header_entries: List[Dict[str, Any]], today_date=None, recent_threshold_days: int = RECENT_THRESHOLD_DAYS
) -> List[Dict[str, Any]]:
    """
    Args:
        header_entries: List of dictionaries containing header metadata
        today_date: Optional date to use for comparison (for testing)
        recent_threshold_days: Number of days to consider recent

    Returns:
        List of warnings that meet the criteria for "recent" status

    Normally I don't like to include arguments specifically for testing, but the
    freezegun testing library doesn't interact with timezones correctly, which
    introduces false failures.
    """
    recent_warnings = []
    today = today_date or get_today_in_bc_timezone()

    for header_data in header_entries:
        if not header_data:
            continue

        entry = header_data['entry']
        parsed_header = header_data['raw_header']

        if not parsed_header.get('date'):
            continue

        skip = False

        # Special handling for wildfire_smoke warnings with ice=issue
        # As per WARNING_SELECTION_LOGIC.md flowchart, we exclude if age >= 1 day
        if parsed_header.get('type', '').lower() == 'wildfire_smoke':
            if parsed_header.get('ice', '').lower() == 'issue':
                age = (today - parsed_header['date']).days
                threshold = 1

                # Skip if age is >= threshold (1+ days old)
                if age >= threshold:
                    skip = True

        if not skip:
            age = (today - parsed_header['date']).days
            if age < recent_threshold_days:
                recent_warnings.append(entry)

    return recent_warnings


def process_input_files():
    """Process all input files and extract headers"""
    header_entries = []

    for file_path in INPUT_FILES:
        if not file_path:
            continue  # Skip empty input lines

        print(f'Processing input file: {file_path}')
        header_data = extract_header_from_file(file_path)
        if header_data:
            header_entries.append(header_data)

    return header_entries


def main():
    """Main function to run the script"""
    print(yaml.safe_dump(INPUT_FILES))

    # Extract headers from all input files
    header_entries = process_input_files()

    # Select recent warnings
    recent_warnings = select_recent_warnings(header_entries)

    # Write output to file
    with open(RECENTS_FILE_NAME, 'w') as output_file:
        yaml.safe_dump(recent_warnings, output_file)


if __name__ == '__main__':
    main()
