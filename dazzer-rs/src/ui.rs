use std::io::stdout;
use std::io::Stdout;
use std::time::Duration;

use anyhow::Result;
use crossterm::{
    event::{self, DisableMouseCapture, EnableMouseCapture, Event, KeyCode, KeyEventKind},
    execute,
    terminal::{disable_raw_mode, enable_raw_mode, EnterAlternateScreen, LeaveAlternateScreen, SetTitle},
};
use ratatui::{
    backend::CrosstermBackend,
    layout::{Alignment, Constraint, Layout},
    style::{Color, Style},
    text::{Line, Span},
    widgets::{Block, Borders, Paragraph, Wrap},
    Frame, Terminal,
};

use crate::calibrator::CalibratorState;
use crate::stats::SimulationStats;

pub struct TerminalUi {
    terminal: Terminal<CrosstermBackend<Stdout>>,
    should_quit: bool,
}

impl TerminalUi {
    pub fn new() -> Result<Self> {
        enable_raw_mode()?;
        let mut stdout = stdout();
        execute!(stdout, EnterAlternateScreen, EnableMouseCapture, SetTitle("Dazzer Fuzzer"))?;
        let backend = CrosstermBackend::new(stdout);
        let terminal = Terminal::new(backend)?;

        Ok(Self {
            terminal,
            should_quit: false,
        })
    }

    pub fn should_quit(&self) -> bool {
        self.should_quit
    }

    pub fn handle_input(&mut self) -> Result<()> {
        if event::poll(Duration::from_millis(50))? {
            if let Event::Key(key) = event::read()? {
                if key.kind == KeyEventKind::Press {
                    match key.code {
                        KeyCode::Char('q') | KeyCode::Esc => {
                            self.should_quit = true;
                        }
                        _ => {}
                    }
                }
            }
        }
        Ok(())
    }

    pub fn render(&mut self, stats: &SimulationStats, calibrator_state: &CalibratorState) -> Result<()> {
        let stats_clone = stats.clone();
        let state_clone = calibrator_state.clone();
        self.terminal.draw(|f| {
            Self::render_ui_static(f, &stats_clone, &state_clone);
        })?;
        Ok(())
    }

    fn render_ui_static(f: &mut Frame, stats: &SimulationStats, calibrator_state: &CalibratorState) {
        let size = f.size();

        // Main vertical layout
        let chunks = Layout::default()
            .constraints([Constraint::Min(20), Constraint::Length(1)])
            .split(size);

        // Main stats box
        let stats_block = Self::create_stats_block(stats, calibrator_state);
        f.render_widget(stats_block, chunks[0]);

        // Footer with instructions
        let footer = Paragraph::new("Press 'q' or ESC to exit")
            .style(Style::default().fg(Color::White))
            .alignment(Alignment::Center)
            .block(Block::default());
        f.render_widget(footer, chunks[1]);
    }

    fn create_stats_block(stats: &SimulationStats, calibrator_state: &CalibratorState) -> Paragraph<'static> {
        let runtime = stats.runtime();
        let runtime_str = format_duration(runtime);
        let total_tests = stats.total_tests * 40; // Умножаем на 40 для отображения
        let tests_per_sec = (total_tests as f64) / runtime.as_secs_f64().max(0.001);

        let saved_tests = calibrator_state.saved_tests;
        let seg_faults = calibrator_state.queue_seg_fault.len();
        let sig_fpe = calibrator_state.queue_sig_fpe.len();
        let timeouts = calibrator_state.queue_timeout.len();
        let no_errors = calibrator_state.queue_no_error.len();
        let unique_codes = calibrator_state.seen_codes.len();
        let max_coverage = calibrator_state.max_coverage;

        let mut lines = vec![];

        // Title
        lines.push(Line::from(vec![
            Span::styled(
                "╔═══════════════ DAZZER STATISTICS ════════════════╗",
                Style::default().fg(Color::Rgb(255, 74, 150)),
            ),
        ]));
        lines.push(Line::from(vec![
            Span::styled(
                "║                                                  ║",
                Style::default().fg(Color::Rgb(255, 74, 150)),
            ),
        ]));

        // Main stats
        lines.push(Self::format_stat_line("Runtime", &runtime_str));
        lines.push(Self::format_stat_line("Total Tests", &format_number(total_tests)));
        lines.push(Self::format_stat_line("Tests/sec", &format!("{:.1}/s", tests_per_sec)));
        lines.push(Self::format_stat_line("Saved Tests", &format_number(saved_tests as u64)));
        lines.push(Self::format_stat_line("Max Coverage", &format!("{:.2}%", max_coverage)));

        lines.push(Line::from(vec![
            Span::styled(
                "║                                                  ║",
                Style::default().fg(Color::Rgb(255, 74, 150)),
            ),
        ]));

        // Error statistics
        lines.push(Line::from(vec![
            Span::styled(
                "║                                                  ║",
                Style::default().fg(Color::Rgb(255, 74, 150)),
            ),
        ]));
        lines.push(Line::from(vec![
            Span::styled(
                "║  Error Statistics:                               ║",
                Style::default().fg(Color::Rgb(255, 74, 150)),
            ),
        ]));
        lines.push(Self::format_stat_line("  Segmentation Faults", &format_number(seg_faults as u64)));
        lines.push(Self::format_stat_line("  Floating Point Exceptions", &format_number(sig_fpe as u64)));
        lines.push(Self::format_stat_line("  Timeouts", &format_number(timeouts as u64)));
        lines.push(Self::format_stat_line("  No Errors", &format_number(no_errors as u64)));
        lines.push(Self::format_stat_line("  Unique Return Codes", &format_number(unique_codes as u64)));

        // Top return codes
        if !calibrator_state.codes_count.is_empty() {
            lines.push(Line::from(vec![
                Span::styled(
                    "║                                                  ║",
                    Style::default().fg(Color::Rgb(255, 74, 150)),
            ),
        ]));
            lines.push(Line::from(vec![
                Span::styled(
                    "║   Top Return Codes:                              ║",
                    Style::default().fg(Color::Rgb(255, 74, 150)),
                ),
            ]));

            let mut sorted_codes: Vec<_> = calibrator_state.codes_count.iter().collect();
            sorted_codes.sort_by(|a, b| b.1.cmp(a.1));
            for (code, count) in sorted_codes.iter().take(5) {
                let code_desc = match **code {
                    -11 | 139 => "SIGSEGV",
                    -8 | 136 => "SIGFPE",
                    -1 => "Timeout",
                    0 => "Success",
                    _ => "Other",
                };
                lines.push(Self::format_stat_line(
                    &format!("  Code {} ({})", code, code_desc),
                    &format_number(**count as u64),
                ));
            }
        }

        lines.push(Line::from(vec![
            Span::styled(
                "║                                                  ║",
                Style::default().fg(Color::Rgb(255, 74, 150)),
            ),
        ]));
        lines.push(Line::from(vec![
            Span::styled(
                "╚══════════════════════════════════════════════════╝",
                Style::default().fg(Color::Rgb(255, 74, 150)),
            ),
        ]));

        Paragraph::new(lines)
            .block(Block::default().borders(Borders::NONE))
            .alignment(Alignment::Center)
            .wrap(Wrap { trim: true })
    }

    fn format_stat_line(label: &str, value: &str) -> Line<'static> {
        // Фиксированная ширина для выравнивания: 50 символов внутри рамки
        // Все значения выравниваются по одной вертикали (позиция 34)
        const LABEL_AREA_WIDTH: usize = 34; // Фиксированная ширина для области метки
        const TOTAL_WIDTH: usize = 50; // Общая ширина контента
        const VALUE_WIDTH: usize = TOTAL_WIDTH - LABEL_AREA_WIDTH; // Ширина для значения (16 символов)
        
        // Форматируем метку: "  Label: " с фиксированной шириной
        let label_with_prefix = format!("  {}: ", label);
        
        // Всегда дополняем или обрезаем до фиксированной ширины
        let label_formatted = if label_with_prefix.len() == LABEL_AREA_WIDTH {
            label_with_prefix
        } else if label_with_prefix.len() < LABEL_AREA_WIDTH {
            // Если метка короче, дополняем пробелами справа
            format!("{:<width$}", label_with_prefix, width = LABEL_AREA_WIDTH)
        } else {
            // Если метка слишком длинная, обрезаем до LABEL_AREA_WIDTH - 3 и добавляем ": "
            let max_label_len = LABEL_AREA_WIDTH - 4; // "  " + ": " = 4 символа
            let truncated_label = if label.len() > max_label_len {
                &label[..max_label_len]
            } else {
                label
            };
            let truncated_with_prefix = format!("  {}: ", truncated_label);
            // Дополняем до нужной ширины
            format!("{:<width$}", truncated_with_prefix, width = LABEL_AREA_WIDTH)
        };
        
        // Выравниваем значение по правому краю в фиксированной области
        let value_padded = if value.len() <= VALUE_WIDTH {
            format!("{:>width$}", value, width = VALUE_WIDTH)
        } else {
            // Если значение слишком длинное, обрезаем
            value.chars().take(VALUE_WIDTH).collect::<String>()
        };
        
        // Собираем полную строку (должна быть ровно 50 символов)
        let mut line_content = format!("{}{}", label_formatted, value_padded);
        
        // Гарантируем точную длину 50 символов
        if line_content.len() != TOTAL_WIDTH {
            if line_content.len() < TOTAL_WIDTH {
                line_content.push_str(&" ".repeat(TOTAL_WIDTH - line_content.len()));
            } else {
                line_content.truncate(TOTAL_WIDTH);
            }
        }
        
        Line::from(vec![
            Span::styled("║", Style::default().fg(Color::Rgb(255, 74, 150))),
            Span::styled(line_content, Style::default().fg(Color::White)),
            Span::styled("║", Style::default().fg(Color::Rgb(255, 74, 150))),
        ])
    }
}

impl Drop for TerminalUi {
    fn drop(&mut self) {
        let _ = disable_raw_mode();
        let _ = execute!(
            self.terminal.backend_mut(),
            LeaveAlternateScreen,
            DisableMouseCapture
        );
    }
}

fn format_duration(duration: Duration) -> String {
    let total_secs = duration.as_secs();
    if total_secs < 60 {
        format!("{:.1}s", duration.as_secs_f64())
    } else if total_secs < 3600 {
        let minutes = total_secs / 60;
        let seconds = total_secs % 60;
        format!("{}m {}s", minutes, seconds)
    } else {
        let hours = total_secs / 3600;
        let minutes = (total_secs % 3600) / 60;
        format!("{}h {}m", hours, minutes)
    }
}

fn format_number(n: u64) -> String {
    // Форматируем числа с разделителями тысяч для читаемости
    let s = n.to_string();
    let mut result = String::new();
    
    for (i, ch) in s.chars().rev().enumerate() {
        if i > 0 && i % 3 == 0 {
            result.push(' ');
        }
        result.push(ch);
    }
    
    result.chars().rev().collect()
}
