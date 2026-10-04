#!/bin/bash
# P19: is the xml_gameinfo::GameIds enum order visible in the binary?
B=/mnt/f/MTKeyWork/analysis/p19/bin
for t in I2014 F2011 I2011; do
  echo "=== $t"
  echo -n "  G_SOLITAIRE occurrences: "; grep -aoc 'G_SOLITAIRE' "$B/$t/start" 2>/dev/null || echo 0
  echo -n "  G_ string count:         "; grep -aoE 'G_[A-Z0-9_]{3,40}' "$B/$t/start" | sort -u | wc -l
  echo "  first 12 unique G_ strings in file order:"
  grep -aoE 'G_[A-Z0-9_]{3,40}' "$B/$t/start" | awk '!seen[$0]++' | head -12 | sed 's/^/    /'
  echo "  GameIds-related symbols:"
  readelf -W --dyn-syms "$B/$t/start" 2>/dev/null | awk '$4=="OBJECT"{print $8}' | sed 's/@.*//' \
    | c++filt | grep -iE 'gameid|gamename|game_name|gametable|xml_gameinfo' | head -10 | sed 's/^/    /'
done
