#![allow(dead_code)]

use std::time::{Duration, Instant};

use parking_lot::Mutex;

#[derive(Debug, Default, Clone)]
pub struct SimulationStats {
    pub total_tests: u64,
    pub start_time: Option<Instant>,
}

impl SimulationStats {
    pub fn new() -> Self {
        Self {
            total_tests: 0,
            start_time: Some(Instant::now()),
        }
    }

    pub fn mark_test(&mut self, count: u64) {
        self.total_tests += count;
    }

    pub fn runtime(&self) -> Duration {
        self.start_time
            .map(|start| start.elapsed())
            .unwrap_or_else(|| Duration::from_secs(0))
    }

    pub fn tests_per_second(&self) -> f64 {
        let runtime = self.runtime().as_secs_f64();
        if runtime <= f64::EPSILON {
            0.0
        } else {
            self.total_tests as f64 / runtime
        }
    }
}

#[derive(Debug, Default)]
pub struct ThreadStats {
    pub thread_name: String,
    pub executed_tests: u64,
}

#[derive(Debug, Default)]
pub struct SharedStats {
    pub overall: Mutex<SimulationStats>,
}

impl SharedStats {
    pub fn new() -> Self {
        Self {
            overall: Mutex::new(SimulationStats::new()),
        }
    }
}

