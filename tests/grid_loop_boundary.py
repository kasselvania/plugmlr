"""Exact removable logical-position query; no playback or ramp rewrite allowed."""
def without_region_query(s):
    return (s.replace('route 0 1 2 3;', 'route 0 1 2;')
        .replace('#X obj 900 65 r \\$0-region-position-query;\n#X msg 900 105 3;\n#X obj 900 450 s \\$0-region-current-position;\n', '')
        .replace('#X connect 19 0 20 0;\n#X connect 20 0 12 0;\n#X connect 14 3 21 0;\n', ''))
