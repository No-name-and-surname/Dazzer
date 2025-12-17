#![allow(dead_code)]

use std::fs;
use std::path::Path;

use anyhow::{Context, Result};

pub fn read_dictionary(path: &Path) -> Result<Vec<String>> {
    let content = fs::read_to_string(path)
        .with_context(|| format!("failed to read dictionary file {}", path.display()))?;
    Ok(content
        .lines()
        .map(|line| line.trim().to_string())
        .filter(|line| !line.is_empty())
        .collect())
}

