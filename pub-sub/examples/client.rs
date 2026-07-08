use pub_sub::protocol::{PubEvent, encode_msg, encode_pub, read_frame};
use bytes::BytesMut;
use tokio::{io::{self, AsyncReadExt, AsyncWriteExt}, net::TcpStream};


#[tokio::main]
async fn main() -> anyhow::Result<()>{
    let addr = "localhost:8989";
    let mut stream = TcpStream::connect(addr).await?;

    let pub_ev = PubEvent {
        client_id: 1001,
        topic: "orders".to_string(),
        channel: "analysis".to_string(),
        msg: b"Hello".to_vec(),
    };
    stream.write_all(&encode_pub(pub_ev)).await?;

    handle_connection(&mut stream).await?;
    Ok(())
}

async fn handle_connection(stream: &mut TcpStream) -> io::Result<()> {
    let mut buf = BytesMut::with_capacity(8 * 1024);
    loop {
        let n = stream.read_buf(&mut buf).await?;
        if n == 0 {
            println!("sever closed");
            break; // server closed
        }

        while let Some(frame) = read_frame(&mut buf) {
            let bs = &frame.freeze().to_vec();
            let msg = String::from_utf8_lossy(bs);
            println!("response from server: {}", msg);
        }
    }

    Ok(())
}