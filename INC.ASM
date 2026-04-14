mvi a, 0h
inc_loop:
out 16h
inr a
jmp inc_loop