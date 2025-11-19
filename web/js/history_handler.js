// js/history_handler.js

function initHistoryHandler(App) {
    const { elements, state, globals } = App;
    let chatToDeleteId = null;

    // --- Core Functions ---

    function openHistoryPanel() {
        populateHistoryList();
        document.body.classList.add('history-active');
    }

    function closeHistoryPanel() {
        document.body.classList.remove('history-active');
    }

    async function populateHistoryList() {
        elements.historyList.innerHTML = '<li>Loading history...</li>';
        try {
            const chats = await eel.get_chat_history_list()();
            elements.historyList.innerHTML = ''; // Clear loading message

            if (chats.length === 0) {
                elements.historyList.innerHTML = '<li>No chat history found.</li>';
                return;
            }

            const groupedChats = groupChatsByDate(chats);
            for (const groupTitle in groupedChats) {
                // Add date header
                const header = document.createElement('li');
                header.className = 'history-date-header';
                header.textContent = groupTitle;
                elements.historyList.appendChild(header);

                // Add chat items for that date
                groupedChats[groupTitle].forEach(chat => {
                    const li = document.createElement('li');
                    li.dataset.id = chat.id;
                    li.textContent = chat.title || 'Untitled Chat';
                    
                    const deleteBtn = document.createElement('span');
                    deleteBtn.className = 'delete-chat-btn';
                    deleteBtn.innerHTML = '&times;';
                    deleteBtn.title = 'Delete Chat';
                    li.appendChild(deleteBtn);
                    
                    elements.historyList.appendChild(li);
                });
            }

        } catch (error) {
            console.error("Failed to load chat history:", error);
            elements.historyList.innerHTML = '<li>Error loading history.</li>';
        }
    }
    
    function groupChatsByDate(chats) {
        const groups = { 'Today': [], 'Yesterday': [], 'This Week': [], 'Older': [] };
        const now = new Date();
        const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
        const yesterday = new Date(today);
        yesterday.setDate(yesterday.getDate() - 1);
        const startOfWeek = new Date(today);
        startOfWeek.setDate(startOfWeek.getDate() - now.getDay());

        for (const chat of chats) {
            const chatDate = new Date(chat.timestamp);
            if (chatDate >= today) {
                groups['Today'].push(chat);
            } else if (chatDate >= yesterday) {
                groups['Yesterday'].push(chat);
            } else if (chatDate >= startOfWeek) {
                groups['This Week'].push(chat);
            } else {
                groups['Older'].push(chat);
            }
        }
        // Remove empty groups
        return Object.fromEntries(Object.entries(groups).filter(([_, v]) => v.length > 0));
    }


    async function loadChatSession(chatId) {
        // --- NEW LOGIC ---
        globals.addSystemMessage(`Loading chat session...`);
        closeHistoryPanel();
        
        const result = await eel.load_chat_session(chatId)();
        
        if (result && result.status === 'success' && Array.isArray(result.content)) {
            globals.setChatActive(true);
            elements.chatDisplay.innerHTML = ''; // Clear current display

            // Use the exact same functions that the live chat uses. This is the key fix.
            for (const turn of result.content) {
                const messageText = turn.parts[0]?.text || ''; // Safely access text
                if (turn.role === 'user') {
                    globals.addUserMessage(messageText);
                } else if (turn.role === 'model') {
                    globals.processApiResponse(messageText);
                }
            }
            // Ensure the AI is ready for a new message
            elements.messageInput.disabled = false;
            elements.recordButton.disabled = false;
            elements.messageInput.placeholder = "Press Enter to send...";

            globals.scrollToBottom();
        } else {
            globals.addSystemMessage(`Error: Could not load chat. ${result?.message || 'Unknown error.'}`);
        }
    }
    
    function confirmDelete(chatId, chatTitle) {
        chatToDeleteId = chatId;
        elements.deleteConfirmMessage.textContent = `Are you sure you want to permanently delete the chat titled "${chatTitle}"? This action cannot be undone.`;
        elements.deleteConfirmModal.classList.add('active');
    }

    async function deleteChat() {
        if (!chatToDeleteId) return;
        
        const result = await eel.delete_chat_session(chatToDeleteId)();
        elements.deleteConfirmModal.classList.remove('active');

        if (result.status === 'success') {
            const itemToRemove = elements.historyList.querySelector(`li[data-id="${chatToDeleteId}"]`);
            if (itemToRemove) {
                itemToRemove.remove();
            }
        } else {
            alert(`Error deleting chat: ${result.message}`);
        }
        chatToDeleteId = null;
    }

    // --- Event Listeners ---

    elements.historyButton.addEventListener('click', openHistoryPanel);
    elements.closeHistoryBtn.addEventListener('click', closeHistoryPanel);
    elements.historyOverlay.addEventListener('click', closeHistoryPanel);

    // Delegated event listener for the list itself
    elements.historyList.addEventListener('click', (event) => {
        const li = event.target.closest('li');
        if (!li || !li.dataset.id) return; // Ignore headers or empty space clicks

        if (event.target.classList.contains('delete-chat-btn')) {
            event.stopPropagation(); // Prevent the li click from firing
            confirmDelete(li.dataset.id, li.textContent.replace('×', '').trim());
        } else {
            loadChatSession(li.dataset.id);
        }
    });
    
    elements.deleteConfirmBtn.addEventListener('click', deleteChat);
    elements.deleteCancelBtn.addEventListener('click', () => {
        elements.deleteConfirmModal.classList.remove('active');
        chatToDeleteId = null;
    });

}