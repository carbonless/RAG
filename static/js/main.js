let currentRagId = null;
let rags = [];

// Initialize the application
document.addEventListener('DOMContentLoaded', () => {
    loadRags();
});

// Load all RAGs from the server
async function loadRags() {
    try {
        const response = await fetch('/api/rags');
        rags = await response.json();
        updateTabs();
    } catch (error) {
        console.error('Error loading RAGs:', error);
        showError('Failed to load RAGs');
    }
}

// Update the tabs in the UI
function updateTabs() {
    const tabList = document.getElementById('ragTabs');
    const tabContent = document.getElementById('ragTabContent');
    
    tabList.innerHTML = '';
    tabContent.innerHTML = '';
    
    rags.forEach((rag, index) => {
        // Create tab
        const tab = document.createElement('li');
        tab.className = 'nav-item';
        tab.innerHTML = `
            <a class="nav-link ${index === 0 ? 'active' : ''}" 
               id="rag-${rag.id}-tab" 
               data-bs-toggle="tab" 
               href="#rag-${rag.id}" 
               role="tab">
                ${rag.name}
            </a>
        `;
        tabList.appendChild(tab);
        
        // Create tab content
        const content = document.createElement('div');
        content.className = `tab-pane fade ${index === 0 ? 'show active' : ''}`;
        content.id = `rag-${rag.id}`;
        content.innerHTML = createRagContent(rag);
        tabContent.appendChild(content);
    });
}

// Create the content for a RAG tab
function createRagContent(rag) {
    return `
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-4">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">Documents</h5>
                        </div>
                        <div class="card-body">
                            <button class="btn btn-primary mb-3" onclick="showUploadModal('${rag.id}')">
                                <i class="bi bi-upload"></i> Upload Documents
                            </button>
                            <div class="document-list" id="documents-${rag.id}">
                                ${rag.documents.map(doc => `
                                    <div class="document-item">
                                        <span>${doc.name}</span>
                                        <button class="btn btn-sm btn-danger" onclick="deleteDocument('${rag.id}', '${doc.id}')">
                                            <i class="bi bi-trash"></i>
                                        </button>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </div>
                </div>
                <div class="col-md-8">
                    <div class="card">
                        <div class="card-header">
                            <h5 class="card-title mb-0">Chat</h5>
                        </div>
                        <div class="card-body">
                            <div class="chat-container" id="chat-${rag.id}">
                                ${rag.messages.map(msg => `
                                    <div class="chat-message ${msg.role === 'user' ? 'user-message' : 'assistant-message'}">
                                        ${msg.content}
                                    </div>
                                `).join('')}
                            </div>
                            <form onsubmit="sendMessage(event, '${rag.id}')">
                                <div class="input-group">
                                    <input type="text" class="form-control" id="message-${rag.id}" placeholder="Type your message...">
                                    <button class="btn btn-primary" type="submit">Send</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    `;
}

// Create a new RAG
async function createNewRag() {
    const form = document.getElementById('newRagForm');
    const formData = new FormData(form);
    
    try {
        const response = await fetch('/api/rags', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                name: formData.get('ragName'),
                model: formData.get('model')
            })
        });
        
        if (response.ok) {
            const newRag = await response.json();
            rags.push(newRag);
            updateTabs();
            bootstrap.Modal.getInstance(document.getElementById('newRagModal')).hide();
            form.reset();
        } else {
            throw new Error('Failed to create RAG');
        }
    } catch (error) {
        console.error('Error creating RAG:', error);
        showError('Failed to create RAG');
    }
}

// Show the upload modal
function showUploadModal(ragId) {
    currentRagId = ragId;
    const modal = new bootstrap.Modal(document.getElementById('uploadModal'));
    modal.show();
}

// Upload documents to a RAG
async function uploadDocuments() {
    const form = document.getElementById('uploadForm');
    const formData = new FormData(form);
    const files = formData.getAll('files');
    
    try {
        const response = await fetch(`/api/rags/${currentRagId}/documents`, {
            method: 'POST',
            body: formData
        });
        
        if (response.ok) {
            const updatedRag = await response.json();
            const ragIndex = rags.findIndex(r => r.id === currentRagId);
            rags[ragIndex] = updatedRag;
            updateTabs();
            bootstrap.Modal.getInstance(document.getElementById('uploadModal')).hide();
            form.reset();
        } else {
            throw new Error('Failed to upload documents');
        }
    } catch (error) {
        console.error('Error uploading documents:', error);
        showError('Failed to upload documents');
    }
}

// Delete a document from a RAG
async function deleteDocument(ragId, docId) {
    try {
        const response = await fetch(`/api/rags/${ragId}/documents/${docId}`, {
            method: 'DELETE'
        });
        
        if (response.ok) {
            const updatedRag = await response.json();
            const ragIndex = rags.findIndex(r => r.id === ragId);
            rags[ragIndex] = updatedRag;
            updateTabs();
        } else {
            throw new Error('Failed to delete document');
        }
    } catch (error) {
        console.error('Error deleting document:', error);
        showError('Failed to delete document');
    }
}

// Send a message to the RAG
async function sendMessage(event, ragId) {
    event.preventDefault();
    const input = document.getElementById(`message-${ragId}`);
    const message = input.value.trim();
    
    if (!message) return;
    
    // Add user message to chat
    const chatContainer = document.getElementById(`chat-${ragId}`);
    chatContainer.innerHTML += `
        <div class="chat-message user-message">
            ${message}
        </div>
    `;
    chatContainer.scrollTop = chatContainer.scrollHeight;
    input.value = '';
    
    try {
        console.log(`Sending message to RAG: ${ragId}`);  // Debug log
        const response = await fetch(`/api/rags/${ragId}/chat`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message })
        });
        
        if (response.ok) {
            const result = await response.json();
            chatContainer.innerHTML += `
                <div class="chat-message assistant-message">
                    ${result.response}
                </div>
            `;
            chatContainer.scrollTop = chatContainer.scrollHeight;
        } else {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Failed to get response');
        }
    } catch (error) {
        console.error('Error sending message:', error);
        showError(error.message || 'Failed to get response');
    }
}

// Show error message
function showError(message) {
    // You can implement this based on your preferred UI feedback method
    alert(message);
} 