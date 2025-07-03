#!/usr/bin/env python3

symbols = ['LIXTW', 'SONN', 'NTRBW', 'AEBI', 'BCTXW', 'CDTTW']

def is_valid_symbol(symbol):
    # Basic filtering
    if len(symbol) > 4 or not symbol.isalpha():
        return False
    # Skip common warrant suffixes
    if symbol.endswith('W') or symbol.endswith('+'):
        return False
    return True

valid = [s for s in symbols if is_valid_symbol(s)]
filtered_out = [s for s in symbols if not is_valid_symbol(s)]

print(f'Original symbols: {symbols}')
print(f'Valid symbols: {valid}')
print(f'Filtered out: {filtered_out}')
print(f'Count: {len(valid)} valid out of {len(symbols)} total') 