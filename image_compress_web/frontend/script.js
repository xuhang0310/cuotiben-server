// 定义全局变量
let currentFolderPath = '';
let currentFiles = [];
let selectedFiles = [];
let isSortedBySize = false;
let isFilterEnabled = false;

// DOM元素引用
let folderPathInput;
let browseFolderBtn;
let refreshBtn;
let targetSizeInput;
let qualityInput;
let formatSelect;
let fileListDiv;
let compressBtn;
let cancelBtn;
let progressContainer;
let progressBar;
let statusMessage;
let progressDetails;
let resultMessage;
let resultText;
let selectAllBtn;
let deselectAllBtn;
let invertSelectionBtn;
let selectedCountSpan;
let filterToggle;
let sortBySizeBtn;

// 函数定义
function initializeElements() {
    folderPathInput = document.getElementById('folderPath');
    browseFolderBtn = document.getElementById('browseFolderBtn');
    refreshBtn = document.getElementById('refreshBtn');
    targetSizeInput = document.getElementById('targetSize');
    qualityInput = document.getElementById('quality');
    formatSelect = document.getElementById('format');
    fileListDiv = document.getElementById('fileList');
    compressBtn = document.getElementById('compressBtn');
    cancelBtn = document.getElementById('cancelBtn');
    progressContainer = document.getElementById('progressContainer');
    progressBar = document.getElementById('progressBar');
    statusMessage = document.getElementById('statusMessage');
    progressDetails = document.getElementById('progressDetails');
    resultMessage = document.getElementById('resultMessage');
    resultText = document.getElementById('resultText');
    selectAllBtn = document.getElementById('selectAllBtn');
    deselectAllBtn = document.getElementById('deselectAllBtn');
    invertSelectionBtn = document.getElementById('invertSelectionBtn');
    selectedCountSpan = document.getElementById('selectedCount');
    filterToggle = document.getElementById('filterToggle');
    sortBySizeBtn = document.getElementById('sortBySizeBtn');
}

function attachEventListeners() {
    // 文件夹选择按钮事件
    browseFolderBtn.addEventListener('click', handleBrowseFolder);
    
    // 刷新按钮事件
    refreshBtn.addEventListener('click', loadFolderContents);
    
    // 全选择按钮事件
    selectAllBtn.addEventListener('click', handleSelectAll);
    
    // 全解除按钮事件
    deselectAllBtn.addEventListener('click', handleDeselectAll);
    
    // 反选按钮事件
    invertSelectionBtn.addEventListener('click', handleInvertSelection);
    
    // 过滤切换事件
    filterToggle.addEventListener('change', handleFilterToggle);
    
    // 大小顺序按钮事件
    sortBySizeBtn.addEventListener('click', handleSortBySize);
    
    // 压缩开始按钮事件
    compressBtn.addEventListener('click', handleCompress);
    
    // 取消按钮事件
    cancelBtn.addEventListener('click', handleCancel);
}

async function handleBrowseFolder() {
    // 由于浏览器限制，模拟文件路径输入
    const folderPath = prompt('请输入图片文件夹的路径:', 'C:\\Users\\Administrator\\Downloads\\');
    if (folderPath) {
        currentFolderPath = folderPath;
        folderPathInput.value = folderPath;
        await loadFolderContents();
    }
}

async function loadFolderContents() {
    if (!currentFolderPath) {
        alert('请先选择一个文件夹');
        return;
    }

    try {
        const response = await fetch('/api/folder/scan', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                directory: currentFolderPath,
                target_size: parseInt(targetSizeInput.value),
                quality: parseInt(qualityInput.value),
                format: formatSelect.value
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        currentFiles = data.files;
        displayFileList(currentFiles);
    } catch (error) {
        console.error('文件夹内容加载错误:', error);
        fileListDiv.innerHTML = `<p class="text-danger text-center py-4">加载失败: ${error.message}</p>`;
    }
}

function displayFileList(files) {
    if (files.length === 0) {
        fileListDiv.innerHTML = '<p class="text-muted text-center py-4">文件夹中没有找到图片文件</p>';
        selectedFiles = [];
        updateSelectedCount();
        return;
    }

    // 根据需要对文件进行排序
    let sortedFiles = [...files];
    if (isSortedBySize) {
        // 按大小降序排列（大的在前）
        sortedFiles.sort((a, b) => b.size_kb - a.size_kb);
    }

    // 根据需要过滤文件
    let filteredFiles = sortedFiles;
    if (isFilterEnabled) {
        // 只显示大于目标大小的文件
        const targetSize = parseInt(targetSizeInput.value) || 128;
        filteredFiles = sortedFiles.filter(file => file.size_kb > targetSize);
    }

    if (filteredFiles.length === 0 && isFilterEnabled) {
        fileListDiv.innerHTML = '<div class="text-center py-4"><p class="text-muted">没有大于目标大小的文件</p></div>';
        selectedFiles = [];
        updateSelectedCount();
        return;
    }

    let html = '<div class="file-grid">';
    filteredFiles.forEach((file, index) => {
        const isChecked = selectedFiles.includes(file.path) ? 'checked' : '';
        // 创建图片预览URL（使用后端API）
        const previewUrl = `/api/preview?file=${encodeURIComponent(file.path)}&t=${new Date().getTime()}`;
        html += `
            <div class="file-card ${isChecked ? 'selected' : ''}">
                <div class="card-img-container">
                    <input type="checkbox" class="file-checkbox" data-file-path="${file.path}" ${isChecked}>
                    <img src="${previewUrl}" class="card-img-top img-preview" alt="${file.name}" onerror="this.onerror=null;this.src='data:image/svg+xml;utf8,<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"100\" height=\"100\" viewBox=\"0 0 24 24\"><rect width=\"24\" height=\"24\" fill=\"#f0f0f0\"/><path d=\"M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-8.5 11.5L7 11l-1.5 1.5L3 9l5.5 5.5L11 12l5 5-7.5-7.5z\" fill=\"#999\"/></svg>';">
                </div>
                <div class="card-body">
                    <h6 class="card-title" title="${file.name}">${file.name}</h6>
                    <p class="card-text"><small class="text-muted">${file.size_kb}KB</small></p>
                </div>
            </div>
        `;
    });
    html += '</div>';

    fileListDiv.innerHTML = html;
    
    // 为新添加的复选框绑定事件监听器
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        checkbox.addEventListener('change', handleFileSelection);
    });
    
    // 更新选择计数
    selectedFiles = filteredFiles.filter(file => selectedFiles.includes(file.path)).map(file => file.path);
    updateSelectedCount();
}

function handleFileSelection(e) {
    const filePath = e.target.dataset.filePath;
    
    if (e.target.checked) {
        if (!selectedFiles.includes(filePath)) {
            selectedFiles.push(filePath);
        }
    } else {
        selectedFiles = selectedFiles.filter(path => path !== filePath);
    }
    
    // 更新卡片的选择状态
    const card = e.target.closest('.file-card');
    if (card) {
        card.classList.toggle('selected', e.target.checked);
    }
    
    updateSelectedCount();
}

function updateSelectedCount() {
    selectedCountSpan.textContent = `已选择: ${selectedFiles.length} 张`;
}

function handleSelectAll() {
    if (currentFiles.length === 0) return;
    
    // 获取全文件路径
    const allFilePaths = currentFiles.map(file => file.path);
    
    // 如果过滤器有效，则只选择过滤后的文件
    if (isFilterEnabled) {
        const targetSize = parseInt(targetSizeInput.value) || 128;
        selectedFiles = currentFiles
            .filter(file => file.size_kb > targetSize)
            .map(file => file.path);
    } else {
        selectedFiles = allFilePaths;
    }
    
    // 更新UI
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        const filePath = checkbox.dataset.filePath;
        checkbox.checked = selectedFiles.includes(filePath);
        
        // 同时更新卡片的选择状态
        const card = checkbox.closest('.file-card');
        if (card) {
            card.classList.toggle('selected', selectedFiles.includes(filePath));
        }
    });
    
    updateSelectedCount();
}

function handleDeselectAll() {
    // 清空选择
    selectedFiles = [];
    
    // 更新UI
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        checkbox.checked = false;
        
        // 同时更新卡片的选择状态
        const card = checkbox.closest('.file-card');
        if (card) {
            card.classList.remove('selected');
        }
    });
    
    updateSelectedCount();
}

function handleInvertSelection() {
    if (currentFiles.length === 0) return;
    
    // 获取全文件路径
    const allFilePaths = currentFiles.map(file => file.path);
    
    // 如果过滤器有效，则只针对过滤后的文件
    let targetFilePaths = allFilePaths;
    if (isFilterEnabled) {
        const targetSize = parseInt(targetSizeInput.value) || 128;
        targetFilePaths = currentFiles
            .filter(file => file.size_kb > targetSize)
            .map(file => file.path);
    }
    
    // 计算反选结果
    selectedFiles = targetFilePaths.filter(path => !selectedFiles.includes(path));
    
    // 更新UI
    document.querySelectorAll('.file-checkbox').forEach(checkbox => {
        const filePath = checkbox.dataset.filePath;
        const shouldCheck = selectedFiles.includes(filePath);
        checkbox.checked = shouldCheck;
        
        // 同时更新卡片的选择状态
        const card = checkbox.closest('.file-card');
        if (card) {
            card.classList.toggle('selected', shouldCheck);
        }
    });
    
    updateSelectedCount();
}

function handleFilterToggle() {
    isFilterEnabled = this.checked;
    // 重新显示文件列表以应用过滤
    displayFileList(currentFiles);
}

function handleSortBySize() {
    isSortedBySize = !isSortedBySize;
    // 更新按钮文本
    this.textContent = isSortedBySize ? '取消排序' : '按大小排序';
    
    // 重新显示文件列表以应用排序
    displayFileList(currentFiles);
}

async function handleCompress() {
    if (!currentFolderPath) {
        alert('请先选择一个文件夹');
        return;
    }

    // 检查是否选择了文件
    let filesToProcess = selectedFiles;
    
    if (filesToProcess.length === 0) {
        if (isFilterEnabled) {
            const targetSize = parseInt(targetSizeInput.value) || 128;
            const allFiles = currentFiles.filter(file => file.size_kb > targetSize);
            
            if (allFiles.length > 0) {
                const shouldProcessAll = confirm(`${allFiles.length}个文件大于目标大小，是否处理全文件？`);
                if (shouldProcessAll) {
                    filesToProcess = allFiles.map(file => file.path);
                } else {
                    alert('请至少选择一张图片');
                    return;
                }
            } else {
                alert('没有大于目标大小的文件');
                return;
            }
        } else {
            alert('请至少选择一张图片');
            return;
        }
    }

    try {
        // 显示进度条
        progressContainer.style.display = 'block';
        resultMessage.style.display = 'none';

        // 开始压缩任务，传递选中的文件列表
        const response = await fetch('/api/compress', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                directory: currentFolderPath,
                target_size: parseInt(targetSizeInput.value),
                quality: parseInt(qualityInput.value),
                format: formatSelect.value,
                selected_files: filesToProcess  // 传递选中的文件列表
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        const taskId = data.task_id;

        // 查询任务状态
        await pollTaskStatus(taskId);
    } catch (error) {
        console.error('压缩开始错误:', error);
        alert('压缩开始失败: ' + error.message);
        progressContainer.style.display = 'none';
    }
}

async function pollTaskStatus(taskId) {
    let completed = false;

    while (!completed) {
        try {
            const response = await fetch(`/api/task/${taskId}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const status = await response.json();

            // 更新进度
            progressBar.style.width = status.progress + '%';
            statusMessage.textContent = status.message;
            progressDetails.textContent = `进度: ${Math.round(status.progress)}% (${status.processed_files}/${status.total_files} 文件)`;

            // 检查任务是否完成
            if (status.status === 'completed' || status.status === 'failed') {
                completed = true;
                
                // 隐藏进度条并显示结果
                progressContainer.style.display = 'none';
                
                if (status.status === 'completed') {
                    resultText.textContent = status.message;
                    resultMessage.className = 'alert alert-success';
                } else {
                    resultText.textContent = status.message;
                    resultMessage.className = 'alert alert-danger';
                }
                
                resultMessage.style.display = 'block';
            }
        } catch (error) {
            console.error('获取任务状态错误:', error);
            statusMessage.textContent = '状态获取失败: ' + error.message;
            completed = true;
        }

        // 等待下次查询
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

function handleCancel() {
    // 重置表单
    folderPathInput.value = '';
    targetSizeInput.value = '128';
    qualityInput.value = '85';
    formatSelect.value = '保持原格式';
    fileListDiv.innerHTML = '<p class="text-muted text-center py-4">请选择一个文件夹以查看内容</p>';
    currentFolderPath = '';
    currentFiles = [];
    selectedFiles = [];
    updateSelectedCount();
    
    // 隐藏进度和结果
    progressContainer.style.display = 'none';
    resultMessage.style.display = 'none';
}

async function loadDefaultSettings() {
    try {
        const response = await fetch('/api/settings');
        if (response.ok) {
            const settings = await response.json();
            targetSizeInput.value = settings.default_target_size;
            qualityInput.value = settings.default_quality;
        }
    } catch (error) {
        console.error('加载默认设置错误:', error);
    }
    
    // 获取系统默认下载路径
    try {
        const response = await fetch('/api/default-path');
        if (response.ok) {
            const data = await response.json();
            if (!folderPathInput.value || folderPathInput.value === '') {
                folderPathInput.value = data.default_path;
                currentFolderPath = data.default_path;
            }
        }
    } catch (error) {
        console.error('获取默认路径错误:', error);
        // 错误时使用硬编码的默认路径
        if (!folderPathInput.value || folderPathInput.value === '') {
            folderPathInput.value = 'C:\\Users\\Administrator\\Downloads\\';
            currentFolderPath = 'C:\\Users\\Administrator\\Downloads\\';
        }
    }
}

// 应用初始化
document.addEventListener('DOMContentLoaded', function() {
    initializeElements();
    attachEventListeners();
    loadDefaultSettings();
});