#!/bin/bash
# P19: symbol census of the extracted Force/ION binaries.
cd /mnt/f/MTKeyWork/analysis/p19/bin || exit 1
O=/mnt/f/MTKeyWork/analysis/p19/raw; mkdir -p "$O"
{
for f in */opsetup.so */start */libtmaxx.so; do
  [ -f "$f" ] || continue
  n=$(readelf --dyn-syms "$f" 2>/dev/null | grep -c FUNC)
  k=$(readelf --dyn-syms "$f" 2>/dev/null | grep -ciE 'keymgr|readkeydata|dallas|option|tourn')
  printf '%-22s dynFUNC=%-6s keyish=%-5s %s\n' "$f" "$n" "$k" "$(file -b "$f" | cut -c1-70)"
done
echo
echo "=== key-related dynamic symbols per binary ==="
for f in */opsetup.so */start; do
  [ -f "$f" ] || continue
  out=$(readelf --dyn-syms "$f" 2>/dev/null | grep -oE '[A-Za-z_][A-Za-z0-9_]*' \
        | grep -iE 'keymgr|KeyData|Dallas|Option|Tourn|Country|Currency|Territory|Lang|Coin|Lockout|Serial|Laser' \
        | sort -u)
  echo "--- $f : $(echo "$out" | grep -c .) matches"
  echo "$out" | head -60
done
} > "$O/syms.txt" 2>&1
grep -E 'dynFUNC|^---' "$O/syms.txt"
