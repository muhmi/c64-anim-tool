.PHONY: build run

build: test.asm player.asm build_player
	64tass -o test.prg test.asm

build_player:
	64tass -o player.prg player.asm

run: build
	x64sc test.prg

.DEFAULT_GOAL := run