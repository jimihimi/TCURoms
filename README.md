# Subaru TCU ROM collection

Images are grouped by transmission family, documented market applicability, and model. `catalog.csv` is the source of truth for provenance, aliases, image type, and evidence status. Markets come from package/part database matches or inherited donor labels, not a universal third-character rule.

## Layout

- `4EAT/`, `5EAT/`, `6AT/`, `CVT/`: family supported by package descriptions or existing shared-image provenance.
- `Unclassified/`: transmission family cannot be assigned from those descriptions.
- Markets: `North-America`, `Europe-General`, `Australia`, `Japan`, or `Unknown`.
- `Unknown-Model` and `Multiple-Models` preserve missing or shared applicability.
- `Review/Cross-ROM-Supported/`: recovered images with cross-ROM key support; advertised release identity remains unverified.
- `Review/Identity-Mismatch/`: the user-accepted E65F33BJ / embedded E62F33BJ naming discrepancy.
- `provenance/`: original repository manifest, database record references, and research qualifications.

## Files and identity

Identical bytes are stored once. Multiple catalog rows preserve every original repository filename and recovered package/member alias. Different contents sharing an identifier remain separate. Existing images take precedence as canonical copies where package payloads match them byte for byte.

New files use `<header-new-ROM-ID>__<package>__<member>__update-payload.bin`. That ID is the package's advertised identifier; `identity_evidence` records what was actually found. Existing shared filenames are retained with a `__shared-image` suffix. Catalog rows separately retain the corrected embedded ID ACD1207000 for the originally named AC91207000 image.

`update-payload` identifies a recovered package member, not a complete flash readout. A `shared-image` label preserves its origin without asserting complete coverage. The same bytes can have both kinds of source alias. No bytes were padded, rebased, patched, or repaired during reorganization. SHA-256 covers exact stored bytes; source package hashes are separate.

## Evidence boundaries

Identity support and cross-ROM key support are distinct from verified processor assignments, physical load addresses, flash capacity, firmware checksums, or suitability for a vehicle. Header download addresses and logical layouts are retained as metadata only. Family folders describe transmission type, not MCU architecture. Package-only applicability is explicitly marked and is weaker than a package-and-part match. Existing market labels remain inherited provenance where stronger evidence is unavailable.

Original `main` files were backed up and verified against their Git blob hashes before reorganization. `provenance/backup-manifest.csv` records their paths and SHA-256 values. `provenance/reorganization.json` records the base commit and counts. This collection is for offline research; it does not establish that any image is suitable for flashing.
