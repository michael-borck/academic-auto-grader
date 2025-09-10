# Icons Directory

This directory contains application icons and assets for the GUI.

## Icon Files

- `grader.ico` - Windows icon (16x16, 32x32, 48x48, 64x64, 128x128, 256x256)
- `grader.icns` - macOS icon bundle (16x16 to 1024x1024)
- `grader.png` - Linux/general PNG icon (256x256)

## Icon Creation Notes

For production builds, replace placeholder files with actual icons:

### Windows (.ico)
- Multi-resolution icon supporting 16x16 through 256x256
- Use tools like GIMP, Paint.NET, or online converters
- Include transparency for rounded corners

### macOS (.icns)
- Icon bundle containing multiple resolutions
- Use `iconutil` on macOS: `iconutil -c icns icon.iconset`
- Include Retina (@2x) versions

### Linux (.png)
- Standard PNG format, 256x256 pixels
- Use for desktop entries and AppImage

## Recommended Icon Design
- Simple, recognizable symbol representing grading/education
- Good contrast for both light and dark themes
- Professional appearance suitable for academic use
- Consider using graduation cap, checkmark, or document symbols