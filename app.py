from flask import Flask, render_template, request, jsonify, send_from_directory
import pydicom
import numpy as np
import zipfile
import os
import shutil
from pathlib import Path
import base64
from io import BytesIO
from PIL import Image
import json

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATASETS_FOLDER'] = 'datasets'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size
app.config['USE_MEMORY_MAPPING'] = False

# Ensure folders exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['DATASETS_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() == 'zip'

def find_dicom_files(directory):
    """Find all DICOM files in a directory"""
    dicom_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            filepath = os.path.join(root, file)
            # Try to read as DICOM
            try:
                pydicom.dcmread(filepath, stop_before_pixels=True)
                dicom_files.append(filepath)
            except:
                continue
    
    return sorted(dicom_files)

def extract_dicom_from_zip(zip_path, extract_to):
    """Extract zip file and return list of DICOM files"""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    
    return find_dicom_files(extract_to)

def load_dicom_slices(dicom_files):
    """Load DICOM slices and sort them"""
    slices = []
    for filepath in dicom_files:
        try:
            ds = pydicom.dcmread(filepath)
            if hasattr(ds, 'pixel_array'):
                slices.append(ds)
        except Exception as e:
            print(f"Error reading {filepath}: {e}")
    
    # Sort by ImagePositionPatient or InstanceNumber
    if slices and hasattr(slices[0], 'ImagePositionPatient'):
        try:
            slices.sort(key=lambda x: float(x.ImagePositionPatient[2]))
        except:
            slices.sort(key=lambda x: int(x.InstanceNumber) if hasattr(x, 'InstanceNumber') else 0)
    elif slices and hasattr(slices[0], 'InstanceNumber'):
        slices.sort(key=lambda x: int(x.InstanceNumber))
    
    return slices

def apply_modality_lut(pixel_array, ds):
    """Apply RescaleSlope and RescaleIntercept if present (for CT Hounsfield Units)"""
    if hasattr(ds, 'RescaleSlope') and hasattr(ds, 'RescaleIntercept'):
        slope = float(ds.RescaleSlope)
        intercept = float(ds.RescaleIntercept)
        pixel_array = pixel_array * slope + intercept
    return pixel_array

def normalize_image(pixel_array, window_center=None, window_width=None):
    """Normalize pixel array to 0-255 range with optional windowing"""
    pixel_array = pixel_array.astype(float)
    
    if window_center is not None and window_width is not None:
        # Apply windowing (same as matplotlib's vmin/vmax)
        img_min = window_center - window_width / 2
        img_max = window_center + window_width / 2
        
        # Clip and normalize based on window range (not actual data range)
        pixel_array = np.clip(pixel_array, img_min, img_max)
        pixel_array = (pixel_array - img_min) / (img_max - img_min) * 255
    else:
        # No windowing - normalize based on actual data range
        pixel_array -= pixel_array.min()
        if pixel_array.max() > 0:
            pixel_array = pixel_array / pixel_array.max() * 255
    
    return pixel_array.astype(np.uint8)

def array_to_base64(pixel_array):
    """Convert numpy array to base64 encoded image"""
    img = Image.fromarray(pixel_array)
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    img_str = base64.b64encode(buffer.read()).decode()
    return f"data:image/png;base64,{img_str}"

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Only ZIP files are allowed'}), 400
    
    # Create unique folder for this upload
    import uuid
    session_id = str(uuid.uuid4())
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    os.makedirs(upload_path, exist_ok=True)
    
    # Save zip file
    zip_path = os.path.join(upload_path, 'dicom.zip')
    file.save(zip_path)
    
    # Extract and process
    extract_path = os.path.join(upload_path, 'extracted')
    os.makedirs(extract_path, exist_ok=True)
    
    try:
        dicom_files = extract_dicom_from_zip(zip_path, extract_path)
        
        if not dicom_files:
            return jsonify({'error': 'No DICOM files found in the ZIP'}), 400
        
        slices = load_dicom_slices(dicom_files)
        
        if not slices:
            return jsonify({'error': 'Could not load any valid DICOM images'}), 400
        
        # Get metadata from first slice
        first_slice = slices[0]
        metadata = {
            'patient_name': str(first_slice.PatientName) if hasattr(first_slice, 'PatientName') else 'Unknown',
            'patient_id': str(first_slice.PatientID) if hasattr(first_slice, 'PatientID') else 'Unknown',
            'study_date': str(first_slice.StudyDate) if hasattr(first_slice, 'StudyDate') else 'Unknown',
            'modality': str(first_slice.Modality) if hasattr(first_slice, 'Modality') else 'Unknown',
            'num_slices': len(slices),
            'rows': int(first_slice.Rows),
            'columns': int(first_slice.Columns),
        }
        
        # Get window center/width if available
        window_center = None
        window_width = None
        if hasattr(first_slice, 'WindowCenter') and hasattr(first_slice, 'WindowWidth'):
            wc = first_slice.WindowCenter
            ww = first_slice.WindowWidth
            if isinstance(wc, pydicom.multival.MultiValue):
                wc = wc[0]
            if isinstance(ww, pydicom.multival.MultiValue):
                ww = ww[0]
            window_center = float(wc)
            window_width = float(ww)
            metadata['window_center'] = window_center
            metadata['window_width'] = window_width
        
        # Save session info
        session_data = {
            'session_id': session_id,
            'metadata': metadata,
            'num_slices': len(slices)
        }
        
        # Save slices data for later retrieval
        session_file = os.path.join(upload_path, 'session.json')
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Build 3D volume for multi-planar views (apply modality LUT for proper HU values)
        volume = np.stack([apply_modality_lut(s.pixel_array, s) for s in slices])
        volume_file = os.path.join(upload_path, 'volume.npy')
        np.save(volume_file, volume)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'metadata': metadata
        })
    
    except Exception as e:
        # Cleanup on error
        shutil.rmtree(upload_path, ignore_errors=True)
        return jsonify({'error': f'Error processing DICOM files: {str(e)}'}), 500

@app.route('/slice/<session_id>/<int:slice_idx>')
def get_slice(session_id, slice_idx):
    """Get a specific slice as base64 image"""
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    
    if not os.path.exists(upload_path):
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        # Load session info
        session_file = os.path.join(upload_path, 'session.json')
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Load volume
        volume_file = os.path.join(upload_path, 'volume.npy')
        if app.config['USE_MEMORY_MAPPING']:
            volume = np.load(volume_file, mmap_mode='r')
        else:
            volume = np.load(volume_file)
        
        if slice_idx < 0 or slice_idx >= volume.shape[0]:
            return jsonify({'error': 'Slice index out of range'}), 400
        
        # Get window settings
        window_center = session_data['metadata'].get('window_center')
        window_width = session_data['metadata'].get('window_width')
        
        # Get slice and normalize
        slice_data = volume[slice_idx]
        normalized = normalize_image(slice_data, window_center, window_width)
        img_base64 = array_to_base64(normalized)
        
        return jsonify({
            'image': img_base64,
            'slice_idx': slice_idx,
            'total_slices': volume.shape[0]
        })
    
    except Exception as e:
        return jsonify({'error': f'Error retrieving slice: {str(e)}'}), 500

@app.route('/views/<session_id>')
def get_multiplanar_views(session_id):
    """Get axial, coronal, and sagittal views"""
    upload_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
    
    if not os.path.exists(upload_path):
        return jsonify({'error': 'Session not found'}), 404
    
    try:
        # Load session info
        session_file = os.path.join(upload_path, 'session.json')
        with open(session_file, 'r') as f:
            session_data = json.load(f)
        
        # Load volume
        volume_file = os.path.join(upload_path, 'volume.npy')
        if app.config['USE_MEMORY_MAPPING']:
            volume = np.load(volume_file, mmap_mode='r')
        else:
            volume = np.load(volume_file)
        
        # Get window settings
        window_center = session_data['metadata'].get('window_center')
        window_width = session_data['metadata'].get('window_width')
        
        # Get middle slices for each view
        axial_slice = volume[0, :, :]
        coronal_slice = volume[:, volume.shape[1]//2, :]
        sagittal_slice = volume[:, :, volume.shape[2]//2]
        
        # Normalize and convert to base64
        axial_img = array_to_base64(normalize_image(axial_slice, window_center, window_width))
        coronal_img = array_to_base64(normalize_image(coronal_slice, window_center, window_width))
        sagittal_img = array_to_base64(normalize_image(sagittal_slice, window_center, window_width))
        
        return jsonify({
            'axial': axial_img,
            'coronal': coronal_img,
            'sagittal': sagittal_img,
            'volume_shape': volume.shape
        })
    
    except Exception as e:
        return jsonify({'error': f'Error generating views: {str(e)}'}), 500

@app.route('/datasets')
def list_datasets():
    """List all available datasets (collections)"""
    try:
        datasets = []
        datasets_path = app.config['DATASETS_FOLDER']
        
        if not os.path.exists(datasets_path):
            return jsonify({'datasets': []})
        
        # List all directories in datasets folder (each is a collection)
        for entry in os.listdir(datasets_path):
            entry_path = os.path.join(datasets_path, entry)
            if os.path.isdir(entry_path):
                # Count patient folders (subdirectories with DICOM files)
                patient_count = 0
                total_dicom_files = 0
                
                for patient_folder in os.listdir(entry_path):
                    patient_path = os.path.join(entry_path, patient_folder)
                    if os.path.isdir(patient_path):
                        dicom_files = find_dicom_files(patient_path)
                        if dicom_files:
                            patient_count += 1
                            total_dicom_files += len(dicom_files)
                
                if patient_count > 0:
                    datasets.append({
                        'id': entry,
                        'name': entry,
                        'num_patients': patient_count,
                        'num_files': total_dicom_files
                    })
        
        datasets.sort(key=lambda x: x.get('name', ''))
        return jsonify({'datasets': datasets})
    
    except Exception as e:
        return jsonify({'error': f'Error listing datasets: {str(e)}'}), 500

@app.route('/datasets/<dataset_id>/patients')
def list_patients(dataset_id):
    """List all patients within a dataset"""
    try:
        dataset_path = os.path.join(app.config['DATASETS_FOLDER'], dataset_id)
        
        if not os.path.exists(dataset_path):
            return jsonify({'error': f'Dataset not found: {dataset_id}'}), 404
        
        patients = []
        
        # List all patient folders
        for patient_folder in os.listdir(dataset_path):
            patient_path = os.path.join(dataset_path, patient_folder)
            if os.path.isdir(patient_path):
                dicom_files = find_dicom_files(patient_path)
                
                if dicom_files:
                    # Get info from first DICOM file
                    try:
                        first_ds = pydicom.dcmread(dicom_files[0], stop_before_pixels=True)
                        patient_info = {
                            'id': patient_folder,
                            'name': patient_folder,
                            'num_files': len(dicom_files),
                            'patient_name': str(first_ds.PatientName) if hasattr(first_ds, 'PatientName') else 'Unknown',
                            'patient_id': str(first_ds.PatientID) if hasattr(first_ds, 'PatientID') else 'Unknown',
                            'study_date': str(first_ds.StudyDate) if hasattr(first_ds, 'StudyDate') else 'Unknown',
                            'modality': str(first_ds.Modality) if hasattr(first_ds, 'Modality') else 'Unknown',
                        }
                        patients.append(patient_info)
                    except Exception as e:
                        # If can't read DICOM metadata, just list basic info
                        patients.append({
                            'id': patient_folder,
                            'name': patient_folder,
                            'num_files': len(dicom_files)
                        })
        
        patients.sort(key=lambda x: x.get('name', ''))
        return jsonify({'patients': patients})
    
    except Exception as e:
        return jsonify({'error': f'Error listing patients: {str(e)}'}), 500

@app.route('/datasets/<dataset_id>/patients/<patient_id>/load', methods=['POST'])
def load_patient(dataset_id, patient_id):
    """Load a specific patient scan from a dataset"""
    try:
        patient_path = os.path.join(app.config['DATASETS_FOLDER'], dataset_id, patient_id)
        
        if not os.path.exists(patient_path):
            return jsonify({'error': f'Patient not found: {dataset_id}/{patient_id}'}), 404
        
        if not os.path.isdir(patient_path):
            return jsonify({'error': f'Patient path is not a directory: {patient_id}'}), 400
        
        # Find all DICOM files for this patient
        dicom_files = find_dicom_files(patient_path)
        
        if not dicom_files:
            return jsonify({'error': 'No DICOM files found in dataset'}), 400
        
        # Load DICOM slices
        slices = load_dicom_slices(dicom_files)
        
        if not slices:
            return jsonify({'error': 'Could not load any valid DICOM images'}), 400
        
        # Create session in uploads folder (reuse existing session structure)
        import uuid
        session_id = f"dataset_{dataset_id}_{patient_id}_{str(uuid.uuid4())[:8]}"
        session_path = os.path.join(app.config['UPLOAD_FOLDER'], session_id)
        os.makedirs(session_path, exist_ok=True)
        
        # Get metadata from first slice
        first_slice = slices[0]
        metadata = {
            'patient_name': str(first_slice.PatientName) if hasattr(first_slice, 'PatientName') else 'Unknown',
            'patient_id': str(first_slice.PatientID) if hasattr(first_slice, 'PatientID') else 'Unknown',
            'study_date': str(first_slice.StudyDate) if hasattr(first_slice, 'StudyDate') else 'Unknown',
            'modality': str(first_slice.Modality) if hasattr(first_slice, 'Modality') else 'Unknown',
            'num_slices': len(slices),
            'rows': int(first_slice.Rows),
            'columns': int(first_slice.Columns),
            'dataset_id': dataset_id,
            'patient_folder': patient_id,
        }
        
        # Get window center/width if available
        window_center = None
        window_width = None
        if hasattr(first_slice, 'WindowCenter') and hasattr(first_slice, 'WindowWidth'):
            wc = first_slice.WindowCenter
            ww = first_slice.WindowWidth
            if isinstance(wc, pydicom.multival.MultiValue):
                wc = wc[0]
            if isinstance(ww, pydicom.multival.MultiValue):
                ww = ww[0]
            window_center = float(wc)
            window_width = float(ww)
            metadata['window_center'] = window_center
            metadata['window_width'] = window_width
        
        # Save session data
        session_data = {
            'session_id': session_id,
            'metadata': metadata,
            'num_slices': len(slices),
            'source': 'dataset',
            'dataset_id': dataset_id,
            'patient_id': patient_id
        }
        
        session_file = os.path.join(session_path, 'session.json')
        with open(session_file, 'w') as f:
            json.dump(session_data, f)
        
        # Build 3D volume
        volume = np.stack([apply_modality_lut(s.pixel_array, s) for s in slices])
        volume_file = os.path.join(session_path, 'volume.npy')
        np.save(volume_file, volume)
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'metadata': metadata
        })
    
    except Exception as e:
        return jsonify({'error': f'Error loading patient scan: {str(e)}'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

