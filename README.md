# DICOM Medical Image Viewer

A web-based DICOM viewer that allows users to upload zipped DICOM folders and visualize medical images with multiple viewing options.

## Features

- 📁 **Upload ZIP Files**: Drag and drop or browse to upload zipped DICOM folders
- 🔍 **Interactive Slice Viewer**: Navigate through DICOM slices with a slider
- 📊 **Multi-Planar Views**: View axial, coronal, and sagittal planes
- 📋 **Metadata Display**: Show patient information, study details, and image properties
- 🎨 **Modern UI**: Beautiful, responsive interface with smooth animations
- 🏥 **CT Window/Level Support**: Automatic windowing for CT scans

## Installation

1. **Clone or navigate to the project directory**

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Create necessary directories**:
```bash
mkdir -p templates uploads
```

## Usage

1. **Start the Flask server**:
```bash
python3 app.py
```

2. **Open your browser** and navigate to:
```
http://localhost:5000
```

3. **Upload DICOM files**:
   - Prepare a ZIP file containing DICOM (.dcm) files
   - Drag and drop the ZIP file onto the upload area, or click to browse
   - Wait for processing (may take a few seconds for large datasets)

4. **View your images**:
   - **Slice Viewer Tab**: Use the slider to navigate through individual slices
   - **Multi-Planar Views Tab**: See axial, coronal, and sagittal cross-sections

## Project Structure

```
medical-ai-tools/
├── app.py                  # Flask backend application
├── templates/
│   └── index.html         # Frontend HTML/CSS/JavaScript
├── requirements.txt       # Python dependencies
├── uploads/               # Temporary storage for uploaded files
└── README.md             # This file
```

## How It Works

1. **Upload**: User uploads a ZIP file containing DICOM files
2. **Extraction**: Server extracts and identifies DICOM files
3. **Processing**: DICOM files are loaded and sorted by slice location
4. **3D Volume**: Slices are stacked into a 3D numpy array
5. **Visualization**: Images are normalized, converted to PNG, and sent to frontend
6. **Display**: Frontend displays images with interactive controls

## API Endpoints

- `GET /` - Main page
- `POST /upload` - Upload DICOM ZIP file
- `GET /slice/<session_id>/<slice_idx>` - Get specific slice image
- `GET /views/<session_id>` - Get multi-planar views

## Configuration

You can modify these settings in `app.py`:

- `MAX_CONTENT_LENGTH`: Maximum file size (default: 500MB)
- `UPLOAD_FOLDER`: Directory for temporary file storage
- Port: Change in `app.run()` (default: 5000)

## Security Notes

⚠️ **Important**: This is a development/demo application. For production use:

1. Add authentication and authorization
2. Implement proper session management
3. Add file validation and sanitization
4. Use HTTPS
5. Implement rate limiting
6. Clean up old upload folders periodically
7. Add HIPAA compliance measures if handling real patient data

## Troubleshooting

**Issue**: "No DICOM files found"
- Make sure your ZIP contains `.dcm` files
- DICOM files may have no extension - the app tries to read all files

**Issue**: "Module not found"
- Run `pip install -r requirements.txt`

**Issue**: Server is slow
- Large DICOM datasets take time to process
- Consider reducing image resolution or implementing caching

## Contributing

Contributions welcome! Feel free to:
- Add new features (3D rendering, measurements, annotations)
- Improve performance
- Enhance UI/UX
- Add more DICOM metadata support

---

## 📱 Next Steps

### For Development:
- Modify `templates/index.html` for UI changes
- Modify `app.py` for backend logic
- Add new features like measurements, annotations, or 3D rendering

### For Production:
- See `DEPLOYMENT.md` for production deployment guide
- Use a production WSGI server (gunicorn, uWSGI)
- Add authentication and authorization
- Implement HTTPS
- Add HIPAA compliance measures

---

## 💡 Tips

1. **Large Datasets**: Processing 500+ slices may take 10-30 seconds
2. **Memory Usage**: Large volumes (1000+ slices) will use significant RAM
3. **Browser Cache**: Clear browser cache if images don't update
4. **Multiple Studies**: Each upload creates a new session
5. **Cleanup**: Old uploads are stored in `uploads/` - clean periodically