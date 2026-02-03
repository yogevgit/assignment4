import os
from pathlib import Path

try:
    from pypdf import PdfReader
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "Missing dependency 'pypdf'. Install it with: pip install pypdf"
    ) from exc


def extract_pdf_text(pdf_path: Path) -> str:
    reader = PdfReader(str(pdf_path))
    parts = []
    for i, page in enumerate(reader.pages, start=1):
        try:
            text = page.extract_text() or ""
        except Exception as exc:  # pragma: no cover
            text = f"[ERROR extracting page {i}: {exc}]"
        parts.append(text)
    return "\n\n".join(parts)


def main() -> None:
    root = Path(__file__).resolve().parent
    output_dir = root / "pdf_text"
    output_dir.mkdir(exist_ok=True)

    pdf_files = sorted(p for p in root.iterdir() if p.suffix.lower() == ".pdf")
    if not pdf_files:
        print("No PDF files found in:", root)
        return

    for pdf in pdf_files:
        text = extract_pdf_text(pdf)
        out_path = output_dir / f"{pdf.stem}.txt"
        out_path.write_text(text, encoding="utf-8")
        print("Extracted:", pdf.name, "->", out_path.name)


if __name__ == "__main__":
    main()
