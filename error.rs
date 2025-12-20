use thiserror::Error;

#[derive(Debug, Error)]
pub enum DazzerError {
    #[error("configuration error: {0}")]
    Config(String),

    #[error("mutation error: {0}")]
    Mutation(String),

    #[error("calibration error: {0}")]
    Calibration(String),
}

