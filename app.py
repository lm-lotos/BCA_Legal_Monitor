import streamlit as st

from collectors.official.gesetze_rss import fetch_updates
from collectors.official.lea_berlin import get_lea_publications
from collectors.official.bamf import fetch_bamf_publications
from collectors.official.arbeitsagentur import fetch_ba_publications
from collectors.official.ba_weisungen import fetch_ba_weisungen
from processing.translator import translate_text
from email.utils import parsedate_to_datetime
from legal_diff.diff_renderer import render_diff, DIFF_CSS
from legal_diff.version_fetcher import build_legal_comparison


st.set_page_config(
    page_title="BCA Legal & Migration Monitor",
    page_icon="🌍",
    layout="wide",
)


# ---------- LANGUAGES ----------

LANGUAGES = {
    "🇩🇪 Deutsch": "de",
    "🇬🇧 English": "en",
    "🇷🇺 Русский": "ru",
    "🇺🇦 Українська": "uk",
    "🌐 العربية": "ar",
}

UI_TEXT = {
    "ru": {
        "language": "Язык",
        "subtitle": "Правовые новости, миграционные новости и изменения законодательства в Германии",
        "current": "Актуальное",
        "possible": "🚦 Релевантность",
        "archive": "Поиск",
        "changes": "БЫЛО ↔ СТАЛО",
        "current_changes": "Наиболее релевантные публикации",
        "new_publications": "Всего публикаций",
        "relevant_bca": "Релевантных для BCA",
        "last_update": "Последнее обновление",
        "now": "сейчас",
        "info": "Отобраны из официальных и законодательных источников по темам миграции и права.",
        "publications": "Актуальные публикации",
        "translation": "Перевод",
        "topics": "Темы BCA",
        "reason": "Почему важно",
        "score": "Оценка BCA",
        "date": "Дата публикации",
        "source": "Открыть официальный источник ↗",
        "nothing_found": "Новых релевантных публикаций пока не найдено.",
        "archive_title": "Поиск",
        "search": "🔎 Поиск",
        "search_placeholder": "Например: Blue Card, §24, Einbürgerung, Aufenthalt...",
        "search_help": "Введите ключевое слово, название закона, тему или §.",
        "search_button": "Найти 🔎",
        "total": "Всего",
        "source_filter": "Источник",
        "all_sources": "Все источники",
        "found": "Найдено",
        "shown": "Показано",
        "of": "из",
        "show_all": "Показать все публикации",
        "open_source": "Открыть источник ↗",
        "show_changes": "⚖️ Показать изменения",
        "translate_diff": "🌐 Перевести БЫЛО / СТАЛО",
        "show_more": "Показать ещё 20",
        "legal_comparison": "⚖️ Сравнение изменений законодательства",
        "legal_act": "Нормативный акт",
        "section": "Раздел",
        "change": "Изменение",
        "before": "🔴 БЫЛО",
        "after": "🟢 СТАЛО",  
    },

    "uk": {
        "language": "Мова",
        "subtitle": "Правові новини, міграційні новини та зміни законодавства в Німеччині",
        "current": "Актуальні",
        "possible": "🚦 Релевантність",
        "archive": "Пошук",
        "changes": "БУЛО ↔ СТАЛО",
        "current_changes": "Найбільш релевантні публікації",
        "new_publications": "Усього публікацій",
        "relevant_bca": "Релевантних для BCA",
        "last_update": "Останнє оновлення",
        "now": "зараз",
        "info": "Відібрано з офіційних та законодавчих джерел за темами міграції та права.",
        "publications": "Актуальні публікації",
        "translation": "Переклад",
        "topics": "Теми BCA",
        "reason": "Чому важливо",
        "score": "Оцінка BCA",
        "date": "Дата публікації",
        "source": "Відкрити офіційне джерело ↗",
        "nothing_found": "Нових релевантних публікацій поки не знайдено.",
        "archive_title": "Пошук",
        "search": "🔎 Пошук",
        "search_placeholder": "Наприклад: Blue Card, §24, Einbürgerung, Aufenthalt...",
        "search_help": "Введіть ключове слово, назву закону, тему або §.",
        "search_button": "Знайти 🔎",
        "source_filter": "Джерело",
        "all_sources": "Усі джерела",
        "total": "Всього",
        "show_all": "Показати всі публікації",
        "found": "Знайдено",
        "shown": "Показано",
        "of": "з",
        "open_source": "Відкрити джерело ↗",
        "show_changes": "⚖️ Показати зміни",
        "translate_diff": "🌐 Перекласти БУЛО / СТАЛО",
        "show_more": "Показати ще 20",
        "legal_comparison": "⚖️ Порівняння змін законодавства",
        "legal_act": "Нормативний акт",
        "section": "Розділ",
        "change": "Зміна",
        "before": "🔴 БУЛО",
        "after": "🟢 СТАЛО",
    },

    "de": {
        "language": "Sprache",
        "subtitle": "Rechts- und Migrationsnachrichten sowie gesetzliche Änderungen in Deutschland",
        "current": "Aktuell",
        "possible": "🚦 Relevanz",
        "archive": "Suche",
        "changes": "VORHER ↔ NACHHER",
        "current_changes": "Relevanteste Veröffentlichungen",
        "new_publications": "Veröffentlichungen insgesamt",
        "relevant_bca": "Relevant für BCA",
        "last_update": "Letzte Aktualisierung",
        "now": "jetzt",
        "info": "Aus offiziellen und gesetzgeberischen Quellen zu den Themen Migration und Recht ausgewählt.",
        "publications": "Aktuelle Veröffentlichungen",
        "translation": "Übersetzung",
        "topics": "BCA-Themen",
        "reason": "Warum wichtig",
        "score": "BCA-Bewertung",
        "date": "Veröffentlichungsdatum",
        "source": "Offizielle Quelle öffnen ↗",
        "nothing_found": "Derzeit wurden keine neuen relevanten Veröffentlichungen gefunden.",
        "archive_title": "Suche",
        "search": "🔎 Suche",
        "search_placeholder": "Zum Beispiel: Blue Card, §24, Einbürgerung, Aufenthalt...",
        "search_help": "Geben Sie ein Stichwort, einen Gesetzesnamen, ein Thema oder einen §.",
        "search_button": "Suchen 🔎",
        "source_filter": "Quelle",
        "all_sources": "Alle Quellen",
        "found": "Gefunden",
        "shown": "Angezeigt",
        "of": "von",
        "total": "Gesamt",
        "open_source": "Quelle öffnen ↗",
        "show_changes": "⚖️ Änderungen anzeigen",
        "translate_diff": "🌐 VORHER / NACHHER übersetzen",
        "show_all": "Alle Veröffentlichungen anzeigen",
        "show_more": "Weitere 20 anzeigen",
        "legal_comparison": "⚖️ Vergleich der Gesetzesänderungen",
        "legal_act": "Rechtsvorschrift",
        "section": "Abschnitt",
        "change": "Änderung",
        "before": "🔴 BESONDERS",
        "after": "🟢 NACHHER",
    },

    "en": {
        "language": "Language",
        "subtitle": "Legal and migration news and legislative changes in Germany",
        "current": "Current",
        "possible": "🚦 Relevance",
        "archive": "Search",
        "changes": "BEFORE ↔ AFTER",
        "current_changes": "Most relevant publications",
        "new_publications": "Total publications",
        "relevant_bca": "Relevant for BCA",
        "last_update": "Last update",
        "now": "now",
        "info": "Selected from official and legislative sources on migration and legal topics.",
        "publications": "Current publications",
        "translation": "Translation",
        "topics": "BCA topics",
        "reason": "Why it matters",
        "score": "BCA score",
        "date": "Publication date",
        "source": "Open official source ↗",
        "nothing_found": "No new relevant publications found.",
        "archive_title": "Search",
        "search": "🔎 Search",
        "search_placeholder": "For example: Blue Card, §24, naturalization, residence...",
        "search_help": "Enter a keyword, law name, topic or §.",
        "search_button": "Search 🔎",
        "source_filter": "Source",
        "all_sources": "All sources",
        "found": "Found",
        "shown": "Shown",
        "of": "of",
        "total": "Total",
        "open_source": "Open source ↗",
        "show_changes": "⚖️ Show changes",
        "translate_diff": "🌐 Translate BEFORE / AFTER",
        "show_all": "Show all publications",
        "show_more": "Show 20 more",
    },

    "ar": {
        "language": "اللغة",
        "subtitle": "أخبار قانونية وأخبار الهجرة والتغييرات التشريعية في ألمانيا",
        "current": "الحالي",
        "possible": "🚦 الصلة",
        "archive": "بحث",
        "changes": "قبل ↔ بعد",
        "current_changes": "المنشورات الأكثر صلة",
        "new_publications": "إجمالي المنشورات",
        "relevant_bca": "ذات صلة بـ BCA",
        "last_update": "آخر تحديث",
        "now": "الآن",
        "info": "تم الاختيار من مصادر رسمية وتشريعية حول موضوعات الهجرة والقانون.",
        "publications": "المنشورات الحالية",
        "translation": "الترجمة",
        "topics": "مواضيع BCA",
        "reason": "لماذا هذا مهم",
        "score": "تقييم BCA",
        "date": "تاريخ النشر",
        "source": "فتح المصدر الرسمي ↗",
        "nothing_found": "لم يتم العثور حالياً على منشورات جديدة ذات صلة.",
        "archive_title": "بحث",
        "search": "🔎 بحث",
        "search_placeholder": "مثال: Blue Card، §24، التجنيس، الإقامة...",
        "search_help": "أدخل كلمة مفتاحية أو اسم قانون أو موضوعًا أو §.",
        "search_button": "بحث 🔎",
        "source_filter": "المصدر",
        "all_sources": "جميع المصادر",
        "total": "المجموع",
        "show_all": "عرض جميع المنشورات",
        "found": "تم العثور على",
        "shown": "المعروض",
        "of": "من",
        "open_source": "فتح المصدر ↗",
        "show_changes": "⚖️ عرض التغييرات",
        "translate_diff": "🌐 ترجمة قبل / بعد",
        "show_more": "عرض 20 منشورًا إضافيًا",
        "legal_comparison": "⚖️ مقارنة التغييرات القانونية",
        "legal_act": "التشريع",
        "section": "القسم",
        "change": "التغيير",
        "before": "🔴 قبل",
        "after": "🟢 بعد",
    },
}

DISPLAY_TRANSLATIONS = {
    "uk": {
        "Признание иностранных квалификаций": "Визнання іноземних кваліфікацій",
        "ВНЖ / право пребывания": "Посвідка на проживання / право на перебування",
        "признание иностранной квалификации": "визнання іноземної кваліфікації",
        "прямой миграционно-правовой термин": "прямий міграційно-правовий термін",
    },
    "ru": {},
    "de": {
        "Признание иностранных квалификаций": "Anerkennung ausländischer Qualifikationen",
        "ВНЖ / право пребывания": "Aufenthaltstitel / Aufenthaltsrecht",
        "признание иностранной квалификации": "Anerkennung ausländischer Qualifikationen",
        "прямой миграционно-правовой термин": "direkter migrationsrechtlicher Begriff",
    },
    "en": {
        "Признание иностранных квалификаций": "Recognition of foreign qualifications",
        "ВНЖ / право пребывания": "Residence permit / right of residence",
        "признание иностранной квалификации": "recognition of foreign qualifications",
        "прямой миграционно-правовой термин": "direct migration-law term",
    },
    "ar": {
        "Признание иностранных квалификаций": "الاعتراف بالمؤهلات الأجنبية",
        "ВНЖ / право пребывания": "تصريح الإقامة / حق الإقامة",
        "признание иностранной квалификации": "الاعتراف بالمؤهلات الأجنبية",
        "прямой миграционно-правовой термин": "مصطلح مباشر في قانون الهجرة",
    },
}

@st.cache_data(ttl=3600, show_spinner=False)
def load_monitor_data():
    try:
        data = fetch_updates()
        if isinstance(data, dict):
            return data
    except Exception:
        pass

    return {
        "results": [],
        "all_publications": [],
        "total_publications": 0,
        "relevant_count": 0,
    }


@st.cache_data(ttl=3600, show_spinner=False)
def load_lea_data():
    try:
        data = get_lea_publications()
        return data if isinstance(data, list) else []
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def load_bamf_data():
    try:
        data = fetch_bamf_publications()
        return data if isinstance(data, list) else []
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def load_ba_data():
    try:
        data = fetch_ba_publications()
        return data if isinstance(data, list) else []
    except Exception:
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def load_ba_weisungen_data():
    try:
        data = fetch_ba_weisungen()
        return data if isinstance(data, list) else []
    except Exception:
        return []


@st.cache_data(ttl=86400, show_spinner=False)
def load_legal_comparison(url):
    try:
        return build_legal_comparison(url)
    except Exception:
        return None


@st.cache_data(ttl=86400, show_spinner=False)
def cached_translate_text(text, language_code, api_key=None):
    return translate_text(text, language_code, api_key=api_key)


lea_publications = load_lea_data()
bamf_publications = load_bamf_data()
ba_publications = load_ba_data()
ba_weisungen = load_ba_weisungen_data()
monitor_data = load_monitor_data()

# Единый поток всех собранных публикаций
all_publications = (
    monitor_data.get("all_publications", [])
    + lea_publications
    + bamf_publications
    + ba_publications
    + ba_weisungen
)

# Реальная статистика по фактически загруженным данным
monitor_data["all_publications"] = all_publications
monitor_data["total_publications"] = len(all_publications)

# Результаты для светофора: HIGH + POSSIBLE + LOW
monitor_data["results"] = monitor_data.get("results") or monitor_data.get("all_publications", [])

monitor_data["relevant_count"] = sum(
    1
    for item in monitor_data["results"]
    if item.get("relevance_level") in ("HIGH", "POSSIBLE")
)

# ---------- HEADER ----------

left, right = st.columns([5, 1])

with right:
    language = st.selectbox(
        "🌐",
        list(LANGUAGES.keys()),
        index=2,
        label_visibility="visible",
    )

    deepl_api_key = st.text_input(
        "🔑 DeepL API",
        type="password",
        placeholder="API key",
        help="Введите собственный DeepL API-ключ для автоматического перевода.",
        key="deepl_api_key",
    )

    st.link_button(
        "🔑 Получить DeepL API key",
        "https://www.deepl.com/en/developers",
        use_container_width=True,
    )

    if deepl_api_key:
        st.caption("✅ Переводчик подключён")
    else:
        st.caption("Переводчик не подключён")

language_code = LANGUAGES[language]
text = UI_TEXT.get(language_code, UI_TEXT["ru"])

if language_code == "ar":
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] {
            direction: rtl;
            text-align: right;
        }

        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stAppViewContainer"] p {
            text-align: right;
        }
        [data-testid="stHorizontalBlock"]:first-of-type {
            direction: ltr;
        }
        [data-testid="stMarkdownContainer"] h4 {
            direction: ltr;
            text-align: left;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

with left:
    st.title("BCA Legal & Migration Monitor")
    st.caption(text["subtitle"])

    st.markdown("##### 🌐 Официальные источники")

source_badges = [
       (
        "🌐 Все",
        len(monitor_data["all_publications"]),
        None,
    ),
    (
        "⚖️ Gesetze",
        monitor_data.get("total_publications", 0),
        "Gesetze im Internet",
    ),
    (
        "💼 BA",
        len(ba_publications) + len(ba_weisungen),
        "Bundesagentur für Arbeit",
    ),
    (
        "🛂 BAMF",
        len(bamf_publications),
        "BAMF",
    ),
    (
        "📍 LEA Berlin",
        len(lea_publications),
        "LEA Berlin",
    ),
]

if "global_source_filter" not in st.session_state:
    st.session_state.global_source_filter = None

source_cols = st.columns(len(source_badges))

for col, (label, count, source) in zip(source_cols, source_badges):
    with col:
        is_active = st.session_state.global_source_filter == source

        button_label = (
            f"✅ {label} · {count}"
            if is_active
            else f"{label} · {count}"
        )

        if st.button(
            button_label,
            key=f"source_badge_{source}",
            use_container_width=True,
            type="secondary",
        ):
           st.session_state.global_source_filter = source
           st.session_state.archive_open = False
           st.session_state.archive_limit = 20
           st.rerun()

# ---------- MEDIA ----------

st.markdown("##### 📰 Медиа")

media_col1, media_col2, media_col3, media_col4 = st.columns(4)

with media_col1:
    st.link_button(
        "🌍 DW",
        "https://www.dw.com/de/",
        use_container_width=True,
    )

with media_col2:
    st.link_button(
        "📍 rbb24",
        "https://www.rbb24.de/",
        use_container_width=True,
    )

with media_col3:
    st.link_button(
        "📰 Tagesspiegel",
        "https://www.tagesspiegel.de/",
        use_container_width=True,
    )

with media_col4:
    st.link_button(
        "💼 Handelsblatt",
        "https://www.handelsblatt.com/",
        use_container_width=True,
    )

# ---------- NAVIGATION ----------

tab_current, tab_possible, tab_archive = st.tabs(
    [
        f"🏠 {text['current']}",
        f"🟡 {text['possible']}",
        f"🗂 {text['archive']}",
    ]
)


with tab_current:
    st.subheader(text["current_changes"])

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        st.caption(text["new_publications"])
        st.markdown(f"**{monitor_data['total_publications']}**")

    with col2:
        st.caption(text["relevant_bca"])
        st.markdown(f"**{monitor_data['relevant_count']}**")

    with col3:
        st.caption(text["last_update"])
        st.markdown(f"**{text['now']}**")

    st.caption(text["info"])


    high_results = [
        item
        for item in monitor_data["results"]
        if item.get("relevance_level", "MEDIUM") == "HIGH"
    ]

    if high_results:
        for item in high_results:
            st.markdown("---")

            st.markdown(f"#### {item['document_title']}")

            translation = cached_translate_text(
                item.get("document_title", ""),
                language_code,
                deepl_api_key,
            )

            if translation:
                st.caption(f"{text['translation']}: {translation}")

            display_map = DISPLAY_TRANSLATIONS.get(language_code, {})

            topics = ", ".join(
                display_map.get(topic, topic)
                for topic in item["topics"]
            ) if item["topics"] else "-"

            reasons = ", ".join(
                display_map.get(reason, reason)
                for reason in item["reasons"]
            ) if item["reasons"] else "-"

            st.write(f"**{text['topics']}:** {topics}")
            st.write(f"**{text['reason']}:** {reasons}")
            st.write(f"**{text['score']}:** {item['score']}")

            publication_date = parsedate_to_datetime(item["date"]).strftime("%d.%m.%Y, %H:%M")
            st.write(f"**{text['date']}:** {publication_date}")

            st.link_button(
                text["source"],
                item["url"],
            )

    else:
        st.info(text["nothing_found"])

with tab_possible:
    st.subheader("🚦 Релевантность публикаций")

    st.write(
    "🟢 Наиболее релевантные  ·  🟡 Средняя релевантность  ·  🔴 Низкая релевантность"
    )
    high_results = [
    item
    for item in monitor_data["results"]
    if item.get("relevance_level") == "HIGH"
    ]

    possible_results = [
    item
    for item in monitor_data["results"]
    if item.get("relevance_level") == "POSSIBLE"
    ]

    low_results = [
    item
    for item in monitor_data["results"]
    if item.get("relevance_level") == "LOW"
    ]

    relevance_groups = [
        ("🟢 Наиболее релевантные", high_results),
        ("🟡 Средняя релевантность", possible_results),
        ("🔴 Низкая релевантность", low_results),
        ]

    for group_title, group_results in relevance_groups:
        st.markdown(f"### {group_title}")

        if group_results:
            for item in group_results:
                st.markdown("---")
                st.markdown(f"#### {item['document_title']}")

                translation = cached_translate_text(
                    item.get("document_title", ""),
                    language_code,
                    deepl_api_key,
                )

                if translation:
                    st.caption(f"{text['translation']}: {translation}")

                display_map = DISPLAY_TRANSLATIONS.get(language_code, {})

                topics = ", ".join(
                    display_map.get(topic, topic)
                    for topic in item["topics"]
                ) if item["topics"] else "-"

                reasons = ", ".join(
                    display_map.get(reason, reason)
                    for reason in item["reasons"]
                ) if item["reasons"] else "-"

                st.write(f"**{text['topics']}:** {topics}")
                st.write(f"**{text['reason']}:** {reasons}")
                st.write(f"**{text['score']}:** {item['score']}")

                publication_date = parsedate_to_datetime(
                    item["date"]
                ).strftime("%d.%m.%Y, %H:%M")

                st.write(f"**{text['date']}:** {publication_date}")

                st.link_button(
                text["source"],
                item["url"],
                )

        else:
            st.caption("Нет публикаций в этой категории.")   

with tab_archive:
    st.subheader(UI_TEXT[language_code]["search"])

    with st.form("archive_search_form"):
        search_col, button_col = st.columns([5, 1])

    with search_col:
        search = st.text_input(
            UI_TEXT[language_code]["search"],
            placeholder=UI_TEXT[language_code]["search_placeholder"],
            key="archive_search",
        )

    with button_col:
        st.write("")
        search_button = st.form_submit_button(
            UI_TEXT[language_code]["search_button"],
            use_container_width=True,
        )

    st.caption(UI_TEXT[language_code]["search_help"])

    st.subheader(f"📚 {UI_TEXT[language_code]['publications']}")

    all_archive_publications = (
        monitor_data["all_publications"] + lea_publications + bamf_publications + ba_publications + ba_weisungen
    )

    if "archive_open" not in st.session_state:
        st.session_state.archive_open = False

    selected_source = st.session_state.global_source_filter

    if selected_source is None:
        filtered_publications = all_archive_publications

    elif selected_source == "Bundesagentur für Arbeit":
        filtered_publications = [
            item
            for item in all_archive_publications
            if item.get("source") in ["Bundesagentur für Arbeit", "BA Weisungen"]
        ]

    else:
        filtered_publications = [
            item
            for item in all_archive_publications
            if item.get("source") == selected_source
        ]

    show_all_button = st.button(
        f"{UI_TEXT[language_code]['show_all']} ({len(filtered_publications)})",
        use_container_width=True,
    )

    if show_all_button:
        st.session_state.archive_open = True

    if "archive_limit" not in st.session_state:
        st.session_state.archive_limit = 20

    if st.session_state.archive_open and not (search_button and search):
        st.write(f"{UI_TEXT[language_code]['total']}: {len(filtered_publications)}")
        st.caption(
            f"{UI_TEXT[language_code]['shown']}: "
            f"{min(st.session_state.archive_limit, len(filtered_publications))} "
            f"{UI_TEXT[language_code]['of']} {len(all_archive_publications)}"
        )
                        
        for item in filtered_publications[:st.session_state.archive_limit]:
            st.markdown(f"#### {item.get('title', '')}")
            st.caption(item.get("source", ""))
            st.link_button(
                UI_TEXT[language_code]["open_source"],
                item.get("url", ""),
            )
            
        if st.session_state.archive_limit < len(filtered_publications):
            if st.button(UI_TEXT[language_code]["show_more"]):
                st.session_state.archive_limit += 20
                st.rerun()

    if "search_results" not in st.session_state:
        st.session_state.search_results = []

    if search_button and search:
        query = search.lower()

        st.session_state.search_results = [
            item
            for item in all_archive_publications
            if query in item.get("title", "").lower()
            or query in item.get("document_title", "").lower()
        ]

    search_results = st.session_state.search_results

    if search_results:
        st.write(f"{UI_TEXT[language_code]['found']}: {len(search_results)}")

        for item in search_results:
            st.markdown(f"#### {item.get('title', '')}")
            st.caption(item.get("source", ""))
            st.link_button(
                UI_TEXT[language_code]["open_source"],
                item.get("url", ""),
            )

            if item.get("source") == "Gesetze im Internet":
                show_comparison = st.button(
                    UI_TEXT[language_code]["show_changes"],
                    key=f"show_comparison_{item.get('url', '')}",
                )

                comparison_key = f"comparison_{item.get('url', '')}"

                if show_comparison:
                    st.session_state[comparison_key] = load_legal_comparison(
                        item.get("url", "")
                 )

                comparison = st.session_state.get(comparison_key)

                if comparison is not None:
                    old_text = comparison.get("old_text")
                    new_text = comparison.get("new_text")

                    if old_text and new_text:
                        st.markdown(
                            f"#### {UI_TEXT[language_code]['legal_comparison']}"
                        )

                        st.markdown(
                            f"**{UI_TEXT[language_code]['legal_act']}:** "
                            f"{comparison.get('law', '')}"
                        )

                        st.markdown(
                            f"**{UI_TEXT[language_code]['section']}:** "
                            f"{comparison.get('section', '')}"
                        )

                        st.markdown(
                            f"**{UI_TEXT[language_code]['change']}:** "
                            f"{comparison.get('instruction', '')}"
                        )

                        show_translation = st.button(
                            UI_TEXT[language_code]["translate_diff"],
                            key=f"translate_diff_{item.get('url', '')}",
                        )

                        translated_old = None
                        translated_new = None

                        if show_translation and language_code != "de":
                            translated_old = cached_translate_text(
                                old_text,
                                language_code,
                                deepl_api_key,
                            )
                            translated_new = cached_translate_text(
                                new_text,
                                language_code,
                                deepl_api_key,
                            )

                        old_col, new_col = st.columns(2)

                        old_diff, new_diff = render_diff(
                            old_text,
                            new_text,
                        )

                        st.markdown(
                            DIFF_CSS,
                            unsafe_allow_html=True,
                        )

                        with old_col:
                            st.markdown(
                                f"#### {UI_TEXT[language_code]['before']}"
                            )
                            st.markdown(
                                old_diff,
                                unsafe_allow_html=True,
                            )
                            if translated_old:
                                st.info(translated_old)

                        with new_col:
                            st.markdown(
                                f"#### {UI_TEXT[language_code]['after']}"
                            )
                            st.markdown(
                                new_diff,
                                unsafe_allow_html=True,
                            )
                            if translated_new:
                                st.info(translated_new)

            st.markdown("---")