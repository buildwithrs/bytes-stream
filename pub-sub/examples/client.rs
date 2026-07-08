use bytes::BytesMut;
use pub_sub::{errors::AppError, protocol::{
    Message, PubEvent, SubEvent, decode_frame, encode_msg, encode_pub, encode_sub, new_ts, read_frame,
}};
use tokio::{
    io::{self, AsyncReadExt, AsyncWriteExt},
    net::TcpStream,
};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let addr = "localhost:8989";
    let mut stream = TcpStream::connect(addr).await?;

    let pub_ev = PubEvent {
        client_id: 1001,
        topic: "orders".to_string(),
        channel: "analysis".to_string(),
        msg: b"Hello".to_vec(),
    };
    println!("sending: pub evenet: {:?}", pub_ev);
    stream.write_all(&encode_pub(pub_ev)).await?;

    let sub_ev = SubEvent {
        client_id: 1001,
        topic: "orders".to_string(),
        channel: "analysis".to_string(),
    };
    println!("sending sub event: {:?}", sub_ev);
    stream.write_all(&encode_sub(sub_ev)).await?;

    let msg = Message {
        id: 1000,
        ts: new_ts(),
        from: 1001,
        body: b"Nice to see you!".to_vec(),
    };
    println!("sending msg: {:?}", msg);
    stream.write_all(&encode_msg(msg)).await?;

    handle_connection(&mut stream).await?;
    Ok(())
}

async fn handle_connection(stream: &mut TcpStream) -> Result<(), AppError> {
    let mut buf = BytesMut::with_capacity(8 * 1024);
    loop {
        let n = stream.read_buf(&mut buf).await?;
        if n == 0 {
            println!("sever closed");
            break; // server closed
        }

        while let Some(mut frame) = read_frame(&mut buf) {
            let ev = decode_frame(&mut frame)?;
            println!("response from server: {}", ev);
        }
    }

    Ok(())
}
