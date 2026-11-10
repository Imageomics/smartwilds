# Validation

`scripts/validation/audit_darwin_core_snapshot.py` is a read-only integrity
audit of a generated table set. Run it after generation and before release.

```bash
python scripts/validation/audit_darwin_core_snapshot.py \
  --snapshot-dir "$SMARTWILDS_DWC_OUT" \
  --stem DARWIN_CORE_AUDIT_$(date +%Y%m%d)
```

| Check | What fails it |
|---|---|
| Source-to-merged parity | A modality row missing from the merged tables, an extra merged row, or a value that differs between the two |
| Event hierarchy | More than one root, an orphaned `parentEventID`, or a cycle |
| Occurrence links and ancestry | An Occurrence whose `eventID` is missing, or whose Event belongs to another modality |
| Scalars | Dates, times, and coordinates that do not parse; sentinel strings such as `nan`, `None`, `-1`, or epoch dates |
| Media | Local `associatedMedia` paths that do not exist (warning) |
| Generator drift | The study root date in the generator differs from the released root Event |

The audit writes `<stem>.json` (machine-readable findings) and `<stem>.md`
(summary) into the table directory. It never modifies the tables.

The release build adds checks the audit does not cover, because they need the
release layout: every Occurrence date inside its parent Event's span and the
study window, no archive paths in any cell, and every `associatedMedia` value
resolving to an included file in the media manifest. Those results are in each
dataset's `RELEASE_BUILD_AUDIT.json` and summarized in the
[supplemental material](../SUPPLEMENTAL.md#s11-validation-checks-run-and-gaps).
