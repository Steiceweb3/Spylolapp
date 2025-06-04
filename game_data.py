import json
import logging
from app import db
from models import Enigma

def setup_initial_enigmas():
    """Setup initial enigmas if they don't exist yet"""
    # Check if we already have enigmas
    enigma_count = Enigma.query.count()
    if enigma_count > 0:
        logging.debug(f"Database already contains {enigma_count} enigmas. Skipping initialization.")
        return
    
    logging.debug("Setting up initial enigmas...")
    
    # Define our initial enigmas
    enigmas = [
        {
            "title": "The Illuminati Code",
            "description": "Decode this message to reveal the secret Illuminati communication protocol:<br><span class='redacted'>A113</span> is the key. <span class='tech-text'>19-5-5 20-8-5 9-14-22-9-19-9-2-12-5</span> to find the truth.",
            "image_url": "https://pixabay.com/get/g6321d9fe872db573c885fbdfd737559ad1615b3afc628d51f0525f4aaf4deaada37a49c5aee5162b5ffd75b350ed47f498e608af0e607c6d13211d25eb7aa031_1280.jpg",
            "answer": "eye",
            "difficulty": 1,
            "points": 10,
            "hint": "Convert the numbers to letters using A=1, B=2, etc.",
            "correct_feedback": "CORRECT! Your third eye is now officially open! The Illuminati welcomes you... or do they? 👁️",
            "incorrect_feedback": "WRONG! The Illuminati has dispatched their reptilian agents to your location. Just kidding... or are we? Try again.",
            "order_position": 1
        },
        {
            "title": "Area 51 Clearance",
            "description": "To gain access to the alien technology vault, solve this security question:<br><span class='classified'>What crashed in Roswell in 1947 that the government claims was a weather balloon?</span> (one word answer)",
            "image_url": "https://pixabay.com/get/gb697dbe7830eba98f4f09058824340378e749741e0d8f59b6b52a2f5463dd3ba88ed2a8e3b5d11bada19ea68714eba0fea78d325941e1001f99890757dd8b441_1280.jpg",
            "answer": "spacecraft",
            "difficulty": 2,
            "points": 15,
            "hint": "It's not from this world and it flies...",
            "correct_feedback": "ACCESS GRANTED! The aliens say hi. They're quite disappointed with your Netflix watchlist though.",
            "incorrect_feedback": "ACCESS DENIED! The Men in Black have been dispatched to neuralize you. Please stare directly at this red light...",
            "order_position": 2
        },
        {
            "title": "Chemtrail Formula",
            "description": "Complete the missing element in the top-secret chemtrail formula:<br><span class='code-font'>H₂O + NaCl + [?] = MIND CONTROL</span><br>What common household chemical is the government adding? (chemical formula)",
            "image_url": "https://pixabay.com/get/g9122146c791dcc187e2cc7484b7e34c5ab35afce0feec6e22b12c1dd93207edcdbc0030f24a8814a178450b529ae48578a9478a3b60ea98f52d835e9d4cf1f08_1280.jpg",
            "answer": "NaF",
            "difficulty": 3,
            "points": 20,
            "hint": "It's added to drinking water and many brands of toothpaste.",
            "correct_feedback": "CONGRATULATIONS! You've identified sodium fluoride! Your dental health is excellent, but your paranoia levels are through the roof!",
            "incorrect_feedback": "WRONG! Maybe the mind control is already working on you. Quick, put on your tinfoil hat and try again!",
            "order_position": 3
        },
        {
            "title": "The Moon Landing Tape",
            "description": "NASA's secret archives contain a tape labeled: <span class='classified'>'STUDIO 27B - JULY 20, 1969'</span>. What famous director was allegedly consulting on this 'project'? (last name only)",
            "image_url": "https://pixabay.com/get/g7b9d3faa97f9ab7aca0245381f8b474576ab92d6ece38bc09f7c576035f71d1819a3b8f1f548f233c5fc211573b5c52a5271c3eaef83d513c8293f807139e1c2_1280.jpg",
            "answer": "kubrick",
            "difficulty": 2,
            "points": 15,
            "hint": "He directed '2001: A Space Odyssey' just before the moon landing.",
            "correct_feedback": "BINGO! Kubrick's involvement has been confirmed. He was such a perfectionist that he insisted on filming on location... on the moon.",
            "incorrect_feedback": "NEGATIVE! Our sources say your answer is as fake as the moon landing. Or is the moon itself fake? Think about it.",
            "order_position": 4
        },
        {
            "title": "The Redacted Files",
            "description": "This classified document has been heavily redacted. Find the hidden message.<br><div class='document'><span class='redacted-block'>████████████</span> THE <span class='redacted-block'>██████</span> TRUTH <span class='redacted-block'>██████████</span> LIES <span class='redacted-block'>████</span> WITHIN <span class='redacted-block'>██████████</span></div>",
            "image_url": "https://pixabay.com/get/gbc63faebecb1865a027293bf22c72023bd643a1d2bb1b4451b358fc5a5477a6b1208c9fda7f21250071e1f90b4e8369306abf43bcf651d74179f215f8f9a8491_1280.jpg",
            "answer": "the truth lies within",
            "difficulty": 1,
            "points": 10,
            "hint": "Focus only on the visible words...",
            "correct_feedback": "DECLASSIFIED! Indeed, the truth lies within... your browser's rendered HTML. Meta, right?",
            "incorrect_feedback": "STILL CLASSIFIED! Your security clearance has been downgraded to 'confused civilian'. Try reading only what you can actually see.",
            "order_position": 5
        },
        {
            "title": "Backdoor Protocol",
            "description": "A secret NSA program requires this passphrase to access global surveillance systems. What 3-letter acronym turns your smart devices into listening posts?<br><span class='tech-text'>$ sudo ./access --global --listen --everywhere</span>",
            "image_url": "https://pixabay.com/get/g1e4ba6785c34cfa2bfb27c34a80cca22e9c74abe60d11bcb53565f14928947d3504ecb1cd99bf6914d2fa318db5b29bbcfb3fd19a0a251d4548ef7f813583ad7_1280.jpg",
            "answer": "IOT",
            "difficulty": 2,
            "points": 15,
            "hint": "These devices are connected to the internet and found in smart homes.",
            "correct_feedback": "SYSTEM BREACHED! Your refrigerator, toaster, and smart toilet are now all aware that you've solved this puzzle. They're very impressed.",
            "incorrect_feedback": "ACCESS VIOLATION! Your smart devices are laughing at you right now. Yes, even your light bulbs. Especially your light bulbs.",
            "order_position": 6
        },
        {
            "title": "Project MKUltra",
            "description": "Complete the CIA's mind control trigger phrase:<br><span class='classified'>\"The <span class='highlight-text'>_______</span> fox jumps over the sleeping guard.\"</span>",
            "image_url": "https://pixabay.com/get/g5559887cb99a5ad9ab1ad1fda4895d12d3bf07250921705abc5f48728471632b704194ae89290a240f35050f531381309a5e32b213d7b0384b24b8ba0a7980f2_1280.jpg",
            "answer": "crimson",
            "difficulty": 4,
            "points": 25,
            "hint": "It's a shade of deep red, often associated with blood.",
            "correct_feedback": "ACTIVATION SUCCESSFUL! Please stand by while we upload new programming to your brain. Don't worry about that sudden craving for government-approved breakfast cereals.",
            "incorrect_feedback": "TRIGGER FAILED! The CIA operatives monitoring this session are very disappointed. Your mind remains tragically under your own control.",
            "order_position": 7
        },
        {
            "title": "The Bitcoin Creator",
            "description": "Decrypt this message to reveal who <span class='tech-text'>really</span> created Bitcoin:<br><span class='code-font'>01001110 01010011 01000001</span>",
            "image_url": "https://pixabay.com/get/ge59e523bf98ccc825ec98cfa9844a69d0119722e6d94d3e6cd7b5d93f02b5563c33ef4fb232f6ad799937cfd200f7f108ebba06d6bc583dfe02c5df4e3d6bbe5_1280.jpg",
            "answer": "NSA",
            "difficulty": 3,
            "points": 20,
            "hint": "It's binary code. Convert each 8-bit sequence to ASCII.",
            "correct_feedback": "BLOCKCHAIN COMPROMISED! Yes, the NSA created Bitcoin to track all your illicit purchases. Those 'anonymous' transactions? Hilarious.",
            "incorrect_feedback": "HASH INVALID! Your attempt to uncover the truth has been added to your permanent record. The blockchain never forgets.",
            "order_position": 8
        }
    ]
    
    # Add enigmas to database
    for enigma_data in enigmas:
        enigma = Enigma(**enigma_data)
        db.session.add(enigma)
    
    db.session.commit()
    logging.debug(f"Added {len(enigmas)} initial enigmas to the database.")
