# Subaru TCU ROM collection

Images are grouped by transmission family, documented market applicability, and model. `catalog.csv` is the source of truth for provenance, aliases, image type, and evidence status. Markets come from package/part database matches or inherited donor labels, not a universal third-character rule.

## Layout

- `4EAT/`, `5EAT/`, `6AT/`, `CVT/`: family supported by package descriptions or existing shared-image provenance.
- `Unclassified/`: reserved for images whose transmission family remains unresolved; none remain after the 2026-11-25 binary-comparison review.
- Markets: `North-America`, `Europe-General`, `Australia`, `Japan`, or `Unknown`.
- `Unknown-Model` preserves missing applicability; other model directories use the evidenced model names, joined when an image has more than one application.
- `Review/Cross-ROM-Supported/`: recovered images with cross-ROM key support; advertised release identity remains unverified.
- `Review/Identity-Mismatch/`: the user-accepted E65F33BJ / embedded E62F33BJ naming discrepancy.
- `provenance/`: original repository manifest, database record references, and research qualifications.

## Files and identity

Identical bytes are stored once. Multiple catalog rows preserve every original repository filename and recovered package/member alias. Different contents sharing an identifier remain separate. Existing images take precedence as canonical copies where package payloads match them byte for byte.

Files use `<years>_<models>__<ROM-ID>__<part-number>__<SHA256-prefix>__<image-type>.bin`, for example `2015_WRX__CAFDD08100__30919AD792__3469c75b91bf__update-payload.bin`. `Multiple-Parts` or `Multiple-ROM-IDs` preserves ambiguous aliases without choosing one arbitrarily. The full part numbers, package/member names, prior paths, and SHA-256 remain in the catalog. The ROM ID can be a package's advertised identifier; `identity_evidence` records what was actually found. Catalog rows separately retain the corrected embedded ID ACD1207000 for the originally named AC91207000 image.

Year/model labels summarize the union of applicability records for identical bytes. They do not imply that every model/year combination is valid; `firmware_model_year_pairs` records the actual database pairs. Discontinuous year sets retain gaps (for example `2003+2005-2006`). `Unknown-Year` is explicit when no defensible year is available. Source-specific fields remain separate even when identical bytes share a filename.

`update-payload` identifies a recovered package member, not a complete flash readout. A `shared-image` label preserves its origin without asserting complete coverage. The same bytes can have both kinds of source alias. No bytes were padded, rebased, patched, or repaired during reorganization. SHA-256 covers exact stored bytes; source package hashes are separate.

## Evidence boundaries

Identity support and cross-ROM key support are distinct from verified processor assignments, physical load addresses, flash capacity, firmware checksums, or suitability for a vehicle. Header download addresses and logical layouts are retained as metadata only. Family folders describe transmission type, not MCU architecture. Package-only applicability is explicitly marked and is weaker than a package-and-part match. Existing market labels remain inherited provenance where stronger evidence is unavailable.

Original `main` files were backed up and verified against their Git blob hashes before reorganization. `provenance/backup-manifest.csv` records their paths and SHA-256 values. `provenance/reorganization.json` records the base commit and counts. This collection is for offline research; it does not establish that any image is suitable for flashing.

## Part-number and model-year enrichment

The 2026-11-21 pass searched 564 new, target, and filename part numbers. `parts.subaru.com` returned HTTP 403, and its indexed exact-part queries returned no results. This is an access/index limitation, not evidence of non-fitment. Queries and outcomes are preserved in `provenance/parts-subaru-search-audit.json`.

Fallback searches used SubaruParts.com (Tacoma Subaru), Subaru Online Parts, and SubaruPartsDeal. `provenance/part-fitment-online.json` retains the exact-part source URLs, explicit seller fitment facts, rejected parser matches, and per-part search status. A missing result means unresolved, not incompatible. Seller titles and fitment tables have separate evidence types; broad seller listings can include configurations that do not apply to a particular firmware.

Hardware fitment is supplemental metadata (`hardware_fitment_json`), never a reason to broaden firmware applicability. Model/year filenames use the selected SSM package/part records, explicit package headers, or documented donor statements. Package-only matches are labeled as such and are weaker than exact part matches. Original database row references, models, years, and transmissions remain in `provenance/market-database-evidence.csv`. Existing images with no matching part or donor evidence retain unknown labels.

At the time of the fitment enrichment, all 289 binaries and 309 source rows were retained. That pass resolved 14 previously unknown model classifications; 284 binaries had model/year labels and five remained unknown. The later CVT addition brings the current catalog to 293 binaries and 313 source rows. SHA-256 values and firmware evidence statuses are unchanged. `provenance/fitment-renames.csv` maps the original paths to their current locations; `provenance/fitment-enrichment-summary.json` records historical counts and input hashes.

Reproduce the plan with `python tools/enrich_fitment.py`; add `--apply` to write it. The script uses the pinned pre-enrichment catalog from Git history and checked-in evidence, so it does not depend on live parts websites. Run regression checks with `python -m unittest discover -s tools -p test_enrich_fitment.py`. Firmware checksums, processor assignments, and physical flash maps are outside this metadata pass.

## Gear-family review of formerly unclassified images

The 2026-11-25 review moved 15 distinct images to `4EAT` and one to `5EAT`.
It compared distinctive 64-byte ROM windows against classified images and
checked exact-part transmission listings where available. No CVT image was
found in this group. [Methods and limits](provenance/unclassified-gear-classification.md)
and [per-image evidence](provenance/unclassified-gear-classification.csv) are
checked in. The catalog and fitment rename map now point to the new locations;
the prior import and enrichment reports remain historical snapshots.
