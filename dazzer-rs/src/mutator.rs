#![allow(dead_code)]

use rand::seq::SliceRandom;
use rand::Rng;

#[derive(Debug, Clone, Copy, Eq, PartialEq, Hash)]
pub enum MutationStrategy {
    Interesting,
    ChangeSymbol,
    ChangeLength,
    Xor,
    Dictionary,
}

#[derive(Debug, Clone)]
pub struct MutationOutcome {
    pub mutated: String,
    pub strategy: MutationStrategy,
}

#[derive(Debug, Default)]
pub struct Mutator {
    interesting_values: Vec<String>,
    dictionary: Vec<String>,
}

impl Mutator {
    pub fn new(dictionary: Vec<String>) -> Self {
        Self {
            interesting_values: default_interesting_values()
                .iter()
                .map(|s| s.to_string())
                .collect(),
            dictionary,
        }
    }

    pub fn mutate(&self, seed: &str, min_length: usize) -> MutationOutcome {
        let strategies = [
            MutationStrategy::Interesting,
            MutationStrategy::ChangeSymbol,
            MutationStrategy::ChangeLength,
            MutationStrategy::Xor,
            MutationStrategy::Dictionary,
        ];
        let mut rng = rand::thread_rng();
        let strategy = *strategies.choose(&mut rng).unwrap_or(&MutationStrategy::Interesting);
        let mutated = match strategy {
            MutationStrategy::Interesting => self.pick_interesting(seed),
            MutationStrategy::ChangeSymbol => change_symbol(seed),
            MutationStrategy::ChangeLength => change_length(seed, min_length),
            MutationStrategy::Xor => xor_mutate(seed),
            MutationStrategy::Dictionary => self.dictionary_mutation(seed, min_length),
        };

        MutationOutcome { mutated, strategy }
    }

    fn pick_interesting(&self, _seed: &str) -> String {
        let mut rng = rand::thread_rng();
        self.interesting_values
            .choose(&mut rng)
            .cloned()
            .unwrap_or_else(|| "0".to_string())
    }

    fn dictionary_mutation(&self, seed: &str, min_length: usize) -> String {
        let mut rng = rand::thread_rng();
        let candidate = self.dictionary.choose(&mut rng);
        match candidate {
            Some(entry) => ensure_min_length(entry, min_length),
            None => change_symbol(seed),
        }
    }
}

fn xor_mutate(seed: &str) -> String {
    let mut rng = rand::thread_rng();
    let xor_value: u8 = rng.gen_range(33..=126);
    seed.chars()
        .map(|c| ((c as u8) ^ xor_value) as char)
        .collect()
}

fn change_symbol(seed: &str) -> String {
    if seed.is_empty() {
        return seed.to_string();
    }

    let mut chars: Vec<char> = seed.chars().collect();
    let mut rng = rand::thread_rng();
    let index = rng.gen_range(0..chars.len());
    let replacement: u8 = rng.gen_range(33..=126);
    chars[index] = replacement as char;
    chars.into_iter().collect()
}

fn change_length(seed: &str, min_length: usize) -> String {
    let mut rng = rand::thread_rng();
    let mut chars: Vec<char> = seed.chars().collect();
    if rng.gen_bool(0.5) {
        // delete a character
        if !chars.is_empty() {
            let index = rng.gen_range(0..chars.len());
            chars.remove(index);
        }
    } else {
        // insert random characters
        let additional = rng.gen_range(1..=3);
        for _ in 0..additional {
            let ch = rng.gen_range(33..=126) as u8 as char;
            let index = rng.gen_range(0..=chars.len());
            chars.insert(index, ch);
        }
    }
    let mut result: String = chars.into_iter().collect();
    if result.len() < min_length {
        let padding_len = min_length.saturating_sub(result.len());
        let padding: String = (0..padding_len)
            .map(|_| rng.gen_range(33..=126) as u8 as char)
            .collect();
        result.push_str(&padding);
    }
    result
}

fn default_interesting_values() -> &'static [&'static str] {
    &[
        "0",
        "1",
        "-1",
        "127",
        "128",
        "255",
        "256",
        "32767",
        "32768",
        "65535",
        "65536",
        "2147483647",
        "-2147483648",
        "4294967295",
        "4294967296",
        "9223372036854775807",
        "-9223372036854775808",
    ]
}

fn ensure_min_length(candidate: &str, min_length: usize) -> String {
    if candidate.len() >= min_length {
        candidate.to_string()
    } else {
        let mut candidate = candidate.to_string();
        let mut rng = rand::thread_rng();
        while candidate.len() < min_length {
            candidate.push(rng.gen_range(33..=126) as u8 as char);
        }
        candidate
    }
}

