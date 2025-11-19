function initThemeHandler(App) {
    const { elements, state } = App;

    // --- Widget Display Function ---
    function displayWeather(data) {
        if (!data || data.error || data.status === 'error') {
            console.error("Weather data error:", data.message || data.error);
            elements.weatherWidgetContainer.innerHTML = '';
            if (!isChatActive) { elements.footerTempContainer.innerHTML = ''; }
            return;
        }
        const iconHTML = `<div class="weather-card"><div class="weather-icon"><img src="${data.condition_icon}" alt="${data.condition_text}"></div></div>`;
        elements.weatherWidgetContainer.innerHTML = iconHTML;
        if (!isChatActive) {
            const tempHTML = `<p class="footer-temp">${Math.round(data.temp_c)}°</p>`;
            elements.footerTempContainer.innerHTML = tempHTML;
        }
    }

    // --- Theme Selection Logic ---
    function updateTheme(data) {
        let themeClass = '';
        if (state.currentThemeMode === 'auto') {
            if (!data || data.error || data.status === 'error') {
                elements.body.className = isChatActive ? 'chat-active' : '';
                elements.backgroundContainer.className = 'background-container';
                return;
            }
            const condition = data.condition_text.toLowerCase();
            const isDay = data.is_day === 1;
            const hour = parseInt(data.localtime.split(' ')[1].split(':')[0]);
            if (isDay && (hour >= 6 && hour < 9)) { themeClass = 'theme-sunrise'; }
            else if (isDay && (hour >= 18 && hour < 20)) { themeClass = 'theme-sunset'; }
            else if (isDay && condition.includes("partly cloudy")) { themeClass = 'theme-day-partly-cloudy'; }
            else if (condition.includes("sunny") || condition.includes("clear")) { themeClass = isDay ? 'theme-day-clear' : 'theme-night-clear'; }
            else if (condition.includes("cloudy") || condition.includes("overcast")) { themeClass = isDay ? 'theme-day-cloudy' : 'theme-night-cloudy'; }
            else if (condition.includes("rain") || condition.includes("drizzle") || condition.includes("thundery")) { themeClass = 'theme-rain'; }
            else if (condition.includes("snow") || condition.includes("sleet") || condition.includes("ice") || condition.includes("blizzard")) { themeClass = 'theme-snow'; }
            else if (condition.includes("mist") || condition.includes("fog")) { themeClass = 'theme-mist'; }
            else { themeClass = isDay ? 'theme-day-clear' : 'theme-night-clear'; }
        } else {
            themeClass = state.currentThemeMode;
        }
        elements.body.className = themeClass;
        if (isChatActive) { elements.body.classList.add('chat-active'); }
        elements.backgroundContainer.className = 'background-container ' + themeClass;
    }

    // --- Main Fetch/Update Function ---
    async function fetchAndUpdateWeather() {
        try {
            const weatherData = await eel.get_latest_weather_data()();
            displayWeather(weatherData);
            updateTheme(weatherData);
        } catch (error) {
            console.error("Failed to fetch and update weather:", error);
            updateTheme(null);
        }
    }

    // --- Event Listeners ---
    elements.themeSelector.addEventListener('change', (event) => {
        state.currentThemeMode = event.target.value;
        fetchAndUpdateWeather();
    });

    // --- Initial Load & Interval ---
    fetchAndUpdateWeather();
    setInterval(fetchAndUpdateWeather, 60000); // Update every minute
}