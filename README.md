# bytes-stream

## `BytesMut`
- mutable
- growable
- ideal for socket read buffers and message encoding

## `Bytes`
- immutable view
- cheap to clone (shared backing storage)
- ideal for passing parsed payloads around and outbound queues

A very practical lifecycle for servers:

1. Read into `BytesMut`
2. Parse frames using split/advance (no payload copy)
3. Convert parsed frame to `Bytes`
4. Clone `Bytes` cheaply when fan-out is needed