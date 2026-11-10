# Using agents on your own data

The SmartWilds documentation was produced with LLM coding agents working in
the project's file system under the authors' direction
([how we used them](../AGENT_ASSISTED_DOCUMENTATION.md)). This page is the
practical version: how to set an agent up on a field archive, what to give it,
and prompts that worked.

## Setup

1. **Run the agent where the data is.** A coding agent (we used
   [Claude Code](https://claude.com/claude-code)) needs read access to the
   archive and write access to a documentation directory. On a shared cluster,
   start it in the project directory on a login or interactive node; it only
   lists directories, reads text and metadata, and runs small scripts.
2. **Give it a project file.** A `CLAUDE.md` (or `AGENTS.md`) at the root
   describing the layout, the modalities, the naming conventions, and where
   notes go saves re-explaining every session. Ours is a page long.
3. **Put the standards in context.** Download the
   [FAIR² Drones template and quick-start checklist](https://github.com/Imageomics/fair_drones)
   and the [Imageomics dataset card template](https://imageomics.github.io/Imageomics-guide/wiki-guide/HF_DatasetCard_Template_Imageomics/)
   into a `documentation/guidelines/` directory and tell the agent to follow
   them. See [Guidelines to give the agent](guidelines.md).
4. **Keep the archive read-only.** Agents propose; people decide. Every change
   to a released table should leave a dated before-copy and a JSON audit
   record.

## Tasks and prompts

=== "Inventory a campaign directory"

    ```text
    Walk thewilds_20250804_20250828/ and write
    thewilds_20250804_20250828_data_report.md. For each modality and
    deployment: file counts and sizes by type, the metadata and log files
    present, the naming convention, date range of the files, and anything
    that looks wrong (clock reporting an impossible year, missing telemetry,
    empty folders, duplicate files). List the people named in the logs.
    Use the directory-tree style of the campaign-1 report.
    ```

=== "Summarize the records"

    ```text
    From occurrences.csv and events.csv in <dir>, tabulate: Events by
    eventType; Occurrences by deployment, by taxon (class and species rank),
    by identificationVerificationStatus, and by campaign; date range per
    table; share of records with coordinates, times, and associatedMedia.
    Write the result as Markdown tables I can paste into the supplement.
    Compute from the tables; do not copy numbers from existing prose.
    ```

=== "Find discrepancies"

    ```text
    Cross-check two things that should agree and report every mismatch:
    (1) the raw WAV inventory against the AudioRecording Events;
    (2) each Occurrence's eventDate against its parent Event's span;
    (3) sentinel strings (nan, None, -1, 1970-01-01) in any date, time, or
    coordinate column; (4) duplicate occurrenceID values; (5) associatedMedia
    paths that do not resolve. For each finding: scope (how many rows, which
    deployments), what detected it, and candidate repairs. Do not repair.
    ```

=== "Turn checks into QA/QC scripts"

    ```text
    Turn the checks we just ran into a read-only audit script
    (scripts/validation/audit_darwin_core_snapshot.py) that takes a table
    directory and writes a JSON and a Markdown report. Standard library only.
    Exit non-zero on any ERROR finding. Include the merged-table parity check.
    ```

=== "Draft a dataset card"

    ```text
    Draft the dataset card for the bioacoustics tables following
    documentation/guidelines/TEMPLATE.md (FAIR² Drones) and the Imageomics
    card template. Fill every section from the tables, sensor_configurations.md,
    and the field notes; leave a visible TODO where the information is not in
    the repository rather than inventing it. Front matter: license, tags,
    size_categories, Darwin Core coverage dates and representative point.
    ```

=== "Keep documentation in sync"

    ```text
    The drone Occurrence table changed (12 duplicate rows dropped). Find every
    number in docs/, metadata/, and README.md that depends on it, update the
    ones you can recompute from the new table, and list the ones you cannot.
    ```

## Review checklist

Agent output is a draft until a person has checked it. What we check:

- **Numbers come from the tables.** Ask the agent to show the computation
  (a code cell or a one-line script), and spot-check against an independent
  count.
- **Nothing was invented.** Empty template sections should say what is
  missing and why (see S8 of the supplement), not be filled in plausibly.
- **Repairs are proposed, not applied.** The author chooses the repair; the
  agent implements it with a before-copy and an audit record.
- **Tone and spelling.** Direct statements, American English, no venue names
  in dataset documentation while a paper is under review.
- **Paths and identifiers.** No cluster paths or internal snapshot names in
  anything public; scripts read locations from environment variables.

## What to expect

With the standards in context the agent produces cards and inventories in the
expected structure on the first pass, and review effort goes into checking
numbers and wording rather than restructuring. The agents found most of the
rows in the [defect inventory](../DEFECT_INVENTORY.md) by cross-checking
artifacts that should agree; the "Detected by" column records what made each
defect visible.
