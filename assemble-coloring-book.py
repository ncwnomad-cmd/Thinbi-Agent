import argparse
import json
import os
import re
import zlib
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(os.environ.get("COLORING_BOOK_ROOT", r"D:\Coloring Books\Cozy Christmas Coloring Book"))
PAGES = ROOT / "Pages"
PRINT = ROOT / "PrintReady"
PAGE_PX = 2550
DPI = 300
TARGET_ILLUSTRATIONS = 50


def page_number(path):
    match = re.search(r"Page[_-]?(\d+)", path.stem, re.I)
    return int(match.group(1)) if match else 999999


class PDFWriter:
    def __init__(self, path):
        self.f = open(path, "wb")
        self.offsets = [0, 0, 0]
        self.next_id = 3
        self.page_ids = []
        self.f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")

    def obj(self, body):
        oid = self.next_id
        self.next_id += 1
        self.offsets.append(self.f.tell())
        self.f.write(f"{oid} 0 obj\n".encode())
        self.f.write(body)
        self.f.write(b"\nendobj\n")
        return oid

    def stream(self, dictionary, data):
        header = dictionary + f" /Length {len(data)} >>\nstream\n".encode()
        return self.obj(header + data + b"\nendstream")

    def add_page(self, image_path=None):
        content = b""
        resources = "<< >>"

        if image_path is not None:
            with Image.open(image_path) as source:
                source.load()
                binary = ImageOps.grayscale(source).point(
                    lambda pixel: 0 if pixel < 210 else 255,
                    mode="1"
                )
                compressed = zlib.compress(binary.tobytes(), 6)
                image_id = self.stream(
                    f"<< /Type /XObject /Subtype /Image /Width {binary.width} /Height {binary.height} /ColorSpace /DeviceGray /BitsPerComponent 1 /Filter /FlateDecode".encode(),
                    compressed
                )
                resources = f"<< /XObject << /Im0 {image_id} 0 R >> >>"
                content = b"q\n612 0 0 612 0 0 cm\n/Im0 Do\nQ\n"

        content_id = self.stream(b"<<", content)
        page_id = self.obj(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 612] /Resources {resources} /Contents {content_id} 0 R >>".encode()
        )
        self.page_ids.append(page_id)

    def close(self):
        kids = " ".join(f"{oid} 0 R" for oid in self.page_ids)
        self.offsets[1] = self.f.tell()
        self.f.write(b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n")
        self.offsets[2] = self.f.tell()
        self.f.write(f"2 0 obj\n<< /Type /Pages /Count {len(self.page_ids)} /Kids [{kids}] >>\nendobj\n".encode())

        xref = self.f.tell()
        size = self.next_id
        self.f.write(f"xref\n0 {size}\n".encode())
        self.f.write(b"0000000000 65535 f \n")
        for oid in range(1, size):
            offset = self.offsets[oid] if oid < len(self.offsets) else 0
            self.f.write(f"{offset:010d} 00000 n \n".encode() if offset else b"0000000000 00000 f \n")
        self.f.write(f"trailer\n<< /Size {size} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
        self.f.close()


def main():
    parser = argparse.ArgumentParser(description="Assemble 50 coloring illustrations into a 100-page KDP interior.")
    parser.add_argument(
        "--target-illustrations", "--target-pages",
        dest="target_illustrations",
        type=int,
        default=TARGET_ILLUSTRATIONS,
        help="Number of illustrated fronts (default: 50; each is followed by a blank back)."
    )
    parser.add_argument("--allow-incomplete", action="store_true")
    args = parser.parse_args()

    if not 1 <= args.target_illustrations <= TARGET_ILLUSTRATIONS:
        parser.error(f"--target-illustrations must be between 1 and {TARGET_ILLUSTRATIONS}")

    PAGES.mkdir(parents=True, exist_ok=True)
    numbered = [
        path for path in PAGES.glob("*.png")
        if page_number(path) < 999999 and "TEST" not in path.stem.upper()
    ]
    unique = {}
    for path in sorted(numbered, key=lambda item: item.name.lower()):
        unique.setdefault(page_number(path), path)
    files = [unique[number] for number in sorted(unique)]

    report = {
        "project": "Cozy Christmas Coloring Book",
        "target_illustrations": args.target_illustrations,
        "target_interior_pages": args.target_illustrations * 2,
        "found_illustrations": len(files),
        "warnings": [],
        "pages": []
    }

    if len(files) != args.target_illustrations and not args.allow_incomplete:
        report["warnings"].append(
            f"Expected {args.target_illustrations} numbered illustrations; found {len(files)}. No final PDF created."
        )
        (ROOT / "quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(json.dumps(report, indent=2))
        raise SystemExit(2)

    if not files:
        raise SystemExit("No numbered PNG illustrations found.")

    PRINT.mkdir(parents=True, exist_ok=True)
    for index, path in enumerate(files, 1):
        with Image.open(path) as source:
            source.load()
            original_size = source.size
            binary = ImageOps.grayscale(source).point(
                lambda pixel: 0 if pixel < 210 else 255,
                mode="1"
            )
            histogram = binary.histogram()
            ink_fraction = histogram[0] / (binary.width * binary.height)

            if ink_fraction < 0.002:
                report["warnings"].append(f"{path.name}: almost blank.")
            if ink_fraction > 0.25:
                report["warnings"].append(f"{path.name}: unusually dense black coverage.")

            art = binary.convert("RGB")
            art.thumbnail((2400, 2400), Image.Resampling.LANCZOS)
            canvas = Image.new("RGB", (PAGE_PX, PAGE_PX), "white")
            canvas.paste(art, ((PAGE_PX - art.width) // 2, (PAGE_PX - art.height) // 2))

            output = PRINT / f"Page_{index:03d}.png"
            canvas.save(output, "PNG", dpi=(DPI, DPI), optimize=True)
            report["pages"].append({
                "page": index,
                "source": path.name,
                "source_size": list(original_size),
                "print_size": [PAGE_PX, PAGE_PX],
                "dpi": DPI,
                "ink_fraction": round(ink_fraction, 5),
                "blank_back_after": True
            })

    pdf_path = ROOT / "Cozy_Christmas_Coloring_Book_Interior.pdf"
    pdf = PDFWriter(pdf_path)
    for index in range(1, len(files) + 1):
        pdf.add_page(PRINT / f"Page_{index:03d}.png")
        pdf.add_page(None)
    pdf.close()

    report["pdf"] = str(pdf_path)
    report["pdf_page_count"] = len(files) * 2
    report["print_ready_folder"] = str(PRINT)
    report["warnings"].append(
        "Automated ink-coverage checks do not replace visual review. Inspect every illustration before KDP upload."
    )
    (ROOT / "quality_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
