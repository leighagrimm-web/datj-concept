import json, re, sys
def card(t, d, more, tag=''): return {"t": t, "d": d, "more": more, "tag": tag, "photo": "", "label": "", "url": ""}
WEAR = "## What to wear"
styles = [
 card("Ballet", "The foundation of every style: Disney Dancing (pre-ballet) through Ballet V, plus Pointe.",
  "## Levels\n- Disney Dancing: pre-ballet to favorite Disney songs\n- Ballet Basics: positions, terms and short combinations, a little barre\n- Combo and Ballet I to V: technique builds level by level\n- Pre Pointe, Pointe I & II: ankle strength and control, then pointe work\n## Good to know\n- The instructor places each dancer in a level\n- Pre Pointe: in Ballet II or III, plus one more ballet class\n- Pointe I: a year of Pre Pointe and in Ballet III or IV\n" + WEAR + "\n- Solid black leotard, studio brand tights; skirt or tutu optional for Disney Dancing\n- Ballet I: studio brand ballet shoes. Ballet I/II and up: So Danca or Capezio canvas\n- Tight ballet bun, bangs away from face"),
 card("Jazz & Lyrical", "Jazz Hip Hop (ages 6+), Jazz II–III and Jazz/Lyrical I–III.",
  "## Levels\n- Jazz Hip Hop I and I/II (ages 6+): beginner jazz technique and body movement\n- Jazz II and III: intermediate to advanced technique\n- Jazz/Lyrical I to III: jazz technique plus lyrical, telling a song’s story through movement\n## Good to know\n- The instructor places each dancer in a level\n- Jazz/Lyrical needs a ballet class too\n" + WEAR + "\n- Solid black leotard, tight shorts or leggings (boys: black shirt and shorts)\n- Jazz Hip Hop: black jazz shoes. Jazz/Lyrical: studio brand tan jazz shoes\n- Bun or ponytail, bangs away from face"),
 card("Tap", "Tiny Tap (ages 3+) through Tap IV.",
  "## Levels\n- Tiny Tap (ages 3–5): first steps and sing-along songs\n- Tap Basics (ages 5+): simple rhythms\n- Tap I to IV: rhythms and sounds get more complex each level\n" + WEAR + "\n- Solid black leotard, tight shorts or leggings (boys: black shirt and shorts)\n- Studio brand tap shoes. Tap 2 & 3: studio premium tap shoes. Tap 4: Capezio Tan Manhattan Xtreme heel\n- Bun or ponytail, bangs away from face"),
 card("Hip Hop", "Hip Hop Basics (ages 4+) through Hip Hop III.",
  "## Levels\n- Hip Hop Basics (ages 4+): rhythm, first steps and sing-alongs\n- Hip Hop I (ages 7+) to III: hip hop culture and technique, beginner to advanced\n" + WEAR + "\n- Basics: black leotard with shorts or leggings. Hip Hop I and up: loose, comfortable clothes (no jeans or belts)\n- Clean gym shoes worn only inside (change at the studio)"),
 card("Breaking", "Intro to Breaking (ages 6+) and Breaking I & II.",
  "## Levels\n- Intro to Breaking (ages 6+): basics that build rhythm, strength, flexibility and focus\n- Breaking I & II: twice a week; footwork, freezes and harder steps with conditioning\n## Good to know\n- Breaking is an Olympic sport now\n- The Breaking I & II combined class is included with Breaking I or II\n" + WEAR + "\n- Loose, comfortable clothes (no jeans or belts)\n- Clean gym shoes worn only inside\n- A spin cap, bought from The Breaking Program at the studio"),
 card("Acro", "Acro Basics (ages 4+) through Acro II.",
  "## Levels\n- Acro Basics (ages 4+): rolls, cartwheels, bridges and balance\n- Acro I (ages 6+) to II: tumbling and balancing skills build each level\n" + WEAR + "\n- Any color leotard, tight shorts or leggings\n- Barefoot\n- Hair pulled back"),
 card("Contemporary", "Modern/Contemporary (ages 8+) and Contemporary.",
  "## Levels\n- Modern/Contemporary I (ages 8+) to III: modern technique with contemporary movement\n- Contemporary: jazz, ballet and modern skills for free-form expression\n## Good to know\n- Modern/Contemporary needs a ballet class too\n" + WEAR + "\n- Modern/Contemporary: any color leotard, shorts or leggings; barefoot\n- Contemporary: solid black leotard, shorts or leggings; half sole shoes\n- Hair pulled back, bangs away from face"),
 card("Musical Theater", "Sing, act and dance: Musical Theater I to III.",
  "## Levels\n- Musical Theater I to III: jazz technique with storytelling, acting and character work\n" + WEAR + "\n- Solid black leotard, tight shorts or leggings (boys: black shirt and shorts)\n- Studio brand tan jazz shoes\n- Tight bun, bangs away from face"),
 card("Tiny Tots", "Mommy/Daddy & Me for babies and toddlers.",
  "Move together and build motor skills in a fun class.\n## Good to know\n- Doesn’t perform in the Annual Performance\n" + WEAR + "\n- Comfortable clothes (no jeans or belts)\n- Barefoot or socks"),
 card("Leaps, Turns & Conditioning", "Technique boosters for every style (ages 10+).",
  "## Classes\n- Leaps & Turns (ages 11+): pointed toes, straight legs, flexibility, jumps and turns\n- Conditioning (ages 10+): strength and stamina\n## Good to know\n- Great for Poms and Orchesis dancers\n- These classes don’t perform in the Annual Performance\n" + WEAR + "\n- Leaps & Turns: any color leotard, shorts or leggings; black or tan jazz shoes\n- Conditioning: comfortable clothes; barefoot or socks"),
 card("Bollywood", "Two age groups: 7+ and 11+.",
  "The instructor places each dancer in a level.\n" + WEAR + "\n- Comfortable clothes (no jeans or belts)\n- Barefoot or socks"),
 card("Adult classes", "Jazz/Contemporary, Hip Hop and Ballet for grown-ups.",
  "## Classes\n- Jazz/Contemporary: mostly jazz technique with a contemporary feel\n- Hip Hop: cardio warm-up, then grounded combinations\n- Ballet: basic terms and technique\n" + WEAR + "\n- Comfortable clothes (no jeans or belts)\n- Hip Hop: clean gym shoes worn only inside. Ballet and Jazz/Contemporary: barefoot or socks"),
]
D = lambda t, d, a, s, h: card(t, d, "- Clothes: " + a + "\n- Shoes: " + s + "\n- Hair: " + h, "Dress code")
dress = [
 card("Every class", "No jewelry or watches except stud earrings. Bring a labeled water bottle.", "- No jewelry or watches in any class, except stud earrings\n- Bring a labeled water bottle\n- The full studio policies are on the Pricing page", "Dress code"),
 D("Ballet, Pointe & Disney Dancing", "Black leotard, studio tights, tight bun.", "solid black leotard, studio brand tights; black shorts or ballet skirt optional (Disney Dancing: any color skirt or tutu). Boys: black fitted shirt or tank, black shorts", "Disney Dancing and Ballet I: studio brand ballet shoes, no laces. Ballet I/II and up: So Danca or Capezio canvas", "tight ballet bun, bangs away from face (no messy buns)"),
 D("Combo", "Black leotard, studio tights, ballet + jazz shoes.", "solid black leotard, studio brand tights; black shorts optional. Boys: black shirt and shorts", "studio brand ballet shoes AND solid black jazz shoes, no laces", "tight bun, bangs away from face"),
 D("Tap, Jazz Hip Hop & Hip Hop Basics", "Black leotard with shorts or leggings.", "solid black leotard, tight shorts or leggings. Boys: black shirt, shorts or leggings", "Tap: studio brand tap shoes (Tap 2 & 3: studio premium; Tap 4: Capezio Tan Manhattan Xtreme heel). Jazz Hip Hop: black jazz shoes. Hip Hop Basics: clean gym shoes worn only inside", "bun or ponytail, bangs away from face"),
 D("Jazz Lyrical, Musical Theater & Contemporary", "Black leotard, tan jazz or half sole shoes.", "solid black leotard, black tight shorts or leggings. Boys: black shirt or tank, black shorts or leggings", "Jazz Lyrical and Musical Theater: studio brand tan jazz shoes. Contemporary: half sole shoes", "tight bun, bangs away from face"),
 D("Modern, Acro & Leaps and Turns", "Any color leotard; barefoot or jazz shoes.", "any color leotard, tight shorts or leggings. Boys: any color shirt or tank, shorts or leggings", "Modern/Contemporary and Acro: barefoot. Leaps & Turns: studio brand black or tan jazz shoes", "pulled back, bangs away from face"),
 D("Hip Hop & Breaking", "Loose clothes and clean indoor gym shoes.", "loose, comfortable clothes (no jeans or belts)", "clean gym shoes worn only inside; change at the studio. Breaking: a spin cap from The Breaking Program", "no requirement"),
 D("Adults, Tiny Tots, Bollywood & Conditioning", "Comfortable clothes; barefoot or socks.", "comfortable clothes (no jeans or belts)", "Adult Hip Hop: clean gym shoes worn only inside. Everything else: barefoot or socks", "no requirement"),
 D("Company rehearsals", "Black leotard or crop top; turners or tan jazz shoes.", "solid black leotard or black crop top, black tight shorts or leggings. No watches", "turners or tan jazz shoes", "pulled back, bangs away from face"),
]
mission = [
 {"t": "create", "d": "Dancers explore their own creative movement in every style.", "more": "", "tag": "", "photo": "", "label": "", "url": ""},
 {"t": "inspire", "d": "Instructors chosen for their passion for dance and teaching, who keep learning themselves.", "more": "", "tag": "", "photo": "", "label": "", "url": ""},
 {"t": "dance", "d": "Fun, positive classes that build confidence, coordination and discipline.", "more": "", "tag": "", "photo": "", "label": "", "url": ""},
]
texts = {
 "auditions": "Company is an audition-based team for dancers ready to work hard and grow. Dancers must be 7 by September 1. Placement is based on attitude, technique, performance and readiness for the commitment.",
 "auditionsMore": "More than a competitive team: Company dancers represent the studio and grow as people.\n## Who can audition\n- 7 years old by September 1\n- New dancers also take the Summer Intensive Week and the Summer Dance Session\n## Classes you need first\n- Petite (Combo / Ballet I level), 2 classes: a full 55-minute Ballet or Combo, plus Jazz Lyrical, Jazz Hip Hop, Combo, Tap or Musical Theater\n- Intermediate, Junior, Teen & Senior (Ballet I/II and up), 3 classes: Ballet; Modern/Contemporary or Jazz Lyrical; plus Jazz Hip Hop, Hip Hop, Tap or Musical Theater\n## What we look for\n- Dedicated, prepared and hardworking\n- Positive leaders and supportive teammates\n- Open to challenge and feedback, proud to represent D&ATJ\n## What Company dancers gain\n- Confidence, strong technique and artistry\n- Time management and accountability\n- A team that feels like family\n- Performances plus 3–4 regional competitions, March to May",
}
def apply(c):
    c['lists']['styles'] = styles; c['lists']['dress'] = dress; c['lists']['mission'] = mission
    c.setdefault('texts', {}).update(texts); return c
# content0.json
p = sys.argv[1]; c = json.load(open(p)); json.dump(apply(c), open(p, 'w'), ensure_ascii=False, indent=1)
# CONTENT0 inside the page shell
h = sys.argv[2]; s = open(h).read(); i = s.index('const CONTENT0 = ') + len('const CONTENT0 = ')
dec = json.JSONDecoder(); obj, end = dec.raw_decode(s, i)
s = s[:i] + json.dumps(apply(obj), ensure_ascii=False) + s[i + (end - i):]
open(h, 'w').write(s); print('ok', len(styles), 'styles', len(dress), 'dress cards')
