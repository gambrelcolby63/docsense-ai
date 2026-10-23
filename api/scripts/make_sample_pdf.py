"""Write the sample brief shipped in web/public. Run from the repo root:

    python api/scripts/make_sample_pdf.py
"""

from pathlib import Path

from fpdf import FPDF

BODY = """
Northwind Field Notes for October 2026.

The Oslo depot warehouse code is Fjord-1842. The shipping cutoff at that depot is 16:00 local time on weekdays. Drivers who miss the cutoff wait for the morning truck.

The Reykjavik pop-up store opens on 12 November 2026 and closes on 4 January 2027. Staff should use door code 4419 after 18:00. The spare key lives in the dock office, not the till.

Returns are accepted within 30 days when the receipt shows the original depot. Hazardous batteries are the exception and must go to the dock office, not the customer desk. A receipt dated after the 30 day window needs a manager initial.

The on-call lead for the Nordic region is Mina Solberg. Her desk extension is 2144. Mina covers night calls from 18:00 until 08:00, including Sundays.

The winter crate order is capped at 180 units unless the regional manager signs a second approval. Wool blankets count toward that cap. Display fixtures do not.
""".strip()


def main() -> None:
    root = Path(__file__).resolve().parents[2]
    target = root / "web" / "public" / "sample-brief.pdf"
    target.parent.mkdir(parents=True, exist_ok=True)
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.multi_cell(0, 10, "Northwind Field Notes")
    pdf.ln(2)
    pdf.set_font("Helvetica", size=12)
    pdf.multi_cell(0, 7, BODY)
    pdf.output(target)
    print(target)


if __name__ == "__main__":
    main()
