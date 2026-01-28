from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from pathlib import Path
import zipfile
from .image_processor import render_certificate_image
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
import io

def _sanitize_filename(s: str):
    return re.sub(r'[^\w\-_\. ]', '_', str(s))

def _generate_single_pdf(args):
    """Helper function for parallel PDF generation"""
    i, row, template_path, placeholders, fonts_dir, output_dir, default_font, filename_field = args
    try:
        img = render_certificate_image(template_path, placeholders, row, fonts_dir, default_font)
        
        # Determine filename
        if filename_field and filename_field in row:
            safe_name = _sanitize_filename(row.get(filename_field, f"row_{i}"))
        else:
            safe_name = _sanitize_filename(row.get("name", f"row_{i}"))
        
        pdf_path = output_dir / f"{i:03d}_{safe_name}.pdf"
        
        # Create PDF from image
        img_w, img_h = img.size
        c = canvas.Canvas(str(pdf_path), pagesize=(img_w, img_h))
        img_reader = ImageReader(img)
        c.drawImage(img_reader, 0, 0, width=img_w, height=img_h)
        c.showPage()
        c.save()
        
        return pdf_path
    except Exception as e:
        print(f"Error generating PDF for row {i}: {str(e)}")
        return None

def create_pdfs_from_rows(template_path: Path, rows: list, placeholders: dict, fonts_dir: Path, output_dir: Path, default_font: str, filename_field: str = None):
    """Generate PDFs with parallel processing for better performance"""
    pdf_paths = []
    
    # Prepare arguments for each row
    args_list = [
        (i, row, template_path, placeholders, fonts_dir, output_dir, default_font, filename_field)
        for i, row in enumerate(rows, start=1)
    ]
    
    # Use ThreadPoolExecutor for parallel PDF generation
    max_workers = min(4, len(rows))  # Use up to 4 parallel workers
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_generate_single_pdf, args) for args in args_list]
        for future in as_completed(futures):
            result = future.result()
            if result:
                pdf_paths.append(result)
    
    # Sort by filename to maintain order
    pdf_paths.sort()
    
    return pdf_paths

def zip_files(files, zip_path: Path):
    """Optimize zip creation with compression"""
    with zipfile.ZipFile(str(zip_path), "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
        for f in files:
            z.write(str(f), arcname=f.name)
