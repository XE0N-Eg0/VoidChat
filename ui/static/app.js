let currentPeerId = null;
let currentPeerIp = null;

// --- Tab Switching ---
function switchTab(tabName) {
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));
    document.querySelector(`.tab-btn[data-tab="${tabName}"]`).classList.add('active');
    document.getElementById(tabName).classList.add('active');
}

// --- Utilities ---
function getAvatarColor(username) {
    const colors = ['#FFB5E8', '#FF9AA2', '#FFB7B2', '#FFDAC1', '#E2F0CB', '#B5EAD7', '#C7CEEA', '#97D2FB'];
    let hash = 0;
    for (let i = 0; i < username.length; i++) {
        hash = username.charCodeAt(i) + ((hash << 5) - hash);
    }
    return colors[Math.abs(hash) % colors.length];
}

function showNotification(message, isError = false) {
    const notif = document.createElement('div');
    notif.style.position = 'fixed';
    notif.style.bottom = '20px';
    notif.style.right = '20px';
    notif.style.padding = '12px 20px';
    notif.style.borderRadius = '8px';
    notif.style.zIndex = '2000';
    notif.style.fontSize = '14px';
    notif.style.boxShadow = '0 4px 12px rgba(0,0,0,0.15)';
    
    if(isError) {
        notif.style.background = '#fef0f0';
        notif.style.color = '#f56c6c';
        notif.style.border = '1px solid #fbc4c4';
    } else {
        notif.style.background = '#fdf6ec';
        notif.style.color = '#e6a23c';
        notif.style.border = '1px solid #f5dab1';
    }
    
    notif.innerText = message;
    document.body.appendChild(notif);
    
    setTimeout(() => {
        notif.style.opacity = '0';
        notif.style.transition = 'opacity 0.5s';
        setTimeout(() => notif.remove(), 500);
    }, 3000);
}

// --- API Calls ---
async function fetchPeers() {
    const res = await fetch('/api/peers');
    const peers = await res.json();
    
    const discoveryList = document.getElementById('discoveryList');
    const contactsList = document.getElementById('contactsList');
    discoveryList.innerHTML = '';
    contactsList.innerHTML = '';

    if(peers.length === 0) {
        discoveryList.innerHTML = '<div class="placeholder-text">No peers discovered yet.</div>';
    }

    peers.forEach(p => {
        // Discovery Row
        const card = document.createElement('div');
        card.className = 'peer-card';
        const statusClass = p.status === 'Online' ? 'status-online' : p.status === 'Discovered' ? 'status-discovered' : 'status-offline';
        
        let actionBtn = '';
        if(!p.is_friend) {
            actionBtn = `<button class="btn" onclick="sendConnReq('${p.ip}', '${p.peer_id}')">Connect</button>`;
        }

        card.innerHTML = `
            <div class="peer-avatar" style="background:${getAvatarColor(p.username)}"></div>
            <div class="peer-info">
                <div class="peer-name">${p.username}</div>
                <div class="peer-ip">${p.ip}</div>
            </div>
            <div class="peer-status ${statusClass}">${p.status}</div>
            ${actionBtn}
        `;
        discoveryList.appendChild(card);

        // Chat Sidebar (only friends)
        if(p.is_friend) {
            const contact = document.createElement('div');
            contact.className = `contact-card ${p.peer_id === currentPeerId ? 'selected' : ''}`;
            contact.onclick = () => selectContact(p);
            contact.innerHTML = `
                <div class="peer-avatar" style="background:${getAvatarColor(p.username)}"></div>
                <div class="peer-name">${p.username}</div>
            `;
            contactsList.appendChild(contact);
        }
    });
}

async function selectContact(peer) {
    currentPeerId = peer.peer_id;
    currentPeerIp = peer.ip;
    
    document.getElementById('chatHeader').innerText = peer.username;
    document.getElementById('chatInputArea').style.display = 'flex';
    
    const historyDiv = document.getElementById('chatHistory');
    historyDiv.innerHTML = '';

    const res = await fetch(`/api/history/${peer.peer_id}`);
    const history = await res.json();
    
    history.forEach(msg => {
        renderBubble(msg, msg.sender_name === localUsername);
    });
    historyDiv.scrollTop = historyDiv.scrollHeight;
    fetchPeers(); 
}

function renderBubble(msg, isSent) {
    const historyDiv = document.getElementById('chatHistory');
    const row = document.createElement('div');
    row.className = `msg-row ${isSent ? 'outgoing' : 'incoming'}`;
    
    const text = msg.payload || "";
    const msgType = msg.message_type || "text";
    const time = msg.timestamp ? new Date(msg.timestamp).toLocaleTimeString([], {hour: '2-digit', minute: '2-digit'}) : '';
    
    let contentHTML = text;
    if (msgType === 'file') {
        const fileUrl = `/downloads/${encodeURIComponent(text)}`;
        contentHTML = `<a href="${fileUrl}" target="_blank" class="file-link">📎 ${text}</a>`;
    }

    row.innerHTML = `
        <div class="chat-bubble">${contentHTML}</div>
        <div class="msg-time">${time}</div>
    `;
    historyDiv.appendChild(row);
}

async function sendMessage() {
    const input = document.getElementById('messageInput');
    const text = input.value.trim();
    if(!text || !currentPeerId) return;
    
    input.value = '';
    renderBubble({payload: text, timestamp: new Date().toISOString(), message_type: 'text'}, true);
    
    const historyDiv = document.getElementById('chatHistory');
    historyDiv.scrollTop = historyDiv.scrollHeight;

    await fetch('/api/send', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ip: currentPeerIp, peer_id: currentPeerId, text: text})
    });
}

async function sendConnReq(ip, pid) {
    try {
        const res = await fetch('/api/connect', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ip: ip, peer_id: pid})
        });
        const data = await res.json();
        if(data.success) {
            showNotification("Connection request sent. Waiting for peer...");
        } else {
            showNotification("Failed to connect: " + (data.error || 'Peer unreachable'), true);
        }
    } catch(err) {
        showNotification('Network error while trying to connect.', true);
    }
}

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    if(!fileInput.files.length) return;
    
    const file = fileInput.files[0];
    const formData = new FormData();
    formData.append('file', file);

    if(!confirm(`Send file "${file.name}" (${(file.size/1024).toFixed(2)} KB)?`)) {
        fileInput.value = '';
        return;
    }

    try {
        const res = await fetch(`/api/upload?ip=${currentPeerIp}&peer_id=${currentPeerId}`, {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if(!data.success) {
            showNotification('File send failed: ' + (data.error || 'Unknown error'), true);
        }
    } catch(err) {
        showNotification('Network error during file upload.', true);
    }
    fileInput.value = '';
}

// --- Real-time Event Stream (SSE) ---
const evtSource = new EventSource('/api/events');
evtSource.onmessage = function(e) {
    const event = JSON.parse(e.data);
    
    if(event.type === 'text_received') {
        if(event.data.peer_id === currentPeerId) {
            renderBubble(event.data.data, false);
            document.getElementById('chatHistory').scrollTop = 999999;
        }
    } 
    else if(event.type === 'file_received') {
        if(event.data.peer_id === currentPeerId) {
            renderBubble(event.data.data, false);
            document.getElementById('chatHistory').scrollTop = 999999;
        }
    }
    else if(event.type === 'file_sent') {
        if(event.data.peer_id === currentPeerId) {
            renderBubble(event.data.data, true);
            document.getElementById('chatHistory').scrollTop = 999999;
        }
    }
    else if(event.type === 'conn_req' || event.type === 'file_req') {
        showModal(event.type, event.data);
    }
    else if(event.type === 'conn_error') {
        showNotification("Connection failed: " + event.data.error, true);
    }
};

// --- Modals ---
function showModal(type, data) {
    const overlay = document.getElementById('modalOverlay');
    const card = document.getElementById('modalCard');
    
    if(type === 'conn_req') {
        card.innerHTML = `
            <h3>Connection Request</h3>
            <p>${data.username} wants to connect.</p>
            <div class="modal-actions">
                <button class="btn" onclick="closeModal()">Decline</button>
                <button class="btn btn-primary" onclick="acceptConn('${data.peer_id}', '${data.username}', '${data.ip}')">Accept</button>
            </div>
        `;
    } else if(type === 'file_req') {
        card.innerHTML = `
            <h3>Incoming File</h3>
            <p>${data.username} wants to send ${data.filename} (${data.size} bytes).</p>
            <div class="modal-actions">
                <button class="btn" onclick="closeModal()">Decline</button>
                <button class="btn btn-primary" onclick="acceptFile('${data.ip}', '${data.session_id}')">Accept</button>
            </div>
        `;
    }
    overlay.style.display = 'flex';
}

function closeModal() {
    document.getElementById('modalOverlay').style.display = 'none';
}

async function acceptConn(pid, uname, ip) {
    await fetch('/api/accept_connection', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({peer_id: pid, username: uname, ip: ip})
    });
    closeModal();
    fetchPeers();
}

async function acceptFile(ip, sid) {
    await fetch('/api/accept_file', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ip: ip, session_id: sid})
    });
    closeModal();
}

// --- Init ---
setInterval(fetchPeers, 3000); // Poll every 3 seconds for snappy UI
fetchPeers();