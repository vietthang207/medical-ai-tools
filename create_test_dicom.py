#!/usr/bin/env python3
"""
Create a test DICOM dataset for development/testing purposes
This creates synthetic DICOM files (not from real patients)
"""

import pydicom
from pydicom.dataset import Dataset, FileDataset
import numpy as np
from datetime import datetime
import os
import zipfile

def create_test_dicom_slice(filename, slice_number, total_slices=10):
    """Create a single test DICOM file"""
    
    # Create a sample 512x512 image with a pattern
    rows, cols = 512, 512
    
    # Create interesting pattern (circles, gradients, etc.)
    x = np.linspace(-256, 256, cols)
    y = np.linspace(-256, 256, rows)
    X, Y = np.meshgrid(x, y)
    
    # Create multiple circles at different depths
    circle_radius = 100 - (slice_number * 5)
    pattern = np.sqrt(X**2 + Y**2) < circle_radius
    
    # Add gradient
    gradient = (X + 256) / 512 * (Y + 256) / 512
    
    # Combine patterns
    pixel_array = (pattern * 2000 + gradient * 1000).astype(np.int16)
    
    # Add some noise
    noise = np.random.normal(0, 50, (rows, cols))
    pixel_array = (pixel_array + noise).astype(np.int16)
    
    # Create the FileDataset instance
    file_meta = Dataset()
    file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.2'  # CT Image Storage
    file_meta.MediaStorageSOPInstanceUID = f'1.2.3.{slice_number}'
    file_meta.TransferSyntaxUID = pydicom.uid.ExplicitVRLittleEndian
    
    ds = FileDataset(filename, {}, file_meta=file_meta, preamble=b"\0" * 128)
    
    # Patient information
    ds.PatientName = "Test^Patient^Synthetic"
    ds.PatientID = "TEST123456"
    ds.PatientBirthDate = "19800101"
    ds.PatientSex = "O"
    
    # Study information
    ds.StudyDate = datetime.now().strftime('%Y%m%d')
    ds.StudyTime = datetime.now().strftime('%H%M%S')
    ds.StudyInstanceUID = '1.2.3.4.5.6.7.8.9'
    ds.StudyDescription = 'Test CT Study'
    
    # Series information
    ds.SeriesInstanceUID = '1.2.3.4.5.6.7.8.9.10'
    ds.SeriesNumber = 1
    ds.SeriesDescription = 'Test Series'
    
    # Image information
    ds.Modality = 'CT'
    ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.2'
    ds.SOPInstanceUID = f'1.2.3.{slice_number}'
    ds.InstanceNumber = slice_number
    
    # Image pixel information
    ds.SamplesPerPixel = 1
    ds.PhotometricInterpretation = "MONOCHROME2"
    ds.Rows = rows
    ds.Columns = cols
    ds.BitsAllocated = 16
    ds.BitsStored = 16
    ds.HighBit = 15
    ds.PixelRepresentation = 1  # signed
    
    # Image position and orientation
    ds.ImagePositionPatient = [0, 0, slice_number * 2.5]  # 2.5mm spacing
    ds.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
    ds.PixelSpacing = [0.5, 0.5]  # 0.5mm x 0.5mm
    ds.SliceThickness = 2.5
    
    # CT-specific tags
    ds.WindowCenter = 1000
    ds.WindowWidth = 2000
    ds.RescaleIntercept = -1024
    ds.RescaleSlope = 1
    
    # Set pixel data
    ds.PixelData = pixel_array.tobytes()
    
    # Save the DICOM file
    ds.save_as(filename, write_like_original=False)
    print(f"Created: {filename}")

def create_test_dicom_series(output_dir="test_dicom", num_slices=20):
    """Create a series of test DICOM files"""
    
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Creating {num_slices} test DICOM slices...")
    
    for i in range(num_slices):
        filename = os.path.join(output_dir, f"slice_{i:04d}.dcm")
        create_test_dicom_slice(filename, i, num_slices)
    
    print(f"\n✅ Created {num_slices} DICOM files in '{output_dir}/'")
    
    # Create a ZIP file
    zip_filename = "test_dicom.zip"
    print(f"\nCreating ZIP file: {zip_filename}...")
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for i in range(num_slices):
            filename = os.path.join(output_dir, f"slice_{i:04d}.dcm")
            zipf.write(filename, f"slice_{i:04d}.dcm")
    
    print(f"✅ Created: {zip_filename}")
    print(f"\n🎉 Test DICOM dataset ready!")
    print(f"\nYou can now:")
    print(f"  1. Start the server: python app.py")
    print(f"  2. Upload the file: {zip_filename}")
    print(f"  3. Or test with: python test_upload.py {zip_filename}")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Create test DICOM files')
    parser.add_argument('--slices', type=int, default=20, help='Number of slices (default: 20)')
    parser.add_argument('--output', type=str, default='test_dicom', help='Output directory (default: test_dicom)')
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("🏥 Test DICOM Generator")
    print("=" * 60)
    print("\n⚠️  Note: This creates SYNTHETIC data for testing only!")
    print("   NOT real patient data.\n")
    
    create_test_dicom_series(args.output, args.slices)

if __name__ == "__main__":
    main()

