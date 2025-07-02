import datetime
import pytz
import os
import re
from typing import List, Dict, Any, Optional

import yaml

"""
This script generates a file as part of the pre-render process for quarto site generation

RECENTS_FILE_NAME will contain a yaml list of files with a date attribute newer than RECENT_THRESHOLD_DAYS
Special handling is applied based on warning type and status.

This is then used in custom listings within the qmd markup
"""

# editable -- consider "end" status warnings less than END_STATUS_THRESHOLD_DAYS days old to be "recent"
END_STATUS_THRESHOLD_DAYS = 3
RECENTS_FILE_NAME = '_recent_warnings.yaml'
METRO_VANCOUVER_FILENAME = '_metro_vancouver.yml'

# globals. do not modify.
_quarto_input_files = os.getenv('QUARTO_PROJECT_INPUT_FILES')
INPUT_FILES = _quarto_input_files.split('\n') if _quarto_input_files is not None else []
INPUT_FILES.append(f'warnings/{METRO_VANCOUVER_FILENAME}')  # Ensure Metro Vancouver file is included

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
        # Check if file exists
        if not os.path.exists(file_path):
            # Try with working directory prefix
            alt_path = os.path.join(os.getcwd(), file_path)
            if os.path.exists(alt_path):
                file_path = alt_path
            else:
                return None

        with open(file_path, 'r') as file:
            contents = file.read()
            match = HEADER_REGEX.search(contents)
            if match:
                doc_preamble = match.group(1)
                parsed_header = yaml.safe_load(doc_preamble)
                # Prepare entry from header
                # For redirect types, use the path from the YAML file if available
                path_to_use = parsed_header.get('path') if parsed_header.get('type') == 'redirect' else file_path

                entry_from_header = {
                    'path': path_to_use,
                    'title': parsed_header.get('title', 'No Title'),
                    'type': parsed_header.get('type', 'N/A'),
                    'ice': parsed_header.get('ice', 'N/A'),
                    'date': parsed_header.get('date'),
                    'location': parsed_header.get('location'),
                }

                return {'entry': entry_from_header, 'raw_header': parsed_header}
            else:
                # For YML files, try loading directly with yaml
                if file_path.endswith('.yml'):
                    try:
                        parsed_header = yaml.safe_load(contents)
                        if isinstance(parsed_header, dict):
                            # For redirect types, use the path from the YAML file if available
                            path_to_use = (
                                parsed_header.get('path') if parsed_header.get('type') == 'redirect' else file_path
                            )

                            entry_from_header = {
                                'path': path_to_use,
                                'title': parsed_header.get('title', 'No Title'),
                                'type': parsed_header.get('type', 'N/A'),
                                'ice': parsed_header.get('ice', 'N/A'),
                                'date': parsed_header.get('date'),
                                'location': parsed_header.get('location'),
                            }

                            return {'entry': entry_from_header, 'raw_header': parsed_header}
                    except Exception as e:
                        print(f'Error loading YAML directly: {e}')
    except Exception as e:
        print(f'Error processing file {file_path}: {e}')

    return None


def select_recent_warnings(
    header_entries: List[Dict[str, Any]], today_date=None, end_status_threshold_days: int = END_STATUS_THRESHOLD_DAYS
) -> List[Dict[str, Any]]:
    """
    Select recent warnings based on type, community, and status.

    Args:
        header_entries: List of dictionaries containing header metadata
        today_date: Optional date to use for comparison (for testing)
        end_status_threshold_days: Number of days to consider "end" status warnings as recent

    Returns:
        List of warnings that meet the criteria for "recent" status

    Selection logic:
    1. Handle Metro Vancouver file specially
    2. For wildfire smoke warnings: keep only the most recent
    3. For other warnings: group by community and keep newest per community
    4. For "end" status warnings: only show if less than end_status_threshold_days old
    """
    recent_warnings = []
    today = today_date or get_today_in_bc_timezone()

    # Special handling for Metro Vancouver
    metro_vancouver_entry = None

    # Group warnings by type and community
    wildfire_warnings = []
    community_warnings = {}  # {community: [warnings]}
    for header_data in header_entries:
        if not header_data:
            continue

        entry = header_data['entry']
        parsed_header = header_data['raw_header']
        file_path = entry.get('path', '')

        # Special handling for Metro Vancouver file
        # Check either by filename or by type=redirect
        if os.path.basename(file_path) == METRO_VANCOUVER_FILENAME or parsed_header.get('type') == 'redirect':
            metro_vancouver_entry = entry
            # Add date if available or use today's date for age calculation
            if parsed_header.get('date'):
                entry['_date'] = parsed_header['date']
                entry['_age'] = (today - parsed_header['date']).days
            else:
                entry['_date'] = today
                entry['_age'] = 0
            continue

        if not parsed_header.get('date'):
            continue

        # Calculate age of the warning
        age = (today - parsed_header['date']).days

        # Store the warning based on type
        warning_type = parsed_header.get('type', '').lower()
        location = parsed_header.get('location', 'unknown')

        # Add age to the entry for sorting
        entry['_age'] = age
        entry['_date'] = parsed_header['date']

        if warning_type == 'wildfire_smoke':
            wildfire_warnings.append(entry)
        else:
            if location not in community_warnings:
                community_warnings[location] = []
            community_warnings[location].append(entry)

    # Process wildfire warnings - keep only the newest one
    if wildfire_warnings:
        # Sort by date in descending order (newest first), then by age in ascending order
        newest_wildfire = sorted(wildfire_warnings, key=lambda w: (-w['_date'].toordinal(), w['_age']))[0]
        ice_status = newest_wildfire.get('ice', '')

        if ice_status.lower() == 'end':
            # Only include "end" status warnings if they're strictly less than threshold days old
            if newest_wildfire['_age'] < end_status_threshold_days:
                recent_warnings.append(newest_wildfire)
        else:
            recent_warnings.append(newest_wildfire)

    # Process community warnings - keep newest per community
    for warnings in community_warnings.values():
        if warnings:
            # Sort by date in descending order (newest first), then by age in ascending order
            newest_warning = sorted(warnings, key=lambda w: (-w['_date'].toordinal(), w['_age']))[0]
            ice_status = newest_warning.get('ice', '')

            if ice_status.lower() == 'end':
                # Only include "end" status warnings if they're strictly less than threshold days old
                if newest_warning['_age'] < end_status_threshold_days:
                    recent_warnings.append(newest_warning)
            else:
                recent_warnings.append(newest_warning)

    # Process Metro Vancouver entry if present, going directly to the "ice = End" check
    if metro_vancouver_entry:
        ice_status = metro_vancouver_entry.get('ice', '')

        if ice_status.lower() == 'end':
            # Only include "end" status warnings if they're strictly less than threshold days old
            if metro_vancouver_entry['_age'] < end_status_threshold_days:
                recent_warnings.append(metro_vancouver_entry)
        else:
            recent_warnings.append(metro_vancouver_entry)

    # Remove temporary fields used for sorting
    for warning in recent_warnings:
        warning.pop('_age', None)
        warning.pop('_date', None)

    return recent_warnings


def process_input_files():
    """Process all input files and extract headers"""
    header_entries = []

    for file_path in INPUT_FILES:
        if not file_path:
            continue  # Skip empty input lines

        header_data = extract_header_from_file(file_path)
        if header_data:
            header_entries.append(header_data)

    return header_entries


def main():
    """Main function to run the script"""
    # Extract headers from all input files
    header_entries = process_input_files()

    # Select recent warnings
    recent_warnings = select_recent_warnings(header_entries)

    # Write output to file
    with open(RECENTS_FILE_NAME, 'w') as output_file:
        yaml.safe_dump(recent_warnings, output_file)


if __name__ == '__main__':
    main()
