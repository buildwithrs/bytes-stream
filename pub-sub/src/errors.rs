use thiserror::Error;
use tokio::io;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("invalid pub event: {0}")]
    InvalidPubEvent(String),

    #[error("unknown event: {0}")]
    UnknownEvent(u8),

    #[error("io error: {0}")]
    IOError(#[from] io::Error)
}