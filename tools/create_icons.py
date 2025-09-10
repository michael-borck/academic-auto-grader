#!/usr/bin/env python3
"""
Icon Generation Tool for Academic Auto Grader
Creates all required icon formats from SVG source
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import io

def print_step(message):
    print(f"🔧 {message}")

def print_success(message):
    print(f"✅ {message}")

def print_error(message):
    print(f"❌ {message}")

def print_warning(message):
    print(f"⚠️  {message}")

def create_png_from_svg(svg_path, output_path, size):
    """Convert SVG to PNG using available tools"""
    try:
        # Try using cairosvg (Python library)
        try:
            import cairosvg
            cairosvg.svg2png(url=str(svg_path), write_to=str(output_path), output_width=size, output_height=size)
            return True
        except ImportError:
            pass
        
        # Try using Inkscape
        try:
            result = subprocess.run([
                'inkscape', 
                '--export-png', str(output_path),
                '--export-width', str(size),
                '--export-height', str(size),
                str(svg_path)
            ], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        # Try using ImageMagick
        try:
            result = subprocess.run([
                'convert',
                '-background', 'transparent',
                '-size', f'{size}x{size}',
                str(svg_path),
                str(output_path)
            ], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            pass
        
        print_warning(f"No SVG converter available. Creating fallback PNG for size {size}x{size}")
        create_fallback_png(output_path, size)
        return True
        
    except Exception as e:
        print_error(f"Failed to convert SVG to PNG: {e}")
        return False

def create_fallback_png(output_path, size):
    """Create a fallback PNG icon when SVG conversion is not available"""
    
    # Create a simple icon using PIL
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Background circle
    margin = size // 8
    circle_bbox = [margin, margin, size - margin, size - margin]
    draw.ellipse(circle_bbox, fill=(30, 58, 138, 255))  # Blue background
    
    # Document rectangle
    doc_margin = size // 4
    doc_width = size // 2
    doc_height = int(size * 0.6)
    doc_x = (size - doc_width) // 2
    doc_y = (size - doc_height) // 2 - size // 12
    
    draw.rectangle([doc_x, doc_y, doc_x + doc_width, doc_y + doc_height], 
                  fill=(255, 255, 255, 255), outline=(226, 232, 240, 255))
    
    # Document lines
    line_spacing = doc_height // 6
    line_start_x = doc_x + doc_width // 8
    line_end_x = doc_x + doc_width - doc_width // 8
    
    for i in range(1, 6):
        line_y = doc_y + i * line_spacing
        if line_y < doc_y + doc_height - line_spacing // 2:
            draw.line([line_start_x, line_y, line_end_x - (i % 2) * doc_width // 4, line_y], 
                     fill=(148, 163, 184, 180), width=max(1, size // 128))
    
    # Check mark circle
    check_radius = size // 8
    check_x = doc_x + doc_width - check_radius // 2
    check_y = doc_y + doc_height - check_radius * 2
    check_bbox = [check_x - check_radius, check_y - check_radius, 
                  check_x + check_radius, check_y + check_radius]
    draw.ellipse(check_bbox, fill=(34, 197, 94, 255))
    
    # Check mark (simplified)
    check_size = check_radius // 2
    check_points = [
        (check_x - check_size//2, check_y),
        (check_x - check_size//4, check_y + check_size//2),
        (check_x + check_size//2, check_y - check_size//2)
    ]
    draw.line([check_points[0], check_points[1]], fill=(255, 255, 255, 255), width=max(2, size // 64))
    draw.line([check_points[1], check_points[2]], fill=(255, 255, 255, 255), width=max(2, size // 64))
    
    # Save the image
    img.save(output_path, 'PNG')

def create_ico_file(png_files, output_path):
    """Create Windows ICO file from multiple PNG files"""
    try:
        images = []
        for png_file in png_files:
            if os.path.exists(png_file):
                img = Image.open(png_file)
                images.append(img)
        
        if images:
            images[0].save(output_path, format='ICO', sizes=[(img.size[0], img.size[1]) for img in images])
            return True
        else:
            print_error("No PNG files found for ICO creation")
            return False
    except Exception as e:
        print_error(f"Failed to create ICO file: {e}")
        return False

def create_icns_file(png_files, output_path):
    """Create macOS ICNS file from multiple PNG files"""
    try:
        # Try using iconutil (macOS only)
        if sys.platform == 'darwin':
            # Create iconset directory
            iconset_dir = output_path.with_suffix('.iconset')
            iconset_dir.mkdir(exist_ok=True)
            
            # Copy PNG files with proper naming
            size_mapping = {
                16: 'icon_16x16.png',
                32: 'icon_16x16@2x.png',
                32: 'icon_32x32.png', 
                64: 'icon_32x32@2x.png',
                128: 'icon_128x128.png',
                256: 'icon_128x128@2x.png',
                256: 'icon_256x256.png',
                512: 'icon_256x256@2x.png',
                512: 'icon_512x512.png',
                1024: 'icon_512x512@2x.png'
            }
            
            for png_file in png_files:
                if os.path.exists(png_file):
                    size = Image.open(png_file).size[0]
                    if size in size_mapping:
                        target_name = size_mapping[size]
                        shutil.copy2(png_file, iconset_dir / target_name)
            
            # Convert to ICNS
            result = subprocess.run(['iconutil', '-c', 'icns', str(iconset_dir)], 
                                  capture_output=True, check=True)
            
            # Clean up iconset directory
            shutil.rmtree(iconset_dir)
            return True
        else:
            # Fallback: create using PIL (limited support)
            print_warning("macOS iconutil not available, creating basic ICNS")
            largest_png = max(png_files, key=lambda x: Image.open(x).size[0] if os.path.exists(x) else 0)
            if os.path.exists(largest_png):
                img = Image.open(largest_png)
                img.save(output_path, format='ICNS')
                return True
            return False
            
    except Exception as e:
        print_error(f"Failed to create ICNS file: {e}")
        return False

def main():
    """Main icon generation function"""
    print_step("Starting icon generation for Academic Auto Grader")
    
    # Paths
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    svg_path = project_root / "gui" / "assets" / "icons" / "grader.svg"
    icons_dir = project_root / "gui" / "assets" / "icons"
    
    # Create icons directory if it doesn't exist
    icons_dir.mkdir(parents=True, exist_ok=True)
    
    # Check if SVG exists
    if not svg_path.exists():
        print_error(f"SVG file not found: {svg_path}")
        return False
    
    print_success(f"Found SVG source: {svg_path}")
    
    # Generate PNG files in various sizes
    sizes = [16, 32, 48, 64, 128, 256, 512, 1024]
    png_files = []
    
    print_step("Generating PNG files...")
    for size in sizes:
        png_path = icons_dir / f"grader_{size}x{size}.png"
        if create_png_from_svg(svg_path, png_path, size):
            png_files.append(png_path)
            print_success(f"Created {size}x{size} PNG")
        else:
            print_error(f"Failed to create {size}x{size} PNG")
    
    # Update the main PNG file (256x256)
    main_png = icons_dir / "grader.png"
    if icons_dir / "grader_256x256.png" in png_files:
        shutil.copy2(icons_dir / "grader_256x256.png", main_png)
        print_success("Updated main grader.png")
    
    # Create Windows ICO file
    print_step("Creating Windows ICO file...")
    ico_sizes = [16, 32, 48, 64, 128, 256]
    ico_png_files = [icons_dir / f"grader_{size}x{size}.png" for size in ico_sizes]
    ico_path = icons_dir / "grader.ico"
    
    if create_ico_file(ico_png_files, ico_path):
        print_success("Created Windows ICO file")
    else:
        print_error("Failed to create Windows ICO file")
    
    # Create macOS ICNS file
    print_step("Creating macOS ICNS file...")
    icns_sizes = [16, 32, 64, 128, 256, 512, 1024]
    icns_png_files = [icons_dir / f"grader_{size}x{size}.png" for size in icns_sizes]
    icns_path = icons_dir / "grader.icns"
    
    if create_icns_file(icns_png_files, icns_path):
        print_success("Created macOS ICNS file")
    else:
        print_error("Failed to create macOS ICNS file")
    
    # Create additional assets
    print_step("Creating additional assets...")
    
    # App icon for different contexts
    app_icon_sizes = {'small': 32, 'medium': 64, 'large': 128}
    for name, size in app_icon_sizes.items():
        source_png = icons_dir / f"grader_{size}x{size}.png"
        target_png = icons_dir / f"app_icon_{name}.png"
        if source_png.exists():
            shutil.copy2(source_png, target_png)
            print_success(f"Created {name} app icon ({size}x{size})")
    
    # Summary
    print_step("Icon generation summary:")
    total_files = len(list(icons_dir.glob("grader_*.png"))) + len(list(icons_dir.glob("grader.*")))
    print_success(f"Generated {total_files} icon files")
    
    # List all created files
    print("\n📁 Created files:")
    for icon_file in sorted(icons_dir.glob("grader*")):
        size_mb = icon_file.stat().st_size / 1024
        print(f"   {icon_file.name} ({size_mb:.1f} KB)")
    
    print_success("Icon generation completed!")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)