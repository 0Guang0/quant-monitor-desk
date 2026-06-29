"""Rehearsal-only boundary marker for ops pilot/probe entrypoints (R3H-10 S10-03).

Not a product live fetch path. R3H-08 product live must use DataSourceService gold path.
"""

REHEARSAL_ONLY = True

REHEARSAL_DISCLAIMER = (
    "REHEARSAL_ONLY: sandbox/staged evidence path; not R3H-08 product live SSOT"
)

PRODUCT_LIVE_READY = False
