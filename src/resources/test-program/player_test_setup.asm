{# This is a template file used by packer.py to create the test setup for animation player #}
SET_CHARSET_CALLBACK         = test_setcharset_index  ; Used by player to signal that we need to change charset when we swap frame
RESTART_CALLBACK             = test_anim_restarted    ;
UNPACK_BUFFER_LOCATION       = $0400                  ; Memory address used by player to unpack the frames
COLOR_UNPACK_BUFFER_LOCATION = $0800                  ; Memory address used by player to unpack the color frames
PLAYER_LOCATION              = $3000                  ; Player location calculated by packer, placed after chardsets and animation data
SCREEN1_LOCATION             = $4400
SCREEN2_LOCATION             = $4800

; Player will now write color changes for border and background to these locations
PLAYER_BORDER_COLOR_VAR      = test_border_color
PLAYER_BACKGROUND_COLOR_VAR  = test_background_color

wait_vblank .macro
-	bit $d011
	bpl -
-	bit $d012
	bmi -
.endm

set_screen_offset .macro
	lda $d018
	and #%00001111
	ora #(((\1 % $4000) / $0400) << 4)
	sta $d018
.endmacro

set_vic_bank .macro
	.if (\1 < 0) || (\1 > 3)
		.error "Invalid bank number. Must be 0-3."
	.endif
	lda #\1
	sta $dd00
.endmacro

; Your existing macros
screen_off .macro
	#wait_vblank
	lda $d011
	and #%01101111
	sta $d011
.endmacro

screen_on .macro
	#wait_vblank
	lda $d011
	ora #%00010000
	and #%01111111
	sta $d011
.endmacro

clear_screen .macro
	lda #\1
	ldx #$fa
-
	dex
	sta $0000+\2,x
	sta $00fa+\2,x
	sta $01f4+\2,x
	sta $02ee+\2,x
	bne -
.endmacro

copy_max_127 .macro
	ldx #\3 - 1
-	lda \1,x
	sta \2,x
	dex
	bpl -
.endmacro

copy_screen .macro
	ldx #125
-
	lda \1 + 000, x
	sta \2 + 000, x

	lda \1 + 125, x
	sta \2 + 125, x

	lda \1 + 250, x
	sta \2 + 250, x

	lda \1 + 375, x
	sta \2 + 375, x

	lda \1 + 500, x
	sta \2 + 500, x

	lda \1 + 625, x
	sta \2 + 625, x

	lda \1 + 750, x
	sta \2 + 750, x

	lda \1 + 875, x
	sta \2 + 875, x

	dex
	bpl -
.endmacro

setup_raster_irq .macro
	sei
	; Position
	lda #\2
	sta $d012

	; Proc
	lda #<\1
	sta $fffe
	lda #>\1
	sta $ffff

	; Enable raster IRQ
	lda $d01a
	ora #$01
	sta $d01a
	lda #$1B
	sta $d011
	asl $d019
	cli
.endmacro

* = $54
	player_data_src_ptr     .addr ?
	player_macro_block_tmp  .fill 1
	player_general_tmp      .fill 1

{% if test_music %}
* = $1000
	.binary	"{{test_music}}"
{% endif %}

* = $0801
	.word (+), 10
	.null $9e, "2064"
	+ .word 0

; Main program
* = $0810
	; Disable interrupts
	ldy #$7f    ; $7f = %01111111
	sty $dc0d   ; Turn off CIAs Timer interrupts
	sty $dd0d   ; Turn off CIAs Timer interrupts

	; Set memory config
	lda $01
	and #%11111000
	ora #%101
	sta $01

; For integration
; * = $fff0
	jmp start

* = $3000
; Variables
{% if TEST_SLOWDOWN > 0 %}
test_slowdown                 .byte {{ TEST_SLOWDOWN - 1 }}
{% endif %}
test_charset_index            .byte 0
test_current_buffer           .byte 0
test_draw_next_frame          .byte 0
test_background_color         .byte 255
test_border_color             .byte 255
test_tick                     .byte 0
; Code
start

	lda #0
	sta test_charset_index
	sta test_current_buffer
	sta test_draw_next_frame
	lda #255
	sta test_background_color
	sta test_border_color

	#screen_off
	#set_vic_bank 2

	{% if not use_color and "player_op_clear_color" not in ops_in_use %}
	#clear_screen 1, $d800
	{% endif %}

	#clear_screen {{ blank_char_index }}, SCREEN1_LOCATION
	#clear_screen {{ blank_char_index }}, SCREEN2_LOCATION
	jsr clear_unpack_buffers

	;jsr test_anim_restarted

	lda #0
	sta $d020
	sta $d021

	jsr test_swap_frame

	lda #0
	sta test_charset_index
	jsr test_setcharset

	#setup_raster_irq test_raster_irq,50

{% if test_music %}
	lda #1
	jsr $1000
{% endif %}

{% if fill_color_with_effect %}
	jsr init_fill_color
{% endif %}

	jsr player_init

forever
	lda test_draw_next_frame
	cmp #1
	bne +

	jsr player_unpack
	jsr test_swap_frame

	lda #0
	sta test_draw_next_frame

+	jmp forever

test_raster_irq .block
	pha
	txa
	pha
	tya
	pha
	asl $d019
{% if test_music %}
	jsr $1003
{% endif %}

	{% if fill_color_with_effect %}
	jsr update_fill_color
	jsr do_one_fill_color_step
	{% endif %}

	lda test_draw_next_frame
	cmp #1
	beq +

	{% if TEST_SLOWDOWN > 0 %}
	inc test_slowdown
	lda test_slowdown
	cmp #{{ TEST_SLOWDOWN }}
	bne +
	lda #0
	sta test_slowdown
	{% endif %}
	lda #1
	sta test_draw_next_frame
+
	pla
	tay
	pla
	tax
	pla
	rti
.endblock

test_swap_frame .block

	lda test_current_buffer
	cmp #0
	bne +

	; Showing buffer 0, which is SCREEN1_LOCATION, write new frame to SCREEN2_LOCATION
	jsr test_copy_to_screen2
	#wait_vblank
	#set_screen_offset $0800
	lda #1
	sta test_current_buffer
	jmp exit

+
	; Showing buffer 1 currently ...
	jsr test_copy_to_screen1
	#wait_vblank
	#set_screen_offset $0400
	lda #0
	sta test_current_buffer

exit
	lda test_border_color
	cmp #$ff
	beq +
	sta $d020
	lda #$ff
	sta test_border_color
+	lda test_background_color
	cmp #$ff
	beq +
	sta $d021
	lda #$ff
	sta test_background_color
+
{% if use_color %}
	lda player_color_changes
	cmp #1
	bne +
	jsr test_copy_color
	lda #0
	sta player_color_changes
+
{% endif %}
	lda test_charset_index
	jsr test_setcharset
	rts
.endblock

test_copy_to_screen1
	#copy_screen UNPACK_BUFFER_LOCATION, SCREEN1_LOCATION
	rts

test_copy_to_screen2
	#copy_screen UNPACK_BUFFER_LOCATION, SCREEN2_LOCATION
	rts

{% if use_color %}
test_copy_color
{% for unroll in range(0, 250) %}
	lda COLOR_UNPACK_BUFFER_LOCATION + {{ unroll}}
	sta $d800 + {{ unroll }}
{% endfor %}
{% for unroll in range(2, 8) %}
	#copy_max_127 COLOR_UNPACK_BUFFER_LOCATION + {{ unroll * 125}}, $d800 + {{ unroll * 125}}, 125
{% endfor %}
	rts
{% endif %}

; Called by player to store what the new charset should be
test_setcharset_index
	sta test_charset_index
	rts

test_anim_restarted

clear_unpack_buffers
	#clear_screen {{ blank_char_index }}, COLOR_UNPACK_BUFFER_LOCATION
	#clear_screen {{ blank_char_index }}, UNPACK_BUFFER_LOCATION
	rts

; A = Charset index
test_setcharset .block
	tay
	lda helper_table,y
	sta or_value+1
	lda $d018
	and #%11110001
or_value
	ora #6
	sta $d018
	rts
helper_table
.byte 6, 8, 10, 12, 14
.endblock
{% if fill_color_with_effect %}
.include "fill_color.asm"
{% endif %}
{% if only_per_row_mode %}
.include "player.asm"
{% endif %}

{% for filename, location in charset_files %}
* = ${{location}}
.binary "{{ filename }}"
{% endfor %}

ANIM_LOCATION=*
.binary "anim.bin"

{% if not only_per_row_mode %}
.include "player.asm"
{% endif %}



