;  2SIO echo routine

	org	0
	;reset UART
	mvi	a,03h
	out	10h
	;no RI, no XI, RTS Low, 8n1, /16
	mvi	a,15h
	out	10h
wtRcv:	
	;character received?
	in	10h
	;receive flag in lsb
	rrc
	jnc	wtRcv
	;read the character
	in	11h
	;echo it back out
	out	11h
	jmp	wtRcv
	end

