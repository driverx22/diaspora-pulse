"""Ghanaian-diaspora (USA) source registry for diaspora-pulse.

Curated as of April 2026. Edit freely — the engine consumes this module
without any code changes required elsewhere.

Each source is a dict with:
  id:        short stable identifier
  name:      human-readable name
  category:  community | diaspora_media | youtube_diaspora | x_diaspora
             | associations | church | podcasts | business
  domain:    primary hostname (for site: queries and URL-based filtering).
             May be a hostname ("okayafrica.com") OR a host + path prefix
             ("reddit.com/r/ghanaians") — the URL matcher in lib/ingest.py
             understands both forms.
  handle:    X/YouTube handle (if applicable)
  weight:    baseline authority weight 0.5-1.5 (used in ranking, neutral=1.0)
  notes:     one-line description of what this source covers

Weighting guidance:
  news / data-dense sources : 1.0-1.3
  community / forum         : 0.9-1.2
  YouTube and X handles     : 0.7-1.0
  niche church / chapter    : 0.5-0.8

Quality > quantity. A source only earns a seat if `site:domain "topic"` can
reliably find content. Dead or gated sites are worse than a shorter list.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# COMMUNITY — where diaspora Ghanaians talk online
# Use path-prefixed domains for subreddits / forum subsections so the URL
# matcher in ingest.py can lock matches to the right section without colliding.
# ---------------------------------------------------------------------------
COMMUNITY = [
    {"id": "r_ghanaians", "name": "r/ghanaians", "category": "community",
     "domain": "reddit.com/r/ghanaians", "weight": 1.2,
     "notes": "Ghanaian subreddit — strong diaspora presence."},
    {"id": "r_ghana", "name": "r/Ghana", "category": "community",
     "domain": "reddit.com/r/Ghana", "weight": 1.1,
     "notes": "Primary English-language Ghana community on Reddit; sizeable diaspora overlap."},
    {"id": "r_ghanaiansabroad", "name": "r/GhanaiansAbroad", "category": "community",
     "domain": "reddit.com/r/GhanaiansAbroad", "weight": 1.0,
     "notes": "Reddit community explicitly oriented around Ghanaians abroad."},
    {"id": "r_africa", "name": "r/africa (Ghana tag)", "category": "community",
     "domain": "reddit.com/r/africa", "weight": 0.8,
     "notes": "Pan-African subreddit; Ghana-tagged threads surface here."},
    {"id": "r_blackpeopletwitter_gh", "name": "r/Ghanaba", "category": "community",
     "domain": "reddit.com/r/Ghanaba", "weight": 0.7,
     "notes": "Smaller Ghana-cultural subreddit."},
    {"id": "ghanaweb_forum", "name": "GhanaWeb Forum (diaspora threads)", "category": "community",
     "domain": "ghanaweb.com/GhanaHomePage/features", "weight": 0.8,
     "notes": "GhanaWeb discussion threads — diaspora-heavy readership."},
    {"id": "nairaland_gh", "name": "Nairaland Ghana", "category": "community",
     "domain": "nairaland.com/ghana", "weight": 0.8,
     "notes": "Ghana subforum on pan-West-African Nairaland."},
    {"id": "sikaman_forum", "name": "Sikaman Forum", "category": "community",
     "domain": "sikaman.com", "weight": 0.6,
     "notes": "Long-running diaspora-heavy Ghana forum."},
]

# ---------------------------------------------------------------------------
# DIASPORA MEDIA — US / pan-African outlets that cover Ghana and the diaspora
# ---------------------------------------------------------------------------
DIASPORA_MEDIA = [
    {"id": "okayafrica", "name": "OkayAfrica", "category": "diaspora_media",
     "domain": "okayafrica.com", "weight": 1.2,
     "notes": "Pan-African diaspora publication with strong Ghana and Afrobeats coverage."},
    {"id": "africa_report", "name": "The Africa Report", "category": "diaspora_media",
     "domain": "theafricareport.com", "weight": 1.2,
     "notes": "English-language Pan-African news magazine."},
    {"id": "african_arguments", "name": "African Arguments", "category": "diaspora_media",
     "domain": "africanarguments.org", "weight": 1.0,
     "notes": "Analysis/opinion platform on African politics and policy."},
    {"id": "quartz_africa", "name": "Quartz Africa", "category": "diaspora_media",
     "domain": "qz.com/africa", "weight": 1.0,
     "notes": "Quartz's Africa vertical."},
    {"id": "semafor_africa", "name": "Semafor Africa", "category": "diaspora_media",
     "domain": "semafor.com/africa", "weight": 1.1,
     "notes": "Semafor's Africa desk and newsletter."},
    {"id": "rest_of_world", "name": "Rest of World", "category": "diaspora_media",
     "domain": "restofworld.org", "weight": 1.1,
     "notes": "Tech-and-society reporting beyond the West; frequent Ghana/West Africa stories."},
    {"id": "techcabal", "name": "TechCabal", "category": "diaspora_media",
     "domain": "techcabal.com", "weight": 1.0,
     "notes": "Pan-African tech coverage with strong Ghana reporting."},
    {"id": "african_business", "name": "African Business Magazine", "category": "diaspora_media",
     "domain": "african.business", "weight": 1.0,
     "notes": "Business and finance across Africa."},
    {"id": "face2face_africa", "name": "Face2Face Africa", "category": "diaspora_media",
     "domain": "face2faceafrica.com", "weight": 0.9,
     "notes": "US-based outlet covering Black and African diaspora news."},
    {"id": "pulse_africa", "name": "Pulse Africa", "category": "diaspora_media",
     "domain": "pulse.africa", "weight": 0.8,
     "notes": "Pan-African lifestyle and news."},
    {"id": "africanews", "name": "Africanews", "category": "diaspora_media",
     "domain": "africanews.com", "weight": 0.9,
     "notes": "Euronews-affiliated pan-African newsroom."},
    {"id": "cnn_africa", "name": "CNN Africa", "category": "diaspora_media",
     "domain": "edition.cnn.com/africa", "weight": 0.8,
     "notes": "CNN's Africa tag/section."},
    {"id": "bbc_africa", "name": "BBC Africa", "category": "diaspora_media",
     "domain": "bbc.com/news/world/africa", "weight": 1.0,
     "notes": "BBC Africa desk — heavily read by diaspora."},
]

# ---------------------------------------------------------------------------
# YOUTUBE — creators who cover or live the US-diaspora life
# ---------------------------------------------------------------------------
YOUTUBE_DIASPORA = [
    {"id": "wode_maya", "name": "Wode Maya", "category": "youtube_diaspora",
     "domain": "youtube.com/@wodemaya", "handle": "@wodemaya", "weight": 1.1,
     "notes": "Ghanaian YouTuber documenting Africa and African life abroad."},
    {"id": "svtv_africa", "name": "SVTV Africa", "category": "youtube_diaspora",
     "domain": "youtube.com/@svtvafrica", "handle": "@svtvafrica", "weight": 1.0,
     "notes": "Diaspora / returnee interviews and lifestyle."},
    {"id": "ameyawtv", "name": "Ameyaw TV", "category": "youtube_diaspora",
     "domain": "youtube.com/@ameyawtv", "handle": "@ameyawtv", "weight": 0.9,
     "notes": "Entertainment-and-culture channel, frequent US coverage."},
    {"id": "zionfelix", "name": "ZionFelix", "category": "youtube_diaspora",
     "domain": "youtube.com/@zionfelix", "handle": "@zionfelix", "weight": 0.8,
     "notes": "Entertainment and celebrity interviews; regular US-tour episodes."},
    {"id": "delay_show", "name": "Delay Show", "category": "youtube_diaspora",
     "domain": "youtube.com/@thedelayshow", "handle": "@thedelayshow", "weight": 0.8,
     "notes": "Long-form interviews with Ghanaian public figures."},
    {"id": "kwaku_manu", "name": "Kwaku Manu Aggressive Interview", "category": "youtube_diaspora",
     "domain": "youtube.com/@kwakumanu", "handle": "@kwakumanu", "weight": 0.7,
     "notes": "Confrontational-style interviews, often with diaspora figures."},
    {"id": "afia_schwar", "name": "Afia Schwarzenegger", "category": "youtube_diaspora",
     "domain": "youtube.com/@afiaschwarofficial", "handle": "@afiaschwarofficial", "weight": 0.7,
     "notes": "Ghanaian media personality with large diaspora audience."},
    {"id": "approx_family", "name": "Approximately Family", "category": "youtube_diaspora",
     "domain": "youtube.com/@approximatelyfamily", "handle": "@approximatelyfamily", "weight": 0.8,
     "notes": "Diaspora-life vlog/commentary channel."},
    {"id": "ghanastartv", "name": "Ghana Star TV", "category": "youtube_diaspora",
     "domain": "youtube.com/@ghanastartv", "handle": "@ghanastartv", "weight": 0.7,
     "notes": "Ghana-diaspora entertainment coverage."},
    {"id": "ksm_show", "name": "The KSM Show", "category": "youtube_diaspora",
     "domain": "youtube.com/@theksmshow", "handle": "@theksmshow", "weight": 0.9,
     "notes": "Long-form interviews with Ghanaian public figures."},
]

# ---------------------------------------------------------------------------
# X / TWITTER — diaspora-relevant handles
# ---------------------------------------------------------------------------
X_DIASPORA = [
    # Institutions
    {"id": "x_ghembusa", "name": "@GhanaEmbassyUSA", "category": "x_diaspora",
     "domain": "x.com/GhanaEmbassyUSA", "handle": "@GhanaEmbassyUSA", "weight": 1.2,
     "notes": "Ghana's embassy in Washington, DC."},
    {"id": "x_mfaghana", "name": "@MFA_Ghana", "category": "x_diaspora",
     "domain": "x.com/MFA_Ghana", "handle": "@MFA_Ghana", "weight": 1.0,
     "notes": "Ghana Ministry of Foreign Affairs (diaspora engagement posts)."},
    {"id": "x_gipc", "name": "@GIPCGhana", "category": "x_diaspora",
     "domain": "x.com/GIPCGhana", "handle": "@GIPCGhana", "weight": 0.9,
     "notes": "Ghana Investment Promotion Centre — diaspora investment outreach."},
    # Diaspora orgs
    {"id": "x_afdiaspora", "name": "@AfDiasporaNet", "category": "x_diaspora",
     "domain": "x.com/AfDiasporaNet", "handle": "@AfDiasporaNet", "weight": 1.0,
     "notes": "African Diaspora Network handle."},
    {"id": "x_usghcc", "name": "@USGhCC", "category": "x_diaspora",
     "domain": "x.com/USGhCC", "handle": "@USGhCC", "weight": 0.8,
     "notes": "US-Ghana Chamber of Commerce."},
    {"id": "x_ncoga", "name": "@NCOGA_USA", "category": "x_diaspora",
     "domain": "x.com/NCOGA_USA", "handle": "@NCOGA_USA", "weight": 0.7,
     "notes": "National Council of Ghanaian Associations (NY-based)."},
    # Diaspora-relevant Ghana media on X
    {"id": "x_joynews", "name": "@JoyNewsOnTV", "category": "x_diaspora",
     "domain": "x.com/JoyNewsOnTV", "handle": "@JoyNewsOnTV", "weight": 0.9,
     "notes": "Joy News — widely followed by diaspora."},
    {"id": "x_ghanaweb", "name": "@ghanaweb", "category": "x_diaspora",
     "domain": "x.com/ghanaweb", "handle": "@ghanaweb", "weight": 0.9,
     "notes": "GhanaWeb headlines."},
    {"id": "x_citi973", "name": "@Citi973", "category": "x_diaspora",
     "domain": "x.com/Citi973", "handle": "@Citi973", "weight": 0.8,
     "notes": "Citi FM — strong diaspora reach."},
    # Commentators frequently amplified in diaspora circles
    {"id": "x_brightgh", "name": "@BrightSimons", "category": "x_diaspora",
     "domain": "x.com/BrightSimons", "handle": "@BrightSimons", "weight": 1.0,
     "notes": "Policy commentary, widely followed across the diaspora."},
    {"id": "x_nanaakufo", "name": "@NAkufoAddo", "category": "x_diaspora",
     "domain": "x.com/NAkufoAddo", "handle": "@NAkufoAddo", "weight": 0.8,
     "notes": "Former President of Ghana (diaspora-relevant statements)."},
    {"id": "x_johnmahama", "name": "@JDMahama", "category": "x_diaspora",
     "domain": "x.com/JDMahama", "handle": "@JDMahama", "weight": 0.8,
     "notes": "John Dramani Mahama (diaspora-relevant statements)."},
]

# ---------------------------------------------------------------------------
# ASSOCIATIONS — Ghanaian-diaspora org websites
# ---------------------------------------------------------------------------
ASSOCIATIONS = [
    {"id": "ncoga", "name": "National Council of Ghanaian Associations (NCOGA)", "category": "associations",
     "domain": "ncoga.com", "weight": 1.1,
     "notes": "NY-based national umbrella for Ghanaian-American associations."},
    {"id": "coga_dc", "name": "Council for Ghanaian Associations — Washington DC (COGA)", "category": "associations",
     "domain": "cogawashingtondc.org", "weight": 1.0,
     "notes": "Umbrella for Ghanaian associations in the DMV area."},
    {"id": "coga_dfw", "name": "Council of Ghanaian Associations — DFW", "category": "associations",
     "domain": "cogadfw.org", "weight": 0.9,
     "notes": "Dallas-Fort Worth Ghanaian community council."},
    {"id": "ghana_council_ga", "name": "Ghana Council of Georgia", "category": "associations",
     "domain": "ghanacouncilofgeorgia.org", "weight": 0.9,
     "notes": "Umbrella for Ghanaian associations in Georgia."},
    {"id": "guaom", "name": "Ghana Unity Association of Maryland (GUAOM)", "category": "associations",
     "domain": "ghanaunityassociationofmd.org", "weight": 0.8,
     "notes": "Maryland Ghanaian community organization."},
    {"id": "ago_usa", "name": "Association of Ghanaian Origin USA (AGO USA)", "category": "associations",
     "domain": "agousa.org", "weight": 0.8,
     "notes": "Ghanaian-origin 501(c)(3) headquartered in Maryland."},
    {"id": "gpsf", "name": "Ghana Physicians and Surgeons Foundation (GPSF)", "category": "associations",
     "domain": "ghanaphysicians.org", "weight": 1.0,
     "notes": "US-registered diaspora physician foundation (NC); health-sector hub."},
    {"id": "usghcc", "name": "US-Ghana Chamber of Commerce", "category": "associations",
     "domain": "usghcc.org", "weight": 1.0,
     "notes": "Bilateral trade org strengthening US-Ghana business ties."},
    {"id": "usghcc_alt", "name": "US-Ghana Chamber of Commerce (alt)", "category": "associations",
     "domain": "usghanachamberofcommerce.org", "weight": 0.8,
     "notes": "Alternate domain used by the US-Ghana Chamber of Commerce."},
    {"id": "adn", "name": "African Diaspora Network", "category": "associations",
     "domain": "africandiasporanetwork.org", "weight": 1.0,
     "notes": "Santa Clara-based pan-African diaspora convener (entrepreneurship and policy)."},
    {"id": "amcham_gh", "name": "American Chamber of Commerce — Ghana", "category": "associations",
     "domain": "amchamghana.org", "weight": 0.8,
     "notes": "Accra-based AmCham; covers US-business-in-Ghana issues."},
]

# ---------------------------------------------------------------------------
# CHURCH — diaspora church networks (massive community hubs)
# ---------------------------------------------------------------------------
CHURCH = [
    {"id": "cop_usa", "name": "Church of Pentecost USA", "category": "church",
     "domain": "copusa.org", "weight": 1.1,
     "notes": "Largest Ghanaian-origin Pentecostal body in the US; national site."},
    {"id": "icgc_na", "name": "ICGC North America", "category": "church",
     "domain": "icgcnorthamerica.com", "weight": 1.0,
     "notes": "International Central Gospel Church — North America HQ."},
    {"id": "pcg_manhattan", "name": "Presbyterian Church of Ghana — Manhattan", "category": "church",
     "domain": "pcg-manhattan.org", "weight": 0.8,
     "notes": "First PCG congregation outside Ghana; Manhattan, NYC."},
    {"id": "pcg_adom", "name": "PCG Adom — Greenbelt, MD", "category": "church",
     "domain": "pcgadom.org", "weight": 0.7,
     "notes": "Presbyterian Church of Ghana congregation, Maryland."},
    {"id": "pcg_ebenezer", "name": "PCG Ebenezer — Bronx, NY", "category": "church",
     "domain": "pcgebenezer.com", "weight": 0.7,
     "notes": "Presbyterian Church of Ghana congregation, Bronx."},
    {"id": "pcg_ascension", "name": "PCG Ascension — Orange, NJ", "category": "church",
     "domain": "pcgascension.com", "weight": 0.6,
     "notes": "Presbyterian Church of Ghana congregation, New Jersey."},
    {"id": "pcg_california", "name": "PCG California", "category": "church",
     "domain": "pcgcalifornia.org", "weight": 0.6,
     "notes": "Presbyterian Church of Ghana congregation, Riverside, CA."},
    {"id": "gwumc_va", "name": "Ghana Wesley United Methodist Church — Woodbridge, VA", "category": "church",
     "domain": "ghanawesleyumc.org", "weight": 0.7,
     "notes": "Ghanaian United Methodist congregation in Northern Virginia."},
    {"id": "gwmc_worcester", "name": "Ghana Wesley Methodist Church — Worcester, MA", "category": "church",
     "domain": "gwmcworcester.com", "weight": 0.6,
     "notes": "Ghanaian Methodist congregation in Worcester, MA."},
    {"id": "wghmatl", "name": "Wesley Ghana Methodist — Atlanta", "category": "church",
     "domain": "wghmatl.com", "weight": 0.6,
     "notes": "Ghanaian Wesley Methodist congregation, Atlanta."},
    {"id": "action_chapel", "name": "Action Chapel International", "category": "church",
     "domain": "actionchapel.net", "weight": 0.9,
     "notes": "Duncan-Williams network; many US branches (UDACI)."},
    {"id": "action_chapel_pa", "name": "Action Chapel Pennsylvania", "category": "church",
     "domain": "actionchapelpennsylvania.org", "weight": 0.5,
     "notes": "Action Chapel branch in Pennsylvania."},
    {"id": "action_chapel_va", "name": "Action Chapel Virginia", "category": "church",
     "domain": "actionchapelva.org", "weight": 0.5,
     "notes": "Action Chapel branch in Virginia."},
    {"id": "daghewardmills", "name": "Dag Heward-Mills / UD-OLGC (Lighthouse)", "category": "church",
     "domain": "daghewardmills.org", "weight": 0.9,
     "notes": "United Denominations Originating from the Lighthouse Group of Churches."},
    {"id": "lci_manhattan", "name": "Laikos Manhattan (Lighthouse)", "category": "church",
     "domain": "lcimanhattan.com", "weight": 0.5,
     "notes": "Manhattan branch of the Lighthouse network."},
    {"id": "icgc_chicago", "name": "ICGC Chicago", "category": "church",
     "domain": "icgcchicago.com", "weight": 0.5,
     "notes": "ICGC congregation in Chicago."},
    {"id": "icgc_loudoun", "name": "ICGC Loudoun / Glory Temple", "category": "church",
     "domain": "icgcloudoun.org", "weight": 0.5,
     "notes": "ICGC Glory Temple, Sterling, VA."},
    {"id": "icgc_pa", "name": "ICGC Philadelphia Temple", "category": "church",
     "domain": "icgcpa.org", "weight": 0.5,
     "notes": "ICGC Philadelphia Temple."},
    {"id": "icgc_nj", "name": "ICGC Liberty Temple — NJ", "category": "church",
     "domain": "icgcnj.org", "weight": 0.5,
     "notes": "ICGC Liberty Temple, Orange, NJ."},
]

# ---------------------------------------------------------------------------
# PODCASTS — diaspora-relevant audio with crawlable show-note pages
# ---------------------------------------------------------------------------
PODCASTS = [
    {"id": "afropop", "name": "Afropop Worldwide", "category": "podcasts",
     "domain": "afropop.org", "weight": 1.0,
     "notes": "Long-running US public-radio programme on African and diaspora music."},
    {"id": "afrobility", "name": "Afrobility", "category": "podcasts",
     "domain": "afrobility.com", "weight": 1.0,
     "notes": "Podcast decoding African business and tech — show notes crawlable."},
    {"id": "african_tech_roundup", "name": "African Tech Roundup", "category": "podcasts",
     "domain": "africantechroundup.com", "weight": 0.9,
     "notes": "Weekly commentary on African tech and innovation."},
    {"id": "techcabal_podcasts", "name": "TechCabal Podcasts", "category": "podcasts",
     "domain": "techcabal.com/podcast", "weight": 0.9,
     "notes": "TechCabal's podcast archive."},
    {"id": "npr_africa", "name": "NPR — Africa", "category": "podcasts",
     "domain": "npr.org/sections/africa", "weight": 0.8,
     "notes": "NPR's Africa section (transcripts often crawlable)."},
]

# ---------------------------------------------------------------------------
# BUSINESS — remittance & diaspora-fintech content hubs, plus diaspora-focused
# government/tourism promotion pages.
# ---------------------------------------------------------------------------
BUSINESS = [
    {"id": "remitly_blog", "name": "Remitly blog", "category": "business",
     "domain": "blog.remitly.com", "weight": 1.0,
     "notes": "Remitly corridor/guide content; frequent Ghana coverage."},
    {"id": "sendwave_blog", "name": "Sendwave blog", "category": "business",
     "domain": "sendwave.com/blog", "weight": 0.9,
     "notes": "Sendwave corridor content — strong Africa focus."},
    {"id": "worldremit_blog", "name": "WorldRemit blog", "category": "business",
     "domain": "worldremit.com/en/blog", "weight": 0.9,
     "notes": "WorldRemit corridor content; Ghana features regularly."},
    {"id": "wise_blog", "name": "Wise — Ghana/US corridor content", "category": "business",
     "domain": "wise.com/us", "weight": 0.8,
     "notes": "Wise currency/corridor guides that cover Ghana."},
    {"id": "gipc", "name": "Ghana Investment Promotion Centre (diaspora pages)", "category": "business",
     "domain": "gipc.gov.gh", "weight": 0.9,
     "notes": "Ghana Investment Promotion Centre — diaspora investment pages."},
    {"id": "year_of_return", "name": "Year of Return", "category": "business",
     "domain": "yearofreturn.com", "weight": 1.0,
     "notes": "Official Year of Return 2019 archive — diaspora homecoming."},
    {"id": "ghana_tourism", "name": "Ghana Tourism Authority — Beyond the Return", "category": "business",
     "domain": "visitghana.com", "weight": 0.8,
     "notes": "Ghana Tourism Authority; hub for Beyond the Return diaspora initiatives."},
    {"id": "diasporaaffairs", "name": "Diaspora Affairs Office (Ghana)", "category": "business",
     "domain": "diasporaaffairs.gov.gh", "weight": 0.9,
     "notes": "Office of Diaspora Affairs — official Ghana-diaspora liaison."},
]

# ---------------------------------------------------------------------------
# AGGREGATE
# ---------------------------------------------------------------------------
ALL_SOURCES = (
    COMMUNITY
    + DIASPORA_MEDIA
    + YOUTUBE_DIASPORA
    + X_DIASPORA
    + ASSOCIATIONS
    + CHURCH
    + PODCASTS
    + BUSINESS
)

CATEGORY_ALIASES = {
    "community": {"community"},
    "forums": {"community"},
    "forum": {"community"},
    "reddit": {"community"},

    "diaspora_media": {"diaspora_media"},
    "media": {"diaspora_media"},
    "news": {"diaspora_media"},

    "youtube_diaspora": {"youtube_diaspora"},
    "youtube": {"youtube_diaspora"},
    "yt": {"youtube_diaspora"},

    "x_diaspora": {"x_diaspora"},
    "x": {"x_diaspora"},
    "twitter": {"x_diaspora"},

    "associations": {"associations"},
    "assoc": {"associations"},
    "orgs": {"associations"},

    "church": {"church"},
    "churches": {"church"},

    "podcasts": {"podcasts"},
    "podcast": {"podcasts"},

    "business": {"business"},
    "remittance": {"business"},
    "fintech": {"business"},

    # Composite aliases for convenience
    "social": {"x_diaspora", "youtube_diaspora"},
    "all_media": {"diaspora_media", "youtube_diaspora", "podcasts"},
}


def get_sources(categories: list[str] | None = None) -> list[dict]:
    """Return sources filtered by category. If None, return all."""
    if not categories:
        return ALL_SOURCES
    wanted: set[str] = set()
    for c in categories:
        wanted |= CATEGORY_ALIASES.get(c.strip().lower(), {c.strip().lower()})
    return [s for s in ALL_SOURCES if s["category"] in wanted]


def source_weight(source: dict) -> float:
    return float(source.get("weight", 1.0))


def domain_filter(sources: list[dict]) -> list[str]:
    return [s["domain"] for s in sources if s.get("domain")]
