use thiserror::Error;

#[derive(Debug, Error)]
pub enum AppError {
    #[error("invalid pub event: {0}")]
    InvalidPubEvent(String),

    #[error("unknown event: {0}")]
    UnknownEvent(u8)
}