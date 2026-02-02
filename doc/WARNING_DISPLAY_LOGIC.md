# Warning Display Logic

For display, automatic titling, and automatic mandatory action generation on the
recent warnings list, the following minimal properties must be present in the
YAML header or YAML file for the warning:

```yaml
date: ISO8601 date
ice: string - "ISSUE", "CONTINUE", or "END"
location: string
type: string - "redirect", "wildfire_smoke", "pollution_prevention", or "local_emissions"
```

In addition, the following properties are optional:

```yaml
path: string - Required only if the type is "redirect".
overrideTitle: - boolean - If true, use the provided title property
title: string - Required only if overrideTitle is present and set to true.
bylaw: boolean - If present and true, Mandatory action will be "Yes". If present and false Mandatory Action will be "No"
burnRestrictions: integer - if present and greater than 0, Mandatory Action will be "Yes". Takes precedence over bylaw property.
pollutant: string - Required only if the type is "local_emissions". "PM25", "O3", "PM10", or "PM25 & PM10"
```

The following locations will have "Mandatory Action" set to "Yes" unless
overridden by `bylaw: false`:

- Burns Lake
- Duncan
- Houston
- Prince George
- Smithers
- Valemount

## Selecting the Title

```mermaid
flowchart TD;
    A[Start] --> B{Is the &quot;overrideTitle&quot; property present?};
    B -- Yes --> C[Set title to provided title property];
    B -- No --> D{Is the type property &quot;redirect&quot;?};
    D -- Yes --> E[Set title to &quot;Air Quality Warning&quot;];
    D -- NO --> F{Is the type &quot;wildfire_smoke&quot;?};
    F -- YES --> G[Set title to &quot;Wildfire Smoke&quot;];
    F -- NO --> S{Is the type &quot;pollution_prevention&quot;?}
    S -- YES --> T[Set title to &quot;Pollution Prevention Notice&quot;]
    S -- NO --> H{Is the type &quot;local_emissions&quot;?};
    H -- NO --> I[Set title to &quot;N/A&quot;];
    H -- YES --> J{Is the &quot;pollutant&quot; property present?};
    J -- NO --> I;
    J -- YES --> K{Is the pollutant &quot;PM25&quot;?};
    K -- YES --> L[Set title to &quot;Fine particulate matter&quot;];
    K -- NO --> M{Is the pollutant &quot;O3&quot;};
    M -- YES --> N[Set title to &quot;Ground level ozone&quot;];
    M -- NO --> O{Is the pollutant &quot;PM10&quot;?};
    O -- YES --> P[Set title to &quot;Dust&quot;];
    O -- NO --> Q{Is the pollutant &quot;PM25 & PM10&quot;?};
    Q -- NO --> I;
    Q -- YES --> R[Set title to &quot;Fine particulate matter and Dust&quot;];
```

## Selecting Mandatory Action

```mermaid
flowchart TD;
    A[START] --> B{Is &quot;burnRestrictions&quot; present and greater than 0?};
    B -- YES --> C[Set Mandatory Action to &quot;Yes&quot;];
    B -- NO --> D{Is &quot;bylaw&quot; Present?};
    D -- NO --> E{Is &quot;location&quot; in the predefined list?};
    E -- YES --> C
    E -- NO --> F[Set Mandatory Action to &quot;No&quot;]
    D -- YES --> G{Is &quot;bylaw&quot; set to true?}
    G -- YES --> C
    G -- NO --> F
```
