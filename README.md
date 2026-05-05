[![Apache 2.0 License](https://img.shields.io/github/license/bcgov/nr-epd-aq-statements.svg)](/LICENSE)
[![Creative Commons BY 4.0 License](https://img.shields.io/badge/license-CC--BY--4.0-green.svg
)](/LICENSE-docs)
[![Lifecycle:Stable](https://img.shields.io/badge/Lifecycle-Stable-97ca00)](https://github.com/bcgov/repomountie/blob/master/doc/lifecycle-badges.md)

# aqwarnings

Web site to host air quality warnings, built using [Quarto](https://quarto.org/) and deployed on [GitHub Pages](https://pages.github.com/).

## Development

### Technologies used

The following technologies are used:
- [Quarto](https://quarto.org/)
- [GitHub Pages](https://pages.github.com/)

### Getting Started

Here is high-level documentation on the development of applications and the use of GitHub in the Government of BC: 
- ["Working in github.com/bcgov" Cheatsheet](https://github.com/bcgov/BC-Policy-Framework-For-GitHub/blob/master/BC-Gov-Org-HowTo/Cheatsheet.md)
- [DevHub DC Developer guide](https://developer.gov.bc.ca/docs/default/component/bc-developer-guide/)

### Running the application in local development environment

Instructions are geared toward the following tools:

- [RStudio Desktop](https://posit.co/download/rstudio-desktop/)
- [GitHub Desktop](https://github.com/apps/desktop)

1. Ensure R, RStudio, and Quarto are installed on the machine
1. Clone this repository using GitHub Desktop
1. Open project in RStudio
1. Make and required changes
1. Render the site locally to review
    Run `quarto render` in the Terminal or select "Render" from RStudio's Source Pane

*Note: we rely on pre-render scripts to generate the front page and process the logo header section of the site, these may not render as expected locally and are better tested via the [PR Preview Action](https://github.com/rossjrw/pr-preview-action) that runs on all PRs in this repo.*

### Updating the website theme and design tokens

The website look and feel is determined by a custom theme, **bcds**, available in this repo under the [`_extensions/bcds`](./frontend/_extensions/bcds) folder. The theme is based on the [B.C. Design System](https://github.com/bcgov/design-system/) to match other BC Government web properties and uses its design tokens package. 

Some notes:
- custom shortcodes what are used can be seen at `./frontend/shortcode_demos.qmd` and are defined in [`bcds.lua`](./frontend/_extensions/bcds/bcds.lua)
- the theme styles can be adjusted or defined in `.scss` files and placed within that repo, any new files will have to be added under `theme` in the [`_extension.yaml`](./frontend/_extensions/bcds/_extension.yaml)
- adjustments to the global navigation, left sidebar, and footer are also made in the [`_extension.yaml`](./frontend/_extensions/bcds/_extension.yaml)

If updates to the B.C. Design System need to be incorporated, the process is to overwrite the [`variables.scss`](./frontend/_extensions/bcds/variables.scss) with a new one. You can either grap it from the [`@bcgov/design-tokens`](https://www.npmjs.com/package/@bcgov/design-tokens) package or get the [latest Design System release](https://github.com/bcgov/design-system/releases) and built it yourself.

*Note: Major updates to the B.C. Design System will require manual effort to reconcile with the custom theme and should not be undertaken without a plan for testing and review.*


### Deploying

To deploy to PROD and to TEST you require a GitHub Account, membership in the `bcgov` organization, and write access to this repository.

#### Testing

Open a PR in this repo and a [PR Preview GitHub Action](https://github.com/rossjrw/pr-preview-action) will automatically run.

Workflow: [.github/workflows/pr.yml](.github/workflows/pr.yml)


#### Production

Any PR that is merged into `main` is automatically deployed to `gh-pages` which is the 'production' or live version of the website.

Workflow: [.github/workflows/merge.yml](.github/workflows/merge.yml)


## Contribution Guidelines

Follow the steps outlined in this repository to contribute: [CONTRIBUTING.md](./CONTRIBUTING.md).

## License
Copyright 2025 Province of British Columbia.

**Code** is licensed under the [Apache License, Version 2.0](./LICENSE) (the “License”); you may not use this file except in compliance with the License. You may obtain a copy of the License at
    http://www.apache.org/licenses/LICENSE-2.0
Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an “AS IS” BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.

**Air quality warnings and website documentation** by the Province of British Columbia is licensed under a [Creative Commons Attribution 4.0 International License](): https://creativecommons.org/licenses/by/4.0/.     

### Third party intellectual property material

Some trademarks/logos found in this repository are the intellectual property rights of our partner organizations and are included here with permission solely for BC government use in association with the official public air quality warnings. These trademarks/logos remain the intellectual property rights of the respective partner organizations:
- First Nations Health Authority Logo is copyright (c) First Nations Health Authority
- Interior Health Authority Logo is copyright (c) Interior Health Authority
- Fraser Health Authority Logo is copyright (c) Fraser Health Authority
- Vancouver Coastal Health Authority Logo is copyright (c) Vancouver Coastal Health Authority
- Vancouver Island Health Authority Logo is copyright (c) Vancouver Island Health Authority Logo
- Northern Health Authority Logo is copyright (c) Northern Health Authority
- BC Centre for Disease Control is copyright (c) Provincial Health Services Authority
- WorkSafeBC Logo is copyright (c) WorkSafeBC
