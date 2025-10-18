{# This is a template file used by packer.py to create the test setup for animation player #}
SET_CHARSET_CALLBACK              = test_setcharset_index  ; Used by player to signal that we need to change charset when we swap frame
PLAYER_SET_ANIM_SLOWDOWN_CALLBACK = test_set_anim_slowdown ; Used by player to set anim frame slowdown counter
RESTART_CALLBACK                  = test_anim_restarted    ;
UNPACK_BUFFER_LOCATION            = $4400                  ; Memory address used by player to unpack the frames
EFFECT_LOCATION				      = {{ effect_start_address }}


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

{% if test_music %}
* = {{test_music_address}}
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

* = EFFECT_LOCATION
; Variables
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

{% if TEST_SLOWDOWN > 0 %}
	lda #{{ TEST_SLOWDOWN - 1 }}
	sta test_slowdown
	lda #{{ TEST_SLOWDOWN }}
	sta test_slowndown_frames
{% endif %}

	#screen_off
	#set_vic_bank 2

	{% if color_aberration_mode %}
	#clear_screen 0, $d800
	{% else %}
	{% if not use_color and "player_op_clear_color" not in ops_in_use %}
	#clear_screen 1, $d800
	{% endif %}
	{% endif %}

	#clear_screen {{ blank_char_index }}, UNPACK_BUFFER_LOCATION

	lda #0
	sta $d020
	sta $d021
	#set_screen_offset $0400

	lda #0
	sta test_charset_index
	jsr test_setcharset

	#setup_raster_irq test_raster_irq, 0

{% if test_music %}
	lda #1
	jsr $1000
{% endif %}

	jsr player_init

forever

	jsr player_unpack
	jsr wait_for_next_frame

	lda #0
	sta test_draw_next_frame

+	jmp forever



wait_for_next_frame .block
-	lda test_draw_next_frame
	cmp #1
	bne -
	rts
.endblock

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

{% if color_aberration_mode %}
	jsr test_color_aberration
{% endif %}

	lda #1
	sta test_draw_next_frame

	pla
	tay
	pla
	tax
	pla
	rti
.endblock

{% if color_aberration_mode %}
test_color_aberration .block
	ldx color_tick
	lda colors, x
	sta $d021
	lda scroll, x
	sta $d016
	inx
	cpx #{{len(color_aberration_colors)}}
	bne +
	ldx #0
+	stx color_tick
	rts
color_tick
	.byte 0
scroll
{% for val in color_aberration_scroll %}
	.byte {{val}}
{% endfor %}
colors
{% for col in color_aberration_colors %}
	.byte {{col}}
{% endfor %}
.endblock
{% endif %}

test_set_anim_slowdown
{% if TEST_SLOWDOWN > 0 %}
	; Update slowdown value we compare our frame counter against
	sta test_slowndown_frames
{% endif %}
	rts


; Called by player to store what the new charset should be
test_setcharset_index
	sta test_charset_index
	rts

; Called by player
test_anim_restarted
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
.byte 4, 6, 8, 10, 12, 14
.endblock
EFFECT_END_LOCATION=*
{% if only_per_row_mode %}
PLAYER_LOCATION=*
.include "player.asm"
{% endif %}

{% for idx, (filename, location) in enumerate(charset_files) %}
* = ${{location}}
CHARSET_{{idx}}_LOCATION={{location}}
.binary "{{ filename }}"
{% endfor %}

ANIM_LOCATION={{anim_start_address}}
* = ANIM_LOCATION
.binary "anim.bin"

{% if not only_per_row_mode %}
PLAYER_LOCATION=*
.include "player.asm"
{% endif %}


