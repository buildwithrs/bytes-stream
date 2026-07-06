use std::net::SocketAddr;

use bytes_stream::protocol::{process, read_frame};
use bytes::BytesMut;
use tokio::{
    io::{self, AsyncReadExt, AsyncWriteExt},
    net::{TcpListener, TcpStream},
};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    println!("Hello, world!");

    let addr = "0.0.0.0:8989";
    let listender = TcpListener::bind(addr).await?;
    println!("server listen on: {}", addr);

    loop {
        let (mut stream, remote) = listender.accept().await?;
        tokio::spawn(async move {
            match handle_connection(&mut stream, remote).await {
                Ok(_) => println!("success handle client stream"),
                Err(e) => eprintln!("failed to handle client stream: {}", e),
            }
        });
    }
}

async fn handle_connection(stream: &mut TcpStream, remote: SocketAddr) -> io::Result<()> {
    println!("handle stream for: {:?}", remote);
    let mut buf = BytesMut::with_capacity(8 * 1024);
    loop {
        let n = stream.read_buf(&mut buf).await?;
        if n == 0 {
            break; // client closed
        }

        while let Some(frame) = read_frame(&mut buf) {
            let payload = frame.freeze();
            let out = process(payload);
            stream.write_all(&out).await?;
        }
    }

    Ok(())
}
