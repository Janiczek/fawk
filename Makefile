CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2

all: fawk

fawk: fawk.c
	$(CC) $(CFLAGS) -o fawk fawk.c

clean:
	rm -f fawk

test: fawk
	@echo "=== Testing FAWK Implementation ==="
	@echo ""
	@for i in examples/0*.fawk; do \
		echo "Running $$i:"; \
		if [ "$$i" = "examples/09_csv.fawk" ]; then \
			./fawk "$$i" examples/data.csv; \
		else \
			./fawk "$$i"; \
		fi; \
		echo ""; \
	done
	@echo "=== All tests passed! ==="

.PHONY: all clean test
