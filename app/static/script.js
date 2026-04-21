document.addEventListener("DOMContentLoaded", () => {
    const dropZone = document.getElementById("drop-zone");
    const pdfInput = document.getElementById("pdf-input");
    const browseBtn = document.getElementById("browse-btn");
    const uploadProgress = document.getElementById("upload-progress");
    const uploadStatusText = document.getElementById("upload-status-text");
    const documentList = document.getElementById("document-list");
    const vectorCountEl = document.getElementById("vector-count");
    const llmModelNameEl = document.getElementById("llm-model-name");
    const resetBtn = document.getElementById("reset-btn");
    const chatForm = document.getElementById("chat-form");
    const userInput = document.getElementById("user-input");
    const chatMessages = document.getElementById("chat-messages");
    const sendBtn = document.getElementById("send-btn");

    // Fetch initial system status
    fetchStatus();

    // Trigger file dialog
    browseBtn.addEventListener("click", () => pdfInput.click());
    dropZone.addEventListener("click", (e) => {
        if (e.target !== browseBtn && !browseBtn.contains(e.target)) {
            pdfInput.click();
        }
    });

    // Drag & Drop handlers
    ["dragenter", "dragover"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.add("dragover");
        });
    });

    ["dragleave", "drop"].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            dropZone.classList.remove("dragover");
        });
    });

    dropZone.addEventListener("drop", (e) => {
        const files = e.dataTransfer.files;
        if (files.length > 0 && files[0].name.endsWith(".pdf")) {
            handleFileUpload(files[0]);
        } else {
            alert("Please upload a valid PDF (.pdf) file.");
        }
    });

    pdfInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    // Handle File Upload API
    async function handleFileUpload(file) {
        const formData = new FormData();
        formData.append("file", file);

        uploadProgress.classList.remove("hidden");
        uploadStatusText.textContent = `Processing & indexing '${file.name}'...`;

        try {
            const response = await fetch("/api/upload", {
                method: "POST",
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                appendSystemMessage(`✅ Successfully indexed **${file.name}** (${data.details.total_pages} pages, ${data.details.chunks_created} vector chunks created).`);
                fetchStatus();
            } else {
                let errorMsg = "Unknown error";
                try {
                    const data = await response.json();
                    errorMsg = data.detail || errorMsg;
                } catch (e) {
                    try {
                        errorMsg = await response.text();
                    } catch (t_err) {}
                }
                alert(`Upload failed: ${errorMsg}`);
            }
        } catch (error) {
            alert(`Network error during upload: ${error.message}`);
        } finally {
            uploadProgress.classList.add("hidden");
            pdfInput.value = "";
        }
    }

    // Fetch Status API
    async function fetchStatus() {
        try {
            const response = await fetch("/api/status");
            if (response.ok) {
                const data = await response.json();
                vectorCountEl.textContent = data.indexed_chunks;
                llmModelNameEl.textContent = data.llm_model;

                // Update document list
                if (data.uploaded_files && data.uploaded_files.length > 0) {
                    documentList.innerHTML = data.uploaded_files
                        .map(file => `
                            <li class="document-item">
                                <i class="fa-solid fa-file-pdf" style="color: #06b6d4;"></i>
                                <span title="${file}">${file}</span>
                                <i class="fa-solid fa-check-circle" style="color: #10b981;"></i>
                            </li>
                        `).join("");
                } else {
                    documentList.innerHTML = `<li class="empty-docs">No PDFs uploaded yet.</li>`;
                }
            }
        } catch (err) {
            console.error("Failed to fetch system status", err);
        }
    }

    // Reset Database API
    resetBtn.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to clear all indexed vector documents and uploaded PDFs?")) return;

        try {
            const response = await fetch("/api/reset", { method: "POST" });
            if (response.ok) {
                const data = await response.json();
                appendSystemMessage("🧹 Knowledge base and indexed documents cleared successfully.");
                fetchStatus();
            } else {
                let errorMsg = "Unknown error";
                try {
                    const data = await response.json();
                    errorMsg = data.message || errorMsg;
                } catch (e) {
                    try {
                        errorMsg = await response.text();
                    } catch (t_err) {}
                }
                alert(`Reset failed: ${errorMsg}`);
            }
        } catch (err) {
            alert(`Error resetting database: ${err.message}`);
        }
    });

    // Chat Form Submit Handler
    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const question = userInput.value.trim();
        if (!question) return;

        // Append User Message
        appendUserMessage(question);
        userInput.value = "";

        // Append Assistant Typing Placeholder
        const typingEl = appendAssistantTyping();
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const response = await fetch("/api/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question: question })
            });

            typingEl.remove();

            if (response.ok) {
                const data = await response.json();
                appendAssistantMessage(data.answer, data.sources);
            } else {
                let errorMsg = "Failed to generate answer.";
                try {
                    const data = await response.json();
                    errorMsg = data.detail || errorMsg;
                } catch (e) {
                    try {
                        errorMsg = await response.text();
                    } catch (t_err) {}
                }
                appendAssistantMessage(`❌ Error: ${errorMsg}`);
            }
        } catch (error) {
            typingEl.remove();
            appendAssistantMessage(`❌ Network error: ${error.message}`);
        }

        chatMessages.scrollTop = chatMessages.scrollHeight;
    });

    // Message Rendering Helpers
    function appendUserMessage(text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message message-user";
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-user"></i></div>
            <div class="message-content"><p>${escapeHtml(text)}</p></div>
        `;
        chatMessages.appendChild(msgDiv);
    }

    function appendAssistantTyping() {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message message-assistant";
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content">
                <div class="spinner" style="display:inline-block;"></div> Searching vector database and generating answer...
            </div>
        `;
        chatMessages.appendChild(msgDiv);
        return msgDiv;
    }

    function appendAssistantMessage(answer, sources = []) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message message-assistant";

        let sourcesHtml = "";
        if (sources && sources.length > 0) {
            sourcesHtml = `
                <div class="sources-container">
                    <div class="sources-header"><i class="fa-solid fa-bookmark"></i> Retrieved Source Citations (${sources.length})</div>
                    <div class="source-cards">
                        ${sources.map(s => `
                            <div class="source-card">
                                <div class="source-title">📄 ${escapeHtml(s.filename)} (Page ${s.page})</div>
                                <div class="source-snippet">"${escapeHtml(s.snippet)}"</div>
                            </div>
                        `).join("")}
                    </div>
                </div>
            `;
        }

        const formattedAnswer = formatMarkdown(answer);

        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-robot"></i></div>
            <div class="message-content">
                <div>${formattedAnswer}</div>
                ${sourcesHtml}
            </div>
        `;
        chatMessages.appendChild(msgDiv);
    }

    function appendSystemMessage(text) {
        const msgDiv = document.createElement("div");
        msgDiv.className = "message message-system";
        msgDiv.innerHTML = `
            <div class="avatar"><i class="fa-solid fa-circle-info"></i></div>
            <div class="message-content"><p>${formatMarkdown(text)}</p></div>
        `;
        chatMessages.appendChild(msgDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Helper functions
    window.useSamplePrompt = function(promptText) {
        userInput.value = promptText;
        userInput.focus();
    };

    function escapeHtml(text) {
        return text
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function formatMarkdown(text) {
        let html = escapeHtml(text);
        html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
        html = html.replace(/\n/g, '<br>');
        return html;
    }
});
