use bytes::{Buf, BufMut, Bytes, BytesMut};

const HEADER_LEN: usize = 4;

pub fn encode_msg(msg: &str) -> Bytes {
    let mut writer = BytesMut::with_capacity(4 + msg.len());
    writer.put_u32(msg.len() as u32);

    let bs = msg.to_string().into_bytes();
    writer.extend_from_slice(&bs);
    writer.freeze()
}

pub fn read_frame(buf: &mut BytesMut) -> Option<BytesMut> {
    if buf.len() < HEADER_LEN {
        return None;
    }

    let size = u32::from_be_bytes([buf[0],buf[1], buf[2], buf[3]]) as usize;
    if buf.len() < size + 4 {
        return None;
    }

    buf.advance(HEADER_LEN);
    Some(buf.split_to( size))
}

pub fn process(payload: Bytes) -> Bytes {
    let mut writer = BytesMut::with_capacity(4 + payload.len());
    writer.put_u32(payload.len() as u32);
    writer.extend_from_slice(&payload);
    writer.freeze()
}