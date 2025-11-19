#!/bin/bash

# DICOM Dataset Management Script
# Helper script to manage datasets folder

DATASETS_DIR="datasets"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        DICOM Dataset Management Tool                   ║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Create datasets directory if it doesn't exist
if [ ! -d "$DATASETS_DIR" ]; then
    echo -e "${YELLOW}⚠️  Datasets directory not found. Creating...${NC}"
    mkdir -p "$DATASETS_DIR"
    echo -e "${GREEN}✓ Created: $DATASETS_DIR/${NC}"
fi

# Function to list datasets
list_datasets() {
    echo -e "${BLUE}📂 Available Datasets:${NC}"
    echo ""
    
    if [ -z "$(ls -A $DATASETS_DIR 2>/dev/null)" ]; then
        echo -e "${YELLOW}  No datasets found${NC}"
        echo ""
        return
    fi
    
    for dataset in "$DATASETS_DIR"/*/ ; do
        if [ -d "$dataset" ]; then
            name=$(basename "$dataset")
            count=$(find "$dataset" -type f \( -name "*.dcm" -o -name "*.DCM" \) 2>/dev/null | wc -l)
            size=$(du -sh "$dataset" 2>/dev/null | cut -f1)
            echo -e "  ${GREEN}📁 $name${NC}"
            echo -e "     Files: $count DICOM files"
            echo -e "     Size: $size"
            echo ""
        fi
    done
}

# Function to add a new dataset
add_dataset() {
    echo -e "${BLUE}➕ Add New Dataset${NC}"
    echo ""
    
    read -p "Enter dataset name (no spaces, use underscores): " name
    
    if [ -z "$name" ]; then
        echo -e "${RED}✗ Dataset name cannot be empty${NC}"
        return 1
    fi
    
    # Sanitize name
    name=$(echo "$name" | tr ' ' '_' | tr -cd '[:alnum:]_-')
    
    dataset_path="$DATASETS_DIR/$name"
    
    if [ -d "$dataset_path" ]; then
        echo -e "${RED}✗ Dataset already exists: $name${NC}"
        return 1
    fi
    
    mkdir -p "$dataset_path"
    echo -e "${GREEN}✓ Created dataset folder: $dataset_path${NC}"
    echo ""
    echo -e "${YELLOW}Now copy your DICOM files to:${NC}"
    echo -e "  $SCRIPT_DIR/$dataset_path/"
    echo ""
    echo -e "Example:"
    echo -e "  cp -r /path/to/dicom/files/* $dataset_path/"
}

# Function to import from directory
import_dataset() {
    echo -e "${BLUE}📥 Import Dataset from Directory${NC}"
    echo ""
    
    read -p "Enter source directory path: " source_dir
    
    if [ ! -d "$source_dir" ]; then
        echo -e "${RED}✗ Directory not found: $source_dir${NC}"
        return 1
    fi
    
    read -p "Enter dataset name: " name
    name=$(echo "$name" | tr ' ' '_' | tr -cd '[:alnum:]_-')
    
    dataset_path="$DATASETS_DIR/$name"
    
    if [ -d "$dataset_path" ]; then
        echo -e "${RED}✗ Dataset already exists: $name${NC}"
        return 1
    fi
    
    echo -e "${YELLOW}Copying files...${NC}"
    cp -r "$source_dir" "$dataset_path"
    
    count=$(find "$dataset_path" -type f \( -name "*.dcm" -o -name "*.DCM" \) | wc -l)
    
    if [ "$count" -eq 0 ]; then
        echo -e "${RED}✗ No DICOM files found in source directory${NC}"
        rm -rf "$dataset_path"
        return 1
    fi
    
    echo -e "${GREEN}✓ Imported $count DICOM files to: $dataset_path${NC}"
}

# Function to remove a dataset
remove_dataset() {
    echo -e "${BLUE}🗑️  Remove Dataset${NC}"
    echo ""
    
    list_datasets
    
    read -p "Enter dataset name to remove: " name
    
    dataset_path="$DATASETS_DIR/$name"
    
    if [ ! -d "$dataset_path" ]; then
        echo -e "${RED}✗ Dataset not found: $name${NC}"
        return 1
    fi
    
    read -p "Are you sure you want to remove '$name'? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo -e "${YELLOW}Cancelled${NC}"
        return 0
    fi
    
    rm -rf "$dataset_path"
    echo -e "${GREEN}✓ Removed dataset: $name${NC}"
}

# Function to check dataset
check_dataset() {
    echo -e "${BLUE}🔍 Check Dataset${NC}"
    echo ""
    
    read -p "Enter dataset name: " name
    
    dataset_path="$DATASETS_DIR/$name"
    
    if [ ! -d "$dataset_path" ]; then
        echo -e "${RED}✗ Dataset not found: $name${NC}"
        return 1
    fi
    
    echo -e "${GREEN}Dataset: $name${NC}"
    echo ""
    
    # Count DICOM files
    dcm_count=$(find "$dataset_path" -type f \( -name "*.dcm" -o -name "*.DCM" \) | wc -l)
    echo -e "  DICOM files: $dcm_count"
    
    # Total files
    total_files=$(find "$dataset_path" -type f | wc -l)
    echo -e "  Total files: $total_files"
    
    # Size
    size=$(du -sh "$dataset_path" | cut -f1)
    echo -e "  Size: $size"
    
    # Permissions
    perms=$(ls -ld "$dataset_path" | awk '{print $1}')
    echo -e "  Permissions: $perms"
    
    # Sample first DICOM file
    first_dcm=$(find "$dataset_path" -type f \( -name "*.dcm" -o -name "*.DCM" \) | head -1)
    
    if [ -n "$first_dcm" ] && command -v dcmdump &> /dev/null; then
        echo ""
        echo -e "${BLUE}Sample DICOM Info:${NC}"
        dcmdump "$first_dcm" 2>/dev/null | grep -E "(PatientName|StudyDate|Modality|SeriesDescription)" | head -5
    fi
}

# Function to fix permissions
fix_permissions() {
    echo -e "${BLUE}🔧 Fix Permissions${NC}"
    echo ""
    
    echo -e "Setting permissions on datasets folder..."
    chmod -R 755 "$DATASETS_DIR"
    
    echo -e "${GREEN}✓ Permissions updated${NC}"
    echo -e "  Directories: 755 (rwxr-xr-x)"
    echo -e "  Files: 644 (rw-r--r--)"
}

# Main menu
show_menu() {
    echo ""
    echo -e "${YELLOW}Choose an option:${NC}"
    echo ""
    echo "  1) List datasets"
    echo "  2) Add new dataset (create empty folder)"
    echo "  3) Import dataset (copy from directory)"
    echo "  4) Remove dataset"
    echo "  5) Check dataset details"
    echo "  6) Fix permissions"
    echo "  7) Exit"
    echo ""
    read -p "Enter choice [1-7]: " choice
    
    case $choice in
        1) list_datasets ;;
        2) add_dataset ;;
        3) import_dataset ;;
        4) remove_dataset ;;
        5) check_dataset ;;
        6) fix_permissions ;;
        7) echo "Goodbye!"; exit 0 ;;
        *) echo -e "${RED}Invalid option${NC}" ;;
    esac
    
    read -p "Press Enter to continue..."
    clear
    show_menu
}

# Run
clear
show_menu

