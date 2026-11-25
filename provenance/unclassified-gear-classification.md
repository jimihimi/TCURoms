# Transmission-family review of formerly unclassified images

On 2026-11-25, all 16 distinct binaries previously under `Unclassified/` were
assigned to a gear family: 15 to `4EAT` and one to `5EAT`. The per-image
SHA-256, old and new paths, nearest classified reference, and overlap counts
are in [unclassified-gear-classification.csv](unclassified-gear-classification.csv).
The underlying top-five comparisons are in
[unclassified-binary-comparison.json](unclassified-binary-comparison.json).

The comparison scans each binary in 64-byte windows at 16-byte steps. Windows
with fewer than 12 distinct byte values are excluded so padding contributes
little. The 15 4EAT assignments share 354–23,197 distinctive windows with
classified 4EAT references, versus 0–62 with the best 5EAT references. The
2005 Outback turbo image shares 18,707 of its 18,772 distinctive windows with
a classified 2005 Legacy 5EAT image, versus zero with 4EAT. These are
cross-image similarities, not a direct decoding of a gear-count constant.

The local Subaru package/part database links each payload to a vehicle and
year but calls its transmission only `AT`. Subaru's
[2016 reprogramming list hosted by NHTSA](https://static.nhtsa.gov/odi/tsbs/2016/MC-10140522-9999.pdf)
independently links `30919AB431` and `30919AB891` to 2011 Forester TCM
updates. An [OEM part catalog listing for 2011 Forester](https://www.subarupartsdeal.com/parts-list/2011-subaru-forester/automatic_transmission/control_unit.html)
labels both exact controller parts `4AT`. The
[2005 Legacy control-unit listing](https://www.subarupartsdeal.com/parts-list/2005-subaru-legacy/automatic_transmission/control_unit.html)
labels exact Outback controller part `31711AJ202` `5AT`. For the 2002–2004
Legacy/Outback, Impreza, Baja, and Forester payloads, the strongest evidence
is shared binary content with already-classified 4EAT images and the matched
package/part applicability. These fitment listings are supporting evidence,
not a substitute for the actual ROM comparisons.

All 16 file SHA-256 values remain unchanged. The catalog retains every
package/member alias and the original firmware evidence statuses. Family
assignment does not validate processor, checksum, memory map, or suitability
for flashing.

Recompute the overlap report with `python tools/compare_unclassified.py` on
the pre-classification commit, then run `python tools/classify_unclassified.py`
to reproduce the moves. The checked-in report preserves the pre-move paths.
