path = r'd:\_Work\goat_bank\uir\projects\uir_base\paper\mdpi_electronics_120\main.tex'
with open(path, 'r', encoding='utf-8') as f:
    for idx, line in enumerate(f, 1):
        if '**' in line or '`' in line:
            print(f"{idx}: {line.strip()}")
