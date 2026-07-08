use std::net::SocketAddr;

use bytes::{Bytes, BytesMut};
use pub_sub::{
    errors::AppError, protocol::{SuccessACK, decode_frame, encode_sucess_ack, process, read_frame},
};
use tokio::{
    io::{self, AsyncReadExt, AsyncWriteExt},
    net::{TcpListener, TcpStream},
};

#[tokio::main]
async fn main() -> anyhow::Result<()> {
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

async fn handle_connection(stream: &mut TcpStream, remote: SocketAddr) -> Result<(), AppError> {
    println!("handle stream for: {:?}", remote);
    let mut buf = BytesMut::with_capacity(8 * 1024);
    loop {
        buf.clear();

        let n = stream.read_buf(&mut buf).await?;
        if n == 0 {
            break; // client closed
        }

        while let Some(mut frame) = read_frame(&mut buf) {
            match decode_frame(&mut frame) {
                Ok(ev) => {
                    println!("received event: {}", ev);
                    stream.write_all(&encode_sucess_ack(SuccessACK {
                        tag: ev.tag(),
                        msg: b"OK".to_vec(),
                    })).await?;
                }
                Err(e) => {
                    eprintln!("decode framed failed: {}", e);
                    stream.write_all(b"FAILED").await?;
                }
            }
        }
    }

    Ok(())
}
