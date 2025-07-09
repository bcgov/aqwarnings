import os


"""
This script removes the whitespace preventing the figure div from rendering as part of a pre-render process for quarto site generation

SEARCH_TEXT contains

REPLACE_TEXT contains 

"""

# editable
SEARCH_TEXT = '::: {layout-ncol= '
REPLACE_TEXT = '::: {layout-ncol='

# globals. do not modify.
_quarto_input_files = os.getenv('QUARTO_PROJECT_INPUT_FILES')
INPUT_FILES = _quarto_input_files.split('\n') if _quarto_input_files is not None else []


def process_input_files():
    for f in INPUT_FILES:
        if not f:
            continue  # skip empty input lines

        print('processing input file: {file}'.format(file=f))

        # Open file in read only mode
        with open(f, 'r') as file:
            # Read the content of the file and store in a new variable
            data = file.read()

            # Search and replace the text
            data = data.replace(SEARCH_TEXT, REPLACE_TEXT)

            # Open file in text in write only mode to write replaced content
            with open(f, 'w') as file:
                # Write the replaced data in the file
                file.write(data)


process_input_files()
