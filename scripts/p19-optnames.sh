#!/bin/bash
# P19: hunt the Gen4 option-name / game-name tables.
B=/mnt/f/MTKeyWork/analysis/p19/bin
R=/mnt/f/MTKeyWork/analysis/p19/raw
echo "=== xml file names referenced by ION 2014 start ==="
grep -aoE '[A-Za-z0-9_./-]+[.]xml' "$B/I2014/start" | sort -u | head -40
echo
echo "=== xml_gameoptions / xml_gameinfo symbols ==="
grep -iE 'xml_gameoptions|xml_gameinfo' "$R/I2014.start.dem.txt" | head -60
echo
echo "=== GameOption-ish symbols ==="
grep -iE 'GameOption|OptionName|OptionDesc|OptionsButton|gameoption' "$R/I2014.start.dem.txt" | head -60
echo
echo "=== dat/cfg/db files referenced ==="
grep -aoE '/usr/local/share/merit/[A-Za-z0-9_./-]+' "$B/I2014/start" | sort -u | head -60
