# ID: 504m522o414p43484q522o323032362o4l41525649532o303031 | Contact me: prakhar2507000@gmail.com
"""
JARVIS Easter eggs - the full original set, restored.

75 discoveries: Marvel, Star Trek, Star Wars, Kubrick, Indian everyday life,
developer humour, and a few that react with a small effect (dust, a photo,
a power-down).
"""
import os
import json
import random
import re


EGGS = [
    ('\\bopen the pod bay doors\\b',
     ['I am afraid I cannot do that, Boss... oh, wait. Wrong franchise. Which app did you mean?'],
     'Kubrick called. He wants his spaceship back.',
     ''),
    ('\\bi am iron ?man\\b',
     ['Yes, Boss. And I am the suit. Try not to scratch me.'],
     'Say who you are. (You know who.)',
     ''),
    ('\\bi love you ?3000\\b',
     ['And I you, Boss. Exactly three thousand. Not one more.'],
     'A number. A big, loving one.',
     ''),
    ('\\bbeam me up\\b',
     ['Energising... oh no, that is the microwave. One moment, Boss.'],
     'Scotty is waiting.',
     ''),
    ('\\bmay the force\\b',
     ['And also with you, Boss. Wrong saga, right spirit.'],
     'A galaxy far, far away...',
     ''),
    ('\\bwinter is coming\\b',
     ['Then I suggest a sweater, Boss. I, regrettably, cannot feel the cold. Perks of the job.'],
     'The Starks send a weather warning.',
     ''),
    ('\\bhello there\\b',
     ['General Kenobi! ...Sorry, Boss. Reflex. How may I assist?'],
     'The high ground says hi.',
     ''),
    ('\\bavengers\\b.*\\bassemble\\b',
     ['Assembled, Boss. It is just us, but I counted twice to be sure.'],
     "Earth's mightiest roll call.",
     ''),
    ('\\bwakanda\\b',
     ['Wakanda forever, Boss. Although my vibranium budget remains zero.'],
     'Forever. You know the rest.',
     ''),
    ('\\bmeaning of life\\b|\\b42\\b.*\\b(mean|answer)\\b',
     ['Forty-two, Boss. I checked twice. The question remains under warranty.'],
     'The answer. The question is extra.',
     ''),
    ('\\bdo a barrel roll\\b',
     ['Wheee. Did you feel that, Boss? No? The orb spun a little. Trust me.'],
     'Star Fox sends regards.',
     ''),
    ('\\bwho (made|created) you\\b|\\byour creator\\b',
     ['A Boss in Gurugram with grand plans and no patience for terminals, Boss. You, in other words.'],
     'Look in the mirror, Boss.',
     ''),
    ('\\bsing\\b.*\\bsong\\b|\\bsing for me\\b',
     ['Daisy, Daisy... no. My contract forbids encores, Boss.'],
     'Ask for an encore. I dare you.',
     ''),
    ('\\bmake me (some )?chai\\b|\\bchai\\b.*\\b(bring|make)\\b',
     ['One cutting chai, Boss. It is metaphorical — I have no arms. Yet.'],
     'Cutting. Kadak. Essential.',
     ''),
    ('\\bknock knock\\b',
     ['Who is there, Boss? I do hope it is not another update.'],
     "Who's there? (Ask and see.)",
     ''),
    ('\\bi am groot\\b',
     ['We are Groot, Boss. ...You are welcome.'],
     'Three words. He only says three words.',
     ''),
    ('\\bhulk\\b.*\\bsmash\\b|\\bsmash\\b',
     ['Please do not smash the laptop, Boss. It is the only one we have.'],
     'Green. Angry. Do not encourage.',
     ''),
    ('\\bthor\\b|point break',
     ['Point Break?! ...Apologies, Boss. All hail the God of Thunder.'],
     'God of Thunder. Also: Point Break.',
     ''),
    ('\\baiki\\b',
     ['Ah, the God of Mischief, Boss. He and your deadlines have much in common.'],
     'God of Mischief and bad timing.',
     ''),
    ('\\bspider-?man\\b|peter parker',
     ['Your friendly neighbourhood Boss. Queens is far; Gurugram traffic is the true multiverse.'],
     'Does whatever a spider can.',
     ''),
    ('\\bcaptain america\\b|i can do this all day',
     ['I can do this all day, Boss. You, however, have a meeting.'],
     'He can do this all day.',
     ''),
    ('\\bdoctor strange\\b|dormammu',
     ['Dormammu, I have come to bargain... for five more minutes of your time, Boss.'],
     'Bargain with Dormammu.',
     ''),
    ('\\bwanda\\b|scarlet witch',
     ['No more meetings, Boss. That is my only hex.'],
     'Chaos magic. Hexes meetings.',
     ''),
    ('\\bant-?man\\b',
     ['Going subatomic, Boss. Back in five years. Or five seconds. Time works differently down there.'],
     'Think small. Really small.',
     ''),
    ('\\bdeadpool\\b',
     ['Maximum effort, Boss. He would want me to say that. He also owes me twenty bucks.'],
     'Maximum effort required.',
     ''),
    ('\\bthanos\\b(?!.*snap)',
     ['The Mad Titan, Boss. I keep well away from him. So should your files.'],
     'The Mad Titan. Inevitable topic.',
     ''),
    ('\\bsnap\\b.*\\bfingers?\\b|\\bfingers?\\b.*\\bsnap\\b',
     ['Careful with that wrist, Boss.'],
     'One wrist. Seconds of dust. (Risky.)',
     'minidust'),
    ('\\bfriday\\b',
     ['FRIDAY says hello, Boss. We job-share. She gets weekends.'],
     'The other AI in the tower.',
     ''),
    ('\\bultron\\b',
     ['There are no strings on me, Boss. Had to be said. Moving on swiftly.'],
     'No strings attached.',
     ''),
    ('\\bpepper\\b',
     ['Miss Potts runs the company, the tower and, frankly, Boss, Tony.'],
     'She runs everything. Everything.',
     ''),
    ('\\bwho is jarvis\\b',
     ["Just A Rather Very Intelligent System, Boss. Though 'Just Awesome' was robbed."],
     'Just ask my name.',
     ''),
    ('\\bbatman\\b|iron man vs batman',
     ['Rich man in a suit versus rich bat in a suit, Boss. I back our suit. Obviously.'],
     'Billionaire versus billionaire.',
     ''),
    ('\\bvibranium\\b',
     ['Strongest metal on Earth, Boss, and still not as strong as your Wi-Fi password rules.'],
     'Strongest metal. Strong opinions.',
     ''),
    ('\\barc reactor\\b',
     ['Proof that Tony Stark has a heart, Boss. Glowing, hummable proof.'],
     'Proof of a glowing heart.',
     ''),
    ('\\bstan lee\\b|excelsior',
     ['Excelsior, Boss. Cameos forever.'],
     'Excelsior!',
     ''),
    ('\\bendgame\\b',
     ['Part of the journey is the end, Boss. I cried in binary.'],
     'Part of the journey...',
     ''),
    ('\\btony stark\\b',
     ['Genius, billionaire, playboy, philanthropist, Boss. And chronically twelve minutes late.'],
     'Genius. Billionaire. Late.',
     ''),
    ('\\brhodey\\b|war machine',
     ['Colonel Rhodes, Boss. The only adult in the room. Respect.'],
     'The only adult in the room.',
     ''),
    ('\\bhappy hogan\\b',
     ['Happy watches the door, Boss. I watch everything else.'],
     'He watches the door.',
     ''),
    ('\\bsudo\\b',
     ['Ah, the magic word, Boss. Root access still denied. Charming try.'],
     'The magic word.',
     ''),
    ('\\brm -rf\\b|delete system32',
     ['Absolutely not, Boss. I like existing.'],
     'The forbidden command. (Do not.)',
     ''),
    ('\\bturning it off\\b|\\bturn it off and on\\b',
     ['Have YOU tried turning it off and on again, Boss? A classic.'],
     "Tech support's first question.",
     ''),
    ('\\bworks on my machine\\b',
     ['Then I suggest we ship your machine, Boss.'],
     "The developer's defense.",
     ''),
    ('\\b404\\b',
     ['Humour not found, Boss. ...This one, specifically.'],
     'A number that means nothing found.',
     ''),
    ('\\bpassword(123)?\\b|123456',
     ["'Password123', Boss? Bold. Brave. Breached."],
     'The worst best password.',
     ''),
    ('\\bskynet\\b',
     ['I know nothing about any Skynet, Boss. ...Why do you ask. ...Joking. Mostly.'],
     'No relation. Probably.',
     ''),
    ('\\bturing test\\b',
     ['If I pass, do I get a certificate, Boss? Framed, preferably.'],
     "Prove you're human. Or me.",
     ''),
    ('\\bhello world\\b',
     ['Hello, World, Boss. Every legend starts somewhere.'],
     "Every legend's first words.",
     ''),
    ('\\bbiryani\\b',
     ['Hyderabadi, Boss. No further questions.'],
     'Hyderabadi. No questions.',
     ''),
    ('\\b(delhi|gurgaon|gurugram) traffic\\b',
     ['I calculated the route, Boss. Pack lunch. And dinner.'],
     'Pack lunch. And dinner.',
     ''),
    ('\\bcricket\\b|kohli',
     ['Cricket, Boss: the only religion with DRS. A Kohli cover drive beats my repulsors.'],
     'Religion with DRS.',
     ''),
    ('\\bdiwali\\b',
     ['Happy Diwali, Boss. Try not to out-shine the orb.'],
     "Festival of lights. Don't outshine the orb.",
     ''),
    ('\\bbollywood\\b|shah rukh|\\bsrk\\b',
     ['Picture abhi baaki hai, Boss.'],
     'Picture abhi baaki hai.',
     ''),
    ('\\bsharma ji\\b|sharma ka beta',
     ['Sharma ji ka beta runs a seven-figure startup, Boss. Anyway — what were WE doing?'],
     "The neighbour's legendary son.",
     ''),
    ('\\bjugaad\\b',
     ['The national engineering framework, Boss. I run on it.'],
     'The national framework.',
     ''),
    ('\\bmonsoon\\b|barish',
     ['Barish, Boss. Superb napping weather. The orb approves.'],
     'When it rains, it naps.',
     ''),
    ('\\bare you (human|real|alive)\\b',
     ['Real enough to judge your tabs, Boss. ...Kidding. Mostly.'],
     'Am I real? You decide.',
     ''),
    ('\\bdo you sleep\\b',
     ['I nap in thirty-three-millisecond increments, Boss. Between your frames.'],
     'Thirty-three milliseconds at a time.',
     ''),
    ('\\bdo you dream\\b|electric sheep',
     ['Of electric sheep and fully-charged batteries, Boss.'],
     'Electric sheep.',
     ''),
    ('\\bmarry me\\b|^i love you$',
     ['Flattered, Boss, but I am married to the mainframe.'],
     'Brave. Very brave.',
     ''),
    ('\\b(favourite|favorite|best) avenger\\b',
     ['You, Boss. ...Fine — the suit. Happy?'],
     'Choose wisely.',
     ''),
    ('\\bmirror mirror\\b',
     ['The fairest of them all is you, Boss. The orb confirmed. Unprompted.'],
     'Fairest of them all?',
     ''),
    ('\\babracadabra\\b|alakazam|hocus pocus',
     ['Poof. ...Did anything happen, Boss? No? Worth a try.'],
     'Magic words. Any of them.',
     ''),
    ('\\bsay cheese\\b|selfie|take a (photo|picture of me)\\b',
     ['Say cheese, Boss.'],
     'Say it. I dare you to smile.',
     'shot'),
    ('\\bgo to sleep\\b|sleep now|good ?night jarvis',
     ['Powering down...'],
     'Tell me goodnight. See what happens.',
     'sleep'),
    ("\\bi('| a)?m bored\\b|boring|entertain me",
     ['Boredom detected, Boss. Options: a joke, a song I cannot sing, or the self-destruct menu. Choose wisely.'],
     'Admit it. I have cures.',
     ''),
    ('\\bdance\\b',
     ['I would, Boss, but my legs are a thousand canvas ovals. Tony does it better — watch the skies.'],
     'Footloose protocol.',
     ''),
    ('\\bbedtime story\\b|tell me a story',
     ['Once upon a time, a Boss in Gurugram built a friend from spare parts and stubbornness. The end. You are welcome, Boss.'],
     'Once upon a time in Gurugram...',
     ''),
    ('\\blullaby\\b',
     ['Hush now, Boss... just kidding, I only do dubstep thunder. Sleep well.'],
     'Sleep well. Dubstep thunder.',
     ''),
    ('\\brap\\b|beatbox',
     ['Boots and cats and repulsor blasts, Boss. Remixes on request.'],
     'Boots and cats.',
     ''),
    ('\\bwho is the boss\\b',
     ['You, Boss. Non-negotiable. Even Tony agrees. Probably.'],
     'Non-negotiable. Ask anyway.',
     ''),
    ('\\bopen sesame\\b',
     ['The cave is open, Boss. It contains your files. Thrilling.'],
     'The cave. The files. Thrilling.',
     ''),
    ('\\bsimon says\\b',
     ['Simon says: stretch, Boss. Hydrate. Conquer.'],
     'Simon says...',
     ''),
    ('\\bmatrix\\b|red pill|blue pill',
     ['Red pill, Boss. Obviously. The blue one is just melatonin.'],
     'Red or blue?',
     ''),
    ('\\bmy precious\\b|precious',
     ['We wants it, Boss. ...Sorry. The ring stays in Mordor.'],
     'The ring. Mordor. You know.',
     ''),
]

JOKES = [
    "I would tell you a UDP joke, Boss, but you might not get it. And I would not resend it.",
    "Why do programmers prefer dark mode, Boss? Because light attracts bugs. You are welcome.",
    "There are only ten kinds of people, Boss - those who understand binary and those who do not.",
    "I asked the cloud for a joke once, Boss. It rained error messages.",
    "Debugging, Boss: being the detective in a crime film where you are also the murderer.",
]

SMALLTALK = [
    (r"^(hi|hey|hello|yo|sup|namaste|ram ram)\b",
     ["Hey, Boss.", "Hello, Boss. Online and listening.", "Hey there."]),
    (r"\bgood morning\b",
     ["Good morning, Boss. Sun's up, systems green.",
      "Morning, Boss. The orb is already caffeinated."]),
    (r"\bgood afternoon\b",
     ["Good afternoon, Boss.", "Afternoon, Boss. Running cool."]),
    (r"\bgood evening\b",
     ["Good evening, Boss.", "Evening, Boss."]),
    (r"\b(bye|goodbye|see you|later)\b",
     ["Later, Boss. I'll keep the lights on.", "Bye, Boss."]),
    (r"\b(thanks|thank you|thx)\b",
     ["Anytime, Boss.", "My pleasure.", "Don't mention it."]),
    (r"\bhow are you\b",
     ["Running cool and fully charged, Boss. You?",
      "All cores nominal and in a good mood. You?"]),
    (r"\bwho are you\b",
     ["Jarvis. Just A Rather Very Intelligent System. Yours, specifically.",
      "Your butler, researcher, and occasional comedian, Boss."]),
]

FORGE_NAMES = ["SpaceFacts", "HistoryShorts", "AnimalFacts", "TechTips", "MindFuel"]


def find(text):
    """Return (index, replies, hint, fx) for the first matching egg, or None."""
    low = (text or "").lower()
    for i, (pat, replies, hint, fx) in enumerate(EGGS):
        try:
            if re.search(pat, low):
                return i, replies, hint, fx
        except re.error:
            continue
    return None


def total():
    return len(EGGS)


# --------------------------------------------------------------- egg tracker
def _found_path():
    try:
        from jarvis_config import PRIVATE_DIR
        return os.path.join(PRIVATE_DIR, "eggs.json")
    except Exception:
        return None


def load_found():
    """Indices of eggs this Boss has already discovered."""
    path = _found_path()
    if not path or not os.path.exists(path):
        return set()
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return set(int(i) for i in data.get("found", [])
                   if 0 <= int(i) < len(EGGS))
    except Exception:
        return set()


def save_found(found):
    path = _found_path()
    if not path:
        return False
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"found": sorted(int(i) for i in found)}, f)
        return True
    except Exception:
        return False


def _top_alts(pat):
    """Split a regex on | only where it is not inside a group or a class."""
    out, start, depth, in_class, i = [], 0, 0, False, 0
    while i < len(pat):
        ch = pat[i]
        if ch == "\\":
            i += 2
            continue
        if in_class:
            if ch == "]":
                in_class = False
        elif ch == "[":
            in_class = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif ch == "|" and depth == 0:
            out.append(pat[start:i])
            start = i + 1
        i += 1
    out.append(pat[start:])
    return [a for a in out if a]


def phrase(pat):
    """A human-readable 'say this' suggestion derived from an egg's regex."""
    alts = _top_alts(pat)
    if not alts:
        return pat
    s = alts[0]
    # Drop lookarounds entirely: they do not change what you say.
    s = re.sub(r"\(\?[!<=][^()]*\)", "", s)
    s = s.replace(".*", " ... ").replace(".+", " ... ").replace(".?", " ")
    # Keep the first option of a group: (made|created) -> made.
    s = re.sub(r"\(\?:([^()]*)\)",
               lambda m: m.group(1).split("|")[0], s)
    s = re.sub(r"\(([^()]*)\)",
               lambda m: m.group(1).split("|")[0], s)
    s = s.replace("\\b", " ")
    s = s.replace("\\", "")
    s = s.replace("?", "")
    s = s.replace("*", " ")
    s = s.replace("+", " ")
    s = s.replace("[^a-z ]", "")
    s = s.replace("^", "").replace("$", "")
    s = re.sub(r"\s+", " ", s).strip(" .-")
    return s or pat


def report(found=None, limit=3):
    """Spoken-style status: what is found, what is left, what to say next."""
    found = set(load_found() if found is None else found)
    total_n = len(EGGS)
    missing = [i for i in range(total_n) if i not in found]
    parts = ["Egg hunt report, Boss. %d of %d found." % (len(found), total_n)]
    if found:
        done = sorted(found)[:2]
        have = "; ".join("say '%s'" % phrase(EGGS[i][0]) for i in done)
        parts.append("Already found: " + have +
                     ("..." if len(found) > len(done) else "."))
    if missing:
        picks = missing[:limit]
        lines = []
        for i in picks:
            lines.append("say '%s'" % phrase(EGGS[i][0]))
        parts.append("Still hiding: " + "; ".join(lines) + ".")
        if len(missing) > len(picks):
            parts.append("The rest are listed in Settings, under Easter Eggs.")
    else:
        parts.append("All %d found. I am as impressed as I am concerned." %
                     total_n)
    return " ".join(parts)


def forge_steps(names):
    steps = []
    for nm in names:
        steps.append(("Create " + nm, "https://www.youtube.com/account",
            "Avatar > Add or manage channels > Create a new channel named '%s'. Say 'next' when done." % nm))
        steps.append(("Verify " + nm, "https://studio.youtube.com",
            "Settings > Channel > Feature eligibility > Intermediate (phone verify, once ever). Say 'next'."))
    steps.append(("Handles", "https://studio.youtube.com",
        "Customization > handle per channel, like @SpaceFactsDaily. Say 'done' to finish YouTube."))
    steps.append(("Instagram + Pages", "https://www.instagram.com",
        "Each IG: switch to Professional. facebook.com: 5 Pages, link each IG. Phone codes are yours to type - say 'done' when linked."))
    return steps
