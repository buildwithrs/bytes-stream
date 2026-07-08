use std::fmt;

use bytes::{Buf, BufMut, Bytes, BytesMut};

use crate::errors::AppError;

pub const PUB_TAG: u8 = 0x01;
pub const SUB_TAG: u8 = 0x03;
pub const MSG_TAG: u8 = 0x05;

pub const MAX_TOPIC_LEN: u8 = 50;
pub const MAX_CHAN_LEN: u8 = 50;
pub const MAX_MSG_LEN: u32 = 8 * 1024;

pub const CRLF: &'static [u8; 2] = b"\r\n";

#[derive(Debug, PartialEq, Clone)]
pub struct PubEvent {
    pub client_id: u64, // 8 bytes
    pub topic: String,
    pub channel: String,
    pub msg: Vec<u8>,
}

#[derive(Debug, PartialEq, Clone, Default)]
pub struct SubEvent {
    pub client_id: u64,
    pub topic: String,
    pub channel: String,
}

#[derive(Debug, PartialEq, Clone, Default)]
pub struct Message {
    pub id: u64,
    pub ts: u64,
    pub from: u64,
    pub body: Vec<u8>,
}

#[derive(Debug, PartialEq)]
pub enum Event {
    Pub(PubEvent),
    Sub(SubEvent),
    Message(Message),
}

impl fmt::Display for Event {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Event::Pub(PubEvent {
                client_id,
                topic,
                channel,
                msg,
            }) => {
                let body = String::from_utf8_lossy(msg);
                write!(
                    f,
                    "PubEvent {{ client_id: {}, topic: {}, channel: {}, msg: {} }}",
                    client_id, topic, channel, body
                )
            }
            Event::Sub(SubEvent {
                client_id,
                topic,
                channel,
            }) => {
                write!(
                    f,
                    "SubEvent {{ client_id: {}, topic: {}, channel: {} }}",
                    client_id, topic, channel
                )
            }
            Event::Message(Message { id, ts, from, body }) => {
                let payload = String::from_utf8_lossy(body);
                write!(
                    f,
                    "Message {{ id: {}, ts: {}, from: {}, body: {} }}",
                    id, ts, from, payload
                )
            }
        }
    }
}

const HEADER_LEN: usize = 4;

pub fn encode_pub(pub_event: PubEvent) -> Bytes {
    let mut out = Vec::new();

    out.put_u8(PUB_TAG);
    out.put_u64(pub_event.client_id);

    out.put_u8(pub_event.topic.len() as u8);
    out.extend_from_slice(&pub_event.topic.into_bytes());

    out.put_u8(pub_event.channel.len() as u8);
    out.extend_from_slice(&pub_event.channel.into_bytes());
    out.extend_from_slice(&pub_event.msg);

    println!("out buf: {:?}", out);

    let mut writer = BytesMut::with_capacity(4 + out.len());
    writer.put_u32(out.len() as u32);
    writer.extend_from_slice(&out);
    writer.freeze()
}

pub fn encode_sub(sub: SubEvent) -> Bytes {
    let mut out = Vec::new();

    out.put_u8(SUB_TAG);
    out.extend_from_slice(&sub.client_id.to_be_bytes());

    out.put_u8(sub.topic.len() as u8);
    out.extend_from_slice(&sub.topic.into_bytes());
    out.extend_from_slice(&sub.channel.into_bytes());

    let mut writer = BytesMut::with_capacity(4 + out.len());
    writer.put_u32(out.len() as u32);
    writer.extend_from_slice(&out);
    writer.freeze()
}

pub fn encode_msg(msg: Message) -> Bytes {
    let mut out = Vec::new();

    out.put_u8(MSG_TAG);
    out.extend_from_slice(&msg.id.to_be_bytes());
    out.extend_from_slice(&msg.ts.to_be_bytes());
    out.extend_from_slice(&msg.from.to_be_bytes());
    out.extend_from_slice(&&msg.body);

    let mut writer = BytesMut::with_capacity(4 + out.len());
    writer.put_u32(out.len() as u32);
    writer.extend_from_slice(&out);
    writer.freeze()
}

pub fn read_frame(buf: &mut BytesMut) -> Option<BytesMut> {
    if buf.len() < HEADER_LEN {
        return None;
    }

    let size = u32::from_be_bytes([buf[0], buf[1], buf[2], buf[3]]) as usize;
    if buf.len() < size + 4 {
        return None;
    }

    buf.advance(HEADER_LEN);
    Some(buf.split_to(size))
}

pub fn decode_frame(f: &mut BytesMut) -> Result<Event, AppError> {
    let tag = f.get_u8();
    match tag {
        PUB_TAG => decode_pub(f),
        SUB_TAG => decode_sub(f),
        MSG_TAG => decode_msg(f),
        _ => Err(AppError::UnknownEvent(tag)),
    }
}

fn decode_pub(bs: &mut BytesMut) -> Result<Event, AppError> {
    let c_id = bs.get_u64();
    let t_len = bs.get_u8() as usize;
    let topic = String::from_utf8_lossy(&bs[0..t_len]);

    let ch_len = bs[t_len] as usize;
    let channel = String::from_utf8_lossy(&bs[t_len + 1..t_len + 1 + ch_len]);
    let msg = bs[t_len + ch_len + 1..].to_vec();

    Ok(Event::Pub(PubEvent {
        client_id: c_id,
        topic: topic.to_string(),
        channel: channel.to_string(),
        msg: msg,
    }))
}

fn decode_sub(bs: &mut BytesMut) -> Result<Event, AppError> {
    let c_id = bs.get_u64();
    let t_len = bs.get_u8() as usize;
    let topic = String::from_utf8_lossy(bs.get(0..t_len).unwrap());
    let channel = String::from_utf8_lossy(&bs[t_len + 1..]);

    Ok(Event::Sub(SubEvent {
        client_id: c_id,
        topic: topic.to_string(),
        channel: channel.to_string(),
    }))
}

fn decode_msg(bs: &mut BytesMut) -> Result<Event, AppError> {
    let id = bs.get_u64();
    let ts = bs.get_u64();
    let from = bs.get_u64();
    let body = bs[..].to_vec();

    Ok(Event::Message(Message { id, ts, from, body }))
}

pub fn process(payload: Bytes) -> Bytes {
    let mut writer = BytesMut::with_capacity(4 + payload.len());
    writer.put_u32(payload.len() as u32);
    writer.extend_from_slice(&payload);
    writer.freeze()
}

#[cfg(test)]
mod tests {
    use std::time::SystemTime;

    use bytes::BytesMut;

    use crate::protocol::{
        Event, Message, PubEvent, decode_frame, encode_msg, encode_pub, read_frame,
    };

    #[test]
    fn test_encode_decode_pub() {
        let pub_ev = PubEvent {
            client_id: 1001,
            topic: "orders".to_string(),
            channel: "analysis".to_string(),
            msg: b"orders:001".to_vec(),
        };

        let bs = encode_pub(pub_ev.clone());
        println!("pub bs: {:?}", bs);

        let mut mut_bs = BytesMut::from(bs);
        let f = read_frame(&mut mut_bs);
        assert!(f.is_some());

        let mut frame = f.unwrap();

        let decode_pub_ev = decode_frame(&mut frame);
        println!("decode_pub_ev: {:?}", decode_pub_ev);
        assert!(decode_pub_ev.is_ok());
        assert_eq!(Event::Pub(pub_ev), decode_pub_ev.unwrap());
        // println!("pub evenet: {}", decode_pub_ev.unwrap());
    }

    #[test]
    fn test_encode_decode_msg() {
        let ts = SystemTime::now()
            .duration_since(SystemTime::UNIX_EPOCH)
            .unwrap();
        let msg = Message {
            id: 1000,
            ts: ts.as_secs(),
            from: 1001,
            body: b"Hello, Friend".to_vec(),
        };

        let msg_bs = encode_msg(msg.clone());
        let mut msg_mut = BytesMut::from(msg_bs);
        let f = read_frame(&mut msg_mut);
        assert!(f.is_some());

        let decode_msg = decode_frame(&mut f.unwrap());
        assert!(decode_msg.is_ok());

        let msg1 = decode_msg.unwrap();
        assert_eq!(Event::Message(msg), msg1);
        println!("decode_msg: {}", msg1);
    }

    #[test]
    fn u8_2_hex() {
        let n1 = 233 as u8;
        println!("{:x}", n1);
    }
}
