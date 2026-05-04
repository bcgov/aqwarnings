# Archiving Warnings

Annually, historic warnings are archived to reduce the build and deploy time of the website while still retaining the ability for the public to view previous warnings.

We accomplish this by:
- converting warnings (.md) into rendered "static" warnings (.html)
- generating a separate metadata file (.yml)
- storing the original generated warnings (.md) in the `[archive/][/archive/]` folder if we ever need to rener them

## Manual steps

We developed scripts (work in progress) to help, the steps are:

1. Download a zip of the latest version of the deployed site from the `gh-pages` branch

2. Copy all the warnings from the download that start with the year (e.g., 2025) from the `warnings/` folder to the **current working repository** into the `frontend/warnings/` folder.

3. Run `extract_yaml_to_files()` to create separate yml files:

   Note: this will try to process all files with a `.md` extension in a directory

4. Run `update_html_and_yaml_files(".", "warnings", "path/to/bootstrap.min/css)` to:
    - Update the path of the css used to render the html file
    - Add the html file path to the corresponding yml file
    - Before you start, identify the minified bootstrap css file that it will use, for example 
      `..\assets\bootstrap-2025-2d2002fe1dd6c3772601408f829c1cf7.min.css`

_Why do we do this? Because quarto adds a hash to the minifed bootstrap css every time it builds the site. Unfortunately, the path for the css file is to a folder ("`site_libs/`") produced by the rendering process which we can't write to. As a result, we can't just add the previous minified css to the same path and have it work, we need to change the path. The pattern of `assets/` is used in Quarto so we feel this is an acceptable workaround._

5. Move the `.md` versions of the warnings that start with the year (e.g., 2025) to the `/archive/` folder. 

6. Commit the changes to a branch, open a PR and review the PR preview of the site as usual. Some things to look for during review (work in progress):
    - Go to the "historical warnings" page in the pr `https://aqwarnings.gov.bc.ca/pr-preview/pr-[###]/warnings.html`, run a link checker report or spot check to ensure warnings show up as clickable
    - Spot-check a few of the archived warnings render correctly, they should appear just as before, with the map embedded, logos and styles showing up. If they don't that points to an issue with the path to the minified bootstrap css file
    - Confirm the number of files you moved to the `archive/` corresponds to the number of files added to `warnings/` (# files moved to archive * 2 = # files added to warnings) 

