# Date-chain correction

Generated period timestamps now advance by each generated cycle's length instead of a fixed 38-day spacing. The patch makes no new random-number draw and does not change classifier inputs: features use arrays, generated labels, and prior logged cycle lengths rather than the displayed timestamps. The regression suite refits the persisted pipeline against current generated data and confirms the frozen raw artifact remains immutable. The frozen one-time result is retained; it was generated before this timestamp-only correction.
