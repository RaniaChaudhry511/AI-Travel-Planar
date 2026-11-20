import textwrap
import unicodedata

from fpdf import FPDF


def export_itinerary_pdf(itinerary: str) -> bytes:
    """Render an itinerary as a simple PDF, including Roman Urdu and English."""
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Helvetica", style="B", size=16)
    pdf.multi_cell(0, 10, "Travel Plan")
    pdf.ln(2)
    pdf.set_font("Helvetica", size=10)

    text = unicodedata.normalize("NFKD", itinerary)
    safe_text = text.encode("latin-1", errors="replace").decode("latin-1")
    for line in safe_text.splitlines():
        wrapped_lines = textwrap.wrap(
            line,
            width=90,
            break_long_words=True,
            break_on_hyphens=False,
        )
        for wrapped_line in wrapped_lines or [" "]:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(0, 6, wrapped_line)

    return bytes(pdf.output())
