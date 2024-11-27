{# This is a template file used by packer.py to create the animation player #}
; These must be defined by user:
.weak
ANIM_LOCATION                = $8000
SET_CHARSET_CALLBACK         = $0000
RESTART_CALLBACK             = $0000
UNPACK_BUFFER_LOCATION       = $4400
COLOR_UNPACK_BUFFER_LOCATION = $4800
PLAYER_BORDER_COLOR_VAR      = $d020
PLAYER_BACKGROUND_COLOR_VAR  = $d021
.endweak

; Constants
SCREEN_WIDTH     = 40
SCREEN_HEIGHT    = 25
Y_STEP           = {{y_step}}
X_STEP           = {{x_step}}
BLOCK_SIZE_X     = {{block_size_x}}
BLOCK_SIZE_Y     = {{block_size_y}}

PLAYER_STATE_IDLE                = 0
PLAYER_STATE_WRITE_TO_SCREEN_BUF = 1
PLAYER_STATE_WRITE_TO_COLOR_BUF  = 2
PLAYER_STATE_FRAME_DONE          = 255

.weak
; Zero page variables
player_data_ptr      = $54 ; And $55 is used too
player_dest_ptr      = $60 ; Unpack buffer pointer
player_state         = $62 ;
player_row           = $63
player_code          = $64
player_color_changes = $65 ; Player has changed color data, shmaybe
.endweak

{% for define in op_use_defines %}
{{define}} = 1
{% endfor %}

player_inc16 .macro
	inc \1
	bne +
	inc \1+1
+
.endm

player_read_next_byte .macro
	ldy #0
	lda (player_data_ptr),y
	#player_inc16 player_data_ptr
.endm

player_read_next_byte_slow
	#player_read_next_byte
	rts

player_setup_data_ptr .macro
	lda #<\1
	sta player_data_ptr
	lda #>\1
	sta player_data_ptr+1
.endm

player_setup_screen_ptr .macro
	lda #<\1
	sta player_screen_ptr
	lda #>\1
	sta player_screen_ptr+1
.endm

player_set_color_data_changed .macro
	lda #1
	sta player_color_changes
.endm

player_init
	lda #0
	sta player_data_ptr
	sta player_data_ptr+1
	sta player_dest_ptr
	sta player_dest_ptr+1
	sta player_state
	sta player_row
	sta player_code
	sta player_color_changes
	#player_setup_data_ptr ANIM_LOCATION
	rts

; Player will return A = 0 when its done rendering, A = 1 when its still working
player_unpack .block
{% if use_color %}
	lda #0
	sta player_color_changes
{% endif %}
	lda player_state
	cmp #PLAYER_STATE_IDLE
	bne still_working
	lda #PLAYER_STATE_WRITE_TO_SCREEN_BUF
	sta player_state
unpack_loop
	#player_read_next_byte
	tay
	; Translate opcode to jump address
	lda player_block_tab_lo,y
	sta op_jump+1
	lda player_block_tab_hi,y
	sta op_jump+2
op_jump
	jsr $0000
	lda player_state
	cmp #PLAYER_STATE_FRAME_DONE
	bne unpack_loop
	lda #0
	sta player_state
still_working
	rts
.endblock

player_block_tab_lo
{% for code, name in all_ops.items() %}
{% if code <= last_used_op_code %}
	.byte <{{name}} ; code {{code}}
{% endif %}
{% endfor %}

player_block_tab_hi
{% for code, name in all_ops.items() %}
{% if code <= last_used_op_code %}
	.byte >{{name}} ; code {{code}}
{% endif %}
{% endfor %}


{% if "player_op_per_row_changes" in ops_in_use %}
row = player_row
code = player_code
rle_count = player_code

update_screen_dest_prt .macro
	ldx row
	lda screen_lo,x
	sta player_dest_ptr
	lda screen_hi,x
	sta player_dest_ptr+1
.endmacro

player_op_per_row_changes
{% if use_color %}
	lda player_state
	cmp #PLAYER_STATE_WRITE_TO_COLOR_BUF
	bne +
	jmp player_op_per_row_changes_color
+
{% endif %}
player_op_per_row_changes_screen .block
	lda #0
	sta row
row_loop
	jsr player_read_next_byte_slow
	cmp #200
	beq next_row

	sta code

process_changes
	cmp #101
	bcc single_change

multiple_changes

	#update_screen_dest_prt

	lda code        ; code > 100
	sec
	sbc #100       ; A now contains count
	sta count+1
	#player_read_next_byte; A = xpos
	clc
	adc player_dest_ptr
	sta player_dest_ptr
	bcc +
	inc player_dest_ptr+1
+
	#player_read_next_byte ; A = value

	; RLE
	ldy #0
-	sta (player_dest_ptr),y
	iny
count
	cpy #0
	bne -

	jmp row_loop    ; Continue row

single_change
	#update_screen_dest_prt

	ldy code
	cpy #40
	bcs skip_write
	clc
	tya
	adc player_dest_ptr
	sta player_dest_ptr
	bcc +
	inc player_dest_ptr+1
+   #player_read_next_byte
	sta (player_dest_ptr),y
skip_write
	jmp row_loop

next_row
	inc row
	lda row
	cmp #25
	bne row_loop

	rts

.endblock

{% if use_color %}

update_color_dest_prt .macro
	ldx row
	lda color_lo,x
	sta player_dest_ptr
	lda color_hi,x
	sta player_dest_ptr+1
.endmacro

player_op_per_row_changes_color .block
	#player_set_color_data_changed
	lda #0
	sta row
row_loop
	jsr player_read_next_byte_slow
	cmp #200
	beq next_row

	sta code

process_changes
	cmp #101
	bcc single_change

multiple_changes

	#update_color_dest_prt

	lda code        ; code > 100
	sec
	sbc #100       ; A now contains count
	sta count+1
	#player_read_next_byte; A = xpos
	clc
	adc player_dest_ptr
	sta player_dest_ptr
	bcc +
	inc player_dest_ptr+1
+
	#player_read_next_byte ; A = value

	; RLE
	ldy #0
-	sta (player_dest_ptr),y
	iny
count
	cpy #0
	bne -

	jmp row_loop    ; Continue row

single_change
	#update_color_dest_prt

	ldy code
	cpy #40
	bcs skip_write
	clc
	tya
	adc player_dest_ptr
	sta player_dest_ptr
	bcc +
	inc player_dest_ptr+1
+   #player_read_next_byte
	sta (player_dest_ptr),y
skip_write
	jmp row_loop

next_row
	inc row
	lda row
	cmp #25
	bne row_loop

	rts

.endblock

{% endif %}

screen_lo
{% for y in range(25) %}
.byte <(UNPACK_BUFFER_LOCATION + {{y * 40}})
{% endfor %}

screen_hi
{% for y in range(25) %}
.byte >(UNPACK_BUFFER_LOCATION + {{y * 40}})
{% endfor %}

{% if use_color %}
color_lo
{% for y in range(25) %}
.byte <(COLOR_UNPACK_BUFFER_LOCATION + {{y * 40}})
{% endfor %}

color_hi
{% for y in range(25) %}
.byte >(COLOR_UNPACK_BUFFER_LOCATION + {{y * 40}})
{% endfor %}
{% endif %}

{% endif %}

{% if "player_op_clear_screen" in ops_in_use %}
player_op_clear_screen .block
	jsr player_read_next_byte_slow
	ldx #$fa
-
	dex
	sta $0000+UNPACK_BUFFER_LOCATION,x
	sta $00fa+UNPACK_BUFFER_LOCATION,x
	sta $01f4+UNPACK_BUFFER_LOCATION,x
	sta $02ee+UNPACK_BUFFER_LOCATION,x
	bne -
	rts
.endblock
{% endif %}

{% if "player_op_clear_color" in ops_in_use %}
player_op_clear_color .block
	jsr player_read_next_byte_slow
	ldx #$fa
-
	dex
	sta $0000+COLOR_UNPACK_BUFFER_LOCATION,x
	sta $00fa+COLOR_UNPACK_BUFFER_LOCATION,x
	sta $01f4+COLOR_UNPACK_BUFFER_LOCATION,x
	sta $02ee+COLOR_UNPACK_BUFFER_LOCATION,x
	bne -

	#player_set_color_data_changed
	rts
.endblock
{% endif %}

{% if "player_op_fullscreen_2x2_blocks" in ops_in_use %}

player_op_fullscreen_2x2_blocks .block
{% if use_color %}
	lda player_state
	cmp #PLAYER_STATE_WRITE_TO_COLOR_BUF
	jmp player_op_mankeli_unpack_color
	bne player_op_mankeli_unpack_screen
{% endif %}
player_op_mankeli_unpack_screen
{% for macro_idx, macro_block in enumerate(macro_blocks) %}
	#player_read_next_byte
	sta changes
	cmp #0
	bne player_unpack_macroblock{{macro_idx}}
	jmp no_changes_{{macro_idx}}
player_unpack_macroblock{{macro_idx}}
	{% for block_idx, block in enumerate(get_blocks(macro_block)) %}
	{% if block in used_blocks %}
	lda changes
	and #{{ bit_mask[block_idx] }}
	beq +
	{% for offset in get_offsets(block) %}
	#player_read_next_byte
	sta UNPACK_BUFFER_LOCATION + {{ offset }}
	{% endfor %}
+
	{% endif %}
	{% endfor %}
no_changes_{{macro_idx}}
{% endfor %}
	rts
.endblock

{% if use_color %}
{% for macro_idx, macro_block in enumerate(macro_blocks) %}
player_unpack_color_macroblock{{macro_idx}} .block
	{% for block_idx, block in enumerate(get_blocks(macro_block)) %}
	{% if block in used_blocks %}
	lda changes
	and #{{ bit_mask[block_idx] }}
	beq +
	{% for offset in get_offsets(block) %}
	#player_read_next_byte
	sta COLOR_UNPACK_BUFFER_LOCATION + {{ offset }}
	{% endfor %}
+
	{% endif %}
	{% endfor %}
	rts
.endblock
{% endfor %}

player_op_mankeli_unpack_color .block
{% for macro_idx, macro_block in enumerate(macro_blocks) %}
	#player_read_next_byte
	sta changes
	cmp #0
	beq no_changes_{{macro_idx}}
	jsr player_unpack_color_macroblock{{macro_idx}}
no_changes_{{macro_idx}}
{% endfor %}
	rts
.endblock
{% endif %}

changes
.byte 0

{% endif %}

{% if use_color %}
player_op_set_color_mode
	lda #PLAYER_STATE_WRITE_TO_COLOR_BUF
	sta player_state
	#player_set_color_data_changed
	rts
{% else %}
player_op_set_color_mode = player_op_error
{% endif %}

player_op_set_screen_mode
	lda #PLAYER_STATE_WRITE_TO_SCREEN_BUF
	sta player_state
	rts

{% if "player_op_set_dest_ptr" in ops_in_use %}
player_op_set_dest_ptr
	#player_read_next_byte
	tay
{% if use_color %}
	lda player_state
	cmp #PLAYER_STATE_WRITE_TO_SCREEN_BUF
	beq +
	lda player_offsets_color_lo,y
	sta player_dest_ptr
	lda player_offsets_color_hi,y
	sta player_dest_ptr + 1
	rts
+
{% endif %}
	lda player_offsets_lo,y
	sta player_dest_ptr
	lda player_offsets_hi,y
	sta player_dest_ptr + 1
	rts
{% endif %}

{% if "player_op_set_border" in ops_in_use %}
player_op_set_border
	jsr player_read_next_byte_slow
	sta PLAYER_BORDER_COLOR_VAR
	rts
{% endif %}

{% if "player_op_set_background" in ops_in_use %}
player_op_set_background
	jsr player_read_next_byte_slow
	sta PLAYER_BACKGROUND_COLOR_VAR
	rts
{% endif %}

player_op_frame_done
	lda #PLAYER_STATE_FRAME_DONE
	sta player_state
	rts

player_op_error
	sty player_state
	lda #2
	sta $d020
	sta $d021
	jmp *

player_clear_screen .macro
	ldx #125
-	sta \1 + 000, x
	sta \1 + 125, x
	sta \1 + 250, x
	sta \1 + 375, x
	sta \1 + 500, x
	sta \1 + 625, x
	sta \1 + 750, x
	sta \1 + 875, x
	dex
	bpl -
.endmacro

{% if "player_op_clear" in ops_in_use %}
player_op_clear
	lda player_state
	cmp #PLAYER_STATE_WRITE_TO_SCREEN_BUF
	bne color
screen
	jsr player_read_next_byte_slow
	#player_clear_screen UNPACK_BUFFER_LOCATION
	rts
color
	jsr player_read_next_byte_slow
	#player_clear_screen COLOR_UNPACK_BUFFER_LOCATION
	rts
{% endif %}

player_op_restart
	#player_setup_data_ptr ANIM_LOCATION
	jsr RESTART_CALLBACK
	rts

player_op_set_charset
	jsr player_read_next_byte_slow
	; sta $d021
	jsr SET_CHARSET_CALLBACK
	rts

{% for size in block_offsets_sizes %}
{% if size > 0 %}
player_op_fill{{size}}
{% for idx in range(0, size) %}
	#player_read_next_byte
	ldy #{{block_offsets[idx]}}
	sta (player_dest_ptr), y
{% endfor %}
	rts
{% endif %}
{% endfor %}

{% if "player_op_fill_rle_fullscreen" in ops_in_use %}
player_op_fill_rle_fullscreen .block
	; figure out which buffer to use

	lda player_state
	cmp #PLAYER_STATE_WRITE_TO_SCREEN_BUF
	beq +

	lda #<COLOR_UNPACK_BUFFER_LOCATION
	sta player_dest_ptr
	lda #>COLOR_UNPACK_BUFFER_LOCATION
	sta player_dest_ptr+1
	jmp decode_loop
+
	lda #<UNPACK_BUFFER_LOCATION
	sta player_dest_ptr
	lda #>UNPACK_BUFFER_LOCATION
	sta player_dest_ptr+1
	jmp decode_loop

	; start decode

decode_loop
	; read count
	#player_read_next_byte
	cmp #{{ PLAYER_RLE_END_MARKER }}
	beq exit
	sta count+1

short_segment
	; read value to A
	#player_read_next_byte

write
	sta (player_dest_ptr), y
	iny
count
	cpy #0
	bne write

	tya
	clc
	adc player_dest_ptr
	sta player_dest_ptr
	bcc +
	inc player_dest_ptr+1
+
	jmp decode_loop

exit
	rts
.endblock
{% endif %}

{% if rle_decode_needed %}
; A = size of encoded data
player_rle_decode .block
	sta encoded_size + 1
	lda #0
	sta buffer_pos
decode_loop
	sta loop_iter

	; read count
	#player_read_next_byte
	tax

	; read value to A
	#player_read_next_byte

	;cpx #4
	;beq copy_4

	ldy buffer_pos

	clc
	cpx #8
	bcc short_segment

unroll8
	.for i := 0, i < 8, i += 1
	sta player_rle_decode_buffer, y
	iny
	dex
	.endfor

	cpx #8
	bcs unroll8

	cpx #0
	beq continue

short_segment
-	sta player_rle_decode_buffer, y
	iny
	dex
	bne -

continue
	sty buffer_pos
	lda loop_iter
	clc
	adc #2
encoded_size
	cmp #$0
	bne decode_loop
	rts
copy_4
	sta player_rle_decode_buffer+0
	sta player_rle_decode_buffer+1
	sta player_rle_decode_buffer+2
	sta player_rle_decode_buffer+3
	lda buffer_pos
	clc
	adc #4
	tay
	jmp continue

buffer_pos
	.byte 0
loop_iter
	.byte 0
.endblock
{% endif %}

{% for op_name, info in FILL_RLE_TEMPLATE_HELPER.items() %}
{% if op_name in ops_in_use %}
{{op_name}} .block
	lda #{{ info['encoded'] }}
	jsr player_rle_decode
{% for idx in range(0, info['decoded']) %}
	lda player_rle_decode_buffer + {{ loop.index - 1 }}
	ldy #{{block_offsets[idx]}}
	sta (player_dest_ptr), y
{% endfor %}
	rts
.endblock
{% endif %}
{% endfor %}

{% for size in block_offsets_sizes %}
{% if size > 0 %}
player_op_fill_same{{size}}
	#player_read_next_byte
{% for idx in range(0, size) %}
	ldy #{{block_offsets[idx]}}
	sta (player_dest_ptr), y
{% endfor %}
	rts
{% endif %}
{% endfor %}

{% if rle_decode_needed %}
player_rle_decode_buffer
{% for i in range(255) %}
.byte 0
{% endfor %}
{% endif %}

{% if "player_op_set_dest_ptr" in ops_in_use %}
player_offsets_lo
{% for block in all_blocks %}
	.byte <(UNPACK_BUFFER_LOCATION + {{ first_offset(block) }})
{% endfor %}
{% if use_color %}
player_offsets_color_lo
{% for block in all_blocks %}
	.byte <(COLOR_UNPACK_BUFFER_LOCATION + {{ first_offset(block) }})
{% endfor %}
{% endif %}

player_offsets_hi
{% for block in all_blocks %}
	.byte >(UNPACK_BUFFER_LOCATION + {{ first_offset(block) }})
{% endfor %}
{% if use_color %}
player_offsets_color_hi
{% for block in all_blocks %}
	.byte >(COLOR_UNPACK_BUFFER_LOCATION + {{ first_offset(block) }})
{% endfor %}
{% endif %}
{% endif %}
