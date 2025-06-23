// Drag and Drop File Upload Functionality
document.addEventListener('DOMContentLoaded', function() {
    // Initialize drag and drop for all file input areas
    initializeDragAndDrop();
    
    // Initialize file preview functionality
    initializeFilePreviews();
    
    // Initialize image gallery
    initializeImageGallery();
});

function initializeDragAndDrop() {
    const dropZones = document.querySelectorAll('.file-drop-zone, input[type="file"]');
    
    dropZones.forEach(zone => {
        // Create drop zone wrapper if it doesn't exist
        if (!zone.classList.contains('file-drop-zone')) {
            const wrapper = createDropZoneWrapper(zone);
            zone.parentNode.insertBefore(wrapper, zone);
            wrapper.appendChild(zone);
        }
        
        // Add event listeners
        zone.addEventListener('dragover', handleDragOver);
        zone.addEventListener('dragenter', handleDragEnter);
        zone.addEventListener('dragleave', handleDragLeave);
        zone.addEventListener('drop', handleDrop);
    });
}

function createDropZoneWrapper(input) {
    const wrapper = document.createElement('div');
    wrapper.className = 'file-drop-zone border-2 border-dashed border-secondary rounded p-4 text-center';
    wrapper.innerHTML = `
        <div class="drop-zone-content">
            <i class="fas fa-cloud-upload-alt fa-3x text-muted mb-3"></i>
            <p class="mb-2"><strong>Arrastra archivos aquí</strong></p>
            <p class="text-muted small">o haz clic para seleccionar</p>
        </div>
        <div class="file-preview-container mt-3"></div>
    `;
    return wrapper;
}

function handleDragOver(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.add('drag-over');
}

function handleDragEnter(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.add('drag-over');
}

function handleDragLeave(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('drag-over');
}

function handleDrop(e) {
    e.preventDefault();
    e.stopPropagation();
    this.classList.remove('drag-over');
    
    const files = e.dataTransfer.files;
    const input = this.querySelector('input[type="file"]') || this;
    
    if (input && files.length > 0) {
        // Create a new FileList object
        const dt = new DataTransfer();
        
        // Add dropped files
        for (let i = 0; i < files.length; i++) {
            dt.items.add(files[i]);
        }
        
        // Update input files
        input.files = dt.files;
        
        // Trigger preview update
        updateFilePreview(input);
        
        // Trigger change event
        input.dispatchEvent(new Event('change', { bubbles: true }));
    }
}

function updateFilePreview(input) {
    const container = input.closest('.file-drop-zone').querySelector('.file-preview-container');
    if (!container) return;
    
    container.innerHTML = '';
    
    if (input.files && input.files.length > 0) {
        container.innerHTML = '<h6 class="mt-3 mb-2">Archivos seleccionados:</h6>';
        
        for (let i = 0; i < input.files.length; i++) {
            const file = input.files[i];
            const fileItem = createFilePreviewItem(file, i);
            container.appendChild(fileItem);
        }
    }
}

function createFilePreviewItem(file, index) {
    const item = document.createElement('div');
    item.className = 'file-preview-item d-flex align-items-center justify-content-between p-2 border rounded mb-2';
    
    const fileIcon = getFileIcon(file.type, file.name);
    const fileSize = formatFileSize(file.size);
    
    item.innerHTML = `
        <div class="d-flex align-items-center">
            <i class="${fileIcon} me-2"></i>
            <div>
                <div class="small fw-bold">${file.name}</div>
                <div class="text-muted small">${fileSize}</div>
            </div>
        </div>
        <button type="button" class="btn btn-sm btn-outline-danger" onclick="removeFileFromPreview(this, ${index})">
            <i class="fas fa-times"></i>
        </button>
    `;
    
    return item;
}

function getFileIcon(mimeType, fileName) {
    const extension = fileName.split('.').pop().toLowerCase();
    
    // Images
    if (mimeType.startsWith('image/') || ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp'].includes(extension)) {
        return 'fas fa-image text-primary';
    }
    
    // Documents
    if (['pdf'].includes(extension)) {
        return 'fas fa-file-pdf text-danger';
    }
    if (['doc', 'docx'].includes(extension)) {
        return 'fas fa-file-word text-primary';
    }
    if (['xls', 'xlsx'].includes(extension)) {
        return 'fas fa-file-excel text-success';
    }
    if (['ppt', 'pptx'].includes(extension)) {
        return 'fas fa-file-powerpoint text-warning';
    }
    
    // Videos
    if (mimeType.startsWith('video/') || ['mp4', 'avi', 'mov', 'wmv', 'flv', 'webm', 'mkv'].includes(extension)) {
        return 'fas fa-video text-warning';
    }
    
    // Audio
    if (mimeType.startsWith('audio/') || ['mp3', 'wav', 'flac', 'aac', 'ogg', 'm4a'].includes(extension)) {
        return 'fas fa-music text-success';
    }
    
    // Archives
    if (['zip', 'rar', '7z', 'tar', 'gz', 'bz2'].includes(extension)) {
        return 'fas fa-file-archive text-secondary';
    }
    
    return 'fas fa-file text-muted';
}

function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function removeFileFromPreview(button, index) {
    const previewItem = button.closest('.file-preview-item');
    const container = button.closest('.file-drop-zone');
    const input = container.querySelector('input[type="file"]');
    
    if (input && input.files) {
        const dt = new DataTransfer();
        
        // Add all files except the one to remove
        for (let i = 0; i < input.files.length; i++) {
            if (i !== index) {
                dt.items.add(input.files[i]);
            }
        }
        
        input.files = dt.files;
        previewItem.remove();
        
        // Update preview
        updateFilePreview(input);
    }
}

function initializeFilePreviews() {
    // Add change listeners to all file inputs
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            updateFilePreview(this);
        });
    });
}

function initializeImageGallery() {
    // Add click listeners to images for preview modal
    const images = document.querySelectorAll('.task-image-preview');
    
    images.forEach(img => {
        img.addEventListener('click', function() {
            showImagePreview(this);
        });
    });
}

function showImagePreview(imgElement) {
    const modal = document.getElementById('imagePreviewModal');
    if (!modal) return;
    
    const modalImg = modal.querySelector('#imagePreviewImg');
    const modalTitle = modal.querySelector('#imagePreviewTitle');
    const modalInfo = modal.querySelector('#imagePreviewInfo');
    const modalDownload = modal.querySelector('#imagePreviewDownload');
    
    if (modalImg && modalTitle && modalInfo && modalDownload) {
        modalImg.src = imgElement.src;
        modalTitle.textContent = imgElement.alt || 'Vista Previa de Imagen';
        modalDownload.href = imgElement.src;
        
        // Add image info if available
        const info = imgElement.dataset;
        let infoHtml = '';
        
        if (info.dimensions) {
            infoHtml += `<span class="badge bg-info me-2">${info.dimensions}</span>`;
        }
        if (info.size) {
            infoHtml += `<span class="badge bg-secondary me-2">${info.size}</span>`;
        }
        if (info.location) {
            infoHtml += `<span class="badge bg-success me-2"><i class="fas fa-map-marker-alt"></i> ${info.location}</span>`;
        }
        
        modalInfo.innerHTML = infoHtml;
        
        // Show modal
        const bsModal = new bootstrap.Modal(modal);
        bsModal.show();
    }
}

// Progress bar for file uploads
function showUploadProgress(formId) {
    const form = document.getElementById(formId);
    if (!form) return;
    
    const progressContainer = document.createElement('div');
    progressContainer.className = 'upload-progress mt-3';
    progressContainer.innerHTML = `
        <div class="progress">
            <div class="progress-bar progress-bar-striped progress-bar-animated" 
                 role="progressbar" style="width: 0%">
                <span class="progress-text">Subiendo...</span>
            </div>
        </div>
    `;
    
    form.appendChild(progressContainer);
    
    return progressContainer;
}

function updateUploadProgress(progressContainer, percentage) {
    if (!progressContainer) return;
    
    const progressBar = progressContainer.querySelector('.progress-bar');
    const progressText = progressContainer.querySelector('.progress-text');
    
    if (progressBar && progressText) {
        progressBar.style.width = percentage + '%';
        progressText.textContent = `Subiendo... ${percentage}%`;
        
        if (percentage >= 100) {
            progressText.textContent = 'Procesando...';
            progressBar.classList.remove('progress-bar-animated');
        }
    }
}

// Enhanced file validation
function validateFiles(files, options = {}) {
    const {
        maxSize = 50 * 1024 * 1024, // 50MB default
        maxCount = 10,
        allowedTypes = [],
        allowedExtensions = []
    } = options;
    
    const errors = [];
    
    if (files.length > maxCount) {
        errors.push(`No puedes subir más de ${maxCount} archivos a la vez.`);
    }
    
    for (let i = 0; i < files.length; i++) {
        const file = files[i];
        
        // Check file size
        if (file.size > maxSize) {
            errors.push(`El archivo "${file.name}" excede el límite de ${formatFileSize(maxSize)}.`);
        }
        
        // Check file type
        if (allowedTypes.length > 0 && !allowedTypes.includes(file.type)) {
            errors.push(`El archivo "${file.name}" tiene un tipo no permitido.`);
        }
        
        // Check file extension
        if (allowedExtensions.length > 0) {
            const extension = file.name.split('.').pop().toLowerCase();
            if (!allowedExtensions.includes(extension)) {
                errors.push(`El archivo "${file.name}" tiene una extensión no permitida.`);
            }
        }
    }
    
    return {
        isValid: errors.length === 0,
        errors: errors
    };
}

// CSS Styles for drag and drop
const style = document.createElement('style');
style.textContent = `
.file-drop-zone {
    transition: all 0.3s ease;
    cursor: pointer;
}

.file-drop-zone.drag-over {
    border-color: #007bff !important;
    background-color: rgba(0, 123, 255, 0.1);
}

.file-drop-zone:hover {
    border-color: #007bff;
    background-color: rgba(0, 123, 255, 0.05);
}

.file-preview-item {
    transition: all 0.2s ease;
}

.file-preview-item:hover {
    background-color: rgba(0, 0, 0, 0.05);
}

.task-image-preview {
    cursor: pointer;
    transition: transform 0.2s ease;
}

.task-image-preview:hover {
    transform: scale(1.05);
}

.upload-progress .progress {
    height: 20px;
}

.upload-progress .progress-text {
    position: absolute;
    width: 100%;
    text-align: center;
    line-height: 20px;
    color: white;
    font-size: 12px;
    font-weight: bold;
}
`;

document.head.appendChild(style);