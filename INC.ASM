mvi a, 0h
inc_loop:
out 10h
inr a
jmp inc_loop