/**
 * Kerala Lottery App Logic
 * Optimized for mobile-first UI and fast loading
 */

let currentLang = localStorage.getItem('lang') || 'en';
let manifestData = [];
let historyData = [];
let currentCategory = 'ALL';

const i18n = {
    en: {
        pageTitle: "Kerala Lottery",
        allResults: "All Results",
        noResults: "No results found for this category.",
        draw: "Draw",
        date: "Date",
        loading: "Loading results...",
        home: "Results",
        live: "Live",
        lucky: "Lucky",
        search: "Search",
        scanner: "Download",
        selectLang: "Select Language"
    },
    ml: {
        pageTitle: "കേരള ലോട്ടറി",
        allResults: "എല്ലാ ഫലങ്ങളും",
        noResults: "ഫലങ്ങളൊന്നുമില്ല.",
        draw: "ഡ്രോ",
        date: "തീയതി",
        loading: "ഫലങ്ങൾ ശേഖരിക്കുന്നു...",
        home: "ഫലങ്ങൾ",
        live: "ലൈവ്",
        lucky: "ലക്കി",
        search: "തിരയുക",
        scanner: "ഡൗൺലോഡ്",
        selectLang: "ഭാഷ തിരഞ്ഞെടുക്കുക"
    },
    ta: {
        pageTitle: "கேரளா லாட்டரி",
        allResults: "அனைத்து முடிவுகள்",
        noResults: "முடிவுகள் இல்லை.",
        draw: "டிரா",
        date: "தேதி",
        loading: "முடிவுகள் ஏற்றப்படுகின்றன...",
        home: "முடிவுகள்",
        live: "நேரலை",
        lucky: "லக்கி",
        search: "தேடல்",
        scanner: "பதிவிறக்க",
        selectLang: "மொழியைத் தேர்ந்தெடுக்கவும்"
    }
};

const catMap = {
    'SAMRUDHI': 'SM', 'BHAGYATHARA': 'BT', 'STHREE_SAKTHI': 'SS',
    'DHANALEKSHMI': 'DL', 'KARUNYA_PLUS': 'KN', 'SUVARNA_KERALAM': 'SK',
    'KARUNYA': 'KR', 'AKSHAYA': 'AK', 'WIN_WIN': 'WW', 'NIRMAL': 'NR',
    'FIFTY_FIFTY': 'FF', 'BUMPER': 'BR', 'VISHU_BUMPER': 'VB',
    'MONSOON_BUMPER': 'MY', 'KERALA_BUMPER': 'RK'
};

// Bumper codes - shown with special gold styling
const bumperCodes = new Set(['BR', 'VB', 'MY', 'RK', 'MC']);

const lotteryNames = {
    // Weekly lotteries
    AK: { en: 'Akshaya', ml: 'അക്ഷയ', ta: 'அக்ஷயா' },
    WW: { en: 'Win Win', ml: 'വിൻ വിൻ', ta: 'வின் வின்' },
    NR: { en: 'Nirmal', ml: 'നിർമ്മൽ', ta: 'நிர்மல்' },
    KR: { en: 'Karunya', ml: 'കരുണ്യ', ta: 'கருண்யா' },
    KN: { en: 'Karunya Plus', ml: 'കരുണ്യ പ്ലസ്', ta: 'கருண்யா பிளஸ்' },
    SS: { en: 'Sthree Sakthi', ml: 'സ്ത്രീ ശക്തി', ta: 'ஸ்த்ரீ-சக்தி' },
    SK: { en: 'Suvarna Keralam', ml: 'സുവർണ കേരളം', ta: 'சுவர்ண கேரளம்' },
    FF: { en: 'Fifty Fifty', ml: 'ഫിഫ്റ്റി-ഫിഫ്റ്റി', ta: 'ஃபிஃப்டி-ஃபிஃப்டி' },
    SKS: { en: 'Fifty Fifty', ml: 'ഫിഫ്റ്റി-ഫിഫ്റ്റി', ta: 'ஃபிஃப்டி-ஃபிஃப்டி' },
    SM: { en: 'Samrudhi', ml: 'സമൃദ്ധി', ta: 'சம்ருத்தி' },
    BT: { en: 'Bhagyathara', ml: 'ഭാഗ്യതാര', ta: 'பாக்யதாரா' },
    DL: { en: 'Dhanalekshmi', ml: 'ധനലക്ഷ്മി', ta: 'தனலட்சுமி' },
    // Bumper lotteries
    BR: { en: 'Bumper Lottery', ml: 'ബമ്പർ ലോട്ടറി', ta: 'பம்பர் லாட்டரி' },
    VB: { en: 'Vishu Bumper', ml: 'വിഷു ബമ്പർ', ta: 'விஷு பம்பர்' },
    MY: { en: 'Monsoon Bumper', ml: 'മൺസൂൺ ബമ്പർ', ta: 'மழை பம்பர்' },
    RK: { en: 'Kerala Bumper', ml: 'കേരള ബമ്പർ', ta: 'கேரளா பம்பர்' },
    MC: { en: 'Xmas New Year Bumper', ml: 'ക്രിസ്മസ് ബമ്പർ', ta: 'கிறிஸ்மஸ் பம்பர்' },
    XX: { en: 'Kerala Lottery', ml: 'കേരള ലോട്ടറി', ta: 'கேரளா லாட்டரி' }
};

// Theme Logic
let currentTheme = localStorage.getItem('theme') || (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
document.body.className = currentTheme;

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
    updateDate();
    initLang();
    initCategories();
    initTheme();
    fetchManifest();

    // Offline Check
    window.addEventListener('online', updateOnlineStatus);
    window.addEventListener('offline', updateOnlineStatus);
    updateOnlineStatus();
});

function initTheme() {
    const toggle = document.getElementById('theme-toggle');
    if (!toggle) return;

    updateThemeIcon();
    toggle.addEventListener('click', () => {
        currentTheme = currentTheme === 'dark' ? 'light' : 'dark';
        document.body.className = currentTheme;
        localStorage.setItem('theme', currentTheme);
        updateThemeIcon();
    });
}

function updateThemeIcon() {
    const icon = document.querySelector('#theme-toggle i');
    if (icon) icon.textContent = currentTheme === 'dark' ? 'light_mode' : 'dark_mode';
}

function updateOnlineStatus() {
    const banner = document.getElementById('offline-banner');
    if (banner) {
        banner.style.display = navigator.onLine ? 'none' : 'block';
    }
}

function updateDate() {
    const now = new Date();
    const options = { weekday: 'long', day: 'numeric', month: 'short' };
    const el = document.getElementById('today-date');
    if (el) el.textContent = now.toLocaleDateString(undefined, options);
}

function initLang() {
    const toggle = document.getElementById('lang-toggle');
    const overlay = document.getElementById('lang-modal-overlay');
    const options = document.querySelectorAll('.lang-option');

    if (toggle && overlay) {
        toggle.addEventListener('click', () => {
            overlay.style.display = 'flex';
        });

        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) overlay.style.display = 'none';
        });

        options.forEach(opt => {
            if (opt.dataset.lang === currentLang) opt.classList.add('active');
            opt.addEventListener('click', () => {
                currentLang = opt.dataset.lang;
                localStorage.setItem('lang', currentLang);
                options.forEach(o => o.classList.remove('active'));
                opt.classList.add('active');
                updateTranslations();
                renderResults();
                setTimeout(() => {
                    overlay.style.display = 'none';
                }, 200);
            });
        });
    }
    updateTranslations();
}

function updateTranslations() {
    const t = i18n[currentLang];
    // const title = document.querySelector('h1');
    // if (title) title.textContent = t.pageTitle;

    const empty = document.getElementById('empty-msg');
    if (empty) empty.textContent = t.noResults;

    const allChip = document.querySelector('[data-category="ALL"]');
    if (allChip) allChip.textContent = t.allResults;

    const langTitle = document.querySelector('.lang-modal h3');
    if (langTitle) langTitle.textContent = t.selectLang;

    const liveBtn = document.querySelector('.live-header-btn');
    if (liveBtn) liveBtn.textContent = ' ' + t.live;

    // Update nav labels
    const navItems = document.querySelectorAll('.nav-item');
    if (navItems.length >= 4) {
        navItems[0].querySelector('span').textContent = t.home;
        navItems[1].querySelector('span').textContent = t.lucky;
        navItems[2].querySelector('span').textContent = t.search;
        navItems[3].querySelector('span').textContent = t.scanner;
    }
}

function initCategories() {
    const chips = document.querySelectorAll('.cat-chip');
    chips.forEach(chip => {
        chip.addEventListener('click', () => {
            chips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            currentCategory = chip.dataset.category;
            renderResults();
        });
    });
}

async function fetchManifest() {
    try {
        const response = await fetch('result_manifest.json');
        manifestData = await response.json();
        renderResults();
    } catch (e) {
        console.error("Failed to load manifest", e);
    }
}

function renderResults() {
    const list = document.getElementById('results-list');
    if (!list) return;
    const empty = document.getElementById('empty-state');

    // Filter
    const filtered = manifestData.filter(item => {
        let code = (item.code || item.lottery_code || '').toUpperCase();
        if (!code && item.filename) {
            code = item.filename.split('-')[0].toUpperCase();
        }
        if (currentCategory === 'ALL') return true;
        if (currentCategory === 'BUMPER') return bumperCodes.has(code);
        return code === catMap[currentCategory];
    }).slice(0, 365);

    if (filtered.length === 0) {
        list.innerHTML = '';
        if (empty) empty.style.display = 'block';
        return;
    }

    if (empty) empty.style.display = 'none';

    // Build fragment
    const fragment = document.createDocumentFragment();

    filtered.forEach((item, index) => {
        const card = document.createElement('a');
        const isLocal = window.location.protocol === 'file:';
        const targetPage = isLocal ? 'result.html' : 'result';
        card.href = `${targetPage}?file=${encodeURIComponent(item.filename)}`;
        card.className = 'result-card fade-in';

        let code = (item.code || item.lottery_code || '').toUpperCase();
        if (!code && item.filename) {
            code = item.filename.split('-')[0].toUpperCase();
        }
        if (!code) code = 'XX';

        const nameObj = lotteryNames[code];
        const name = nameObj ? (nameObj[currentLang] || nameObj.en) : (code + ' Lottery');
        const date = item.date ? item.date.split('-').reverse().join('/') : '';
        const isBumper = bumperCodes.has(code);

        // Draw number display - for bumpers the draw_number may be a date label
        let drawNo = item.draw_number || item.draw || '';
        if (!drawNo && item.filename) {
            drawNo = item.filename.split('-')[1] || '';
        }
        const drawLabel = drawNo && /^\d+$/.test(drawNo)
            ? code + '-' + drawNo
            : (isBumper ? '★ BUMPER' : code);

        const isNew = (index === 0);
        const newBadge = isNew ? '<span class="badge-new">NEW</span>' : '';
        const bumperStyle = isBumper
            ? 'background: linear-gradient(135deg, #92400e, #b45309); border: 1.5px solid #f59e0b;'
            : '';

        card.innerHTML = `
            <div class="card-upper" style="${bumperStyle}">
                 ${newBadge}
                 <span class="badge-code" style="${isBumper ? 'background:#f59e0b;color:#1c1917;' : ''}">${drawLabel}</span>
                 <div class="card-title">${name}</div>
            </div>
            <div class="card-lower">
                 <div class="card-date">${date}</div>
                 ${isBumper ? '<div style="font-size:0.7rem;font-weight:700;color:#f59e0b;letter-spacing:0.5px;">🏆 BUMPER LOTTERY</div>' : ''}
            </div>
        `;
        fragment.appendChild(card);
    });

    list.innerHTML = '';
    list.appendChild(fragment);
}
