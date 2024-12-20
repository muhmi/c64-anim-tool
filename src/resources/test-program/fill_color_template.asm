{% for idx, offsets in enumerate(fill_color_blocks) %}
fill_color_step{{idx}}
	lda fill_color
	{% for offset in offsets %}
    sta ${{hex(0xd800 + offset)[2:]}}
    {% endfor %}
    rts
{% endfor %}


init_fill_color
    lda #0
    sta fill_color_idx
    sta fill_color_step
    ldx fill_color_idx
    lda fill_color_values,x
    sta fill_color
    lda #0
    sta fill_color_tick
    rts

update_fill_color .block
    inc fill_color_tick
    lda fill_color_tick
    cmp #3
    bne exit

    lda #0
    sta fill_color_tick

    ldx fill_color_idx
    lda fill_color_values,x
    sta fill_color
    inx
    cpx #8
    bne +
    ldx #0
+   stx fill_color_idx
exit
    rts
.endblock

fill_color_tick
.byte 0

do_one_fill_color_step .block
    ldx fill_color_step
    lda fill_color_tab_lo,x
    sta jmp_to_fill+1
    lda fill_color_tab_hi,x
    sta jmp_to_fill+2

    inx
    cpx #{{len(fill_color_blocks)}}
    bne +
    ldx #0
+   stx fill_color_step

jmp_to_fill
    jmp $0000

.endblock

fill_color_values
.byte $1, $7, $3, $5, $4, $2, $6, $0


fill_color_tab_lo
{% for idx, _ in enumerate(fill_color_blocks) %}
.byte <fill_color_step{{idx}}
{% endfor %}

fill_color_tab_hi
{% for idx, _ in enumerate(fill_color_blocks) %}
.byte >fill_color_step{{idx}}
{% endfor %}

fill_color_step
.byte 0
fill_color_idx
.byte 0
fill_color
.byte 0
