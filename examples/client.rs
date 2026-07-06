use bytes_stream::protocol::{encode_msg, read_frame};
use bytes::BytesMut;
use tokio::{io::{self, AsyncReadExt, AsyncWriteExt}, net::TcpStream};


#[tokio::main]
async fn main() -> anyhow::Result<()>{
    let addr = "localhost:8989";
    let mut stream = TcpStream::connect(addr).await?;

    stream.write_all(&encode_msg("Hello, My Friend!")).await?;
    stream.write_all(&encode_msg("Nice to see you")).await?;
    stream.write_all(&encode_msg("Test Client Stream with Bytes")).await?;

    handle_connection(&mut stream).await?;
    Ok(())
}

async fn handle_connection(stream: &mut TcpStream) -> io::Result<()> {
    let mut buf = BytesMut::with_capacity(8 * 1024);
    loop {
        let n = stream.read_buf(&mut buf).await?;
        if n == 0 {
            break; // client closed
        }

        while let Some(frame) = read_frame(&mut buf) {
            let bs = &frame.freeze().to_vec();
            let msg = String::from_utf8_lossy(bs);
            println!("response from server: {}", msg);
        }
    }

    Ok(())
}