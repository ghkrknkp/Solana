mod pb;

use pb::my::solana::transfers::v1::{Transfer, Transfers};
use substreams::errors::Error;
use substreams_solana::pb::sf::solana::r#type::v1::Block;

const SYSTEM_PROGRAM: &str = "11111111111111111111111111111111";
const TOKEN_PROGRAM: &str = "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA";
const TOKEN_2022_PROGRAM: &str = "TokenzQdBNbLqP5VEhdkAS6EPFLC1PHnBqCXEpPxuEb";

#[substreams::handlers::map]
pub fn map_transfers(block: Block) -> Result<Transfers, Error> {
    let mut transfers = Vec::new();

    for confirmed_trx in block.transactions() {
        // Skip failed transactions
        if let Some(meta) = &confirmed_trx.meta {
            if meta.err.is_some() {
                continue;
            }
        }

        let trx = match &confirmed_trx.transaction {
            Some(t) => t,
            None => continue,
        };

        let message = match &trx.message {
            Some(m) => m,
            None => continue,
        };

        // Fully resolve static and Address Lookup Table (ALT) accounts
        let accounts: Vec<String> = confirmed_trx.resolved_accounts();

        // 1. Process top-level instructions
        for ix in &message.instructions {
            let program_id_idx = ix.program_id_index as usize;
            if program_id_idx < accounts.len() {
                let program_id = &accounts[program_id_idx];
                extract_transfer_from_instruction(
                    program_id,
                    &ix.accounts,
                    &ix.data,
                    &accounts,
                    &mut transfers,
                );
            }
        }

        // 2. Process inner instructions (CPI calls)
        if let Some(meta) = &confirmed_trx.meta {
            for inner in &meta.inner_instructions {
                for inner_ix in &inner.instructions {
                    let program_id_idx = inner_ix.program_id_index as usize;
                    if program_id_idx < accounts.len() {
                        let program_id = &accounts[program_id_idx];
                        extract_transfer_from_instruction(
                            program_id,
                            &inner_ix.accounts,
                            &inner_ix.data,
                            &accounts,
                            &mut transfers,
                        );
                    }
                }
            }
        }
    }

    Ok(Transfers { transfers })
}

fn extract_transfer_from_instruction(
    program_id: &str,
    account_indices: &[u8],
    data: &[u8],
    accounts: &[String],
    transfers: &mut Vec<Transfer>,
) {
    if program_id == SYSTEM_PROGRAM {
        // System Program: Transfer (instruction index 2)
        // Data layout: [2, 0, 0, 0] (4 bytes little-endian) + lamports (8 bytes little-endian)
        if data.len() >= 12 && data[0..4] == [2, 0, 0, 0] {
            if account_indices.len() >= 2 {
                let from_idx = account_indices[0] as usize;
                let to_idx = account_indices[1] as usize;
                if from_idx < accounts.len() && to_idx < accounts.len() {
                    let amount = u64::from_le_bytes(data[4..12].try_into().unwrap());
                    transfers.push(Transfer {
                        from: accounts[from_idx].clone(),
                        to: accounts[to_idx].clone(),
                        amount,
                    });
                }
            }
        }
        // System Program: TransferWithSeed (instruction index 11)
        // Data layout: [11, 0, 0, 0] (4 bytes little-endian) + lamports (8 bytes little-endian)
        else if data.len() >= 12 && data[0..4] == [11, 0, 0, 0] {
            if account_indices.len() >= 3 {
                let from_idx = account_indices[0] as usize;
                let to_idx = account_indices[2] as usize;
                if from_idx < accounts.len() && to_idx < accounts.len() {
                    let amount = u64::from_le_bytes(data[4..12].try_into().unwrap());
                    transfers.push(Transfer {
                        from: accounts[from_idx].clone(),
                        to: accounts[to_idx].clone(),
                        amount,
                    });
                }
            }
        }
    } else if program_id == TOKEN_PROGRAM || program_id == TOKEN_2022_PROGRAM {
        if data.is_empty() {
            return;
        }

        // SPL Token: Transfer (instruction index 3)
        // Data layout: [3] (1 byte) + amount (8 bytes little-endian)
        if data[0] == 3 && data.len() >= 9 {
            if account_indices.len() >= 2 {
                let from_idx = account_indices[0] as usize;
                let to_idx = account_indices[1] as usize;
                if from_idx < accounts.len() && to_idx < accounts.len() {
                    let amount = u64::from_le_bytes(data[1..9].try_into().unwrap());
                    transfers.push(Transfer {
                        from: accounts[from_idx].clone(),
                        to: accounts[to_idx].clone(),
                        amount,
                    });
                }
            }
        }
        // SPL Token: TransferChecked (instruction index 12)
        // Data layout: [12] (1 byte) + amount (8 bytes little-endian) + decimals (1 byte)
        // Account keys: [source, mint, destination, authority]
        else if data[0] == 12 && data.len() >= 10 {
            if account_indices.len() >= 3 {
                let from_idx = account_indices[0] as usize;
                let to_idx = account_indices[2] as usize;
                if from_idx < accounts.len() && to_idx < accounts.len() {
                    let amount = u64::from_le_bytes(data[1..9].try_into().unwrap());
                    transfers.push(Transfer {
                        from: accounts[from_idx].clone(),
                        to: accounts[to_idx].clone(),
                        amount,
                    });
                }
            }
        }
    }
}

