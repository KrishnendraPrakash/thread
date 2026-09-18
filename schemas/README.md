# Schema design locations

Define versioned contracts here when record serialization is implemented. The current planning trace version is illustrative and must not be treated as a frozen production schema.

records/ will hold shared record schemas. traces/ will hold event/envelope schemas and migration notes. Follow SPEC.md for immutable records, hashes, producer identity, status projections, and replay completeness.
