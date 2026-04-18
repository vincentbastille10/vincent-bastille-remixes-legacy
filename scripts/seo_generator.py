import os
import json
import requests
import sys
import random
from datetime import date

TOGETHER_API_KEY = os.getenv("TOGETHER_API_KEY")
if not TOGETHER_API_KEY:
    print("❌ TOGETHER_API_KEY manquante")
    sys.exit(1)
print("✅ API KEY OK")

API_URL = "https://api.together.xyz/v1/chat/completions"
MODEL = "meta-llama/Meta-Llama-3-8B-Instruct-Lite"
BASE_URL = "https://vincent-bastille-remixes-legacy.vercel.app"
BANDCAMP_URL = "https://vincentbastille.bandcamp.com/album/vincent-bastille-remixes-legacy"
BANDCAMP_ARTIST = "https://vincentbastille.bandcamp.com"
OUTPUT_DIR = "seo-pages"
PAGES_PER_RUN = 150

# ─────────────────────────────────────────
# TRACKS RÉELS DE L'ALBUM
# ─────────────────────────────────────────
REAL_TRACKS = [
    {"artiste": "Jennifer Lopez", "titre": "Can't Get Enough", "style": "pop latine house"},
    {"artiste": "Modjo", "titre": "Lady", "style": "disco house french touch"},
    {"artiste": "Michael Jackson", "titre": "You Rock My World", "style": "disco house funk"},
    {"artiste": "Madonna", "titre": "Ray Of Light", "style": "électronique trance pop"},
    {"artiste": "Sade", "titre": "Smooth Operator", "style": "deep house soul"},
    {"artiste": "Nana Mouskouri", "titre": "Quand Tu Chantes", "style": "house chanson française"},
    {"artiste": "The Eagles", "titre": "Hotel California", "style": "rock électronique house"},
    {"artiste": "Calvin Harris", "titre": "Promises", "style": "house progressive"},
    {"artiste": "Bruno Mars", "titre": "I Just Might", "style": "funk house pop"},
]

# ─────────────────────────────────────────
# LIENS INTERNES (maillage)
# ─────────────────────────────────────────
ALL_SLUGS = [
    "vincent-bastille-remixes",
    "remixes-house-music-france",
    "dj-vincent-bastille-mix",
    "vincent-bastille-deep-house",
    "remix-jennifer-lopez-cant-get-enough",
    "remix-madonna-ray-of-light",
    "remix-michael-jackson-you-rock-my-world",
    "remix-sade-smooth-operator",
    "remix-modjo-lady-french-touch",
    "remix-calvin-harris-promises",
    "remix-bruno-mars-funk-house",
    "remix-eagles-hotel-california",
    "remix-nana-mouskouri-chanson-house",
    "french-touch-remixes-daft-punk-influence",
    "house-music-francaise-histoire",
    "meilleurs-remixes-electroniques-2026",
    "remix-pop-electronique-achat",
    "vincent-bastille-bandcamp",
    "remix-disco-house-france",
    "acheter-remixes-electroniques-france",
]

# ─────────────────────────────────────────
# 150 TOPICS ULTRA-CIBLÉS
# ─────────────────────────────────────────
TOPICS = [
    # === TRACKS RÉELS DE L'ALBUM ===
    {"slug": "remix-jennifer-lopez-cant-get-enough", "sujet": "le remix house de Jennifer Lopez Can't Get Enough par Vincent Bastille", "artistes_connexes": ["Jennifer Lopez", "Beyoncé", "Rihanna", "Shakira", "Pitbull"], "track_reel": True},
    {"slug": "remix-madonna-ray-of-light", "sujet": "le remix électronique de Madonna Ray Of Light par Vincent Bastille (finaliste Beatport Remix Challenge)", "artistes_connexes": ["Madonna", "Björk", "Lady Gaga", "Kylie Minogue", "Annie Lennox"], "track_reel": True},
    {"slug": "remix-michael-jackson-you-rock-my-world", "sujet": "le remix disco house de Michael Jackson You Rock My World par Vincent Bastille", "artistes_connexes": ["Michael Jackson", "Bruno Mars", "Prince", "Stevie Wonder", "James Brown"], "track_reel": True},
    {"slug": "remix-sade-smooth-operator", "sujet": "le remix deep house de Sade Smooth Operator par Vincent Bastille", "artistes_connexes": ["Sade", "Erykah Badu", "Lauryn Hill", "Amy Winehouse", "Alicia Keys"], "track_reel": True},
    {"slug": "remix-modjo-lady-french-touch", "sujet": "le remix disco house de Modjo Lady par Vincent Bastille (French Touch)", "artistes_connexes": ["Modjo", "Daft Punk", "Cassius", "Stardust", "Bob Sinclar"], "track_reel": True},
    {"slug": "remix-calvin-harris-promises", "sujet": "le remix house progressif de Calvin Harris Promises par Vincent Bastille", "artistes_connexes": ["Calvin Harris", "David Guetta", "Martin Garrix", "Tiësto", "Avicii"], "track_reel": True},
    {"slug": "remix-bruno-mars-funk-house", "sujet": "le remix funk house de Bruno Mars I Just Might par Vincent Bastille", "artistes_connexes": ["Bruno Mars", "Mark Ronson", "Silk Sonic", "Anderson .Paak", "Charlie Puth"], "track_reel": True},
    {"slug": "remix-eagles-hotel-california", "sujet": "le remix électronique de The Eagles Hotel California par Vincent Bastille", "artistes_connexes": ["The Eagles", "Fleetwood Mac", "Tame Impala", "MGMT", "The Doors"], "track_reel": True},
    {"slug": "remix-nana-mouskouri-chanson-house", "sujet": "le remix house chanson française de Nana Mouskouri par Vincent Bastille", "artistes_connexes": ["Nana Mouskouri", "Édith Piaf", "Charles Aznavour", "Mireille Mathieu", "Dalida"], "track_reel": True},

    # === PAGES ARTISTE CONNEXE — MADONNA UNIVERSE ===
    {"slug": "remix-electronique-madonna-universe", "sujet": "les remixes électroniques dans l'univers de Madonna", "artistes_connexes": ["Madonna", "Björk", "Lady Gaga", "Sabrina Carpenter", "Charli XCX"], "track_reel": False},
    {"slug": "bjork-remixes-electroniques-influence", "sujet": "l'influence de Björk sur les remixes électroniques modernes", "artistes_connexes": ["Björk", "FKA twigs", "Arca", "Portishead", "Massive Attack"], "track_reel": False},
    {"slug": "lady-gaga-remix-house-electronique", "sujet": "les remixes house électroniques dans le style Lady Gaga", "artistes_connexes": ["Lady Gaga", "Madonna", "Kylie Minogue", "Dua Lipa", "Lizzo"], "track_reel": False},
    {"slug": "sabrina-carpenter-remix-electronique", "sujet": "les remixes électroniques pop dans le style de Sabrina Carpenter", "artistes_connexes": ["Sabrina Carpenter", "Olivia Rodrigo", "Taylor Swift", "Ariana Grande", "Dua Lipa"], "track_reel": False},
    {"slug": "charli-xcx-brat-remixes-house", "sujet": "les remixes house et club dans l'univers Brat de Charli XCX", "artistes_connexes": ["Charli XCX", "Caroline Polachek", "Troye Sivan", "Christine and the Queens", "Rina Sawayama"], "track_reel": False},
    {"slug": "kylie-minogue-remixes-disco-house", "sujet": "les remixes disco house dans l'univers de Kylie Minogue", "artistes_connexes": ["Kylie Minogue", "Madonna", "Donna Summer", "Gloria Gaynor", "Robyn"], "track_reel": False},

    # === MICHAEL JACKSON UNIVERSE ===
    {"slug": "michael-jackson-remixes-electroniques", "sujet": "les remixes électroniques dans l'univers de Michael Jackson", "artistes_connexes": ["Michael Jackson", "Bruno Mars", "Prince", "Stevie Wonder", "Justin Timberlake"], "track_reel": False},
    {"slug": "prince-remixes-funk-electronique", "sujet": "l'influence de Prince sur les remixes funk électroniques", "artistes_connexes": ["Prince", "Michael Jackson", "Stevie Wonder", "Rick James", "Chic"], "track_reel": False},
    {"slug": "stevie-wonder-remixes-soul-house", "sujet": "les remixes soul house dans l'univers de Stevie Wonder", "artistes_connexes": ["Stevie Wonder", "Marvin Gaye", "Al Green", "Curtis Mayfield", "Sade"], "track_reel": False},
    {"slug": "bruno-mars-silk-sonic-remixes", "sujet": "les remixes funk house dans l'univers de Bruno Mars et Silk Sonic", "artistes_connexes": ["Bruno Mars", "Anderson .Paak", "Mark Ronson", "Dua Lipa", "The Weeknd"], "track_reel": False},
    {"slug": "james-brown-funk-electronique-remix", "sujet": "l'influence de James Brown sur les remixes électroniques et house", "artistes_connexes": ["James Brown", "Bootsy Collins", "George Clinton", "Rick James", "Chic"], "track_reel": False},

    # === FRENCH TOUCH ===
    {"slug": "french-touch-remixes-daft-punk-influence", "sujet": "la French Touch et l'influence de Daft Punk sur les remixes électroniques", "artistes_connexes": ["Daft Punk", "Cassius", "Modjo", "Stardust", "Kavinsky"], "track_reel": False},
    {"slug": "daft-punk-remixes-heritage-electronique", "sujet": "l'héritage de Daft Punk dans les remixes électroniques français", "artistes_connexes": ["Daft Punk", "Justice", "Gesaffelstein", "SebastiAn", "Étienne de Crécy"], "track_reel": False},
    {"slug": "justice-remixes-electro-rock", "sujet": "l'influence de Justice sur les remixes électro rock français", "artistes_connexes": ["Justice", "Daft Punk", "Kavinsky", "SebastiAn", "Gesaffelstein"], "track_reel": False},
    {"slug": "modjo-lady-french-touch-histoire", "sujet": "l'histoire de Lady de Modjo et la French Touch", "artistes_connexes": ["Modjo", "Daft Punk", "Cassius", "Stardust", "Bob Sinclar"], "track_reel": False},
    {"slug": "bob-sinclar-house-music-france", "sujet": "Bob Sinclar et la house music française", "artistes_connexes": ["Bob Sinclar", "David Guetta", "Martin Solveig", "Dimitri from Paris", "Joachim Garraud"], "track_reel": False},

    # === HOUSE MUSIC ===
    {"slug": "house-music-francaise-histoire", "sujet": "l'histoire de la house music française", "artistes_connexes": ["Daft Punk", "Bob Sinclar", "Martin Solveig", "Cassius", "David Guetta"], "track_reel": False},
    {"slug": "deep-house-remixes-france", "sujet": "le deep house et les remixes en France", "artistes_connexes": ["Disclosure", "Jamie xx", "Nicolas Jaar", "Four Tet", "Shlomo"], "track_reel": False},
    {"slug": "disco-house-remixes-classics", "sujet": "les remixes disco house de classiques musicaux", "artistes_connexes": ["Chic", "Donna Summer", "Gloria Gaynor", "ABBA", "Earth Wind & Fire"], "track_reel": False},
    {"slug": "remixes-house-dancefloor-2026", "sujet": "les meilleurs remixes house pour le dancefloor en 2026", "artistes_connexes": ["Fisher", "Chris Lake", "John Summit", "Peggy Gou", "Fred again.."], "track_reel": False},
    {"slug": "house-music-remix-achat-bandcamp", "sujet": "où acheter des remixes house de qualité sur Bandcamp", "artistes_connexes": ["Daft Punk", "Bob Sinclar", "Modjo", "Cassius", "Étienne de Crécy"], "track_reel": False},

    # === SADE UNIVERSE ===
    {"slug": "sade-remixes-deep-house-soul", "sujet": "l'univers de Sade et les remixes deep house soul", "artistes_connexes": ["Sade", "Erykah Badu", "D'Angelo", "Maxwell", "Jhené Aiko"], "track_reel": False},
    {"slug": "soul-electronique-remixes-modernes", "sujet": "les remixes soul électronique modernes", "artistes_connexes": ["Sade", "Frank Ocean", "SZA", "H.E.R.", "Jhené Aiko"], "track_reel": False},
    {"slug": "amy-winehouse-remixes-soul-house", "sujet": "l'influence d'Amy Winehouse sur les remixes soul house", "artistes_connexes": ["Amy Winehouse", "Sade", "Erykah Badu", "Lauryn Hill", "Alicia Keys"], "track_reel": False},

    # === POP ÉLECTRONIQUE ===
    {"slug": "remix-pop-electronique-achat", "sujet": "comment acheter des remixes pop électroniques de qualité", "artistes_connexes": ["Madonna", "Lady Gaga", "Dua Lipa", "Kylie Minogue", "Robyn"], "track_reel": False},
    {"slug": "dua-lipa-remixes-disco-house", "sujet": "les remixes disco house dans l'univers de Dua Lipa", "artistes_connexes": ["Dua Lipa", "Kylie Minogue", "Donna Summer", "Gloria Gaynor", "Nile Rodgers"], "track_reel": False},
    {"slug": "beyonce-remixes-house-electronique", "sujet": "les remixes house électronique dans l'univers de Beyoncé", "artistes_connexes": ["Beyoncé", "Rihanna", "Solange", "FKA twigs", "Grace Jones"], "track_reel": False},
    {"slug": "rihanna-remixes-dance-electronique", "sujet": "les remixes dance électronique inspirés de Rihanna", "artistes_connexes": ["Rihanna", "Beyoncé", "Jennifer Lopez", "Nicki Minaj", "Cardi B"], "track_reel": False},
    {"slug": "robyn-dance-alone-remixes-house", "sujet": "l'influence de Robyn sur les remixes house et dance", "artistes_connexes": ["Robyn", "Kylie Minogue", "Dua Lipa", "Christine and the Queens", "Years & Years"], "track_reel": False},

    # === ROCK ÉLECTRONIQUE ===
    {"slug": "remix-electronique-rock-classiques", "sujet": "les remixes électroniques de classiques rock", "artistes_connexes": ["The Eagles", "Fleetwood Mac", "The Doors", "Led Zeppelin", "Pink Floyd"], "track_reel": False},
    {"slug": "tame-impala-remixes-psychedelique-electronique", "sujet": "l'influence de Tame Impala sur les remixes psychédéliques électroniques", "artistes_connexes": ["Tame Impala", "MGMT", "The Flaming Lips", "Pond", "Washed Out"], "track_reel": False},
    {"slug": "fleetwood-mac-remixes-house", "sujet": "les remixes house de Fleetwood Mac et la nostalgie électronique", "artistes_connexes": ["Fleetwood Mac", "The Eagles", "Stevie Nicks", "Christine McVie", "ABBA"], "track_reel": False},

    # === CHANSON FRANÇAISE ÉLECTRONIQUE ===
    {"slug": "chanson-francaise-remixes-electroniques", "sujet": "les remixes électroniques de chansons françaises", "artistes_connexes": ["Nana Mouskouri", "Édith Piaf", "Dalida", "Charles Aznavour", "Jacques Brel"], "track_reel": False},
    {"slug": "dalida-remixes-disco-house", "sujet": "l'univers de Dalida et les remixes disco house", "artistes_connexes": ["Dalida", "Nana Mouskouri", "Mireille Mathieu", "Édith Piaf", "Sylvie Vartan"], "track_reel": False},
    {"slug": "edith-piaf-remixes-electroniques-modernes", "sujet": "les remixes électroniques modernes d'Édith Piaf", "artistes_connexes": ["Édith Piaf", "Charles Aznavour", "Jacques Brel", "Dalida", "Serge Gainsbourg"], "track_reel": False},
    {"slug": "serge-gainsbourg-remixes-house", "sujet": "l'influence de Serge Gainsbourg sur les remixes house français", "artistes_connexes": ["Serge Gainsbourg", "Jane Birkin", "Charlotte Gainsbourg", "Air", "Phoenix"], "track_reel": False},
    {"slug": "air-remixes-electronique-francais", "sujet": "l'influence d'Air sur la musique électronique française", "artistes_connexes": ["Air", "Phoenix", "Daft Punk", "Cassius", "Modjo"], "track_reel": False},

    # === ACHETER DES REMIXES ===
    {"slug": "acheter-remixes-electroniques-france", "sujet": "où acheter des remixes électroniques français de qualité", "artistes_connexes": ["Daft Punk", "Bob Sinclar", "Justice", "Cassius", "Kavinsky"], "track_reel": False},
    {"slug": "vincent-bastille-bandcamp", "sujet": "Vincent Bastille sur Bandcamp — remixes et discographie complète", "artistes_connexes": ["Daft Punk", "Justice", "Modjo", "Cassius", "Bob Sinclar"], "track_reel": False},
    {"slug": "telecharger-remixes-electroniques-legalement", "sujet": "télécharger légalement des remixes électroniques de qualité", "artistes_connexes": ["Daft Punk", "Justice", "Bob Sinclar", "Modjo", "Cassius"], "track_reel": False},
    {"slug": "remixes-electroniques-flac-qualite", "sujet": "acheter des remixes électroniques en qualité FLAC", "artistes_connexes": ["Daft Punk", "Justice", "Gesaffelstein", "SebastiAn", "Kavinsky"], "track_reel": False},
    {"slug": "meilleurs-remixes-electroniques-2026", "sujet": "les meilleurs remixes électroniques de 2026", "artistes_connexes": ["Fred again..", "Four Tet", "Peggy Gou", "Skrillex", "Diplo"], "track_reel": False},

    # === LE MANS / LOCAL ===
    {"slug": "musique-electronique-le-mans", "sujet": "la scène musique électronique au Mans", "artistes_connexes": ["Vincent Bastille", "Daft Punk", "Laurent Garnier", "Bob Sinclar", "Cassius"], "track_reel": False},
    {"slug": "producteur-musique-electronique-le-mans", "sujet": "producteur de musique électronique au Mans — Vincent Bastille", "artistes_connexes": ["Daft Punk", "Justice", "Cassius", "Kavinsky", "SebastiAn"], "track_reel": False},

    # === GENRES SPÉCIFIQUES ===
    {"slug": "techno-house-remixes-france", "sujet": "les remixes techno house français", "artistes_connexes": ["Laurent Garnier", "Gesaffelstein", "Vitalic", "Miss Kittin", "Agoria"], "track_reel": False},
    {"slug": "ambient-electronique-remixes", "sujet": "les remixes électroniques ambient et atmosphériques", "artistes_connexes": ["Brian Eno", "Aphex Twin", "The Orb", "Moby", "Bonobo"], "track_reel": False},
    {"slug": "nu-disco-remixes-france", "sujet": "le nu-disco et les remixes modernes en France", "artistes_connexes": ["Daft Punk", "Chilly Gonzales", "Yuksek", "Zimmer", "Para One"], "track_reel": False},
    {"slug": "electro-pop-remixes-achat-digital", "sujet": "acheter des remixes electro pop en digital", "artistes_connexes": ["Dua Lipa", "Charli XCX", "Kylie Minogue", "Robyn", "Years & Years"], "track_reel": False},
    {"slug": "downtempo-remixes-electroniques", "sujet": "les remixes downtempo et chill électroniques", "artistes_connexes": ["Portishead", "Massive Attack", "Tricky", "Bonobo", "Nicolas Jaar"], "track_reel": False},

    # === ARTISTES CONNEXES SUPPLÉMENTAIRES ===
    {"slug": "the-weeknd-remixes-synthwave", "sujet": "les remixes synthwave dans l'univers de The Weeknd", "artistes_connexes": ["The Weeknd", "Daft Punk", "Giorgio Moroder", "Kavinsky", "Chromatics"], "track_reel": False},
    {"slug": "taylor-swift-remixes-electroniques", "sujet": "les remixes électroniques de Taylor Swift", "artistes_connexes": ["Taylor Swift", "Sabrina Carpenter", "Olivia Rodrigo", "Ariana Grande", "Billie Eilish"], "track_reel": False},
    {"slug": "ariana-grande-remixes-house", "sujet": "les remixes house dans l'univers d'Ariana Grande", "artistes_connexes": ["Ariana Grande", "Dua Lipa", "Lady Gaga", "Mariah Carey", "Whitney Houston"], "track_reel": False},
    {"slug": "whitney-houston-remixes-soul-house", "sujet": "les remixes soul house de Whitney Houston", "artistes_connexes": ["Whitney Houston", "Mariah Carey", "Celine Dion", "Toni Braxton", "Sade"], "track_reel": False},
    {"slug": "mariah-carey-remixes-electroniques", "sujet": "les remixes électroniques de Mariah Carey", "artistes_connexes": ["Mariah Carey", "Whitney Houston", "Ariana Grande", "Lady Gaga", "Beyoncé"], "track_reel": False},
    {"slug": "celine-dion-remixes-house-dance", "sujet": "les remixes house dance de Céline Dion", "artistes_connexes": ["Céline Dion", "Whitney Houston", "Mariah Carey", "Nana Mouskouri", "Lara Fabian"], "track_reel": False},
    {"slug": "adele-remixes-deep-house", "sujet": "les remixes deep house d'Adele", "artistes_connexes": ["Adele", "Amy Winehouse", "Sade", "Duffy", "Lana Del Rey"], "track_reel": False},
    {"slug": "lana-del-rey-remixes-dream-pop", "sujet": "les remixes dream pop électroniques de Lana Del Rey", "artistes_connexes": ["Lana Del Rey", "Lorde", "Billie Eilish", "Mazzy Star", "Beach House"], "track_reel": False},
    {"slug": "billie-eilish-remixes-electroniques", "sujet": "les remixes électroniques de Billie Eilish", "artistes_connexes": ["Billie Eilish", "Lana Del Rey", "Lorde", "Halsey", "Phoebe Bridgers"], "track_reel": False},
    {"slug": "prince-funk-remixes-electroniques", "sujet": "l'héritage de Prince dans les remixes funk électroniques", "artistes_connexes": ["Prince", "Michael Jackson", "Rick James", "Morris Day", "Sheila E."], "track_reel": False},
    {"slug": "disco-electronique-remixes-classics", "sujet": "les remixes électroniques de classiques disco", "artistes_connexes": ["Donna Summer", "Gloria Gaynor", "Chic", "Nile Rodgers", "Earth Wind & Fire"], "track_reel": False},
    {"slug": "donna-summer-remixes-house", "sujet": "l'héritage de Donna Summer dans les remixes house modernes", "artistes_connexes": ["Donna Summer", "Gloria Gaynor", "Diana Ross", "Grace Jones", "Thelma Houston"], "track_reel": False},
    {"slug": "abba-remixes-house-electronique", "sujet": "les remixes house électronique d'ABBA", "artistes_connexes": ["ABBA", "Kylie Minogue", "Dua Lipa", "Years & Years", "Scissor Sisters"], "track_reel": False},
    {"slug": "david-bowie-remixes-electroniques", "sujet": "l'influence de David Bowie sur les remixes électroniques", "artistes_connexes": ["David Bowie", "Brian Eno", "Giorgio Moroder", "Iggy Pop", "Roxy Music"], "track_reel": False},
    {"slug": "giorgio-moroder-synthwave-remixes", "sujet": "l'influence de Giorgio Moroder sur les remixes synthwave", "artistes_connexes": ["Giorgio Moroder", "Daft Punk", "Kavinsky", "The Weeknd", "Chromatics"], "track_reel": False},
    {"slug": "kraftwerk-influence-electronique-france", "sujet": "l'influence de Kraftwerk sur la musique électronique française", "artistes_connexes": ["Kraftwerk", "Daft Punk", "Jean-Michel Jarre", "Air", "Cassius"], "track_reel": False},
    {"slug": "jean-michel-jarre-remixes-electroniques", "sujet": "l'héritage de Jean-Michel Jarre dans l'électronique française", "artistes_connexes": ["Jean-Michel Jarre", "Kraftwerk", "Brian Eno", "Tangerine Dream", "Klaus Schulze"], "track_reel": False},
    {"slug": "disclosure-remixes-uk-house", "sujet": "l'influence de Disclosure sur la UK house et les remixes", "artistes_connexes": ["Disclosure", "Jamie xx", "Shlomo", "AlunaGeorge", "Sam Smith"], "track_reel": False},
    {"slug": "four-tet-remixes-electroniques-experimentaux", "sujet": "l'influence de Four Tet sur les remixes électroniques expérimentaux", "artistes_connexes": ["Four Tet", "Caribou", "Bonobo", "Nicolas Jaar", "Burial"], "track_reel": False},
    {"slug": "burial-remixes-dark-electronic", "sujet": "l'influence de Burial sur les remixes électroniques atmosphériques", "artistes_connexes": ["Burial", "Massive Attack", "Portishead", "The XX", "James Blake"], "track_reel": False},
    {"slug": "james-blake-remixes-soul-electronique", "sujet": "l'influence de James Blake sur les remixes soul électronique", "artistes_connexes": ["James Blake", "Frank Ocean", "Bon Iver", "Sade", "Nicolas Jaar"], "track_reel": False},
    {"slug": "frank-ocean-remixes-rnb-electronique", "sujet": "les remixes R&B électronique dans l'univers de Frank Ocean", "artistes_connexes": ["Frank Ocean", "James Blake", "SZA", "The Weeknd", "Daniel Caesar"], "track_reel": False},
    {"slug": "sza-remixes-rnb-house", "sujet": "les remixes R&B house dans l'univers de SZA", "artistes_connexes": ["SZA", "Solange", "Erykah Badu", "FKA twigs", "Kelela"], "track_reel": False},
    {"slug": "kendrick-lamar-remixes-electroniques", "sujet": "les remixes électroniques dans l'univers de Kendrick Lamar", "artistes_connexes": ["Kendrick Lamar", "J. Cole", "Flying Lotus", "Thundercat", "Kamasi Washington"], "track_reel": False},
    {"slug": "flying-lotus-electronique-jazz-remixes", "sujet": "l'influence de Flying Lotus sur les remixes jazz électroniques", "artistes_connexes": ["Flying Lotus", "Thundercat", "Kamasi Washington", "Herbie Hancock", "Miles Davis"], "track_reel": False},
    {"slug": "herbie-hancock-jazz-electronique-remixes", "sujet": "l'héritage de Herbie Hancock dans les remixes jazz électroniques", "artistes_connexes": ["Herbie Hancock", "Miles Davis", "Chick Corea", "Quincy Jones", "Roy Ayers"], "track_reel": False},
    {"slug": "quincy-jones-remixes-funk-electronique", "sujet": "l'influence de Quincy Jones sur les remixes funk électronique", "artistes_connexes": ["Quincy Jones", "Michael Jackson", "James Ingram", "Patti Austin", "Siedah Garrett"], "track_reel": False},
    {"slug": "nile-rodgers-chic-remixes-disco", "sujet": "l'influence de Nile Rodgers et Chic sur les remixes disco house", "artistes_connexes": ["Nile Rodgers", "Chic", "Daft Punk", "Madonna", "David Bowie"], "track_reel": False},
    {"slug": "earth-wind-fire-remixes-electroniques", "sujet": "les remixes électroniques dans l'univers d'Earth Wind & Fire", "artistes_connexes": ["Earth Wind & Fire", "James Brown", "Stevie Wonder", "Chic", "Kool & the Gang"], "track_reel": False},
    {"slug": "portishead-trip-hop-remixes", "sujet": "l'influence de Portishead sur les remixes trip-hop électroniques", "artistes_connexes": ["Portishead", "Massive Attack", "Tricky", "Lamb", "Sneaker Pimps"], "track_reel": False},
    {"slug": "massive-attack-remixes-electroniques", "sujet": "l'influence de Massive Attack sur les remixes électroniques", "artistes_connexes": ["Massive Attack", "Portishead", "Tricky", "Burial", "Archive"], "track_reel": False},
    {"slug": "aphex-twin-remixes-experimentaux", "sujet": "l'influence d'Aphex Twin sur les remixes électroniques expérimentaux", "artistes_connexes": ["Aphex Twin", "Boards of Canada", "Autechre", "Squarepusher", "Four Tet"], "track_reel": False},
    {"slug": "boards-of-canada-remixes-ambient", "sujet": "l'influence de Boards of Canada sur les remixes ambient", "artistes_connexes": ["Boards of Canada", "Aphex Twin", "Bibio", "Tycho", "Com Truise"], "track_reel": False},
    {"slug": "bonobo-remixes-downtempo", "sujet": "l'influence de Bonobo sur les remixes downtempo", "artistes_connexes": ["Bonobo", "Caribou", "Four Tet", "Floating Points", "Catching Flies"], "track_reel": False},
    {"slug": "nicolas-jaar-remixes-dark-house", "sujet": "l'influence de Nicolas Jaar sur les remixes dark house", "artistes_connexes": ["Nicolas Jaar", "Four Tet", "Burial", "James Blake", "Objekt"], "track_reel": False},
    {"slug": "peggy-gou-remixes-house-berlin", "sujet": "l'influence de Peggy Gou sur la house berlinoise et les remixes", "artistes_connexes": ["Peggy Gou", "DJ Koze", "Âme", "Dixon", "Henrik Schwarz"], "track_reel": False},
    {"slug": "fred-again-remixes-uk-house", "sujet": "l'influence de Fred again.. sur les remixes UK house modernes", "artistes_connexes": ["Fred again..", "Four Tet", "Skrillex", "Romy", "Barry Can't Swim"], "track_reel": False},
    {"slug": "skrillex-remixes-electroniques", "sujet": "l'influence de Skrillex sur les remixes électroniques modernes", "artistes_connexes": ["Skrillex", "Diplo", "Zedd", "Marshmello", "Flume"], "track_reel": False},
    {"slug": "flume-remixes-future-bass", "sujet": "l'influence de Flume sur les remixes future bass", "artistes_connexes": ["Flume", "Odesza", "Lane 8", "Petit Biscuit", "Kaytranada"], "track_reel": False},
    {"slug": "kaytranada-remixes-dance-electronique", "sujet": "l'influence de Kaytranada sur les remixes dance électronique", "artistes_connexes": ["Kaytranada", "Jessie Ware", "Solange", "Pharrell", "Anderson .Paak"], "track_reel": False},
    {"slug": "jessie-ware-remixes-dance-pop", "sujet": "les remixes dance pop dans l'univers de Jessie Ware", "artistes_connexes": ["Jessie Ware", "Kylie Minogue", "Dua Lipa", "MNEK", "Sade"], "track_reel": False},
    {"slug": "years-years-olly-remixes-synthpop", "sujet": "les remixes synthpop dans l'univers de Years & Years", "artistes_connexes": ["Years & Years", "Troye Sivan", "Kim Petras", "Sam Smith", "Kylie Minogue"], "track_reel": False},
    {"slug": "troye-sivan-remixes-pop-electronique", "sujet": "les remixes pop électronique de Troye Sivan", "artistes_connexes": ["Troye Sivan", "Charli XCX", "Years & Years", "Kim Petras", "Rina Sawayama"], "track_reel": False},
    {"slug": "christine-queens-remixes-electro-pop", "sujet": "l'influence de Christine and the Queens sur l'electro pop", "artistes_connexes": ["Christine and the Queens", "Stromae", "Indochine", "Étienne Daho", "Alain Bashung"], "track_reel": False},
    {"slug": "stromae-remixes-electronique-belge", "sujet": "l'influence de Stromae sur la musique électronique francophone", "artistes_connexes": ["Stromae", "Angèle", "Roméo Elvis", "Calogero", "Yelle"], "track_reel": False},
    {"slug": "angele-remixes-pop-electronique-belge", "sujet": "les remixes pop électronique dans l'univers d'Angèle", "artistes_connexes": ["Angèle", "Stromae", "Pomme", "Clara Luciani", "Zaho de Sagazan"], "track_reel": False},
    {"slug": "clara-luciani-remixes-pop-francaise", "sujet": "les remixes pop française dans l'univers de Clara Luciani", "artistes_connexes": ["Clara Luciani", "Angèle", "Pomme", "Zaho de Sagazan", "Barbara Pravi"], "track_reel": False},
    {"slug": "yuksek-remixes-nu-disco", "sujet": "l'influence de Yuksek sur les remixes nu-disco français", "artistes_connexes": ["Yuksek", "Zimmer", "Para One", "Cassius", "Etienne de Crecy"], "track_reel": False},
    {"slug": "kavinsky-remixes-synthwave-france", "sujet": "l'influence de Kavinsky sur les remixes synthwave français", "artistes_connexes": ["Kavinsky", "Perturbator", "Carpenter Brut", "Gesaffelstein", "Justice"], "track_reel": False},
    {"slug": "gesaffelstein-remixes-techno-industrie", "sujet": "l'influence de Gesaffelstein sur les remixes techno industriels", "artistes_connexes": ["Gesaffelstein", "Kanye West", "The Weeknd", "Daft Punk", "Justice"], "track_reel": False},
    {"slug": "vitalic-remixes-electro-hard", "sujet": "l'influence de Vitalic sur l'electro hard française", "artistes_connexes": ["Vitalic", "Gesaffelstein", "Laurent Garnier", "Miss Kittin", "Agoria"], "track_reel": False},
    {"slug": "laurent-garnier-techno-france", "sujet": "l'héritage de Laurent Garnier dans la techno française", "artistes_connexes": ["Laurent Garnier", "Daft Punk", "Étienne de Crécy", "Aphex Twin", "Richie Hawtin"], "track_reel": False},
    {"slug": "richie-hawtin-techno-remixes", "sujet": "l'influence de Richie Hawtin sur les remixes techno minimaux", "artistes_connexes": ["Richie Hawtin", "Robert Hood", "Surgeon", "Jeff Mills", "Carl Craig"], "track_reel": False},
    {"slug": "carl-craig-detroit-techno-remixes", "sujet": "l'influence de la Detroit Techno sur les remixes électroniques", "artistes_connexes": ["Carl Craig", "Derrick May", "Juan Atkins", "Kevin Saunderson", "Jeff Mills"], "track_reel": False},

    # === PAGES GÉNÉRALES SEO ===
    {"slug": "vincent-bastille-remixes", "sujet": "les remixes de Vincent Bastille — producteur électronique du Mans", "artistes_connexes": ["Daft Punk", "Bob Sinclar", "Justice", "Modjo", "Cassius"], "track_reel": False},
    {"slug": "remixes-house-music-france", "sujet": "la house music française — histoire et meilleurs remixes", "artistes_connexes": ["Daft Punk", "Bob Sinclar", "David Guetta", "Martin Solveig", "Cassius"], "track_reel": False},
    {"slug": "dj-vincent-bastille-mix", "sujet": "Vincent Bastille DJ — mix et sets électroniques", "artistes_connexes": ["Laurent Garnier", "Gesaffelstein", "Bob Sinclar", "David Guetta", "Étienne de Crécy"], "track_reel": False},
    {"slug": "vincent-bastille-deep-house", "sujet": "Vincent Bastille et le deep house — discographie et remixes", "artistes_connexes": ["Disclosure", "Jamie xx", "Four Tet", "Nicolas Jaar", "Bonobo"], "track_reel": False},
    {"slug": "remixes-electroniques-francais-achat", "sujet": "acheter des remixes électroniques français en ligne", "artistes_connexes": ["Daft Punk", "Bob Sinclar", "Justice", "Kavinsky", "Modjo"], "track_reel": False},
    {"slug": "remix-disco-house-france", "sujet": "le disco house français — histoire et remixes modernes", "artistes_connexes": ["Daft Punk", "Stardust", "Modjo", "Cassius", "Nile Rodgers"], "track_reel": False},
    {"slug": "musique-electronique-francaise-2026", "sujet": "la musique électronique française en 2026", "artistes_connexes": ["Daft Punk", "Justice", "Gesaffelstein", "Kavinsky", "Fred again.."], "track_reel": False},
    {"slug": "beatport-remix-challenge-gagnants", "sujet": "les meilleurs remixes du Beatport Remix Challenge", "artistes_connexes": ["Madonna", "David Guetta", "Martin Garrix", "Tiësto", "Kygo"], "track_reel": False},
    {"slug": "remix-competition-electronique", "sujet": "les compétitions de remix électronique — comment participer", "artistes_connexes": ["Daft Punk", "Justice", "David Guetta", "Calvin Harris", "Avicii"], "track_reel": False},
    {"slug": "musique-electronique-le-mans-scene", "sujet": "la scène musicale électronique au Mans et dans les Pays de la Loire", "artistes_connexes": ["Daft Punk", "Bob Sinclar", "Cassius", "Justice", "Laurent Garnier"], "track_reel": False},
    {"slug": "telecharger-musique-electronique-bandcamp", "sujet": "télécharger de la musique électronique sur Bandcamp", "artistes_connexes": ["Daft Punk", "Modjo", "Bob Sinclar", "Justice", "Kavinsky"], "track_reel": False},
    {"slug": "remixes-classics-electronique-2026", "sujet": "les remixes de classiques musicaux en version électronique 2026", "artistes_connexes": ["Daft Punk", "Bob Sinclar", "Justice", "Modjo", "Cassius"], "track_reel": False},
    {"slug": "house-music-classics-remixes-france", "sujet": "les remixes house music de classiques en France", "artistes_connexes": ["Daft Punk", "Bob Sinclar", "Stardust", "Cassius", "Modjo"], "track_reel": False},
    {"slug": "electro-house-france-remixes-achat", "sujet": "acheter des remixes electro house français", "artistes_connexes": ["David Guetta", "Bob Sinclar", "Martin Solveig", "DJ Snake", "Kungs"], "track_reel": False},
    {"slug": "remix-progressive-house-2026", "sujet": "les meilleurs remixes progressive house de 2026", "artistes_connexes": ["Eric Prydz", "Deadmau5", "Knife Party", "Feed Me", "Wolfgang Gartner"], "track_reel": False},
    {"slug": "remixes-vintage-pop-electronique", "sujet": "les remixes vintage pop en version électronique", "artistes_connexes": ["ABBA", "Donna Summer", "Boney M.", "Village People", "Gloria Gaynor"], "track_reel": False},
    {"slug": "boney-m-remixes-disco-electronique", "sujet": "les remixes disco électronique de Boney M.", "artistes_connexes": ["Boney M.", "ABBA", "Gloria Gaynor", "Donna Summer", "Village People"], "track_reel": False},
    {"slug": "remixes-pop-90s-electronique", "sujet": "les remixes électroniques des tubes pop des années 90", "artistes_connexes": ["Spice Girls", "Backstreet Boys", "Destiny's Child", "TLC", "En Vogue"], "track_reel": False},
    {"slug": "spice-girls-remixes-house-dance", "sujet": "les remixes house dance dans l'univers des Spice Girls", "artistes_connexes": ["Spice Girls", "Kylie Minogue", "Robyn", "Steps", "S Club 7"], "track_reel": False},
    {"slug": "remixes-pop-2000s-electronique", "sujet": "les remixes électroniques des tubes pop des années 2000", "artistes_connexes": ["Britney Spears", "Beyoncé", "Christina Aguilera", "Pink", "Kelly Clarkson"], "track_reel": False},
    {"slug": "britney-spears-remixes-dance-electronique", "sujet": "les remixes dance électronique de Britney Spears", "artistes_connexes": ["Britney Spears", "Christina Aguilera", "Pink", "Kylie Minogue", "Fergie"], "track_reel": False},
    {"slug": "remix-hip-hop-electronique-france", "sujet": "les remixes hip-hop électroniques en France", "artistes_connexes": ["Kanye West", "Jay-Z", "Pharrell Williams", "Timbaland", "Missy Elliott"], "track_reel": False},
    {"slug": "pharrell-remixes-funk-electronique", "sujet": "l'influence de Pharrell Williams sur les remixes funk électronique", "artistes_connexes": ["Pharrell Williams", "Daft Punk", "N.E.R.D.", "Jay-Z", "Kendrick Lamar"], "track_reel": False},
    {"slug": "remixes-new-wave-electronique", "sujet": "les remixes électroniques de la new wave des années 80", "artistes_connexes": ["Depeche Mode", "New Order", "The Cure", "Joy Division", "Tears for Fears"], "track_reel": False},
    {"slug": "depeche-mode-remixes-electroniques", "sujet": "l'influence de Depeche Mode sur les remixes électroniques modernes", "artistes_connexes": ["Depeche Mode", "New Order", "The Cure", "Bauhaus", "Sisters of Mercy"], "track_reel": False},
    {"slug": "new-order-blue-monday-remixes", "sujet": "l'influence de Blue Monday de New Order sur les remixes électroniques", "artistes_connexes": ["New Order", "Joy Division", "Pet Shop Boys", "OMD", "Yazoo"], "track_reel": False},
    {"slug": "pet-shop-boys-remixes-synth-pop", "sujet": "l'influence des Pet Shop Boys sur les remixes synth-pop", "artistes_connexes": ["Pet Shop Boys", "Erasure", "Yazoo", "OMD", "Soft Cell"], "track_reel": False},
    {"slug": "erasure-remixes-eurodance-electronique", "sujet": "l'influence d'Erasure sur les remixes eurodance électroniques", "artistes_connexes": ["Erasure", "Pet Shop Boys", "Yazoo", "Human League", "Soft Cell"], "track_reel": False},
    {"slug": "eurodance-remixes-electroniques-90s", "sujet": "les remixes eurodance des années 90 en version moderne", "artistes_connexes": ["Aqua", "Haddaway", "Dr. Alban", "2 Unlimited", "Ace of Base"], "track_reel": False},
]

# ─────────────────────────────────────────
# LIENS INTERNES (maillage 10+)
# ─────────────────────────────────────────
def get_internal_links(current_slug):
    """Retourne 10 liens internes vers d'autres pages"""
    other_slugs = [t["slug"] for t in TOPICS if t["slug"] != current_slug]
    selected = random.sample(other_slugs, min(10, len(other_slugs)))
    links = []
    for slug in selected:
        label = slug.replace("-", " ").title()
        links.append({"url": f"{BASE_URL}/seo-pages/{slug}.html", "label": label})
    # Toujours ajouter Bandcamp en premier
    links.insert(0, {"url": BANDCAMP_URL, "label": "🎵 Écouter et acheter sur Bandcamp", "external": True})
    return links

# ─────────────────────────────────────────
# GÉNÉRATION IA
# ─────────────────────────────────────────
def generate_content(sujet, artistes_connexes, track_reel=False):
    print(f"\n📡 Génération : {sujet[:60]}...")

    artistes_str = ", ".join(artistes_connexes)

    if track_reel:
        context = f"""Il s'agit d'un vrai remix de Vincent Bastille disponible sur Bandcamp ({BANDCAMP_URL}).
Le remix est à vendre à 10€ l'album complet, disponible en téléchargement FLAC et MP3.
Vincent Bastille est basé au Mans, France. Il a participé au Beatport Remix Challenge avec son remix de Madonna Ray Of Light."""
    else:
        context = f"""Vincent Bastille est un producteur électronique du Mans, France.
Son album de remixes est disponible sur Bandcamp : {BANDCAMP_URL}
Il propose des remixes de Jennifer Lopez, Madonna (finaliste Beatport), Michael Jackson, Sade, Modjo, Calvin Harris, Bruno Mars, The Eagles, Nana Mouskouri."""

    prompt = f"""Tu es un expert SEO, critique musical et rédacteur web passionné de musique électronique.
Génère le contenu d'une page SEO ultra-riche sur : {sujet}

Contexte : {context}

Artistes connexes à mentionner naturellement : {artistes_str}

Retourne UNIQUEMENT un JSON valide (pas de markdown, pas de backticks) :
{{
  "title": "...(55-60 chars, accrocheur, inclut le sujet principal)...",
  "meta_description": "...(145-155 chars, bénéfice clair, donne envie de cliquer)...",
  "h1": "...(percutant, différent du title)...",
  "intro": "...(250 mots minimum, accrocheur, passionné, parle d'émotions musicales, mentionne naturellement les artistes connexes et Vincent Bastille)...",
  "section1_h2": "...",
  "section1_body": "...(250 mots, contenu riche sur le genre musical, compare les artistes, analyse musicale)...",
  "section2_h2": "...",
  "section2_body": "...(250 mots, parle de l'influence sur la musique électronique, du dancefloor, des émotions)...",
  "section3_h2": "...",
  "section3_body": "...(200 mots, call to action naturel vers l'achat du remix sur Bandcamp, parle de la qualité FLAC)...",
  "faq": [
    {{"q": "...", "a": "...(réponse complète de 2-3 phrases)..."}},
    {{"q": "...", "a": "...(réponse complète de 2-3 phrases)..."}},
    {{"q": "...", "a": "...(réponse complète de 2-3 phrases)..."}},
    {{"q": "...", "a": "...(réponse complète de 2-3 phrases)..."}}
  ]
}}

Règles ABSOLUES :
- Contenu 100% unique, passionné, humain — pas de style robotique
- Mentionner Vincent Bastille naturellement dans le texte
- Mentionner Bandcamp et le prix (10€ album, téléchargement FLAC/MP3)
- Faire des liens sémantiques entre les artistes (ex: "comme Daft Punk a influencé...", "dans la lignée de...")
- Pas de placeholder, pas de [brackets], contenu 100% prêt
- JSON strict : pas d'apostrophes dans les clés, pas de guillemets non échappés
"""

    payload = {
        "model": MODEL,
        "max_tokens": 2500,
        "temperature": 0.92,
        "messages": [{"role": "user", "content": prompt}],
    }

    try:
        r = requests.post(API_URL, headers={
            "Authorization": f"Bearer {TOGETHER_API_KEY}",
            "Content-Type": "application/json",
        }, json=payload, timeout=90)
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        print(f"❌ HTTP {r.status_code}: {r.text}")
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        print(f"❌ Réseau: {e}")
        sys.exit(1)

    print("✅ Réponse reçue")
    raw = r.json()["choices"][0]["message"]["content"].strip()

    # Nettoyage
    if "```" in raw:
        parts = raw.split("```")
        for part in parts:
            if part.strip().startswith("{") or part.strip().startswith("json\n{"):
                raw = part.strip()
                if raw.startswith("json"):
                    raw = raw[4:].strip()
                break

    raw = raw.strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
        raise

# ─────────────────────────────────────────
# BUILD HTML
# ─────────────────────────────────────────
def build_html(slug, sujet, artistes_connexes, content):
    today = date.today().isoformat()
    canonical = f"{BASE_URL}/seo-pages/{slug}.html"
    internal_links = get_internal_links(slug)

    faq_items = content.get("faq", [])
    faq_jsonld = json.dumps({
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": i["q"],
             "acceptedAnswer": {"@type": "Answer", "text": i["a"]}}
            for i in faq_items
        ]
    }, ensure_ascii=False, indent=2)

    faq_html = "\n".join(f"""
    <div class="faq-item">
      <h3>{i['q']}</h3>
      <p>{i['a']}</p>
    </div>""" for i in faq_items)

    # Liens internes HTML — Bandcamp en premier bien visible
    bandcamp_link = internal_links[0]
    other_links = internal_links[1:]

    other_links_html = "\n".join(
        f'<li><a href="{l["url"]}">{l["label"]}</a></li>'
        for l in other_links
    )

    artistes_tags = " ".join(
        f'<span class="tag">{a}</span>' for a in artistes_connexes
    )

    return f"""<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{content['title']}</title>
  <meta name="description" content="{content['meta_description']}">
  <link rel="canonical" href="{canonical}">
  <meta property="og:title" content="{content['title']}">
  <meta property="og:description" content="{content['meta_description']}">
  <meta property="og:url" content="{canonical}">
  <meta property="og:type" content="music.album">
  <meta property="og:image" content="https://f4.bcbits.com/img/a0541613845_10.jpg">
  <script type="application/ld+json">
{faq_jsonld}
  </script>
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "MusicAlbum",
    "name": "Vincent Bastille - Remixes (Legacy)",
    "byArtist": {{"@type": "MusicGroup", "name": "Vincent Bastille"}},
    "url": "{BANDCAMP_URL}",
    "genre": ["Electronic", "House", "Remix"],
    "datePublished": "2026-03-24"
  }}
  </script>
  <style>
    *{{box-sizing:border-box;margin:0;padding:0}}
    body{{font-family:'Segoe UI',system-ui,sans-serif;background:#080810;color:#e0e0f0;line-height:1.8;font-size:1.05rem}}
    header{{background:linear-gradient(160deg,#1a0040 0%,#0a0a2e 50%,#001a3a 100%);padding:4rem 2rem 3rem;text-align:center;position:relative;overflow:hidden;border-bottom:1px solid rgba(124,58,237,0.3)}}
    header::before{{content:'';position:absolute;top:-50%;left:-50%;width:200%;height:200%;background:radial-gradient(ellipse,rgba(124,58,237,0.15) 0%,transparent 60%);pointer-events:none}}
    header h1{{font-size:2.4rem;color:#fff;font-weight:800;margin-bottom:0.8rem;line-height:1.2;position:relative}}
    header .subtitle{{color:#a78bfa;font-size:1.1rem;position:relative}}
    nav{{background:#0d0d1a;padding:0.8rem 2rem;border-bottom:1px solid rgba(124,58,237,0.2);display:flex;flex-wrap:wrap;gap:0.5rem;justify-content:center}}
    nav a{{color:#a78bfa;text-decoration:none;padding:0.4rem 1rem;border-radius:20px;font-size:0.85rem;border:1px solid rgba(124,58,237,0.3);transition:all 0.2s}}
    nav a:hover{{background:rgba(124,58,237,0.2);color:#fff}}
    .container{{max-width:920px;margin:0 auto;padding:2.5rem 1.5rem}}
    .bandcamp-cta{{background:linear-gradient(135deg,#1db954 0%,#158f3e 100%);border-radius:16px;padding:2rem;text-align:center;margin:2rem 0;box-shadow:0 8px 32px rgba(29,185,84,0.3)}}
    .bandcamp-cta p{{color:#fff;margin-bottom:1rem;font-size:1.1rem}}
    .bandcamp-cta a{{display:inline-block;background:#fff;color:#1db954;font-weight:800;padding:1rem 2.5rem;border-radius:50px;text-decoration:none;font-size:1.1rem;transition:transform 0.2s;box-shadow:0 4px 15px rgba(0,0,0,0.2)}}
    .bandcamp-cta a:hover{{transform:scale(1.05)}}
    .bandcamp-cta .price{{color:rgba(255,255,255,0.85);font-size:0.9rem;margin-top:0.5rem}}
    .intro-box{{background:rgba(124,58,237,0.08);border:1px solid rgba(124,58,237,0.2);border-radius:16px;padding:2rem;margin:2rem 0}}
    h2{{font-size:1.7rem;color:#c4b5fd;margin:3rem 0 1rem;padding-left:1.2rem;border-left:4px solid #7c3aed;line-height:1.3}}
    h3{{font-size:1.15rem;color:#a78bfa;margin:1.5rem 0 0.5rem}}
    p{{color:#c8c8d8;margin-bottom:1.3rem}}
    .tags{{display:flex;flex-wrap:wrap;gap:0.5rem;margin:1.5rem 0}}
    .tag{{background:rgba(124,58,237,0.15);color:#a78bfa;padding:0.3rem 0.8rem;border-radius:20px;font-size:0.85rem;border:1px solid rgba(124,58,237,0.3)}}
    .faq-section{{margin:3rem 0}}
    .faq-item{{background:#0d0d1a;border:1px solid rgba(124,58,237,0.2);border-radius:12px;padding:1.5rem;margin:1rem 0;transition:border-color 0.2s}}
    .faq-item:hover{{border-color:rgba(124,58,237,0.5)}}
    .faq-item h3{{color:#c4b5fd;margin:0 0 0.5rem;font-size:1rem}}
    .faq-item p{{color:#a0a0b8;margin:0;font-size:0.95rem}}
    .internal-links{{background:#0d0d1a;border:1px solid rgba(124,58,237,0.2);border-radius:16px;padding:1.8rem;margin:2.5rem 0}}
    .internal-links h3{{color:#c4b5fd;margin-bottom:1rem;font-size:1rem}}
    .internal-links ul{{list-style:none;display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:0.6rem}}
    .internal-links a{{color:#a78bfa;text-decoration:none;font-size:0.85rem;padding:0.4rem 0.8rem;background:rgba(124,58,237,0.1);border-radius:8px;display:block;transition:background 0.2s;border:1px solid rgba(124,58,237,0.2)}}
    .internal-links a:hover{{background:rgba(124,58,237,0.25);color:#fff}}
    .tracks-list{{background:#0d0d1a;border:1px solid rgba(124,58,237,0.2);border-radius:16px;padding:1.8rem;margin:2rem 0}}
    .track-item{{display:flex;align-items:center;gap:1rem;padding:0.8rem 0;border-bottom:1px solid rgba(124,58,237,0.1)}}
    .track-item:last-child{{border-bottom:none}}
    .track-num{{color:#7c3aed;font-weight:700;min-width:2rem;font-size:1.1rem}}
    .track-info{{flex:1}}
    .track-title{{color:#e0e0f0;font-weight:600}}
    .track-artist{{color:#a78bfa;font-size:0.85rem}}
    footer{{background:#0d0d1a;border-top:1px solid rgba(124,58,237,0.2);padding:2rem;text-align:center;color:#666;font-size:0.9rem;margin-top:3rem}}
    footer a{{color:#a78bfa;text-decoration:none}}
    @media(max-width:600px){{header h1{{font-size:1.7rem}}.container{{padding:1.5rem 1rem}}.internal-links ul{{grid-template-columns:1fr}}}}
  </style>
</head>
<body>
  <header>
    <h1>🎵 {content['h1']}</h1>
    <p class="subtitle">Vincent Bastille — Remixes Électroniques — Le Mans, France</p>
  </header>

  <nav>
    <a href="{BASE_URL}/seo-pages/vincent-bastille-remixes.html">🎧 Tous les remixes</a>
    <a href="{BASE_URL}/seo-pages/remix-madonna-ray-of-light.html">Madonna</a>
    <a href="{BASE_URL}/seo-pages/remix-michael-jackson-you-rock-my-world.html">Michael Jackson</a>
    <a href="{BASE_URL}/seo-pages/remix-sade-smooth-operator.html">Sade</a>
    <a href="{BASE_URL}/seo-pages/french-touch-remixes-daft-punk-influence.html">French Touch</a>
    <a href="{BASE_URL}/seo-pages/house-music-francaise-histoire.html">House Music</a>
    <a href="{BANDCAMP_URL}" target="_blank">🛒 Bandcamp</a>
  </nav>

  <div class="container">

    <div class="bandcamp-cta">
      <p>🎵 Écouter et télécharger les remixes de Vincent Bastille</p>
      <a href="{BANDCAMP_URL}" target="_blank" rel="noopener">→ Acheter sur Bandcamp</a>
      <p class="price">Album complet : 10€ · MP3 + FLAC haute qualité · Streaming illimité</p>
    </div>

    <div class="intro-box">
      <p>{content['intro']}</p>
    </div>

    <div class="tags">{artistes_tags}</div>

    <h2>{content['section1_h2']}</h2>
    <p>{content['section1_body']}</p>

    <h2>{content['section2_h2']}</h2>
    <p>{content['section2_body']}</p>

    <div class="tracks-list">
      <h3>🎶 L'album Remixes (Legacy) — Tracklist complète</h3>
      <div class="track-item"><span class="track-num">1</span><div class="track-info"><div class="track-title">Can't Get Enough (Vincent Bastille Remix)</div><div class="track-artist">Jennifer Lopez</div></div></div>
      <div class="track-item"><span class="track-num">2</span><div class="track-info"><div class="track-title">Lady (Vincent Bastille Disco House Remix)</div><div class="track-artist">Modjo</div></div></div>
      <div class="track-item"><span class="track-num">3</span><div class="track-info"><div class="track-title">You Rock My World (Vincent Bastille Remix)</div><div class="track-artist">Michael Jackson</div></div></div>
      <div class="track-item"><span class="track-num">4</span><div class="track-info"><div class="track-title">Ray Of Light (Vincent Bastille Remix) ⭐ Beatport</div><div class="track-artist">Madonna</div></div></div>
      <div class="track-item"><span class="track-num">5</span><div class="track-info"><div class="track-title">Smooth Operator (Vincent Bastille Remix)</div><div class="track-artist">Sade</div></div></div>
      <div class="track-item"><span class="track-num">6</span><div class="track-info"><div class="track-title">Quand Tu Chantes (Vincent Bastille Remix)</div><div class="track-artist">Nana Mouskouri</div></div></div>
      <div class="track-item"><span class="track-num">7</span><div class="track-info"><div class="track-title">Hotel California (Vincent Bastille Remix)</div><div class="track-artist">The Eagles</div></div></div>
      <div class="track-item"><span class="track-num">8</span><div class="track-info"><div class="track-title">Promises (Vincent Bastille Remix)</div><div class="track-artist">Calvin Harris</div></div></div>
      <div class="track-item"><span class="track-num">9</span><div class="track-info"><div class="track-title">I Just Might (Vincent Bastille Remix)</div><div class="track-artist">Bruno Mars</div></div></div>
    </div>

    <h2>{content['section3_h2']}</h2>
    <p>{content['section3_body']}</p>

    <div class="internal-links">
      <h3>🔗 Explorer d'autres pages</h3>
      <ul>{other_links_html}</ul>
    </div>

    <div class="faq-section">
      <h2>❓ Questions fréquentes</h2>
      {faq_html}
    </div>

    <div class="bandcamp-cta">
      <p>🎵 Prêt à ajouter ces remixes à votre collection ?</p>
      <a href="{BANDCAMP_URL}" target="_blank" rel="noopener">→ Écouter et acheter sur Bandcamp</a>
      <p class="price">Vincent Bastille · Remixes (Legacy) · 10€ · FLAC + MP3</p>
    </div>

  </div>

  <footer>
    <p>© {today[:4]} Vincent Bastille — Musique Électronique Française |
    <a href="{BANDCAMP_URL}" target="_blank">Bandcamp</a> ·
    <a href="{BASE_URL}/seo-pages/vincent-bastille-remixes.html">Tous les remixes</a> ·
    <a href="https://vincentbastille.online" target="_blank">Site officiel</a></p>
  </footer>

</body>
</html>"""

# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    generated = []
    errors = []

    to_generate = TOPICS[:PAGES_PER_RUN]
    print(f"🚀 Génération de {len(to_generate)} pages...")

    for topic in to_generate:
        slug = topic["slug"]
        try:
            content = generate_content(
                topic["sujet"],
                topic["artistes_connexes"],
                topic.get("track_reel", False)
            )
            html = build_html(
                slug,
                topic["sujet"],
                topic["artistes_connexes"],
                content
            )
            filepath = os.path.join(OUTPUT_DIR, f"{slug}.html")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(html)
            print(f"✅ {filepath}")
            generated.append(slug)
        except Exception as e:
            print(f"❌ Erreur {slug}: {e}")
            errors.append(slug)
            continue

    print(f"\n🎉 {len(generated)}/{len(to_generate)} pages générées !")
    if errors:
        print(f"⚠️ Erreurs sur : {', '.join(errors)}")

if __name__ == "__main__":
    main()
