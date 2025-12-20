use std::fs;
use std::path::{Path, PathBuf};

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum FuzzingType {
    White,
    Gray,
    Black,
}

impl Default for FuzzingType {
    fn default() -> Self {
        Self::White
    }
}

#[derive(Debug, Clone, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum TargetLanguage {
    C,
    Go,
    Other(String),
}

impl Default for TargetLanguage {
    fn default() -> Self {
        Self::C
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NetworkConfig {
    pub host: String,
    pub port: u16,
    pub timeout_secs: u64,
}

impl Default for NetworkConfig {
    fn default() -> Self {
        Self {
            host: "localhost".to_string(),
            port: 1337,
            timeout_secs: 5,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct PerformanceConfig {
    pub num_threads: usize,
    pub enable_coverage_caching: bool,
    pub coverage_cache_size: usize,
    pub mutation_cache_size: usize,
    pub testing_cache_size: usize,
    pub batch_size: usize,
    pub adaptive_mutation: bool,
    pub coverage_timeout_secs: f64,
    pub testing_timeout_secs: f64,
    pub fast_mode: bool,
    pub super_speed: bool,
    pub safe_mode: bool,
    pub cache_aggressively: bool,
}

impl Default for PerformanceConfig {
    fn default() -> Self {
        Self {
            num_threads: 8,
            enable_coverage_caching: true,
            coverage_cache_size: 10_000,
            mutation_cache_size: 10_000,
            testing_cache_size: 5_000,
            batch_size: 1,
            adaptive_mutation: true,
            coverage_timeout_secs: 1.0,
            testing_timeout_secs: 1.0,
            fast_mode: true,
            super_speed: true,
            safe_mode: true,
            cache_aggressively: true,
        }
    }
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ResultPaths {
    pub output_file: PathBuf,
    pub dict_file: PathBuf,
    pub corpus_dir: PathBuf,
    pub coverage_dir: PathBuf,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct TargetPaths {
    pub base_dir: PathBuf,
    pub tests_dir: PathBuf,
    pub out_dir: PathBuf,
    pub binary_path: PathBuf,
    pub source_file: Option<PathBuf>,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FuzzerConfig {
    pub fuzz_marker: String,
    pub fuzzing_type: FuzzingType,
    pub target_language: TargetLanguage,
    pub args: Vec<String>,
    pub network: NetworkConfig,
    pub performance: PerformanceConfig,
    pub result_paths: ResultPaths,
    pub target_paths: TargetPaths,
}

impl FuzzerConfig {
    pub fn load_default() -> Result<Self> {
        let base_dir = locate_base_dir()?;
        let tests_dir = base_dir.join("Test_examples");
        let out_dir = base_dir.join("out");
        let corpus_dir = out_dir.clone();
        let coverage_dir = out_dir.clone();
        let dict_file = base_dir.join("dict.txt");
        let output_file = base_dir.join("output.txt");
        let binary_path = tests_dir.join("multy");
        let source_file = tests_dir.join("multy.c");

        fs::create_dir_all(&tests_dir)
            .context("failed to ensure tests directory exists")?;
        fs::create_dir_all(&out_dir)
            .context("failed to ensure output directory exists")?;

        Ok(Self {
            fuzz_marker: "qW3r7y_A5d_4sD_1234567890".to_string(),
            fuzzing_type: FuzzingType::White,
            target_language: TargetLanguage::C,
            args: vec!["1".to_string(), "1".to_string()],
            network: NetworkConfig::default(),
            performance: PerformanceConfig::default(),
            result_paths: ResultPaths {
                output_file,
                dict_file,
                corpus_dir,
                coverage_dir,
            },
            target_paths: TargetPaths {
                base_dir,
                tests_dir,
                out_dir,
                binary_path,
                source_file: Some(source_file),
            },
        })
    }

    pub fn ensure_runtime_dirs(&self) -> Result<()> {
        fs::create_dir_all(&self.target_paths.tests_dir)
            .context("failed to create tests directory")?;
        fs::create_dir_all(&self.target_paths.out_dir)
            .context("failed to create out directory")?;
        fs::create_dir_all(&self.result_paths.corpus_dir)
            .context("failed to create corpus directory")?;
        if matches!(self.target_language, TargetLanguage::Go) {
            fs::create_dir_all(&self.result_paths.coverage_dir)
                .context("failed to create coverage directory")?;
        }
        Ok(())
    }
}

fn locate_base_dir() -> Result<PathBuf> {
    let manifest_dir = std::env::var("CARGO_MANIFEST_DIR").ok().map(PathBuf::from);

    if let Some(dir) = manifest_dir {
        let parent = dir.parent().map(Path::to_path_buf);
        if let Some(parent_dir) = parent {
            if parent_dir.join("config.py").exists() {
                return Ok(parent_dir);
            }
        }
        return Ok(dir);
    }

    let current_dir = std::env::current_dir().context("unable to read current dir")?;
    Ok(current_dir)
}

impl TargetLanguage {
    pub fn as_str(&self) -> &str {
        match self {
            TargetLanguage::C => "c",
            TargetLanguage::Go => "go",
            TargetLanguage::Other(s) => s.as_str(),
        }
    }
}

impl std::fmt::Display for TargetLanguage {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "{}", self.as_str())
    }
}

impl std::fmt::Display for FuzzingType {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        let name = match self {
            FuzzingType::White => "White",
            FuzzingType::Gray => "Gray",
            FuzzingType::Black => "Black",
        };
        f.write_str(name)
    }
}

