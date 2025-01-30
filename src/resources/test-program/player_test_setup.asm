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

* = {{ effect_start_address }}
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
{% if scroll_copy %}
test_scroll_x                 .byte 0
test_scroll_sx                .byte 0
test_scrolly                  .byte 0
test_scroll_src_ptr           = $66
test_scroll_dst_ptr           = $68
{% endif %}
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

	{% if scroll_copy %}
	jsr init_scroll
	{% endif %}

	lda #0
	sta $d020
	sta $d021

	jsr test_swap_frame

	lda #0
	sta test_charset_index
	jsr test_setcharset

	#setup_raster_irq test_raster_irq,0

{% if test_music %}
	lda #1
	jsr $1000
{% endif %}

{% if fill_color_with_effect %}
	jsr init_fill_color
{% endif %}

	jsr player_init

forever
	jsr player_unpack
	jsr copy_buffer
	jsr wait_for_next_frame
	jsr test_swap_frame

	lda #0
	sta test_draw_next_frame

+	jmp forever

copy_buffer .block
	lda test_current_buffer
	cmp #0
	bne +
	jsr test_copy_to_screen2
	jmp exit
+
	jsr test_copy_to_screen1
exit
	rts
.endblock

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

	{% if fill_color_with_effect %}
	jsr update_fill_color
	jsr do_one_fill_color_step
	{% endif %}

	lda test_draw_next_frame
	cmp #1
	beq exit

	{% if scroll_direction == "up"%}

	lda test_scrolly
	jsr test_set_scrolly

	lda test_scrolly
	clc
	sbc #1
	cmp #$ff
	bne +
	lda #7
+	sta test_scrolly

	lda test_scrolly
	cmp #7
	bne +
	lda #1
	sta test_draw_next_frame
+
	{% elif scroll_direction == "down" %}

	lda test_scrolly
	jsr test_set_scrolly

	lda test_scrolly
	clc
	adc #1
	cmp #8
	bne +
	lda #0
+	sta test_scrolly

	lda test_scrolly
	cmp #0
	bne +
	lda #1
	sta test_draw_next_frame
+

	{% else %}

	{% if TEST_SLOWDOWN > 0 %}
	inc test_slowdown
	lda test_slowdown
	cmp #{{ TEST_SLOWDOWN }}
	bne exit
	lda #0
	sta test_slowdown
	{% endif %}
	lda #1
	sta test_draw_next_frame
	{% endif %}

exit
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
	#wait_vblank
	#set_screen_offset $0800
	lda #1
	sta test_current_buffer
	jmp exit
+
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


{% if scroll_copy %}
init_scroll
	{% if scroll_direction == "up" or scroll_direction == "down" %}

	{% if scroll_direction == "up" %}
	lda #0

	sta test_scroll_sx

	lda #7
	{% else %}
	lda #{{used_area.x + used_area.height / 2}}
	sta test_scroll_sx

	lda #0
	{% endif %}
	sta test_scrolly


	{% else %}
	{% if not scroll_disable_repeat %}
	lda #{{used_area.x}}
	sta test_scroll_x
	lda #{{used_area.x}}
	sta test_scroll_sx
	{% else %}
	lda #0
	sta test_scroll_x
	lda #0
	sta test_scroll_sx
	{% endif %}
	{% endif %}
	rts

{% if scroll_direction == "left" %}
copy_scroll .macro
.block
{% if not scroll_disable_repeat %}
min_x = {{used_area.x}}
max_x = {{used_area.x + used_area.width - 1}}
{% else %}
min_x = 0
max_x = 39
{% endif %}
min_y = {{used_area.y}}
max_y = {{used_area.y + used_area.height}}

	ldx test_scroll_x
	ldy test_scroll_sx
loop
	.for row := min_y, row < max_y, row += 1
 	lda \1 + (row * 40), y
	sta \2 + (row * 40), x
	.endfor

	iny
	cpy #max_x+1
	bne +
	ldy #min_x
+

	inx
	cpx #40
	beq +
	jmp loop
+

	lda test_scroll_x
	cmp #0
	beq zero
	dec test_scroll_x
	jmp out
zero

	lda test_scroll_sx
	cmp #max_x
	bne +
	lda #min_x
	sta test_scroll_sx
+	inc test_scroll_sx
out
.endblock
.endmacro
{% elif scroll_direction == "right" %}
copy_scroll .macro
.block
{% if not scroll_disable_repeat %}
min_x = {{used_area.x}}
max_x = {{used_area.x + used_area.width - 1}}
{% else %}
min_x = 0
max_x = 39
{% endif %}
min_y = {{used_area.y}}
max_y = {{used_area.y + used_area.height}}


	ldx test_scroll_x
	ldy test_scroll_sx
loop
	.for row := min_y, row < max_y, row += 1
 	lda \1 + (row * 40), y
	sta \2 + (row * 40), x
	.endfor

	iny
	cpy #max_x+1
	bne +
	ldy #min_x
+

	inx
	cpx #40
	beq +
	jmp loop
+

	lda test_scroll_x
	cmp #0
	beq zero
	dec test_scroll_x
	jmp out
zero

	lda test_scroll_sx
	cmp #min_x
	bne +
	lda #max_x
	sta test_scroll_sx
+	dec test_scroll_sx
out
.endblock
.endmacro
{% elif scroll_direction == "up" or scroll_direction == "down" %}
copy_scroll .macro
.block
min_x = {{used_area.x}}
max_x = 1 + {{used_area.x + used_area.width}}
min_y = {{used_area.y}}
max_y = {{used_area.y + used_area.height}}
	ldx test_scroll_sx


{% for row in range(used_area.y, used_area.y + used_area.height) %}

	lda copy_src_lo,x
	sta test_scroll_src_ptr
	lda copy_src_hi,x
	sta test_scroll_src_ptr+1

	ldy #min_x
loop{{row}}
	lda (test_scroll_src_ptr),y
	sta \2 + {{row * 40}},y
	iny
	cpy #max_x
	bne loop{{row}}

	inx
	cpx #{{used_area.y + used_area.height}}
	bne +
	ldx #0
+

{% endfor %}

{% if scroll_direction == "up" %}
	inc test_scroll_sx
	lda test_scroll_sx
	cmp #{{used_area.y + used_area.height}}
	bne +
	lda #0
+	sta test_scroll_sx
{% else %}
	dec test_scroll_sx
	lda test_scroll_sx
	cmp #{{used_area.y-1}}
	bne +
	lda #{{max(0, used_area.y + used_area.height - 1)}}
+	sta test_scroll_sx
{% endif %}

	rts

.endblock
.endmacro
{% endif %}


{% if scroll_direction == "up" or scroll_direction == "down" %}
copy_src_lo
{% for row in range(0, 25) %}
.byte <(UNPACK_BUFFER_LOCATION + {{row * 40}} )
{% endfor %}
copy_src_hi
{% for row in range(0, 25) %}
.byte >(UNPACK_BUFFER_LOCATION + {{row * 40}} )
{% endfor %}
{% endif %}

test_set_scrolly
	sta $58
	lda $d011
	and #$78
	ora $58
	and #$7F
	sta $d011
	rts

{% endif %}


test_copy_to_screen1
{% if scroll_copy %}
	#copy_scroll UNPACK_BUFFER_LOCATION, SCREEN1_LOCATION
{% else %}
	#copy_screen UNPACK_BUFFER_LOCATION, SCREEN1_LOCATION
{% endif %}
	rts

test_copy_to_screen2
{% if scroll_copy %}
	#copy_scroll UNPACK_BUFFER_LOCATION, SCREEN2_LOCATION
{% else %}
	#copy_screen UNPACK_BUFFER_LOCATION, SCREEN2_LOCATION
{% endif %}
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
{% if fill_color_with_effect %}
.include "fill_color.asm"
{% endif %}


