import json, sys
texts = {
 "losIntro": "Dance education scholarships for Dance & All That Jazz students.",
 "losStory": "The Light On Stage Foundation was established in December 2023 by Dance & All That Jazz Founder and Studio Owner, Brittany Brady, in loving memory of Kat Koziara, one of our beloved Breaking students and student instructors, who tragically lost her life in a car accident.\n\nKat was truly a light on stage, bringing joy, passion, and energy to every performance. Her love for dance and the impact she made on our studio community continue to inspire us.\n\nTo honor Kat’s memory and keep her light shining, the foundation provides dance education scholarships to children and families experiencing financial hardships. Our mission is to ensure that financial challenges never prevent a child from experiencing the joy of dance.\n\nThrough the Light On Stage Foundation, Kat’s light continues to shine, giving more children the opportunity to dance, grow, and follow their passion.",
 "losSquare": "",
 "losZelle": "lightonstagefoundation",
 "losGiveNote": "Every gift goes to dance education scholarships for D&ATJ families experiencing financial hardship.",
 "absenceNote": "Report it in the Parent Portal. No need to email or call the studio.",
}
def apply(c): c.setdefault('texts', {}).update(texts); return c
p = sys.argv[1]; c = json.load(open(p)); json.dump(apply(c), open(p, 'w'), ensure_ascii=False, indent=1)
h = sys.argv[2]; s = open(h).read(); i = s.index('const CONTENT0 = ') + len('const CONTENT0 = ')
obj, end = json.JSONDecoder().raw_decode(s, i)
s = s[:i] + json.dumps(apply(obj), ensure_ascii=False) + s[end:]
open(h, 'w').write(s); print('ok')
