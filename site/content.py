# -*- coding: utf-8 -*-
"""Contenu structure du site The Rabbit Tree Hostel, repris du site Wix."""

HOSTEL = {
    "name": "The Rabbit Tree Hostel",
    "tagline": "Welcome to the edge of reality",
    "phone_display": "+62 8810 370 928 55",
    "phone_tel": "+62881037092855",
    "whatsapp": "https://wa.me/62881037092855",
    "email": "therabbittreegilimeno@gmail.com",
    "address": "Gili Meno, Kabupaten Lombok Utara, West Nusa Tenggara, 83352",
    "maps": "https://goo.gl/maps/gdDktcyKkJ8Vy9LZ8",
    "booking": "https://www.booking.com/hotel/id/gili-gila.html",
    "hostelworld": "https://www.hostelworld.com/hosteldetails.php/The-Rabbit-Tree-Hostel/Gili-Meno/274111",
    "instagram": "https://www.instagram.com/therabbittreehostel/",
    "facebook": "https://www.facebook.com/gilimenohostel/",
    "tripadvisor": "https://www.tripadvisor.com/Hotel_Review-g664665-d12053721-Reviews-Gili_Gila_Hostel-Gili_Meno_Gili_Islands_Lombok_West_Nusa_Tenggara.html",
}

INTRO = ("Experience a truly unique and creative stay at The Rabbit Tree Hostel. Our accommodations "
         "stand out as the most entertaining in Lombok and among all hotels in Gili Meno. With a friendly "
         "staff, vibrant atmosphere, and an array of amenities including a ball pit room and escape room, "
         "your stay with us will be unforgettable.\n\n"
         "Enjoy a wide range of activities, from yoga classes to bonfires to movie nights. Immerse yourself "
         "in the vibrant and friendly atmosphere of The Rabbit Tree Hostel and create memories that will "
         "last a lifetime!")

# Les entrees de la carte dessinee de la page d'accueil
MAP_SPOTS = [
    {"slug": "gallery", "label": "Gallery", "art": "spiral.webp", "x": 76.4, "y": 11.0, "w": 22.4,
     "blurb": "Photos of the hostel and its secret passageways"},
    {"slug": "rooms", "label": "Rooms", "art": "tree-home.webp", "x": 50.2, "y": 27.0, "w": 22.4,
     "blurb": "Eleven rooms, none of them ordinary"},
    {"slug": "transports", "label": "Cheap Boats", "art": "fast-boat-and-transport-to-the-gilis.webp", "x": 28.2, "y": 32.0, "w": 12.4,
     "blurb": "Boats to and from Bali and Lombok"},
    {"slug": "activities", "label": "Activities", "art": "rabbits.webp", "x": 24.6, "y": 39.5, "w": 30.0,
     "blurb": "What to do on Gili Meno, every day"},
    {"slug": "reservations", "label": "Reservations", "art": "boat-line.webp", "x": 49.7, "y": 46.0, "w": 20.0,
     "blurb": "10% cheaper than the booking websites"},
    {"slug": "how-to-get-here", "label": "How To Get There", "art": "traveler.webp", "x": 50.0, "y": 62.0, "w": 20.0,
     "blurb": "Finding us once you are on the island"},
    {"slug": "our-story", "label": "Our Story", "art": "tree-rooms.webp", "x": 79.0, "y": 55.0, "w": 30.0,
     "blurb": "How a rabbit grew into a tree"},
    {"slug": "tours", "label": "Adventures", "art": "dragon-edited-png.webp", "x": 33.4, "y": 84.0, "w": 19.7,
     "blurb": "Komodo by boat, Rinjani on foot"},
]

# "badge" = logo propre de la chambre (sans spirale, comme sur les pages chambres Wix).
# "spiral" = disque spirale independant pose par-dessus sur l'arbre ; "spiral_on" = visible.
# Toutes les chambres affichent leur spirale : un clic l'ouvre comme une porte et revele le logo.
# x / y / w = centre et largeur en % de l'image d'arbre, releves sur la page Wix d'origine.
ROOMS = [
    {
        "slug": "tree-house", "name": "Tree House", "cat": "Fan dorm",
        "badge": "tree-house-rabbit-tree-contour-png.webp", "spiral": "img-14d7de906fbb4c.webp", "spiral_on": True,
        "x": 40.7, "y": 21.9, "w": 14.4,
        "beds": "5 single beds", "air": "Fans", "bath": "Shared bathroom", "sleeps": "1 person per bed",
        "desc": ["The Tree House is a dorm style room containing 5 beds and fans for each bed. Lockers are provided in the room. Please note that access to the room is via a ladder staircase."],
    },
    {
        "slug": "grandma-room", "name": "Grandma Room", "cat": "Twin room",
        "badge": "img-24082e164ed1a6.webp", "spiral": "img-c98edb30a91abd.webp", "spiral_on": True,
        "x": 58.1, "y": 13.6, "w": 19.9,
        "beds": "2 single beds", "air": "Air conditioning", "bath": "Shared bathroom", "sleeps": "2 people",
        "desc": ["Take a trip down memory lane in this quaint designed room fitted with AC, two single beds, window and retro decor with grandma's China.",
                 "This dorm room looks over the courtyard and is a fantastic choice for two friends traveling."],
    },
    {
        "slug": "family-rabbit-cave", "name": "Family Rabbit Cave", "cat": "Triple room",
        "badge": "img-1b45943c49f143.webp", "spiral": "img-4390b57989cfe6.webp", "spiral_on": True,
        "x": 14.9, "y": 22.5, "w": 16.9,
        "beds": "3 single beds", "air": "Air conditioning", "bath": "Shared bathroom", "sleeps": "3 people",
        "desc": ["This room has three single beds with an abundance of storage space. The room is equipped with AC and is in a close vicinity to the shared bathrooms.",
                 "This room holds sound extremely well and is perfect for a well earned rest from traveling."],
    },
    {
        "slug": "bird-nest", "name": "Bird Nest", "cat": "Double / Twin",
        "badge": "img-886241f5da6045.webp", "spiral": "img-c4fa9ee6dbd005.webp", "spiral_on": True,
        "x": 86.5, "y": 19.9, "w": 15.4,
        "beds": "Queen bed or 2 singles", "air": "Fans", "bath": "Shared bathroom", "sleeps": "2 people",
        "desc": ["Look out onto the mountains of Lombok from your room with the best views in the whole hostel.",
                 "This room can work either as a queen size bed for two or as a twin room with two separate single beds. Fans and mosquito nets are provided and access to the room is via a ladder."],
    },
    {
        "slug": "passion-room", "name": "Passion Room", "cat": "Double ensuite",
        "badge": "img-25a71d5def56a1.webp", "spiral": "img-d69537421d8908.webp", "spiral_on": True,
        "x": 30.3, "y": 38.1, "w": 18.0,
        "beds": "Double bed", "air": "Air conditioning", "bath": "Private ensuite bathroom", "sleeps": "2 people",
        "desc": ["This is maybe the most special of our double rooms amongst The Rabbit Tree's private rooms that boasts an ensuite bathroom.",
                 "The unexpected meeting between a tree and an angel, jalousing each other for what they will never have."],
    },
    {
        "slug": "bamboo-forest", "name": "Bamboo Forest 1 & 2", "cat": "Deluxe double",
        "badge": "img-35c590b8d9652a.webp", "spiral": "img-cdf416228812cd.webp", "spiral_on": True,
        "x": 56.5, "y": 38.9, "w": 16.9,
        "beds": "Double bed", "air": "Air conditioning", "bath": "Private ensuite bathroom", "sleeps": "2 people",
        "desc": ["The Rabbit Tree's deluxe rooms boast a sophisticated design and private ensuite bathroom.",
                 "The Bamboo Forest 1 is located on the first floor on top of the garden and sport area.",
                 "The Bamboo Forest 2 is located in a separate building to the main hostel, less than 10 seconds walk away. Of course you are still welcome for breakfast and use of all the facilities in the main building. For those looking for a serene, tranquil stay on Gili Meno, this is the perfect choice."],
    },
    {
        "slug": "rabbit-dream", "name": "Rabbit Dream", "cat": "Private double",
        "badge": "rabbit-dream-surround-png.webp", "spiral": "rabbit-dream-vortexcolor-png.webp", "spiral_on": True,
        "x": 88.9, "y": 74.4, "w": 20.6,
        "beds": "Double bed", "air": "Air conditioning", "bath": "Private ensuite + terrace", "sleeps": "2 people",
        "desc": ["Situated 30 seconds away from the main building, this private room immerses you in the dream of a rabbit.",
                 "Slightly cheeky, it may give you some inspiration for your own fantasies.",
                 "Like the other double rooms it includes an ensuite bathroom, but also its own little terrace."],
    },
    {
        "slug": "flying-boat", "name": "Flying Boat", "cat": "Twin room",
        "badge": "img-d662437612ccc7.webp", "spiral": "img-f8ccb569b68bbd.webp", "spiral_on": True,
        "x": 10.4, "y": 51.4, "w": 17.7,
        "beds": "2 single beds", "air": "A large fan for each bed", "bath": "Shared bathroom", "sleeps": "2 people",
        "desc": ["This room is in the heart of all the fun in the hostel.",
                 "You can find The Flying Boat suspended above the common areas in an airy, bamboo made boat shaped room with a large fan for each bed.",
                 "There are two single beds making it perfect for two friends or a solo traveler."],
    },
    {
        "slug": "bola-bola", "name": "Bola Bola", "cat": "Triple / ball pit",
        "badge": "img-fa244306688fa0.webp", "spiral": "img-1e32badce2fb23.webp", "spiral_on": True,
        "x": 37.2, "y": 69.2, "w": 18.7,
        "beds": "Ball pit + beds for 3", "air": "Air conditioning", "bath": "Shared bathroom", "sleeps": "3 people",
        "desc": ["Welcome to your childhood dream come true! Dive into this giant ball pit straight from your bed and get lost in a sea of colour.",
                 "This room would be perfect if you are traveling in a group of three or are looking to make new friends on Gili Meno."],
    },
    {
        "slug": "pillow-room", "name": "Pillow Room", "cat": "Triple / escape game",
        "badge": "pillow-room-on-pillow-png.webp", "spiral": "img-4d19fc461bbb77.webp", "spiral_on": True,
        "x": 79.5, "y": 57.1, "w": 17.4,
        "beds": "3 beds", "air": "Air conditioning", "bath": "Shared bathroom", "sleeps": "3 people",
        "desc": ["You would expect this bedroom to be full of pillows. But hang on! There is not even one on the bed!",
                 "Or maybe if you look a bit better you could spot them. Locked in a net... Will you be smart enough to find the way to free them?",
                 "This bedroom is perfect for a group of 3 people who like challenges."],
    },
    {
        "slug": "twin-rabbit-cave", "name": "Twin Rabbit Cave", "cat": "Twin room",
        "badge": "img-5ab13b2a9ee36b.webp", "spiral": "img-2d7a9570caf366.webp", "spiral_on": True,
        "x": 60.6, "y": 78.7, "w": 15.9,
        "beds": "2 single beds", "air": "Air conditioning", "bath": "Shared bathroom", "sleeps": "2 people",
        "desc": ["Located within the rabbit caves is a twin room perfect for a traveling pair.",
                 "This room has AC, opens out onto the courtyard and is in close vicinity to the shared bathrooms.",
                 "The outer texture of this room is sand and stone, cooling down the inside — perfect after a long day at the beach!"],
    },
    {
        "slug": "monk", "name": "Monk", "cat": "Fan dorm",
        "badge": "img-56372fe7702694.webp", "spiral": "img-a88e84fde22637.webp", "spiral_on": True,
        "x": 12.6, "y": 79.8, "w": 17.7,
        "beds": "Bunk beds", "air": "Fans", "bath": "Shared bathroom", "sleeps": "Group",
        "desc": ["A quiet corner of the tree, upside down and out of the noise.",
                 "Ask at the reception if you would like to sleep in the Monk room."],
    },
]

# Dessin "baby psychopath" present sur l'arbre Wix, sans page ni lien (chambre a venir).
TREE_EXTRA = [
    {"name": "Baby Psychopath", "badge": "img-7f17b28b4ce224.webp", "spiral": None,
     "spiral_on": False, "x": 87.6, "y": 40.2, "w": 15.2, "soon": "coming soon"},
]

BOOKING_NOTE = ('Our booking system lets you reserve the corresponding category of room. '
                'If you want to be allocated in one specific room, write its name in the "Comment" '
                'section of the booking form.')

# Photos, bannieres et dessins recuperes du scrape Wix, tries par page.
# Chaque entree : (fichier dans images/, legende). "banner" = visuel pleine largeur.
PAGE_MEDIA = {
    "activities": {
        "banner": ("img-433a75fd6d2978.webp", "Freediving in the clear water off the reef", 0.8),
        "gallery": [
            ("img-a0bea03d339020.webp", "The Trash Heroes, cleaning the island every Sunday"),
            ("img-baeed1388d8c8b.webp", "Traditional dinner shared on the island"),
            ("img-b56438840f5c97.webp", "Horse riding along the beach"),
            ("img-a547bb719d71a2.webp", "Freediving in clear water"),
            ("img-91d2743badcb18.webp", "Baby turtles at the sanctuary"),
            ("img-138645e042cd2d.webp", "Diver exploring the reef"),
            ("img-642eb4c7a81abb.webp", "Divers forming a circle underwater"),
            ("img-b53dddc746eb67.webp", "Traditional boat on the sand"),
            ("img-36cb89e13743e9.webp", "Gili Meno from above, the lake at its centre"),
            ("img-1d67aafc7c59ac.webp", "The bay, seen from the hills"),
        ],
    },
    "tours": {
        "banner": None,
        "gallery": [
            ("komodo-pink-beach-edited-jpg.webp", "The famous pink beach of Komodo"),
            ("img-66fce4000fd111.webp", "A volcano crater lake at dawn"),
            ("img-da9e83ee3f45cd.webp", "Climbing towards the Rinjani summit"),
            ("tiup-kelep-waterfall.webp", "A waterfall stop on the way down"),
        ],
    },
    "komodo": {
        "banner": ("komodo-dragons-jpg.webp", "Meeting a Komodo dragon up close"),
        "gallery": [
            ("img-b53dddc746eb67.webp", "Anchored on a deserted beach"),
            ("img-3470ae751e2dd7.webp", "A Komodo dragon on the trail"),
        ],
        "deco": [("komodo-trip-boat.webp", "The wooden live-on-board boat")],
    },
    "rinjani": {
        "banner": ("rinjani-banner.webp", "Mount Rinjani and the crater lake"),
        "gallery": [
            ("img-da9e83ee3f45cd.webp", "The long ridge walk to the crater rim"),
            ("rinjani-trek-view-of-the-lake-segara-anak.webp", "View of Lake Segara Anak"),
        ],
    },
    "transports": {
        "banner": ("img-ad6ed82f5d5f8b.webp", "A boat crossing at sunset"),
        "gallery": [],
        "deco": [("old-fashion-boat.webp", "The old-fashioned public boat between the islands")],
    },
    "how-to-get-here": {
        "banner": None,
        "gallery": [
            ("map-to-come-to-rabbit-tree-png.webp", "Hand drawn map to find The Rabbit Tree from the harbour"),
            ("img-c29931b495af7b.webp", "Map of Gili Meno showing the hostel between the harbour and the beach"),
        ],
    },
    "welcome": {
        "banner": None,
        "gallery": [
            ("img-c29931b495af7b.webp", "Map of Gili Meno with The Rabbit Tree marked"),
        ],
        "deco": [
            ("logo-dessin-png.webp", "The Rabbit Tree, drawn by hand"),
            ("snorkeling-gear.webp", "Snorkelling gear to borrow at the reception"),
        ],
    },
    "culture": {
        "banner": None,
        "gallery": [],
        "deco": [
            ("img-77dddf225dab47.webp", "A few Indonesian words, from the hostel's own book"),
            ("img-319c0b2d3b6017.webp", "The mosque on the island"),
        ],
    },
    "services": {
        "banner": None,
        "gallery": [],
        "deco": [
            ("img-faf21b6019fced.webp", "Towels"),
            ("img-e3ecbb2b2c7472.webp", "Snorkelling mask rental"),
            ("img-57769765ad8335.webp", "Bike rental"),
            ("img-c6c3b8b4e38308.webp", "Special transport prices for our guests"),
        ],
    },
    "reservations": {
        "banner": ("img-bc50b66a9e4795.webp", "A bed in the Grandma Room, one of the rooms you can book"),
        "gallery": [],
    },
    "useful-information": {
        "banner": None,
        "gallery": [("img-a8c510bc8319f3.webp", "The reef just off the shore")],
    },
}

NAV = [
    ("rooms", "Rooms", "/rooms/"),
    ("reservations", "Reservations", "/reservations/"),
    ("activities", "Activities", "/activities/"),
    ("tours", "Adventures", "/tours/"),
    ("transports", "Transports", "/transports/"),
    ("how-to-get-here", "How to get here", "/how-to-get-here/"),
    ("gallery", "Gallery", "/gallery/"),
    ("our-story", "Our story", "/our-story/"),
]

INFO_LINKS = [
    ("services", "Services", "/services/"),
    ("culture", "Culture", "/culture/"),
    ("useful-information", "Before you arrive", "/useful-information/"),
    ("welcome", "Welcome", "/welcome/"),
]
