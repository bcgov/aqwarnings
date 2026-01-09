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

The necessary format of the YAML header in the markdown file, or the YAML file is as follows:

---
date: REQUIRED ISO8601 date
ice: REQUIRED string - "Issue" or "Continue" or "End"
location: REQUIRED string
type: REQUIRED - "redirect" or "wildfire_smoke" or "local_emissions"
path: OPTIONAL - the URL for the redirect link. Only used if type is "redirect"
title: OPTIONAL string
overrideTitle: OPTIONAL boolean - This will force the rendered Title to be the provided title
bylaw: OPTIONAL boolean - if present, this will override other mandatory action logic, *except* burn restrictions.
burnRestrictions: OPTIONAL integer
pollutant: REQUIRED if type is local_emissions, string - "PM10" or "PM25" or "O3" or "PM25 & PM10"
---

Other parameters and values will be ignored by this script.

"""

# editable -- consider "end" status warnings less than END_STATUS_THRESHOLD_DAYS days old to be "recent"
END_STATUS_THRESHOLD_DAYS = 3
RECENTS_FILE_NAME = '_recent_warnings.yaml'
METRO_VANCOUVER_FILENAME = '_metro_vancouver.yml'

# Editable - Input Values to match within the YAML for determining the warning title. Useful if you want to change the
# capitalization or spelling in the yaml header.
REDIRECT_TYPE = 'redirect'
WILDFIRE_SMOKE_TYPE = 'wildfire_smoke'
LOCAL_EMISSIONS_TYPE = 'local_emissions'
PM25_POLLUTANT = 'PM25'
O3_POLLUTANT = 'O3'
PM10_POLLUTANT = 'PM10'
PM25_AND_PM10_POLLUTANT = 'PM25 & PM10'
# Locations where local bylaws affect Mandatory Action. This can be overridden with the 'blylaw' key.
MANDATORY_ACTION_LOCATIONS = ['Burns Lake', 'Duncan', 'Houston', 'Prince George', 'Smithers', 'Valemount']

# Editable - Display strings for easy modification without developer involvement
METRO_VAN_LINK_TITLE = 'Air Quality Warning'
WILDFIRE_SMOKE_TITLE = 'Wildfire Smoke'
PM_25_TITLE = 'Fine particulate matter'
O3_TITLE = 'Ground level ozone'
PM10_TITLE = 'Dust'
PM25_AND_PM10_TITLE = 'Fine particulate matter and Dust'
DEFAULT_TITLE = 'N/A'  # When the title cannot be derived from the provided values.
MANDATORY_ACTION_YES = 'Yes'
MANDATORY_ACTION_NO = 'No'

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
    parsed_header = None
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
            else:
                # For YML files, try loading directly with yaml
                if file_path.endswith('.yml') or file_path.endswith('.yaml'):
                    try:
                        parsed_header = yaml.safe_load(contents)
                    except Exception as e:
                        print(f'Error loading YAML directly: {e}')
    except Exception as e:
        print(f'Error processing file {file_path}: {e}')

    if parsed_header is not None:
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
            'pollutant': parsed_header.get('pollutant', 'N/A'),
            'burn_restrictions': parsed_header.get('burnRestrictions', 0),
            'bylaw': parsed_header.get('bylaw', None),
            'override_title': parsed_header.get('overrideTitle', False),
        }

        return {'entry': entry_from_header, 'raw_header': parsed_header}
    else:
        return None


def select_recent_warnings(
    header_entries: List[Dict[str, Any]],
    today: datetime.date,
    end_status_threshold_days: int = END_STATUS_THRESHOLD_DAYS,
) -> List[Dict[str, Any]]:
    """
    Select recent warnings based on type, community, and status.

    Args:
        header_entries: List of dictionaries containing header metadata
        today: Date to use for comparison
        end_status_threshold_days: Number of days to consider "end" status warnings as recent

    Returns:
        List of warnings that meet the criteria for "recent" status

    Selection logic:
    1. Handle Metro Vancouver file specially
    2. For wildfire smoke warnings: keep only the most recent
    3. For other warnings: group by community and keep newest per community
    4. For "end" status warnings: only show if less than end_status_threshold_days old

    The date parameter is included the date as a parameter to keep this as a pure function, making it easier to test.
    """
    recent_warnings = []

    # Special handling for Metro Vancouver
    metro_vancouver_entry = None

    # Group warnings by type and community
    wildfire_warnings = []
    community_warnings = {}  # { name_of_community: [warnings] }
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


def process_warning_entries(warnings: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Derive the final values to be displayed for the recent warnings list.

    Args:
        warnings: a list of the warnings to process.

    Returns:
        List of warnings with their final display values.
    """
    processed_warnings = []

    for warning in warnings:
        processed_warning = {}

        # Values that get passed through:
        processed_warning['type'] = warning['type']
        processed_warning['path'] = warning['path']
        processed_warning['location'] = warning['location']
        processed_warning['status'] = warning['ice']  # ICE - Issue, Continue, End.
        processed_warning['date'] = warning['date']

        # Determine the display title based on the warning type.
        if 'override_title' in warning and warning['override_title']:
            # Allow the user to override automatic titling.
            processed_warning['title'] = warning['title']
        elif warning['type'] == REDIRECT_TYPE:
            # This will render a link to the given path. It's only used for Metro Vancouver presently.
            processed_warning['title'] = METRO_VAN_LINK_TITLE
        elif warning['type'] == WILDFIRE_SMOKE_TYPE:
            processed_warning['title'] = WILDFIRE_SMOKE_TITLE
        elif warning['type'] == LOCAL_EMISSIONS_TYPE:
            if 'pollutant' in warning:
                if warning['pollutant'] == PM25_POLLUTANT:
                    processed_warning['title'] = PM_25_TITLE
                elif warning['pollutant'] == O3_POLLUTANT:
                    processed_warning['title'] = O3_TITLE
                elif warning['pollutant'] == PM10_POLLUTANT:
                    processed_warning['title'] = PM10_TITLE
                elif warning['pollutant'] == PM25_AND_PM10_POLLUTANT:
                    processed_warning['title'] = PM25_AND_PM10_TITLE
                else:
                    processed_warning['title'] = DEFAULT_TITLE
            else:
                processed_warning['title'] = DEFAULT_TITLE
        else:
            processed_warning['title'] = DEFAULT_TITLE

        # Determine the display value for the Mandatory Action column
        if warning['burn_restrictions'] > 0:
            # Any burn restrictions will override local bylaws.
            processed_warning['mandatoryAction'] = MANDATORY_ACTION_YES
        elif 'bylaw' in warning:
            # If the bylaw key is present, allow it to override the automatic location list.
            if warning['bylaw']:
                processed_warning['mandatoryAction'] = MANDATORY_ACTION_YES
            else:
                processed_warning['mandatoryAction'] = MANDATORY_ACTION_NO
        elif warning['location'] in MANDATORY_ACTION_LOCATIONS:
            processed_warning['mandatoryAction'] = MANDATORY_ACTION_YES
        else:
            processed_warning['mandatoryAction'] = MANDATORY_ACTION_NO

        processed_warnings.append(processed_warning)

    return processed_warnings


def main():
    """Main function to run the script"""
    # Extract headers from all input files
    header_entries = process_input_files()

    # Select recent warnings
    unprocessed_recent_warnings = select_recent_warnings(header_entries, get_today_in_bc_timezone())

    # Process the warnings into their final form for display.
    processed_recent_warnings = process_warning_entries(unprocessed_recent_warnings)

    # Write output to file
    with open(RECENTS_FILE_NAME, 'w') as output_file:
        yaml.safe_dump(processed_recent_warnings, output_file)


if __name__ == '__main__':
    main()
