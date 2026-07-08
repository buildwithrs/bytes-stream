"""
Manim animation that visualizes how `decode_pub` from
`pub-sub/src/protocol.rs` parses bytes back into a PubEvent.

`read_frame` already strips the 4-byte length header.
`decode_frame` already consumed PUB_TAG via `f.get_u8()`.
So `decode_pub(bs)` receives these 34 bytes:

    byte index : 00 01 02 03 04 05 06 07  08    09 10 11 12 13 14    15    16 17 18 19 20 21 22 23    24 25 26 27 28 29 30 31 32 33
    hex value  : 00 00 00 00 00 00 03 E9  06    6F 72 64 65 72 73    08    61 6E 61 6C 79 73 69 73    6F 72 64 65 72 73 3A 30 30 31
    meaning    : --------- client_id -----  t_len  ---- "orders" ----  ch_len  ---- "analysis" ----------  ---- "orders:001" ----
    field      : u64 BE = 1001            u8 = 6  bytes              u8 = 8  bytes                     bytes

decode_pub body:
    let c_id    = bs.get_u64();                       // cursor advances by 8
    let t_len   = bs.get_u8() as usize;               // cursor advances by 1
    let topic   = String::from_utf8_lossy(&bs[0..t_len]);          // slice
    let ch_len  = bs[t_len] as usize;                             // index read
    let channel = String::from_utf8_lossy(&bs[t_len+1..t_len+1+ch_len]); // slice
    let msg     = bs[t_len+ch_len+1..].to_vec();                  // slice

Note: indices inside `bs[..]` are relative to the cursor.  After step 2
the cursor sits at offset 9 (start of the topic), so bs[0..6] reads
bytes 9..15 = "orders".

Run with:
    manim -pqh decode_pub_animation.py DecodePubScene
"""

from manim import (
    Scene,
    VGroup,
    Rectangle,
    Text,
    Create,
    FadeIn,
    FadeOut,
    Write,
    Indicate,
    Flash,
    SurroundingRectangle,
    Triangle,
    Line,
    Arrow,
    UP,
    DOWN,
    LEFT,
    RIGHT,
    ORIGIN,
    ORANGE,
    YELLOW,
    BLUE,
    GREEN,
    GREY,
    WHITE,
    BLACK,
    RED,
    TEAL,
    LIGHT_GREY,
    config,
    PI,
    DEGREES,
)

# ---------- helpers -------------------------------------------------------

def hex2(b: int) -> str:
    return f"{b:02X}"


def char_view(b: int) -> str:
    """Render a byte as printable ASCII (or '.' if not printable)."""
    return chr(b) if 32 <= b < 127 else "."


def make_cell(hex_text: str, char_text: str | None = None,
              *, fill=None, height=0.75, width=0.62,
              stroke=WHITE, stroke_w=2) -> VGroup:
    """A single byte cell with hex label (and optional ASCII char)."""
    fill = fill if fill is not None else BLUE
    cell = Rectangle(height=height, width=width,
                     fill_color=fill, fill_opacity=0.85,
                     stroke_color=stroke, stroke_width=stroke_w)
    label = Text(hex_text, font="monospace", font_size=18, color=WHITE)
    label.move_to(cell.get_center())
    group = VGroup(cell, label)
    if char_text is not None:
        sub = Text(char_text, font="monospace", font_size=14, color=WHITE)
        sub.move_to(cell.get_center()).shift(DOWN * 0.22)
        group.add(sub)
    return group


def make_input_box(title: str, body: str, *, color=GREEN,
                   width=3.4, height=1.4, body_color=WHITE,
                   body_font="monospace") -> VGroup:
    box = Rectangle(width=width, height=height, fill_color=color,
                    fill_opacity=0.12, stroke_color=color, stroke_width=3)
    title_t = Text(title, font_size=20, color=color, weight="BOLD")
    body_t = Text(body, font=body_font, font_size=22, color=body_color)
    title_t.next_to(box.get_top(), DOWN, buff=0.12)
    body_t.move_to(box.get_center()).shift(DOWN * 0.15)
    return VGroup(box, title_t, body_t)


# ---------- the scene -----------------------------------------------------

class DecodePubScene(Scene):
    """Step-by-step visualization of `decode_pub`."""

    # ----- payload layout (the 34 bytes decode_pub actually sees) -------
    # decoded values
    PUBEVENT = {
        "client_id": 1001,
        "topic":     "orders",
        "channel":   "analysis",
        "msg":       b"orders:001",
    }

    def _build_payload_bytes(self) -> list[tuple[int, str, str]]:
        """Return [(hex_str, ascii_char_or_None, field_label), ...]."""
        c_id_bytes = self.PUBEVENT["client_id"].to_bytes(8, "big")
        topic_b    = self.PUBEVENT["topic"].encode()
        channel_b  = self.PUBEVENT["channel"].encode()
        msg_b      = self.PUBEVENT["msg"]

        # (hex, ascii, field_label)
        out: list[tuple[int, str, str]] = []
        for b in c_id_bytes:
            out.append((b, char_view(b), "client_id"))
        out.append((len(topic_b), ".", "t_len"))
        for b in topic_b:
            out.append((b, char_view(b), "topic"))
        out.append((len(channel_b), ".", "ch_len"))
        for b in channel_b:
            out.append((b, char_view(b), "channel"))
        for b in msg_b:
            out.append((b, char_view(b), "msg"))
        return out

    # ------------------------------------------------------------------

    def construct(self) -> None:
        # ---------- title -------------------------------------------------
        title = Text("decode_pub  —  pub-sub/protocol.rs",
                     font_size=40, color=YELLOW)
        title.to_edge(UP, buff=0.35)
        subtitle = Text(
            "How the on-the-wire bytes become a PubEvent",
            font_size=24, color=LIGHT_GREY,
        )
        subtitle.next_to(title, DOWN, buff=0.12)
        self.play(Write(title), FadeIn(subtitle, shift=UP * 0.2))
        self.wait(1.2)

        # ---------- pre-amble: what decode_pub actually sees ---------------
        pre_text = Text(
            "read_frame stripped the 4-byte length header, "
            "decode_frame already consumed PUB_TAG.",
            font_size=22, color=LIGHT_GREY,
        )
        pre_text.next_to(subtitle, DOWN, buff=0.3)
        self.play(FadeIn(pre_text, shift=UP * 0.2), run_time=1.2)
        self.wait(1.4)
        self.play(FadeOut(pre_text, shift=UP * 0.2))
        self.wait(0.4)

        # ---------- the encoded byte buffer -------------------------------
        bytes_data = self._build_payload_bytes()      # 34 entries
        assert len(bytes_data) == 34

        # We split into two rows for visibility:
        #   row A: 0..15  (client_id + t_len + "orders" + ch_len)
        #   row B: 16..33 (rest of "analysis" + "orders:001")
        field_color = {
            "client_id": BLUE,
            "t_len":     TEAL,
            "topic":     GREEN,
            "ch_len":    TEAL,
            "channel":   GREEN,
            "msg":       RED,
        }

        SLOT_W, SLOT_H, BUFF = 0.48, 0.78, 0.035

        def make_row(start: int, end: int) -> VGroup:
            cells = []
            for i in range(start, end):
                h, ch, lbl = bytes_data[i]
                cells.append(make_cell(
                    hex2(h), ch,
                    fill=field_color[lbl],
                    height=SLOT_H, width=SLOT_W,
                ))
            return VGroup(*cells).arrange(RIGHT, buff=BUFF)

        row_a = make_row(0, 16)    # 16 cells  ≈ 8.25 units wide
        row_b = make_row(16, 34)   # 18 cells  ≈ 9.30 units wide
        rows = VGroup(row_a, row_b).arrange(DOWN, buff=0.4)
        # shift buffer left so the output boxes on the right have room
        rows.move_to(ORIGIN).shift(UP * 0.25 + LEFT * 2.2)

        # field-label bracket rows above each row
        rowA_label = Text("byte 0..15   (client_id | t_len | \"orders\" | ch_len)",
                          font_size=18, color=LIGHT_GREY)
        rowB_label = Text("byte 16..33  (\"analysis\" | \"orders:001\")",
                          font_size=18, color=LIGHT_GREY)
        rowA_label.next_to(row_a, UP, buff=0.18).align_to(row_a, LEFT)
        rowB_label.next_to(row_b, UP, buff=0.18).align_to(row_b, LEFT)

        self.play(FadeIn(row_a, shift=DOWN * 0.2),
                  FadeIn(rowB_label), run_time=1.2)
        self.play(FadeIn(row_b, shift=UP * 0.2),
                  FadeIn(rowA_label), run_time=1.2)
        self.wait(1.0)

        # ---------- the cursor pointer ------------------------------------
        # Convention: cursor is a yellow triangle pointing DOWN at the cell
        # that the cursor is currently AT.  Always positioned above the cell.
        cursor = Triangle(fill_color=YELLOW, fill_opacity=1.0,
                          stroke_color=YELLOW).scale(0.22)
        cursor.rotate(180 * DEGREES)         # apex points DOWN
        cursor.next_to(row_a[0], UP, buff=0.5)
        self.play(FadeIn(cursor, shift=DOWN * 0.2), run_time=0.8)

        # ---------- output PubEvent placeholder ---------------------------
        out_label = Text("Decoded PubEvent", font_size=24,
                         color=YELLOW, weight="BOLD")
        out_label.to_edge(RIGHT).shift(UP * 1.8)

        f_client = make_input_box("client_id : u64", "—", color=GREEN)
        f_topic  = make_input_box("topic : String", "—", color=GREEN)
        f_chan   = make_input_box("channel : String", "—", color=GREEN)
        f_msg    = make_input_box("msg : Vec<u8>", "—", color=GREEN)

        outputs = VGroup(f_client, f_topic, f_chan, f_msg) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.22) \
            .next_to(out_label, DOWN, aligned_edge=LEFT, buff=0.25)

        self.play(FadeIn(out_label, shift=LEFT * 0.2))
        for box in outputs:
            self.play(FadeIn(box, shift=LEFT * 0.2), run_time=0.55)
        self.wait(0.8)

        # ---------- helpers used in the steps -----------------------------
        def move_cursor(idx: int) -> None:
            """Re-position cursor above the cell at global index `idx`."""
            target = row_a[idx] if idx < 16 else row_b[idx - 16]
            new_pos = target.get_top() + UP * 0.5
            self.play(cursor.animate.move_to(new_pos), run_time=0.6)
            # cursor is already rotated once at setup; do not re-rotate.

        def narrate(step: int, text: str) -> Text:
            cap = Text(f"step {step}: {text}",
                       font_size=22, color=YELLOW)
            cap.to_edge(DOWN, buff=0.45)
            self.play(FadeIn(cap, shift=UP * 0.2), run_time=0.8)
            return cap

        def fill_box(box: VGroup, value: str, *, color=WHITE) -> None:
            """Replace the body text of `box` with `value`."""
            new_body = Text(value, font="monospace",
                            font_size=22, color=color)
            # the body is the third element (index 2) of the VGroup
            old_body = box[2]
            new_body.move_to(old_body.get_center())
            self.play(FadeOut(old_body, shift=LEFT * 0.1),
                      FadeIn(new_body, shift=RIGHT * 0.1),
                      run_time=0.9)
            # swap for future updates
            box.remove(old_body)
            box.add(new_body)

        def highlight_cells(start: int, end: int) -> SurroundingRectangle:
            if end <= start:
                end = start + 1
            cells = []
            for i in range(start, end):
                cells.append(row_a[i] if i < 16 else row_b[i - 16])
            rect = SurroundingRectangle(
                VGroup(*cells),
                color=YELLOW, buff=0.06, stroke_width=5,
            )
            return rect

        # =============================================================
        # STEP 1 — c_id = bs.get_u64()
        #   cursor was at 0, advances to 8.  Reads client_id (8 bytes).
        # =============================================================
        cap = narrate(1, "let c_id = bs.get_u64()  —  read 8 bytes, cursor += 8")
        hl = highlight_cells(0, 8)
        self.play(Create(hl), Indicate(f_client, color=YELLOW,
                                       scale_factor=1.05), run_time=1.4)
        # advance the cursor: now points at byte 8 (the t_len byte)
        move_cursor(8)
        fill_box(f_client, "1001")
        self.wait(1.0)
        self.play(FadeOut(cap), FadeOut(hl), run_time=0.6)

        # =============================================================
        # STEP 2 — t_len = bs.get_u8() as usize
        #   cursor advances from 8 -> 9.  Reads topic_len (1 byte).
        # =============================================================
        cap = narrate(2, "let t_len = bs.get_u8()  —  read 1 byte, cursor += 1")
        hl = highlight_cells(8, 9)
        self.play(Create(hl), run_time=1.0)
        move_cursor(9)
        fill_box(f_topic, '...', color=LIGHT_GREY)
        self.wait(0.9)
        self.play(FadeOut(cap), FadeOut(hl), run_time=0.6)

        # =============================================================
        # STEP 3 — topic = String::from_utf8_lossy(&bs[0..t_len])
        #   no cursor advance.  slice indices relative to cursor at 9.
        #   bs[0..6] reads bytes 9..15 = "orders".
        # =============================================================
        cap = narrate(3, 'topic = &bs[0..t_len]   (no cursor advance, slice only)')
        hl = highlight_cells(9, 15)        # 6 bytes = "orders"
        self.play(Create(hl), Indicate(f_topic, color=YELLOW,
                                       scale_factor=1.05), run_time=1.4)
        fill_box(f_topic, '"orders"')
        self.wait(1.0)
        self.play(FadeOut(cap), FadeOut(hl), run_time=0.6)

        # =============================================================
        # STEP 4 — ch_len = bs[t_len] as usize
        #   t_len = 6.  reads bs[6] from current cursor at 9, i.e. byte 15.
        # =============================================================
        cap = narrate(4, "ch_len = bs[t_len]  —  read 1 byte at index t_len (6)")
        hl = highlight_cells(15, 16)
        self.play(Create(hl), run_time=1.0)
        fill_box(f_chan, "...", color=LIGHT_GREY)
        self.wait(0.9)
        self.play(FadeOut(cap), FadeOut(hl), run_time=0.6)

        # =============================================================
        # STEP 5 — channel = &bs[t_len + 1 .. t_len + 1 + ch_len]
        #   indices 7..15 from cursor at 9, i.e. bytes 16..23 = "analysis".
        # =============================================================
        cap = narrate(5, 'channel = &bs[t_len+1 .. t_len+1+ch_len]   —  slice "analysis"')
        hl = highlight_cells(16, 24)       # 8 bytes = "analysis"
        self.play(Create(hl), Indicate(f_chan, color=YELLOW,
                                       scale_factor=1.05), run_time=1.4)
        fill_box(f_chan, '"analysis"')
        self.wait(1.0)
        self.play(FadeOut(cap), FadeOut(hl), run_time=0.6)

        # =============================================================
        # STEP 6 — msg = bs[t_len + ch_len + 1 ..]
        #   t_len + ch_len + 1 = 6 + 8 + 1 = 15.  Reads bytes 15..34
        #   from cursor at 9, i.e. absolute bytes 24..33 = "orders:001".
        # =============================================================
        cap = narrate(6, 'msg = bs[t_len+ch_len+1..].to_vec()   —  remaining bytes')
        hl = highlight_cells(24, 34)
        self.play(Create(hl), Indicate(f_msg, color=YELLOW,
                                       scale_factor=1.05), run_time=1.4)
        fill_box(f_msg, 'b"orders:001"')
        self.wait(1.2)
        self.play(FadeOut(cap), FadeOut(hl), run_time=0.6)

        # =============================================================
        # STEP 7 — final wrap-up
        # =============================================================
        sum_text = Text(
            "PubEvent { client_id: 1001, topic: \"orders\", "
            "channel: \"analysis\", msg: b\"orders:001\" }",
            font_size=22, color=YELLOW,
        )
        sum_text.to_edge(DOWN, buff=0.45)
        self.play(FadeIn(sum_text, shift=UP * 0.2), run_time=1.0)
        self.wait(2.5)

        # optional: a "result equals encode input" callout
        ok = Text("✓ round-trips with encode_pub",
                  font_size=22, color=GREEN, weight="BOLD")
        ok.next_to(sum_text, UP, buff=0.2)
        self.play(FadeIn(ok, shift=UP * 0.2), run_time=0.8)
        self.wait(2.0)


# ---------- suggested rendering config -----------------------------------
if __name__ == "__main__":
    config.media_dir = "./_manim_out"
    config.quality = "high_quality"
