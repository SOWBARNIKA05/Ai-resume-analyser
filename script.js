// Tab Navigation
function showTab(tabId) {
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
    document.querySelectorAll('nav button').forEach(b => b.classList.remove('active-tab'));
    
    document.getElementById(`content-${tabId}`).classList.add('active');
    document.getElementById(`tab-${tabId}`).classList.add('active-tab');

    if (tabId === 'dashboard') loadDashboard();
}

// File Input Display
document.getElementById('fileInput').addEventListener('change', (e) => {
    const fileName = e.target.files[0]?.name || "";
    document.getElementById('fileNameDisplay').innerText = fileName;
});

// Form Submission
document.getElementById('analyzeForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const btn = document.getElementById('analyzeBtn');
    const loader = document.getElementById('loader');
    const name = document.getElementById('candName').value;
    const file = document.getElementById('fileInput').files[0];
    const text = document.getElementById('resumeText').value;

    const formData = new FormData();
    formData.append('name', name);
    if (file) formData.append('file', file);
    if (text) formData.append('resume_text', text);

    btn.disabled = true;
    loader.classList.remove('hidden');

    try {
        const res = await fetch('/analyze', { method: 'POST', body: formData });
        const data = await res.json();

        if (data.error) {
            alert(data.error);
        } else {
            alert(`Analysis complete for ${data.name}!`);
            showTab('dashboard');
            loadDashboard();
        }
    } catch (err) {
        alert("Upload error: " + err.message);
    } finally {
        btn.disabled = false;
        loader.classList.add('hidden');
    }
});

// Load Dashboard
async function loadDashboard() {
    const list = document.getElementById('candidatesList');
    const count = document.getElementById('candidateCount');
    
    try {
        const res = await fetch('/dashboard');
        const data = await res.json();
        
        count.innerText = `${data.length} / 3`;
        
        if (data.length === 0) {
            list.innerHTML = `<div class="col-span-full text-center py-20 text-slate-400"><i class="fas fa-folder-open text-5xl mb-4"></i><p>No candidates analyzed yet.</p></div>`;
            return;
        }

        list.innerHTML = data.map(c => `
            <div class="bg-white p-6 rounded-2xl shadow-md border border-slate-100 hover:shadow-lg transition">
                <div class="flex justify-between items-start mb-4">
                    <div>
                        <h3 class="font-bold text-xl">${c.name}</h3>
                        <p class="text-xs text-blue-600 font-bold uppercase tracking-wider">${c.top_job}</p>
                    </div>
                    <span class="bg-green-100 text-green-700 font-bold px-2 py-1 rounded text-lg">
                        ${c.score}%
                    </span>
                </div>
                
                <div class="space-y-3">
                    <div>
                        <p class="text-[10px] font-bold text-slate-400 uppercase">Top Skills</p>
                        <div class="flex flex-wrap gap-1 mt-1">
                            ${c.skills.slice(0, 5).map(s => `<span class="bg-slate-100 px-2 py-0.5 rounded text-[10px] font-medium">${s}</span>`).join('')}
                        </div>
                    </div>
                    
                    <div>
                        <p class="text-[10px] font-bold text-slate-400 uppercase">Summary</p>
                        <p class="text-xs text-slate-600 line-clamp-3 mt-1 leading-relaxed">${c.summary}</p>
                    </div>
                </div>
            </div>
        `).join('');

    } catch (err) {
        console.error(err);
    }
}

// Chat logic
async function sendChat() {
    const input = document.getElementById('chatInput');
    const container = document.getElementById('chatMessages');
    const msg = input.value.trim();
    if (!msg) return;

    // Append User message
    container.innerHTML += `
        <div class="flex items-start gap-3 justify-end">
            <div class="bg-blue-600 text-white p-3 rounded-2xl rounded-tr-none text-sm max-w-[80%]">${msg}</div>
            <div class="bg-blue-600 text-white p-2 rounded-lg"><i class="fas fa-user text-xs"></i></div>
        </div>
    `;
    input.value = '';
    container.scrollTop = container.scrollHeight;

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: msg })
        });
        const data = await res.json();

        // Append AI message
        container.innerHTML += `
            <div class="flex items-start gap-3">
                <div class="bg-blue-100 text-blue-600 p-2 rounded-lg"><i class="fas fa-robot"></i></div>
                <div class="bg-slate-100 p-3 rounded-2xl rounded-tl-none text-sm max-w-[80%]">${data.answer}</div>
            </div>
        `;
        container.scrollTop = container.scrollHeight;
    } catch (err) {
        alert("Chat error: " + err.message);
    }
}

// Clear Data
async function clearData() {
    if (!confirm("Delete all candidate data?")) return;
    await fetch('/clear', { method: 'POST' });
    loadDashboard();
    alert("Data reset.");
}

// Init
window.onload = () => {
    loadDashboard();
};