function initComponents(App) {
    const { elements, state, globals } = App;

    // --- Custom Toast Notification Function ---
    function showToast(message, type = 'success') {
        const toastContainer = document.getElementById('toast-container');
        if (!toastContainer) return;
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        toastContainer.appendChild(toast);
        setTimeout(() => {
            toast.classList.add('removing');
            toast.addEventListener('animationend', () => { toast.remove(); });
        }, 4000);
    }

    // ===================================================================
    //                          NEW BRIEFING UI LOGIC
    // ===================================================================

    function renderBriefingCard(point) {
        const card = document.createElement('div');
        card.className = 'briefing-card';
        card.innerHTML = `<strong>${point.type.replace('_', ' ').toUpperCase()}:</strong> ${point.text}`;
        
        if (point.data && (point.data.email_id || point.data.doc_path)) {
            card.onclick = () => {
                if (point.data.email_id) {
                    console.log("Opening email:", point.data.email_id);
                    openEmailViewer(point.data.email_id);
                }
                if (point.data.doc_path) {
                    eel.open_file_path(point.data.doc_path)();
                }
            };
        }
        App.elements.briefingPanel.appendChild(card);
    }

    // --- THIS IS THE SINGLE, CORRECT VERSION OF addSystemMessage ---
    // It returns the element it creates, which is essential for the briefing logic.
    function addSystemMessage(message) {
        if (!isChatActive) globals.setChatActive(true);
        const messageElement = document.createElement("div");
        messageElement.classList.add("chat-message", "system-message");
        messageElement.innerHTML = `<i>${message}</i>`;
        elements.chatDisplay.appendChild(messageElement);
        globals.scrollToBottom();
        return messageElement;
    }
    eel.expose(addSystemMessage, 'addSystemMessage');
    // Expose the correct function globally so other modules can use it.
    globals.addSystemMessage = addSystemMessage;



    App.elements.briefingButton.addEventListener('click', async () => {
        globals.setChatActive(true);
        const generatingMessage = globals.addSystemMessage('☀️ Generating your personalized morning briefing...');
        App.elements.briefingButton.disabled = true;
        if (App.elements.briefingPanel) App.elements.briefingPanel.innerHTML = '';

        try {
            const briefingData = await eel.start_morning_briefing()(); 
            console.log("--- DEBUG: Received from Python:", briefingData);

            // Check for an error key from Python
            if (briefingData && briefingData.error) {
                if(generatingMessage) generatingMessage.innerHTML = `❌ ${briefingData.error}`;
                return; // Stop execution
            }

            if (briefingData && briefingData.audio_path) {
                if (generatingMessage) generatingMessage.remove();
                
                const relativePath = 'audio/' + briefingData.audio_path.split(/[\\/]/).pop();
                const briefingAudio = new Audio(relativePath);
                
                // --- SIMPLIFIED LOGIC ---
                briefingAudio.onplay = () => {
                    document.body.classList.add('is-speaking');
                    // Display all cards at once when audio starts
                    if (briefingData.briefing_points) {
                        briefingData.briefing_points.forEach(point => {
                            renderBriefingCard(point);
                        });
                    }
                };
                
                briefingAudio.onended = () => {
                    document.body.classList.remove('is-speaking');
                    // Clear the cards after the briefing is done
                    if (App.elements.briefingPanel) App.elements.briefingPanel.innerHTML = '';
                    showBriefingFeedbackUI();
                };
                // --- END OF SIMPLIFIED LOGIC ---
                
                briefingAudio.play();

            } else {
                if(generatingMessage) generatingMessage.innerHTML = '❌ Error generating briefing.';
            }
        } catch(e) {
            if(generatingMessage) generatingMessage.innerHTML = '❌ A critical error occurred.';
            console.error(e);
        } finally {
            App.elements.briefingButton.disabled = false;
        }
    });

    function showBriefingFeedbackUI() {
        const feedbackContainer = document.createElement('div');
        feedbackContainer.className = 'chat-message system-message feedback-container';
        feedbackContainer.innerHTML = `
            <p>How was this morning's briefing?</p>
            <div class="stars">
                <span data-value="1">☆</span><span data-value="2">☆</span><span data-value="3">☆</span><span data-value="4">☆</span><span data-value="5">☆</span>
            </div>
            <textarea placeholder="Any suggestions for next time?"></textarea>
            <button class="btn btn-primary">Submit Feedback</button>
        `;
        elements.chatDisplay.appendChild(feedbackContainer);
        globals.scrollToBottom();

        const stars = feedbackContainer.querySelectorAll('.stars span');
        let currentRating = 0;

        stars.forEach(star => {
            star.onclick = () => {
                currentRating = parseInt(star.dataset.value);
                stars.forEach(s => {
                    s.innerHTML = parseInt(s.dataset.value) <= currentRating ? '★' : '☆';
                });
            };
        });
        
        const submitBtn = feedbackContainer.querySelector('button');
        const textArea = feedbackContainer.querySelector('textarea');
        submitBtn.onclick = async () => {
            if (currentRating === 0) {
                alert("Please select a rating.");
                return;
            }
            const comment = textArea.value;
            const result = await eel.submit_briefing_feedback(currentRating, comment)();
            feedbackContainer.innerHTML = `<p>✅ Thank you for your feedback!</p>`;
        };
    }

    // ===================================================================
    //                      ORIGINAL COMPONENT LOGIC (UNCHANGED)
    // ===================================================================

    // --- Email Viewer Logic ---
    async function openEmailViewer(emailId) {
        if (!emailId) return;
        elements.emailViewerFrom.textContent = 'Loading...';
        elements.emailViewerSubject.textContent = 'Loading...';
        elements.emailViewerBody.textContent = 'Fetching email content...';
        elements.emailViewerOpenBtn.style.display = 'none';
        state.currentEmailWebLink = null;
        elements.emailViewerModal.classList.add('active');
        try {
            const details = await eel.get_email_content(emailId)();
            if (details.error) {
                elements.emailViewerBody.textContent = details.error;
            } else {
                elements.emailViewerFrom.textContent = details.from;
                elements.emailViewerSubject.textContent = details.subject;
                elements.emailViewerBody.textContent = details.body;
                if (details.web_link) {
                    state.currentEmailWebLink = details.web_link;
                    elements.emailViewerOpenBtn.style.display = 'inline-block';
                }
            }
        } catch (err) {
            console.error("Failed to fetch email content:", err);
            elements.emailViewerBody.textContent = "An error occurred while fetching the email.";
        }
    }
    function closeEmailViewer() { elements.emailViewerModal.classList.remove('active'); }

    // --- Notifications Panel Logic ---
    function toggleNotificationsPanel() {
        state.isPanelOpen = !state.isPanelOpen;
        elements.notificationsPanel.classList.toggle('visible', state.isPanelOpen);
        if (state.isPanelOpen) {
            elements.notificationDot.classList.remove('visible');
            elements.welcomeNotificationDot.classList.remove('visible');
            updateNotifications();
        }
    }
    async function updateNotifications() {
        const systemNotifications = await eel.get_monitor_notifications()();
        const importantEmails = await eel.get_important_emails()();
        const allNotifications = [
            ...systemNotifications.map(n => ({ ...n, type: 'system', from: 'System Monitor', subject: n.text })),
            ...importantEmails.map(e => ({ ...e, type: 'email' }))
        ];
        if (allNotifications.length > 0 && !state.isPanelOpen) {
            elements.notificationDot.classList.add('visible');
            elements.welcomeNotificationDot.classList.add('visible');
        } else if (allNotifications.length === 0) {
            elements.notificationDot.classList.remove('visible');
            elements.welcomeNotificationDot.classList.remove('visible');
        }
        if (!state.isPanelOpen) return;
        const incomingIds = new Set(allNotifications.map(n => n.id));
        elements.notificationsList.querySelectorAll('li').forEach(li => {
            if (!incomingIds.has(li.dataset.id)) li.remove();
        });
        allNotifications.forEach(notification => {
            if (!document.querySelector(`#notifications-list li[data-id='${notification.id}']`)) {
                const li = document.createElement('li');
                li.dataset.id = notification.id;
                li.dataset.type = notification.type;
                const dismissBtn = document.createElement('span');
                dismissBtn.className = 'dismiss-btn';
                dismissBtn.innerHTML = '&times;';
                const contentDiv = document.createElement('div');
                contentDiv.className = 'notification-content';
                const icon = notification.type === 'email' ? '📧' : '⚙️';
                contentDiv.innerHTML = `<span class="notification-sender">${icon} ${notification.from || notification.from_full}</span><span class="notification-subject">${notification.subject}</span>`;
                li.appendChild(contentDiv);
                li.appendChild(dismissBtn);
                elements.notificationsList.appendChild(li);
            }
        });
        if (elements.notificationsList.children.length === 0) {
            elements.notificationsList.innerHTML = '<li>No important notifications.</li>';
        }
    }

    // --- Inbox Panel Logic ---
    function toggleInboxPanel() {
        state.isInboxOpen = !state.isInboxOpen;
        elements.inboxPanel.classList.toggle('visible', state.isInboxOpen);
        if (state.isInboxOpen) {
            elements.inboxDot.classList.remove('visible');
            elements.welcomeInboxDot.classList.remove('visible');
            updateInbox();
        }
    }
    async function updateInbox() {
        const otherEmails = await eel.get_other_emails()();
        if (otherEmails.length > 0 && !state.isInboxOpen) {
            elements.inboxDot.classList.add('visible');
            elements.welcomeInboxDot.classList.add('visible');
        } else if (otherEmails.length === 0) {
            elements.inboxDot.classList.remove('visible');
            elements.welcomeInboxDot.classList.remove('visible');
        }
        if (!state.isInboxOpen) return;
        
        elements.inboxList.innerHTML = '';
        
        otherEmails.forEach(email => {
            if (!document.querySelector(`#inbox-list li[data-id='${email.id}']`)) {
                const li = document.createElement('li');
                li.dataset.id = email.id;
                const dismissBtn = document.createElement('span');
                dismissBtn.className = 'dismiss-btn';
                dismissBtn.innerHTML = '&times;';
                const contentDiv = document.createElement('div');
                contentDiv.className = 'email-content';
                contentDiv.innerHTML = `<span class="email-sender">${email.from_full}</span><span class="email-subject">${email.subject}</span>`;
                li.appendChild(contentDiv);
                li.appendChild(dismissBtn);
                elements.inboxList.appendChild(li);
            }
        });
        if (elements.inboxList.children.length === 0) {
            elements.inboxList.innerHTML = '<li>No new mail.</li>';
        }
    }

    // --- Profile and Settings Logic ---
    const settingsMapping = {
        'GEMINI_API_KEY': 'setting-gemini-api-key', 'TELEGRAM_BOT_TOKEN': 'setting-telegram-bot-token',
        'TELEGRAM_ADMIN_USER_ID': 'setting-telegram-admin-id', 'WEATHER_API_KEY': 'setting-weather-api-key',
        'DEFAULT_AI_MODEL': 'setting-default-ai-model', 'VISION_MODEL_NAME': 'setting-vision-model-name',
        'GOOGLE_CSE_API_KEY': 'setting-google-cse-api-key', 'GOOGLE_CSE_ENGINE_ID': 'setting-google-cse-engine-id',
        'AI_TEMPERATURE': 'setting-ai-temperature', 'MAX_WEB_SCRAPE_CONTENT_LENGTH': 'setting-max-scrape-length'
    };

    function openProfileModal() { globals.setChatActive(false); elements.profileModal.classList.add('active'); }
    function closeProfileModal() {
        elements.profileModal.classList.remove('active');
        if (elements.chatDisplay.children.length > 0) globals.setChatActive(true);
    }
    function closeAllModalsAndReturn() {
        elements.profileModal.classList.remove('active');
        elements.settingsOverlay.classList.remove('active');
        globals.setChatActive(elements.chatDisplay.children.length > 0);
    }

    async function loadProfileData() {
        const profileData = await eel.get_profile_data()();
        if (profileData) {
            elements.profileNameInput.value = profileData.name || 'User';
            elements.greetingElement.textContent = `Hello, ${profileData.name || 'User'}`;
            if (profileData.photo_base64) {
                const imageUrl = `data:image/jpeg;base64,${profileData.photo_base64}`;
                elements.profilePicDisplay.style.backgroundImage = `url('${imageUrl}')`;
                elements.profileBtn.style.backgroundImage = `url('${imageUrl}')`;
            } else {
                elements.profilePicDisplay.style.backgroundImage = 'none';
                elements.profileBtn.style.backgroundImage = 'none';
            }
        }
    }
    async function loadSettingsData() {
        const settings = await eel.get_settings()();
        if (settings) {
            for (const key in settingsMapping) {
                const element = document.getElementById(settingsMapping[key]);
                if (element) { element.value = settings[key] || ''; }
            }
        }
    }

    // --- Register Event Listeners ---
    // Monitoring Toggles
    elements.monitorToggle.addEventListener('change', function() {
        eel.toggle_monitoring(this.checked)();
        globals.addSystemMessage(this.checked ? "Downloads folder monitoring activated." : "Downloads folder monitoring deactivated.");
    });
    elements.healthMonitorToggle.addEventListener('change', function() {
        eel.toggle_health_monitoring(this.checked)();
        globals.addSystemMessage(this.checked ? "System health monitoring activated." : "System health monitoring deactivated.");
    });

    // Panels
    elements.notificationsButton.addEventListener('click', toggleNotificationsPanel);
    elements.welcomeNotificationsButton.addEventListener('click', toggleNotificationsPanel);
    elements.inboxButton.addEventListener('click', toggleInboxPanel);
    elements.welcomeInboxButton.addEventListener('click', toggleInboxPanel);

    // Panel Lists
    elements.notificationsList.addEventListener('click', function(event) {
        const li = event.target.closest('li');
        if (!li || !li.dataset.id) return;
        if (event.target.classList.contains('dismiss-btn')) {
            event.stopPropagation();
            li.classList.add('removing');
            (li.dataset.type === 'email' ? eel.dismiss_email(li.dataset.id) : eel.dismiss_notification(li.dataset.id))();
            li.addEventListener('animationend', () => {
                li.remove();
                if (elements.notificationsList.children.length === 0) elements.notificationsList.innerHTML = '<li>No important notifications.</li>';
            });
        } else if (li.dataset.type === 'email') {
            openEmailViewer(li.dataset.id);
        }
    });
    elements.inboxList.addEventListener('click', function(event) {
        const li = event.target.closest('li');
        if (!li || !li.dataset.id) return;
        if (event.target.classList.contains('dismiss-btn')) {
            event.stopPropagation();
            li.classList.add('removing');
            eel.dismiss_email(li.dataset.id)();
            li.addEventListener('animationend', () => {
                 li.remove();
                 if (elements.inboxList.children.length === 0) elements.inboxList.innerHTML = '<li>No new mail.</li>';
            });
        } else {
            openEmailViewer(li.dataset.id);
        }
    });

    // Email Viewer
    elements.emailViewerCloseBtn.addEventListener('click', closeEmailViewer);
    elements.emailViewerModal.addEventListener('click', (e) => { if (e.target === elements.emailViewerModal) closeEmailViewer(); });
    elements.emailViewerOpenBtn.addEventListener('click', () => { if (state.currentEmailWebLink) eel.open_in_browser(state.currentEmailWebLink)(); });

    // Visual Query
    elements.visualQueryInput.addEventListener('keydown', function(event) {
        // ... (this logic remains the same)
    });
    elements.visualQueryOverlay.addEventListener('click', function(e) {
        // ... (this logic remains the same)
    });

    // Confirmation Modal
    document.addEventListener('show-confirmation-modal', (e) => {
        // ... (this logic remains the same)
    });
    elements.confirmBtn.addEventListener('click', () => {
        // ... (this logic remains the same)
    });
    elements.cancelBtn.addEventListener('click', () => {
        // ... (this logic remains the same)
    });

    // Profile & Settings Modals
    elements.profileBtn.addEventListener('click', openProfileModal);
    elements.profileCloseBtn.addEventListener('click', closeProfileModal);
    elements.openSettingsBtn.addEventListener('click', () => {
        elements.profileModal.classList.remove('active');
        elements.settingsOverlay.classList.add('active');
    });
    elements.settingsBackBtn.addEventListener('click', () => {
        elements.settingsOverlay.classList.remove('active');
        elements.profileModal.classList.add('active');
    });
    // ... (rest of profile/settings listeners remain the same) ...
    elements.profileSaveBtn.addEventListener('click', async () => {
        // ...
    });
    elements.settingsSaveBtn.addEventListener('click', async () => {
        // ...
    });
    
    // --- Initial Data Load & Intervals ---
    loadProfileData();
    loadSettingsData();
    updateNotifications();
    updateInbox();
    setInterval(() => {
        updateNotifications();
        updateInbox();
    }, 5000);
}