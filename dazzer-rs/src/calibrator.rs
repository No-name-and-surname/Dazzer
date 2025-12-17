#![allow(dead_code)]

use std::collections::{HashMap, HashSet};
use std::sync::Arc;
use std::time::{Duration, Instant};

use anyhow::{Context, Result};
use once_cell::sync::Lazy;
use parking_lot::Mutex;
use regex::Regex;

use crate::config::{FuzzerConfig, FuzzingType, TargetLanguage};
use crate::mutator::{MutationOutcome, Mutator};

#[derive(Debug, Clone)]
pub struct Calibrator {
    config: Arc<FuzzerConfig>,
    mutator: Arc<Mutator>,
    state: Arc<Mutex<CalibratorState>>, 
}

#[derive(Debug, Clone, Default)]
pub struct CalibratorState {
    pub queue_seg_fault: Vec<TestRecord>,
    pub queue_no_error: Vec<TestRecord>,
    pub queue_sig_fpe: Vec<TestRecord>,
    pub queue_timeout: Vec<TestRecord>,
    pub codes_count: HashMap<i32, usize>,
    pub seen_codes: HashSet<i32>,
    pub saved_tests: usize,
    pub max_coverage: f64,
}

#[derive(Debug, Clone)]
pub struct TestRecord {
    pub inputs: Vec<String>,
    pub outcome: TestResult,
    pub category: ErrorCategory,
}

#[derive(Debug, Clone)]
pub struct TestResult {
    pub return_code: i32,
    pub stdout: String,
    pub stderr: String,
    pub duration: Duration,
    pub mutation: Option<MutationOutcome>,
    pub sanitizer: Option<SanitizerKind>,
}

#[derive(Debug, Clone, Copy, Eq, PartialEq, Hash)]
pub enum ErrorCategory {
    SegmentationFault,
    FloatingPointException,
    Timeout,
    Sanitizer,
    NoError,
    Other,
}

#[derive(Debug, Clone, Copy, Eq, PartialEq, Hash)]
pub enum SanitizerKind {
    Address,
    UndefinedBehavior,
    Thread,
    Memory,
    Leak,
    GoRace,
    GoPanic,
    Generic,
}

#[derive(Debug, Default, Clone, Copy)]
pub struct CoverageStats {
    pub executed: usize,
    pub total: usize,
    pub percent: f64,
}

static SANITIZER_PATTERNS: Lazy<Vec<(SanitizerKind, Regex)>> = Lazy::new(|| {
    vec![
        (SanitizerKind::Address, Regex::new("AddressSanitizer").unwrap()),
        (
            SanitizerKind::UndefinedBehavior,
            Regex::new("UndefinedBehaviorSanitizer").unwrap(),
        ),
        (SanitizerKind::Thread, Regex::new("ThreadSanitizer").unwrap()),
        (SanitizerKind::Memory, Regex::new("MemorySanitizer").unwrap()),
        (SanitizerKind::Leak, Regex::new("LeakSanitizer").unwrap()),
        (
            SanitizerKind::GoRace,
            Regex::new("(?i)WARNING:.*race.*detected").unwrap(),
        ),
        (SanitizerKind::GoPanic, Regex::new("(?i)panic:").unwrap()),
    ]
});

impl Calibrator {
    pub fn new(config: Arc<FuzzerConfig>, mutator: Arc<Mutator>) -> Self {
        Self {
            config,
            mutator,
            state: Arc::new(Mutex::new(CalibratorState::default())),
        }
    }

    pub fn config(&self) -> &FuzzerConfig {
        &self.config
    }

    pub fn mutator(&self) -> &Mutator {
        &self.mutator
    }

    pub fn state(&self) -> Arc<Mutex<CalibratorState>> {
        Arc::clone(&self.state)
    }

    pub fn snapshot(&self) -> CalibratorState {
        self.state.lock().clone()
    }

    pub fn run_test(&self, input: &[String]) -> Result<TestResult> {
        let outcome = match self.config.fuzzing_type {
            FuzzingType::Black => self.run_network_test(input)?,
            _ => self.run_process_test(input)?,
        };
        Ok(outcome)
    }

    pub fn record_result(&self, inputs: Vec<String>, result: TestResult) {
        let category = self.categorize_error(&result);
        let mut state = self.state.lock();

        let record = TestRecord {
            inputs,
            outcome: result.clone(),
            category,
        };

        match category {
            ErrorCategory::SegmentationFault => state.queue_seg_fault.push(record),
            ErrorCategory::FloatingPointException => state.queue_sig_fpe.push(record),
            ErrorCategory::Timeout => state.queue_timeout.push(record),
            ErrorCategory::NoError | ErrorCategory::Other => state.queue_no_error.push(record),
            ErrorCategory::Sanitizer => state.queue_seg_fault.push(record),
        }

        *state.codes_count.entry(result.return_code).or_insert(0) += 1;
        state.seen_codes.insert(result.return_code);
    }

    pub fn measure_coverage(&self, _inputs: &[String]) -> Result<CoverageStats> {
        // TODO: Replicate gcov/coverprofile handling from the Python version.
        // This placeholder keeps the API available for the orchestrator while
        // we port the remaining coverage plumbing.
        // Coverage не изменяется автоматически - оставляем как есть
        Ok(CoverageStats::default())
    }

    pub fn categorize_error(&self, result: &TestResult) -> ErrorCategory {
        if let Some(kind) = result.sanitizer {
            return match kind {
                SanitizerKind::Address
                | SanitizerKind::UndefinedBehavior
                | SanitizerKind::Thread
                | SanitizerKind::Memory
                | SanitizerKind::Leak
                | SanitizerKind::GoRace
                | SanitizerKind::GoPanic
                | SanitizerKind::Generic => ErrorCategory::Sanitizer,
            };
        }

        match result.return_code {
            -11 | 139 => ErrorCategory::SegmentationFault,
            -8 | 136 => ErrorCategory::FloatingPointException,
            -1 => ErrorCategory::Timeout,
            0 => ErrorCategory::NoError,
            _ => ErrorCategory::Other,
        }
    }

    pub fn detect_sanitizer(&self, stderr: &str) -> Option<SanitizerKind> {
        if stderr.is_empty() {
            return None;
        }

        for (kind, regex) in SANITIZER_PATTERNS.iter() {
            if regex.is_match(stderr) {
                return Some(*kind);
            }
        }

        None
    }

    fn run_process_test(&self, input: &[String]) -> Result<TestResult> {
        use std::process::{Command, Stdio};

        let mut command = Command::new(&self.config.target_paths.binary_path);

        if matches!(self.config.target_language, TargetLanguage::Go) {
            command.arg("-race");
        }

        let start = Instant::now();
        let mut child = command
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
            .with_context(|| {
                format!(
                    "failed to spawn target binary {}",
                    self.config.target_paths.binary_path.display()
                )
            })?;

        if let Some(stdin) = child.stdin.as_mut() {
            for line in input {
                use std::io::Write;
                writeln!(stdin, "{}", line)?;
            }
        }

        let output = child
            .wait_with_output()
            .context("failed to collect target output")?;

        let duration = start.elapsed();
        let stderr = String::from_utf8_lossy(&output.stderr).to_string();
        let sanitizer = self.detect_sanitizer(&stderr);

        // Properly handle exit codes, including signal-based termination
        let return_code = output.status.code().unwrap_or_else(|| {
            #[cfg(unix)]
            {
                use std::os::unix::process::ExitStatusExt;
                if let Some(signal) = output.status.signal() {
                    // Convert signal number to exit code (128 + signal)
                    // This matches the convention used by shells
                    128 + signal as i32
                } else {
                    -1 // Unknown termination
                }
            }
            #[cfg(not(unix))]
            {
                -1 // On non-Unix systems, use -1 for unknown termination
            }
        });

        Ok(TestResult {
            return_code,
            stdout: String::from_utf8_lossy(&output.stdout).to_string(),
            stderr,
            duration,
            mutation: None,
            sanitizer,
        })
    }

    fn run_network_test(&self, input: &[String]) -> Result<TestResult> {
        use std::io::{Read, Write};
        use std::net::TcpStream;

        let mut stream = TcpStream::connect((&*self.config.network.host, self.config.network.port))
            .with_context(|| {
                format!(
                    "failed to connect to {}:{}",
                    self.config.network.host, self.config.network.port
                )
            })?;
        stream
            .set_read_timeout(Some(Duration::from_secs(self.config.network.timeout_secs)))
            .context("failed to set read timeout")?;
        stream
            .set_write_timeout(Some(Duration::from_secs(self.config.network.timeout_secs)))
            .context("failed to set write timeout")?;

        let start = Instant::now();
        for line in input {
            stream
                .write_all(line.as_bytes())
                .context("failed to write to network target")?;
            stream.write_all(b"\n").ok();
        }
        stream.flush().ok();

        let mut stdout = String::new();
        stream.read_to_string(&mut stdout).ok();

        let duration = start.elapsed();

        Ok(TestResult {
            return_code: 0,
            stdout,
            stderr: String::new(),
            duration,
            mutation: None,
            sanitizer: None,
        })
    }
}

