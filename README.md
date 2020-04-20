# Backbase

Backbase Interview Task. This program is written using Python 3.8.2 but any Python 3 shell versions should work.

## Instructions

Run in desired terminal on Windows/macOS/Linux. All csv files should be in the same directory as the python file.

Install dependencies:

```bash
pip install -r requirements.txt
```

Run with:

```bash
python program_noComment.py
```

## Assumptions

1. All accounts balance start at 0.
2. Csv files are only valid in format 'customer-xxxxxxx-ledger.csv', where xxxxxxx is the 7 digit custome number with integers between 0-9 for each character.
3. Modified files are exported in the name format 'customer-xxxxxxx-ledger-modified.csv', where xxxxxx is the 7 digit customer number with integers between 0-9 for each character.
4. Savings account can't drop below 0.
5. Import format in columns order AccountID, AccountType, InitiatorType, DataTime,
TransactionValue
6. System initiated transactions are initiated immediately post detection of negative
    current account balance and where savings amount permit a transfer to current
    account.
