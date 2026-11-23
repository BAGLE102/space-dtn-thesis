CC ?= gcc
CFLAGS ?= -O2 -std=c11 -Wall -Wextra

dtn: main.c curve.c rules.c search.c dtn.h rat.h
	$(CC) $(CFLAGS) -o dtn main.c curve.c rules.c search.c

clean:
	rm -f dtn

.PHONY: clean
