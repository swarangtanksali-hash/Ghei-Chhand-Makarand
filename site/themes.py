import re
D=r"\u0900-\u097F"
THEMES=[
 ("nam","नामस्मरण","Remembering the Name",[r"नाम",r"जप",r"स्मरण",r"पाठ"],4),
 ("sam","समाधान","Peace & contentment",[r"समाधान",r"शांत",r"शांती",r"शांति",r"निश्चिंत"],3),
 ("guru","गुरुकृपा","Guru & the saints",[r"सद्गुरू",r"सद्गुरु",r"गुरू",r"गुरु",r"महाराज",r"संत",r"ब्रह्मचैतन्य",r"गोंदवले",r"माऊली",r"रामदास"],1),
 ("man","मन","The restless mind",[r"(?<!["+D+r"])मन(?!ुष)",r"चंचल",r"चिंता",r"काळजी",r"ताण",r"तणाव",r"राग",r"त्रास",r"भीती",r"नैराश्य",r"बैचेन",r"अस्वस्थ",r"भटक",r"विचार",r"इच्छा"],3),
 ("jiv","जीवन","Living, day to day",[r"जीवन",r"आयुष्य",r"प्रपंच",r"परमार्थ",r"जगण",r"नाते",r"नाती",r"वर्तमान",r"कर्म",r"नशीब",r"जिंदगी",r"संवाद",r"वेळ"],3),
 ("swar","स्वर","Song & music",[r"स्वर",r"सूर",r"गाण",r"गायन",r"संगीत",r"सुरेल",r"नाट्य",r"ताल",r"भजन",r"सप्तक",r"गाता",r"गावा"],2),
 ("nis","निसर्ग","Nature & small things",[r"निसर्ग",r"पाऊस",r"पावसा",r"वारा",r"फूल",r"फुल",r"कळी",r"ऋतू",r"सूर्य",r"चंद्र",r"तापमान",r"हवा",r"झाड",r"नदी",r"अन्न",r"पोहे",r"उपमा",r"हुरडा",r"तीळ",r"भूक",r"चहा",r"जेवण",r"आंबा",r"चाक",r"तळे",r"थेंब"],1),
]
HI=re.compile(r"(?<!["+D+r"])(है|हैं|नही|नहीं|में|को|हर|जो|रहे|करते|बहुत|हमारी|हमारा|मेरे|मेरा|तेरा|तुम|कैसे|जिंदगी|सुबह|दिन|नाम का|किसका|कभी|सब|कुछ|होता|होते)(?![" + D + r"])")
def tags(text):
    out=[]; sc={}
    for key,mr,en,pats,th in THEMES:
        s=sum(len(re.findall(p,text)) for p in pats)
        if s>=th: out.append(key)
        sc[key]=s/th
    if not out:
        best=max(sc,key=sc.get)
        out.append(best if sc[best]>0 else "nam")
    if len(set(m.group(0) for m in HI.finditer(text)))>=2 : out.append("hin")
    if re.search(r"[A-Za-z]{3,}",text): out.append("eng")
    return out

def primary(text):
    t=tags(text)
    th=[k for k in t if k not in("hin","eng")]
    if not th: return t
    return t
