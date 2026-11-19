# Metadata serialization

[MetadataSerializer.java](MetadataSerializer.java) writes physical partition bitmap files and returns their actual size in bytes.

Format:

| Segment | Contents |
| --- | --- |
| Magic (4 bytes) | CMP1 |
| Header (12 bytes) | Three little-endian unsigned 32-bit fields: partition count, payload bytes per partition, schema length |
| Schema | Shared ASCII method/component schema, including positions where relevant and hash-version identifier |
| Payload | For each partition, the bitmap bytes of each component, in order |

The serializer checks the payload budget and validates the physical file size: 16 + schema length + partition count × payload bytes per partition. The reported metadata_total_bytes is the actual serialized file size, and actual BPK is 8 × that size / number of stored keys.

For Experiment 3 the bitmap payload is 366 × 512 = 187,392 bytes per statistic. Headers and schemas add a small shared overhead. The physical representation excludes benchmark-only Java data structures and exact projection diagnostics.

See [statistics](../statistics/README.md).
