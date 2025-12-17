use std::sync::atomic::{AtomicBool, Ordering};
use std::sync::Arc;
use std::thread;
use std::time::Duration;

use anyhow::{Context, Result};
use crossbeam_channel::{unbounded, Receiver};

use crate::calibrator::{Calibrator, CoverageStats, TestRecord};
use crate::config::FuzzerConfig;
use crate::mutator::Mutator;
use crate::stats::SharedStats;
use crate::ui::TerminalUi;
use crate::utils::read_dictionary;

struct WorkerEvent {
    thread_name: String,
    record: TestRecord,
    coverage: CoverageStats,
}

pub fn run() -> Result<()> {
    let config = FuzzerConfig::load_default()
        .context("failed to load default configuration for Dazzer")?;
    config.ensure_runtime_dirs()?;

    let dictionary = read_dictionary(&config.result_paths.dict_file).unwrap_or_default();
    let mutator = Arc::new(Mutator::new(dictionary));
    let initial_args = config.args.clone();
    let config = Arc::new(config);
    let calibrator = Arc::new(Calibrator::new(Arc::clone(&config), Arc::clone(&mutator)));

    let baseline = calibrator
        .run_test(&initial_args)
        .context("failed to execute baseline test run")?;
    calibrator.record_result(initial_args.clone(), baseline.clone());

    let shared_stats = Arc::new(SharedStats::new());
    let mut ui = TerminalUi::new()?;

    let (work_tx, work_rx) = unbounded::<Vec<String>>();
    let (result_tx, result_rx) = unbounded::<WorkerEvent>();
    let stop_flag = Arc::new(AtomicBool::new(false));

    work_tx
        .send(initial_args.clone())
        .context("failed to enqueue initial test case")?;

    let mut handles = Vec::new();

    for worker_id in 0..config.performance.num_threads {
        let thread_name = format!("fuzz-worker-{}", worker_id + 1);
        let worker_rx = work_rx.clone();
        let worker_tx = result_tx.clone();
        let worker_calibrator = Arc::clone(&calibrator);
        let worker_mutator = Arc::clone(&mutator);
        let worker_stats = Arc::clone(&shared_stats);
        let worker_stop = Arc::clone(&stop_flag);

        let handle = thread::Builder::new()
            .name(thread_name.clone())
            .spawn(move || worker_loop(
                thread_name,
                worker_rx,
                worker_tx,
                worker_calibrator,
                worker_mutator,
                worker_stats,
                worker_stop,
            ))
            .context("failed to spawn fuzzing worker")?;

        handles.push(handle);
    }

    drop(result_tx);

    loop {
        // Handle input
        ui.handle_input()?;
        if ui.should_quit() {
            break;
        }

        // Process events - обрабатываем все доступные события
        let mut events_processed = 0;
        while events_processed < 10 {
            match result_rx.recv_timeout(Duration::from_millis(10)) {
                Ok(event) => {
                    work_tx.send(event.record.inputs.clone()).ok();
                    events_processed += 1;
                }
                Err(crossbeam_channel::RecvTimeoutError::Timeout) => break,
                Err(crossbeam_channel::RecvTimeoutError::Disconnected) => break,
            }
        }

        // Get stats snapshot
        let stats_snapshot = {
            let guard = shared_stats.overall.lock();
            guard.clone()
        };

        // Get calibrator state
        let calibrator_state = calibrator.snapshot();

        // Render UI (обновляем каждые 100ms для плавности)
        ui.render(&stats_snapshot, &calibrator_state)?;
        
        // Небольшая задержка для плавного обновления UI
        thread::sleep(Duration::from_millis(50));
    }

    stop_flag.store(true, Ordering::Relaxed);
    drop(work_tx);

    for handle in handles {
        let _ = handle.join();
    }

    Ok(())
}

fn worker_loop(
    thread_name: String,
    work_rx: Receiver<Vec<String>>,
    result_tx: crossbeam_channel::Sender<WorkerEvent>,
    calibrator: Arc<Calibrator>,
    mutator: Arc<Mutator>,
    shared_stats: Arc<SharedStats>,
    stop_flag: Arc<AtomicBool>,
) {
    while !stop_flag.load(Ordering::Relaxed) {
        let seed = match work_rx.recv() {
            Ok(seed) => seed,
            Err(_) => break,
        };

        if seed.is_empty() {
            continue;
        }

        let mut mutated_input = seed.clone();
        let target_index = 0;
        let base_value = mutated_input[target_index].clone();
        let min_length = base_value.len().max(4);
        let outcome = mutator.mutate(&base_value, min_length);
        mutated_input[target_index] = outcome.mutated.clone();

        match calibrator.run_test(&mutated_input) {
            Ok(mut test_result) => {
                test_result.mutation = Some(outcome.clone());
                calibrator.record_result(mutated_input.clone(), test_result.clone());

                {
                    let mut guard = shared_stats.overall.lock();
                    guard.mark_test(1);
                }

                // Измеряем покрытие (оно автоматически обновляет max_coverage внутри)
                let coverage = calibrator
                    .measure_coverage(&mutated_input)
                    .unwrap_or_default();
                
                let category = calibrator.categorize_error(&test_result);
                let record = TestRecord {
                    inputs: mutated_input,
                    outcome: test_result,
                    category,
                };

                let _ = result_tx.send(WorkerEvent {
                    thread_name: thread_name.clone(),
                    record,
                    coverage,
                });
            }
            Err(_err) => {
                // Ошибки не выводятся в терминал, чтобы не портить TUI
                // Можно добавить счетчик ошибок в состояние калибратора при необходимости
            }
        }
    }
}

