"""
Manim animation that visualizes how `encode_pub` from
`pub-sub/src/protocol.rs` builds the on-the-wire bytes.

Sample input mirrors `test_encode_decode_pub`:
    PubEvent {
        client_id: 1001,
        topic:     "orders",
        channel:   "analysis",
        msg:       b"orders:001",
    }

Wire layout produced by encode_pub (big-endian throughout):

    [0..4]   : u32 BE   = total payload length  (1 + 8 + 1 + 6 + 1 + 8 + 10 = 35 -> 0x00000023)
    [4]      : u8       = PUB_TAG               (0x01)
    [5..13]  : u64 BE   = client_id             (1001 -> 0x00000000000003E9)
    [13]     : u8       = topic length          (6)
    [14..20] : str      = "orders"              (6F 72 64 65 72 73)
    [20]     : u8       = channel length        (8)
    [21..29] : str      = "analysis"            (61 6E 61 6C 79 73 69 73)
    [29..39] : bytes    = b"orders:001"         (6F 72 64 65 72 73 3A 30 30 31)

Total: 4 + 35 = 39 bytes.

Run with:
    manim -pqh encode_pub_animation.py EncodePubScene
"""

from manim import (
    Scene,
    VGroup,
    Rectangle,
    Text,
    MathTex,
    Create,
    FadeIn,
    FadeOut,
    Write,
    Indicate,
    Flash,
    SurroundingRectangle,
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
)
import manim

# ---------- helpers ----------------------------------------------------------

def hex2(b: int) -> str:
    """Two-digit uppercase hex."""
    return f"{b:02X}"


def make_cell(hex_text: str, *, fill=BLUE, height=0.5, width=0.35) -> Rectangle:
    """A single byte cell with a hex label inside."""
    cell = Rectangle(height=height, width=width, fill_color=fill,
                     fill_opacity=0.85, stroke_color=WHITE, stroke_width=2)
    label = Text(hex_text, font="monospace", font_size=18, color=WHITE)
    label.move_to(cell.get_center())
    return VGroup(cell, label)


def make_cell_row(cells: list[VGroup], *, buff=0.05) -> VGroup:
    """Lay out cells horizontally."""
    group = VGroup(*cells)
    group.arrange(RIGHT, buff=buff)
    return group


def make_input_box(title: str, body: str, *, color=GREEN) -> VGroup:
    """A labeled box representing one field of PubEvent."""
    box = Rectangle(width=2.8, height=1.0, fill_color=color,
                    fill_opacity=0.15, stroke_color=color, stroke_width=3)
    title_t = Text(title, font_size=20, color=color, weight="BOLD")
    body_t = Text(body, font="monospace", font_size=20, color=WHITE)
    title_t.next_to(box.get_top(), DOWN, buff=0.12)
    body_t.move_to(box.get_center()).shift(DOWN * 0.1)
    return VGroup(box, title_t, body_t)


# ---------- the scene -------------------------------------------------------

class EncodePubScene(Scene):
    """Step-by-step visualization of `encode_pub`."""

    def construct(self) -> None:
        # ---------- title --------------------------------------------------
        title = Text("encode_pub  —  pub-sub/protocol.rs", font_size=40, color=YELLOW)
        title.to_edge(UP, buff=0.4)
        subtitle = Text(
            "How a PubEvent becomes bytes on the wire",
            font_size=24, color=LIGHT_GREY,
        )
        subtitle.next_to(title, DOWN, buff=0.15)
        self.play(Write(title), FadeIn(subtitle, shift=UP * 0.2))
        self.wait(1.2)

        # ---------- the input PubEvent --------------------------------------
        pub_label = Text("Input: PubEvent", font_size=26, color=GREEN, weight="BOLD")
        pub_label.to_edge(LEFT).shift(UP * 1.5)

        f_client = make_input_box("client_id : u64", "1001", color=GREEN)
        f_topic  = make_input_box("topic : String", '"orders"',   color=GREEN)
        f_chan   = make_input_box("channel : String", '"analysis"', color=GREEN)
        f_msg    = make_input_box("msg : Vec<u8>", 'b"orders:001"', color=GREEN)

        inputs = VGroup(f_client, f_topic, f_chan, f_msg) \
            .arrange(DOWN, aligned_edge=LEFT, buff=0.18) \
            .next_to(pub_label, DOWN, aligned_edge=LEFT, buff=0.25)

        self.play(FadeIn(pub_label, shift=RIGHT * 0.2))
        for box in inputs:
            self.play(FadeIn(box, shift=RIGHT * 0.3), run_time=0.7)
        self.wait(1.0)

        # ---------- the output buffer placeholder ---------------------------
        out_label = Text("Encoded bytes (output buffer)", font_size=22,
                         color=YELLOW, weight="BOLD")
        out_label.to_edge(RIGHT).shift(UP * 1.5)

        # We will render cells in two rows so they fit on screen:
        # row 1: 20 cells  (4-byte len header + first 16 payload bytes)
        # row 2: 19 cells  (remaining payload bytes)
        row1_label = Text("offset 0..20",  font_size=16, color=LIGHT_GREY)
        row2_label = Text("offset 20..39", font_size=16, color=LIGHT_GREY)

        # empty "slot" placeholders for the buffer — sized to match make_cell
        SLOT_W, SLOT_H, BUFF = 0.35, 0.5, 0.04
        def empty_cell():
            return Rectangle(width=SLOT_W, height=SLOT_H,
                             stroke_color=GREY, stroke_width=2)

        slots_r1 = VGroup(*[empty_cell() for _ in range(20)]).arrange(RIGHT, buff=BUFF)
        slots_r2 = VGroup(*[empty_cell() for _ in range(19)]).arrange(RIGHT, buff=BUFF)

        # stack row2 just below row1 *before* placing the labels so each
        # label sits above the row it actually describes (otherwise both
        # labels overlap at the same y because slots_r2 hasn't moved yet).
        slots_r2.next_to(slots_r1, DOWN, buff=0.4)
        row1_label.next_to(slots_r1, UP, buff=0.15).align_to(slots_r1, LEFT)
        row2_label.next_to(slots_r2, UP, buff=0.15).align_to(slots_r1, LEFT)

        # group the slots + their row labels (NOT out_label, which stays at
        # the right edge), and place the whole thing to the right of the
        # input boxes with a comfortable gap.
        slots_group = VGroup(row1_label, row2_label, slots_r1, slots_r2) \
            .move_to(RIGHT * 0.4 + DOWN * 0.3)

        self.play(FadeIn(out_label, shift=DOWN * 0.2))
        self.play(FadeIn(slots_r1), FadeIn(slots_r2),
                  FadeIn(row1_label), FadeIn(row2_label), run_time=1.2)
        self.wait(0.8)

        # Keep references to all output cells and to the slots they replace
        all_cells: list[VGroup] = [None] * 39     # type: ignore
        all_slots = list(slots_r1) + list(slots_r2)

        # ---------- per-field step narration -------------------------------
        def narrate(step_no: int, source_box: VGroup, explain: str) -> None:
            self.play(
                Indicate(source_box, color=YELLOW, scale_factor=1.05),
                run_time=1.2,
            )
            cap = Text(f"step {step_no}: {explain}", font_size=24, color=YELLOW)
            cap.to_edge(DOWN, buff=0.6)
            self.play(FadeIn(cap, shift=UP * 0.2), run_time=0.8)
            return cap

        def drop_in(caps: list[Text]) -> None:
            if caps:
                self.play(FadeOut(caps[-1]), run_time=0.5)

        # === step 1: PUB_TAG ===
        caps: list[Text] = []
        c = narrate(1, f_client,
                    "push PUB_TAG = 0x01 (1 byte, u8)")
        # We are placing TAG into the PAYLOAD, *after* the 4-byte length header.
        # The length header is filled in last.  So position 4 (after the 4 slots
        # of the header).  Render TAG into slot index 4 (= row1, cell 4, 0-based).
        tag_cell = make_cell("01", fill=ORANGE)
        tag_cell.move_to(all_slots[4].get_center())
        self.play(FadeIn(tag_cell), run_time=0.9)
        all_cells[4] = tag_cell
        caps.append(c)
        drop_in(caps)
        self.wait(1.0)

        # === step 2: client_id (u64 big-endian, 1001) ===
        client_bytes = [0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x03, 0xE9]
        c = narrate(2, f_client, "client_id → u64 BE  (8 bytes)")
        cells = []
        for i, b in enumerate(client_bytes):
            cell = make_cell(hex2(b), fill=BLUE)
            cell.move_to(all_slots[5 + i].get_center())
            cells.append(cell)
            all_cells[5 + i] = cell
        # appear in a slow cascade
        for cell in cells:
            self.play(FadeIn(cell), run_time=0.35)
        caps.append(c)
        drop_in(caps)
        self.wait(1.0)

        # === step 3: topic length (u8) ===
        c = narrate(3, f_topic, 'topic.len() → u8 = 6')
        len_cell = make_cell("06", fill=TEAL)
        len_cell.move_to(all_slots[13].get_center())
        self.play(FadeIn(len_cell), run_time=0.9)
        all_cells[13] = len_cell
        caps.append(c)
        drop_in(caps)
        self.wait(0.9)

        # === step 4: topic bytes ===
        topic_bytes = list(b"orders")  # 6F 72 64 65 72 73
        c = narrate(4, f_topic, 'topic.into_bytes()  —  "orders"')
        cells = []
        for i, b in enumerate(topic_bytes):
            cell = make_cell(hex2(b), fill=GREEN)
            cell.move_to(all_slots[14 + i].get_center())
            cells.append(cell)
            all_cells[14 + i] = cell
        for cell in cells:
            self.play(FadeIn(cell), run_time=0.4)
        caps.append(c)
        drop_in(caps)
        self.wait(1.0)

        # === step 5: channel length (u8) ===
        c = narrate(5, f_chan, 'channel.len() → u8 = 8')
        len_cell = make_cell("08", fill=TEAL)
        len_cell.move_to(all_slots[20].get_center())
        self.play(FadeIn(len_cell), run_time=0.9)
        all_cells[20] = len_cell
        caps.append(c)
        drop_in(caps)
        self.wait(0.9)

        # === step 6: channel bytes ===
        chan_bytes = list(b"analysis")  # 61 6E 61 6C 79 73 69 73
        c = narrate(6, f_chan, 'channel.into_bytes()  —  "analysis"')
        cells = []
        for i, b in enumerate(chan_bytes):
            cell = make_cell(hex2(b), fill=GREEN)
            cell.move_to(all_slots[21 + i].get_center())
            cells.append(cell)
            all_cells[21 + i] = cell
        for cell in cells:
            self.play(FadeIn(cell), run_time=0.4)
        caps.append(c)
        drop_in(caps)
        self.wait(1.0)

        # === step 7: msg bytes ===
        msg_bytes = list(b"orders:001")
        c = narrate(7, f_msg, 'msg  (raw bytes)')
        cells = []
        for i, b in enumerate(msg_bytes):
            cell = make_cell(hex2(b), fill=RED)
            cell.move_to(all_slots[29 + i].get_center())
            cells.append(cell)
            all_cells[29 + i] = cell
        for cell in cells:
            self.play(FadeIn(cell), run_time=0.4)
        caps.append(c)
        drop_in(caps)
        self.wait(1.0)

        # === step 8: prepend u32 length header (35 = 0x23) ===================
        explain = Text(
            "step 8: total payload = 35 bytes → u32 BE = 0x00000023, "
            "prepended as 4-byte length header",
            font_size=22, color=YELLOW,
        )
        explain.to_edge(DOWN, buff=0.6)
        self.play(FadeIn(explain, shift=UP * 0.2), run_time=0.8)

        # length bytes 0x00, 0x00, 0x00, 0x23
        len_header = [0x00, 0x00, 0x00, 0x23]
        cells = []
        for i, b in enumerate(len_header):
            cell = make_cell(hex2(b), fill=ORANGE)
            cell.move_to(all_slots[i].get_center())
            cells.append(cell)
            all_cells[i] = cell
        # flash to emphasize "prepending"
        self.play(Flash(all_slots[0].get_center(), color=ORANGE,
                        flash_radius=0.6, line_length=0.4, num_lines=12),
                  run_time=1.0)
        for cell in cells:
            self.play(FadeIn(cell), run_time=0.5)
        self.wait(1.0)

        # ---------- final summary -----------------------------------------
        self.play(FadeOut(explain, shift=DOWN * 0.2))

        # bracket grouping the length header
        bracket = SurroundingRectangle(
            VGroup(*[c for c in all_cells[:4] if c is not None]),
            color=ORANGE, buff=0.1, stroke_width=4,
        )
        bracket_label = Text("length\n(u32 BE)", font_size=18,
                             color=ORANGE, weight="BOLD")
        bracket_label.next_to(bracket, UP, buff=0.15)
        self.play(Create(bracket), FadeIn(bracket_label, shift=DOWN * 0.1))
        self.wait(1.0)

        final_note = Text(
            "Total frame: 4 + 35 = 39 bytes  —  returned as Bytes (frozen BytesMut)",
            font_size=22, color=WHITE,
        )
        final_note.to_edge(DOWN, buff=0.5)
        self.play(FadeIn(final_note, shift=UP * 0.2))
        self.wait(2.5)


# ---------- suggested rendering config --------------------------------------
if __name__ == "__main__":
    config.media_dir = "./_manim_out"
    config.quality = "high_quality"
    # Slow pacing: we deliberately use long run_time per animation above.
