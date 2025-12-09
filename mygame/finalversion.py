import pygame
import sys
import math
import random

pygame.init()
pygame.mixer.init()

screenwidth = 1600
screenheight = 900
screen = pygame.display.set_mode((screenwidth, screenheight))
pygame.display.set_caption("Q-UP BUT BAD")
print("GAME INITIALIZED")

toparea = int(screenheight * 0.65)
fps = 60
clock = pygame.time.Clock()

bigfont = pygame.font.SysFont("comicsansms", 28, bold=True)
smallfont = pygame.font.SysFont("comicsansms", 18)
tinyfont = pygame.font.SysFont("comicsansms", 14)

musicvolume = 0.5
pygame.mixer.music.load("assets/cat.mp3")
pygame.mixer.music.play(-1)
pygame.mixer.music.set_volume(musicvolume)


clicksnd = pygame.mixer.Sound("assets/click.mp3")

circimg = pygame.image.load("assets/circle.png")
rectimg = pygame.image.load("assets/rectangle.png")

circache = {}
rectcache = {}

def getcircle(size, color=None):
    col = tuple(color) if color else None
    key = (size, col)
    if key not in circache:
        scaled = pygame.transform.scale(circimg, (size, size))
        if color:
            scaled = scaled.copy()
            scaled.fill(color, special_flags=pygame.BLEND_MULT)
        circache[key] = scaled
    return circache[key]

def getrectangle(w, h, color=None):
    col = tuple(color) if color else None
    key = (w, h, col)
    if key not in rectcache:
        scaled = pygame.transform.scale(rectimg, (w, h))
        if color:
            scaled = scaled.copy()
            scaled.fill(color, special_flags=pygame.BLEND_MULT)
        rectcache[key] = scaled
    return rectcache[key]

allskills = []
currentcharacter = "medic"
savedpositions = {
    "medic": {},
    "gambler": {},
    "markiplier": {}
}

playerlevel = 1
hexsize = 55
hexheight = math.sqrt(3) * hexsize
boardradius = 8
hexpickdistance = 57

hexcells = []
for q in range(-boardradius, boardradius + 1):
    for r in range(-boardradius, boardradius + 1):
        if abs(q + r) <= boardradius:
            hexcells.append((q, r))

hexpositions = {}
for cell in hexcells:
    q, r = cell
    x = hexsize * (1.5 * q) + screenwidth // 2
    y = hexheight * (r + q/2) + toparea // 2
    hexpositions[cell] = (int(x), int(y))

class button:
    def __init__(self, img, hoverimg, x, y, txt):
        self.norm = img
        self.hover = hoverimg
        self.cur = img
        self.rect = img.get_rect(center=(x, y))
        self.txtsurf = bigfont.render(txt, True, pygame.Color("white"))

    def draw(self, mouse):
        self.cur = self.hover if self.rect.collidepoint(mouse) else self.norm
        screen.blit(self.cur, self.rect)
        trect = self.txtsurf.get_rect(center=self.rect.center)
        screen.blit(self.txtsurf, trect)

    def clicked(self, mouse):
        if self.rect.collidepoint(mouse):
            clicksnd.play()
            return True
        return False


class skill:
    def __init__(self, name, desc, col, pos, stype, trig):
        self.name = name
        self.desc = desc
        self.col = col
        self.x, self.y = pos
        self.homex, self.homey = pos
        self.rad = 37
        self.cell = None
        self.stype = stype
        self.trig = trig
        self.active = False
        self.trigcount = 0

    def activate(self, state, allsk, actthisflip):
        if self.trigcount >= 3:
            return
        self.trigcount += 1
        self.active = True
        cv = state.get('charvar', 0)
        
        if self.name == "BITE OF '82":
            added = 5000 + 2000 * cv
            state['points'] += added
            print(f"{self.name} ADDED {added} POINTS! (TRIGGER #{self.trigcount})")
        elif self.name == "BITE OF '83":
            added = 3.0 + 1.5 * cv
            state['mult'] += added
            print(f"{self.name} ADDED MULT {added:.2f}! (TRIGGER #{self.trigcount})")
        elif self.name == "BITE OF '84":
            adj = self.getadjacentskills(allsk)
            totrig = 4 if cv > 3 else 2
            random.shuffle(adj)
            c = 0
            for s in adj:
                if s.trigcount < 3:
                    s.activate(state, allsk, actthisflip)
                    c += 1
                    if c >= totrig:
                        break
            print(f"{self.name} TRIGGERED {c} ADJACENT. (TRIGGER #{self.trigcount})")
        elif self.name == "BITE OF '85":
            state['points'] += 50000
            state['charvar'] = 0
            print(f"{self.name} ADDED 50000 POINTS AND RESET WARFSTACHE TO 0! (TRIGGER #{self.trigcount})")
        elif self.name == "BITE OF '86":
            if cv == 0:
                state['mult'] += 8.0
                print(f"{self.name} ADDED MULT 8.00 (WARFSTACHE 0). (TRIGGER #{self.trigcount})")
            else:
                state['mult'] += 2.0
                print(f"{self.name} ADDED MULT 2.00 (WARFSTACHE >0). (TRIGGER #{self.trigcount})")
        elif self.name == "BITE OF '87":
            if cv == 0:
                adj = self.getadjacentskills(allsk)
                c = 0
                for s in adj:
                    if s.trigcount < 3:
                        s.activate(state, allsk, actthisflip)
                        c += 1
                print(f"{self.name} TRIGGERED {c} ADJACENT (DARKIPLIER). (TRIGGER #{self.trigcount})")
            else:
                print(f"{self.name} DID NOTHING (WARFSTACHE != 0). (TRIGGER #{self.trigcount})")
        elif self.name == "COMBAT TRIAGE":
            added = 3000 * cv
            state['points'] += added
            print(f"{self.name} ADDED {added} POINTS! (TRIGGER #{self.trigcount})")
        elif self.name == "FIELD SURGERY":
            added = 2.5 * cv
            state['mult'] += added
            print(f"{self.name} ADDED MULT {added:.2f}! (TRIGGER #{self.trigcount})")
        elif self.name == "EMERGENCY PROTOCOL":
            adj = self.getadjacentskills(allsk)
            if not adj:
                print(f"{self.name} HAD NO ADJACENT TO TRIGGER. (TRIGGER #{self.trigcount})")
            else:
                random.shuffle(adj)
                trigged = []
                for s in adj:
                    if s.trigcount < 3 and len(trigged) < 2:
                        s.activate(state, allsk, actthisflip)
                        trigged.append(s)
                for fst in trigged:
                    sec = fst.getadjacentskills(allsk)
                    random.shuffle(sec)
                    for s2 in sec:
                        if s2.trigcount < 3:
                            s2.activate(state, allsk, actthisflip)
                            print(f"{self.name} CHAIN TRIGGERED {s2.name}. (TRIGGER #{self.trigcount})")
                            break
        elif self.name == "PREVENTIVE MEDICINE":
            state['points'] += 30000
            print(f"{self.name} ADDED 30000 POINTS. (TRIGGER #{self.trigcount})")
            if cv > 4:
                adj = self.getadjacentskills(allsk)
                random.shuffle(adj)
                c = 0
                for s in adj:
                    if s.trigcount < 3:
                        s.activate(state, allsk, actthisflip)
                        c += 1
                        if c >= 2:
                            break
                print(f"{self.name} ADDITIONALLY TRIGGERED {c} NODES DUE TO HIGH BATTLE BONUS.")
        elif self.name == "STIMULANT OVERDOSE":
            if cv > 5:
                state['mult'] += 12.0
                print(f"{self.name} ADDED MULT 12.00 (BATTLE BONUS > 5). (TRIGGER #{self.trigcount})")
            else:
                state['mult'] += 3.0
                print(f"{self.name} ADDED MULT 3.00 (BATTLE BONUS <= 5). (TRIGGER #{self.trigcount})")
        elif self.name == "MASS CASUALTY":
            adj = self.getadjacentskills(allsk)
            c = 0
            for s in adj:
                if s.trig == self.trig and s.trigcount < 3:
                    s.activate(state, allsk, actthisflip)
                    c += 1
            print(f"{self.name} TRIGGERED {c} ADJACENT MATCHING NODES. (TRIGGER #{self.trigcount})")
        elif self.name == "LUCKY STREAK":
            added = 4000 * cv
            state['points'] += added
            print(f"{self.name} ADDED {added} POINTS! (TRIGGER #{self.trigcount})")
        elif self.name == "COMPOUNDING RETURNS":
            added = 2.0 * cv
            state['mult'] += added
            print(f"{self.name} ADDED MULT {added:.2f}! (TRIGGER #{self.trigcount})")
        elif self.name == "MOMENTUM PLAY":
            adj = self.getadjacentskills(allsk)
            if not adj:
                print(f"{self.name} HAD NO ADJACENT TO TRIGGER. (TRIGGER #{self.trigcount})")
            else:
                limit = min(5, cv)
                random.shuffle(adj)
                c = 0
                for s in adj:
                    if s.trigcount < 3:
                        s.activate(state, allsk, actthisflip)
                        c += 1
                        if c >= limit:
                            break
                print(f"{self.name} TRIGGERED {c} ADJACENT (LIMIT {limit}). (TRIGGER #{self.trigcount})")
        elif self.name == "INSURANCE POLICY":
            state['points'] += 100000
            print(f"{self.name} ADDED 100000 POINTS! (TRIGGER #{self.trigcount})")
        elif self.name == "CALCULATED LOSS":
            state['mult'] += 10.0
            print(f"{self.name} ADDED MULT 10.00! (TRIGGER #{self.trigcount})")
        elif self.name == "HOUSE EDGE":
            adj = self.getadjacentskills(allsk)
            if not adj:
                print(f"{self.name} HAD NO ADJACENT TO TRIGGER. (TRIGGER #{self.trigcount})")
            else:
                best = None
                bestcount = -1
                for s in adj:
                    cnt = len(s.getadjacentskills(allsk))
                    if cnt > bestcount and s.trigcount < 3:
                        bestcount = cnt
                        best = s
                if best:
                    best.activate(state, allsk, actthisflip)
                    if best.trigcount < 3:
                        best.activate(state, allsk, actthisflip)
                    print(f"{self.name} TRIGGERED {best.name} TWICE (HAD {bestcount} ADJACENT). (TRIGGER #{self.trigcount})")
                else:
                    print(f"{self.name} FOUND NO ELIGIBLE ADJACENT TO TRIGGER. (TRIGGER #{self.trigcount})")
        else:
            if self.stype == "points":
                state['points'] += 5000
                print(f"{self.name} (DEFAULT) ADDED 5000 POINTS! (TRIGGER #{self.trigcount})")
            elif self.stype == "mult":
                state['mult'] += 2.0
                print(f"{self.name} (DEFAULT) ADDED MULT 2.0! (TRIGGER #{self.trigcount})")
            elif self.stype == "trigger":
                state['points'] += 2000
                print(f"{self.name} (DEFAULT) TRIGGERED ADJACENT! (TRIGGER #{self.trigcount})")
                self.triggeradjacent(allsk, state, actthisflip)

    def triggeradjacent(self, allsk, state, actthisflip):
        adj = self.getadjacentskills(allsk)
        for s in adj:
            if s.trigcount < 3:
                s.activate(state, allsk, actthisflip)

    def getadjacentskills(self, allsk):
        if self.cell is None:
            return []
        q, r = self.cell
        neigh = [
            (q+1, r), (q-1, r),
            (q, r+1), (q, r-1),
            (q+1, r-1), (q-1, r+1)
        ]
        adj = []
        for s in allsk:
            if s.cell in neigh:
                adj.append(s)
        return adj

    def draw(self, sx, sy, inv):
        if self.cell is not None:
            bx, by = hexpositions[self.cell]
            px = bx + sx
            py = by + sy
        else:
            px = self.x
            py = self.y - inv
        drawcol = pygame.Color("gold") if self.active else self.col
        size = self.rad * 2
        circ = getcircle(size, drawcol)
        screen.blit(circ, (int(px - self.rad), int(py - self.rad)))
        
        words = self.name.split()
        lines = []
        current_line = []
        max_width = self.rad * 3
        
        for word in words:
            test_line = ' '.join(current_line + [word])
            test_surf = smallfont.render(test_line, True, pygame.Color("white"))
            if test_surf.get_width() <= max_width:
                current_line.append(word)
            else:
                if current_line:
                    lines.append(' '.join(current_line))
                current_line = [word]
        if current_line:
            lines.append(' '.join(current_line))
        
        line_height = smallfont.get_height()
        total_height = line_height * len(lines)
        start_y = py - total_height // 2
        
        max_line_width = max(smallfont.render(line, True, pygame.Color("white")).get_width() for line in lines)
        pad = 4
        rw = max_line_width + pad * 2
        rh = total_height + pad
        rect = getrectangle(rw, rh).copy()
        rect.set_alpha(64)
        screen.blit(rect, (px - max_line_width//2 - pad, start_y - pad//2))
        
        for i, line in enumerate(lines):
            txt = smallfont.render(line, True, pygame.Color("white"))
            tw = txt.get_width()
            screen.blit(txt, (px - tw//2, start_y + i * line_height))
        
        if self.cell is not None:
            ttxt = tinyfont.render(self.trig, True, pygame.Color("yellow"))
            screen.blit(ttxt, (px - ttxt.get_width()//2, py + 20))

    def ishovered(self, mouse, sx, sy, inv):
        mx, my = mouse
        if self.cell is not None:
            bx, by = hexpositions[self.cell]
            ax = bx + sx
            ay = by + sy
        else:
            ax = self.x
            ay = self.y - inv
        dist = math.sqrt((mx - ax)**2 + (my - ay)**2)
        return dist <= self.rad
    
def mainmenu():
    btn = pygame.transform.scale(pygame.image.load("assets/button.png"), (200, 80))
    hov = pygame.transform.scale(pygame.image.load("assets/buttonhover.png"), (200, 80))
    bg = pygame.transform.scale(pygame.image.load("assets/background.png"), (screenwidth, screenheight))
    bg.set_alpha(255)
    
    playbtn = button(btn, hov, screenwidth//5*1, 70, "PLAY")
    skillbtn = button(btn, hov, screenwidth//5*2, 70, "SKILLS")
    optbtn = button(btn, hov, screenwidth//5*3, 70, "OPTIONS")
    quitbtn = button(btn, hov, screenwidth//5*4, 70, "QUIT")
    
    while True:
        m = pygame.mouse.get_pos()
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.MOUSEBUTTONDOWN:
                if playbtn.clicked(m):
                    b = [s for s in allskills if s.cell is not None]
                    if len(b) >= 4:
                        return "play"
                if skillbtn.clicked(m):
                    return "skills"
                if optbtn.clicked(m):
                    return "options"
                if quitbtn.clicked(m):
                    return "quit"
        
        screen.fill(pygame.Color("gray20"))
        screen.blit(bg, (0, 0))
        playbtn.draw(m)
        skillbtn.draw(m)
        optbtn.draw(m)
        quitbtn.draw(m)
        
        
        b = [s for s in allskills if s.cell is not None]
        skill_count = len(b)
        if skill_count < 4:
            warning = tinyfont.render(f"NEED 4+ SKILLS TO PLAY ({skill_count}/4)", True, pygame.Color("red"))
            warning_rect = warning.get_rect(center=(screenwidth//5*1, 120))
            
            padding = 6
            bg_rect = pygame.Surface((warning_rect.width + padding * 2, warning_rect.height + padding * 2))
            bg_rect.set_alpha(128)
            bg_rect.fill(pygame.Color("black"))
            screen.blit(bg_rect, (warning_rect.x - padding, warning_rect.y - padding))
            
            screen.blit(warning, warning_rect)
        
        
        credit = smallfont.render("MUSIC MADE BY SENTRYTURBO ON NEWGROUNDS", True, pygame.Color("white"))
        credit_rect = credit.get_rect(center=(screenwidth//2, screenheight - 30))
        
        padding = 10
        bg_rect = pygame.Surface((credit_rect.width + padding * 2, credit_rect.height + padding * 2))
        bg_rect.set_alpha(128)
        bg_rect.fill(pygame.Color("black"))
        screen.blit(bg_rect, (credit_rect.x - padding, credit_rect.y - padding))
        
        screen.blit(credit, credit_rect)
        
        pygame.display.update()
        clock.tick(fps)


def genoppboard(ch):
    sx = 550
    sy = toparea + 137
    
    if ch == "medic":
        data = [
            ("COMBAT TRIAGE", "GAIN 3K POINTS PER BATTLE BONUS", pygame.Color("lightsalmon"), "points", "tails"),
            ("FIELD SURGERY", "GAIN 2.5 MULT PER BATTLE BONUS", pygame.Color("lightblue"), "mult", "tails"),
            ("EMERGENCY PROTOCOL", "TRIGGER 2 ADJACENT, CHAIN TWICE", pygame.Color("plum"), "trigger", "tails"),
            ("PREVENTIVE MEDICINE", "GAIN 30K POINTS, TRIGGER 2 IF BB>4", pygame.Color("lightyellow"), "points", "heads"),
            ("STIMULANT OVERDOSE", "GAIN 12 MULT IF BB>5, ELSE 3", pygame.Color("lightcoral"), "mult", "heads"),
            ("MASS CASUALTY", "TRIGGER ALL MATCHING ADJACENT", pygame.Color("powderblue"), "trigger", "heads")
        ]
        place = [(0, 0), (-1, 0), (1, 0), (0, -1), (-1, 1), (1, -1)]
    elif ch == "gambler":
        data = [
            ("LUCKY STREAK", "GAIN 4K POINTS PER RISK", pygame.Color("darkseagreen"), "points", "heads"),
            ("COMPOUNDING RETURNS", "GAIN 2 MULT PER RISK", pygame.Color("lightgray"), "mult", "heads"),
            ("MOMENTUM PLAY", "TRIGGER X ADJ (X=RISK, MAX5)", pygame.Color("lightgreen"), "trigger", "heads"),
            ("INSURANCE POLICY", "GAIN 100K POINTS", pygame.Color("palegreen"), "points", "tails"),
            ("CALCULATED LOSS", "GAIN 10 MULT", pygame.Color("gainsboro"), "mult", "tails"),
            ("HOUSE EDGE", "TRIGGER BEST CONNECTED TWICE", pygame.Color("darkgray"), "trigger", "tails")
        ]
        place = [(0, 0), (1, 0), (0, 1), (-1, 0), (0, -1), (1, -1)]
    else:
        data = [
            ("BITE OF '82", "GAIN 5K + 2K PER WARFSTACHE", pygame.Color("lightcoral"), "points", "heads"),
            ("BITE OF '83", "GAIN 3 + 1.5 PER WARFSTACHE", pygame.Color("tan"), "mult", "heads"),
            ("BITE OF '84", "TRIGGER 2 OR 4", pygame.Color("lightsalmon"), "trigger", "heads"),
            ("BITE OF '85", "GAIN 50K, RESET WARFSTACHE", pygame.Color("lightpink"), "points", "tails"),
            ("BITE OF '86", "GAIN 8 OR 2", pygame.Color("rosybrown"), "mult", "tails"),
            ("BITE OF '87", "TRIGGER ALL IF WARFSTACHE=0", pygame.Color("peachpuff"), "trigger", "tails")
        ]
        place = [(0, 0), (-1, 1), (1, 0), (0, -1), (-1, 0), (0, 1)]
    
    out = []
    for i, (n, d, c, tg, tr) in enumerate(data):
        if i < 3:
            x = sx + i * 200
            y = sy
        else:
            x = sx + (i - 3) * 200
            y = sy + 100
        s = skill(n, d, c, (x, y), tg, tr)
        cell = place[i]
        s.cell = cell
        s.x, s.y = hexpositions[cell]
        out.append(s)
    return out

def playloop():
    global currentcharacter, allskills
    
    
    pygame.mixer.music.stop()
    musicchoice = random.choice(["assets/music1.mp3", "assets/music2.mp3", "assets/music3.mp3"])
    pygame.mixer.music.load(musicchoice)
    pygame.mixer.music.play(-1)
    pygame.mixer.music.set_volume(musicvolume)
    
    oppchar = random.choice(["medic", "gambler", "markiplier"])
    oppskills = genoppboard(oppchar)
    
    paused = False
    flipping = False
    flipres = None
    fliptime = 0
    flipframe = 0
    rndover = False
    playerwin = False
    
    pw = 0
    ow = 0
    flipnum = 0
    
    actlog = []
    showlog = False
    logi = 0
    logt = 0
    logdelay = 30
    
    coinframes = []
    for i in range(1, 25):
        fr = pygame.image.load(f"assets/coinanim/{i}.png")
        fr = pygame.transform.scale(fr, (fr.get_width()//2, fr.get_height()//2))
        coinframes.append(fr)
    
    chasnd = pygame.mixer.Sound("assets/chaching.mp3")
    
    bg = pygame.transform.scale(pygame.image.load("assets/background.png"), (screenwidth, screenheight))
    bg.set_alpha(26)
    btn = pygame.transform.scale(pygame.image.load("assets/button.png"), (200, 80))
    hov = pygame.transform.scale(pygame.image.load("assets/buttonhover.png"), (200, 80))
    
    flipbtn = button(btn, hov, screenwidth//2, screenheight - 100, "FLIP COIN")
    
    panelw = 350
    panelh = 180
    
    circ40cache = {}
    
    
    resov = pygame.Surface((screenwidth, screenheight))
    resov.set_alpha(200)
    resov.fill(pygame.Color("gray20"))
    
    pasov = getrectangle(screenwidth, screenheight)
    pasov.set_alpha(128)
    
    gamestate = {'points': 0, 'mult': 1.0, 'charvar': 0}
    oppstate = {'points': 0, 'mult': 1.0, 'charvar': 0}
    
    while True:
        m = pygame.mouse.get_pos()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                
                pygame.mixer.music.stop()
                pygame.mixer.music.load("assets/cat.mp3")
                pygame.mixer.music.play(-1)
                pygame.mixer.music.set_volume(musicvolume)
                return "quit"
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_ESCAPE:
                    
                    pygame.mixer.music.stop()
                    pygame.mixer.music.load("assets/cat.mp3")
                    pygame.mixer.music.play(-1)
                    pygame.mixer.music.set_volume(musicvolume)
                    return "menu"
                if e.key == pygame.K_SPACE:
                    paused = not paused
            if e.type == pygame.MOUSEBUTTONDOWN:
                if flipbtn.clicked(m) and not flipping and not rndover:
                    showlog = False
                    actlog = []
                    flipping = True
                    fliptime = 72
                    flipframe = 0
                    flipres = random.choice(["heads", "tails"])
                    print(f"COIN FLIP: {flipres}")
        
        if not paused and flipping:
            fliptime -= 1
            flipframe += 1
            
            if fliptime <= 0:
                flipping = False
                flipnum += 1
                
                prevcv = gamestate.get('charvar', 0)
                prevoppcv = oppstate.get('charvar', 0)
                
                gamestate = {'points': 0, 'mult': 1.0, 'charvar': prevcv}
                oppstate = {'points': 0, 'mult': 1.0, 'charvar': prevoppcv}
                
                for s in allskills:
                    s.active = False
                    s.trigcount = 0
                for s in oppskills:
                    s.active = False
                    s.trigcount = 0
                
                actlog = []
                triglist = []
                
                for s in allskills:
                    if s.cell is not None and s.trig == flipres:
                        p0 = gamestate['points']
                        m0 = gamestate['mult']
                        s.activate(gamestate, allskills, triglist)
                        pg = gamestate['points'] - p0
                        mg = gamestate['mult'] - m0
                        if pg > 0:
                            if pg >= 1000:
                                actlog.append(f"{s.name} (+{pg//1000}K POINTS)")
                            else:
                                actlog.append(f"{s.name} (+{pg} POINTS)")
                        if mg > 0:
                            actlog.append(f"{s.name} (+{mg:.1f}X MULT)")
                
                if currentcharacter == "medic":
                    if flipres == "tails":
                        gamestate['charvar'] += 1
                    else:
                        gamestate['charvar'] = max(0, gamestate['charvar'] - 2)
                elif currentcharacter == "gambler":
                    if flipres == "heads":
                        gamestate['charvar'] += 2
                    else:
                        gamestate['charvar'] = 0
                else:
                    if flipres == "heads":
                        gamestate['charvar'] += 1
                    else:
                        gamestate['charvar'] = max(0, gamestate['charvar'] - 2)
                
                oppflip = random.choice(["heads", "tails"])
                triglist2 = []
                for s in oppskills:
                    if s.cell is not None and s.trig == oppflip:
                        s.activate(oppstate, oppskills, triglist2)
                
                if oppchar == "medic":
                    if oppflip == "tails":
                        oppstate['charvar'] += 1
                    else:
                        oppstate['charvar'] = max(0, oppstate['charvar'] - 2)
                elif oppchar == "gambler":
                    if oppflip == "heads":
                        oppstate['charvar'] += 2
                    else:
                        oppstate['charvar'] = 0
                else:
                    if oppflip == "heads":
                        oppstate['charvar'] += 1
                    else:
                        oppstate['charvar'] = max(0, oppstate['charvar'] - 2)
                
                if len(actlog) > 0:
                    showlog = True
                    logi = 1
                    chasnd.play()
                    logt = logdelay
                
                ps = int(gamestate['points'] * gamestate['mult']) + gamestate['charvar']
                os = int(oppstate['points'] * oppstate['mult']) + oppstate['charvar']
                
                if ps > os:
                    pw += 1
                    print(f"PLAYER WON FLIP {flipnum}! SCORE: {pw}-{ow} (PLAYER: {ps}, OPPONENT: {os})")
                elif os > ps:
                    ow += 1
                    print(f"OPPONENT WON FLIP {flipnum}! SCORE: {pw}-{ow} (PLAYER: {ps}, OPPONENT: {os})")
                else:
                    print(f"FLIP {flipnum} TIED! SCORE: {pw}-{ow} (BOTH: {ps})")
                
                if pw >= 4:
                    rndover = True
                    playerwin = True
                elif ow >= 4:
                    rndover = True
                    playerwin = False
        
        if showlog and not paused:
            logt -= 1
            if logt <= 0:
                if logi < len(actlog):
                    logi += 1
                    chasnd.play()
                    logt = logdelay
        
        ps = int(gamestate['points'] * gamestate['mult']) + gamestate['charvar']
        os = int(oppstate['points'] * oppstate['mult']) + oppstate['charvar']
        
        screen.fill(pygame.Color("gray20"))
        screen.blit(bg, (0, 0))
        
        t = bigfont.render(f"PLAYING AS: {currentcharacter.upper()}", True, pygame.Color("white"))
        screen.blit(t, (50, 10))
        
        ot = bigfont.render(f"OPPONENT: {oppchar.upper()}", True, pygame.Color("red"))
        screen.blit(ot, (screenwidth - 350, 10))
        
        bst = bigfont.render(f"BEST OF 7: {pw}-{ow}", True, pygame.Color("yellow"))
        screen.blit(bst, (screenwidth//2 - bst.get_width()//2, 10))
        
        fc = smallfont.render(f"FLIP #{flipnum + 1}" if not rndover else f"FINAL FLIP: #{flipnum}", True, pygame.Color("gray70"))
        screen.blit(fc, (screenwidth//2 - fc.get_width()//2, 45))
        
        cx = screenwidth // 2
        cy = screenheight // 2 - 125
        
        if flipping:
            fr = coinframes[flipframe % 24]
            screen.blit(fr, (cx - fr.get_width()//2, cy - fr.get_height()//2))
        elif flipres:
            fr = coinframes[0 if flipres == "heads" else 12]
            screen.blit(fr, (cx - fr.get_width()//2, cy - fr.get_height()//2))
            rt = bigfont.render(f"RESULT: {flipres.upper()}", True, pygame.Color("yellow"))
            screen.blit(rt, (screenwidth//2 - rt.get_width()//2, screenheight//2 + 40))
        
        if showlog and actlog:
            sy = screenheight // 2 + 80
            for i in range(min(logi, len(actlog))):
                lg = smallfont.render(actlog[i], True, pygame.Color("gold"))
                screen.blit(lg, (screenwidth//2 - lg.get_width()//2, sy + i * 25))
        
        py = 80
        panel_rect = pygame.Rect(50, py, panelw, panelh)
        pygame.draw.rect(screen, pygame.Color("gray15"), panel_rect)
        pygame.draw.rect(screen, pygame.Color("gray40"), panel_rect, 2)
        
        p1 = smallfont.render("POINTS:", True, pygame.Color("lightblue"))
        pv = smallfont.render(str(gamestate['points']), True, pygame.Color("white"))
        screen.blit(p1, (70, py + 20))
        screen.blit(pv, (70, py + 45))
        
        m1 = smallfont.render("MULT:", True, pygame.Color("lightgreen"))
        mv = smallfont.render(f"X{gamestate['mult']:.2f}", True, pygame.Color("white"))
        screen.blit(m1, (200, py + 20))
        screen.blit(mv, (200, py + 45))
        
        cn = "BATTLE BONUS" if currentcharacter == "medic" else "RISK" if currentcharacter == "gambler" else "WARFSTACHE"
        c1 = smallfont.render(f"{cn}:", True, pygame.Color("yellow"))
        cvv = smallfont.render(str(gamestate['charvar']), True, pygame.Color("white"))
        screen.blit(c1, (70, py + 85))
        screen.blit(cvv, (70, py + 110))
        
        sc1 = smallfont.render("THIS FLIP:", True, pygame.Color("gold"))
        scv = bigfont.render(str(ps), True, pygame.Color("gold"))
        screen.blit(sc1, (200, py + 85))
        screen.blit(scv, (200, py + 110))
        
        opp_panel_rect = pygame.Rect(screenwidth - 400, py, panelw, panelh)
        pygame.draw.rect(screen, pygame.Color("gray15"), opp_panel_rect)
        pygame.draw.rect(screen, pygame.Color("gray40"), opp_panel_rect, 2)
        
        op1 = smallfont.render("POINTS:", True, pygame.Color("lightblue"))
        opv = smallfont.render(str(oppstate['points']), True, pygame.Color("white"))
        screen.blit(op1, (screenwidth - 380, py + 20))
        screen.blit(opv, (screenwidth - 380, py + 45))
        
        om1 = smallfont.render("MULT:", True, pygame.Color("lightgreen"))
        omv = smallfont.render(f"X{oppstate['mult']:.2f}", True, pygame.Color("white"))
        screen.blit(om1, (screenwidth - 230, py + 20))
        screen.blit(omv, (screenwidth - 230, py + 45))
        
        ocn = "BATTLE BONUS" if oppchar == "medic" else "RISK" if oppchar == "gambler" else "WARFSTACHE"
        oc1 = smallfont.render(f"{ocn}:", True, pygame.Color("yellow"))
        ocv = smallfont.render(str(oppstate['charvar']), True, pygame.Color("white"))
        screen.blit(oc1, (screenwidth - 380, py + 85))
        screen.blit(ocv, (screenwidth - 380, py + 110))
        
        osc1 = smallfont.render("THIS FLIP:", True, pygame.Color("gold"))
        oscv = bigfont.render(str(os), True, pygame.Color("gold"))
        screen.blit(osc1, (screenwidth - 230, py + 85))
        screen.blit(oscv, (screenwidth - 230, py + 110))
        
        boardy = 300
        pbt = smallfont.render("YOUR BOARD:", True, pygame.Color("white"))
        screen.blit(pbt, (50, boardy))
        
        bskills = [s for s in allskills if s.cell is not None]
        for i, s in enumerate(bskills):
            circx = 70
            circy = boardy + 40 + i * 50
            dcol = pygame.Color("gold") if s.active else s.col
            ck = tuple(dcol)
            if ck not in circ40cache:
                circ40cache[ck] = getcircle(40, dcol)
            screen.blit(circ40cache[ck], (circx - 20, circy - 20))
            stxt = tinyfont.render(f"{s.name} ({s.trig})", True, pygame.Color("white"))
            screen.blit(stxt, (100, circy - 10))
            ttxt = tinyfont.render(s.stype, True, pygame.Color("gray70"))
            screen.blit(ttxt, (100, circy + 5))
        
        obt = smallfont.render("OPPONENT BOARD:", True, pygame.Color("red"))
        screen.blit(obt, (screenwidth - 400, boardy))
        
        obs = [s for s in oppskills if s.cell is not None]
        for i, s in enumerate(obs):
            circx = screenwidth - 380
            circy = boardy + 40 + i * 50
            dcol = pygame.Color("gold") if s.active else s.col
            ck = tuple(dcol)
            if ck not in circ40cache:
                circ40cache[ck] = getcircle(40, dcol)
            screen.blit(circ40cache[ck], (circx - 20, circy - 20))
            stxt = tinyfont.render(f"{s.name} ({s.trig})", True, pygame.Color("white"))
            screen.blit(stxt, (screenwidth - 350, circy - 10))
            ttxt = tinyfont.render(s.stype, True, pygame.Color("gray70"))
            screen.blit(ttxt, (screenwidth - 350, circy + 5))
        
        if not rndover:
            flipbtn.draw(m)
        
        if rndover:
            screen.blit(resov, (0, 0))
            rt = bigfont.render("YOU WIN!" if playerwin else "YOU LOSE!", True, pygame.Color("green") if playerwin else pygame.Color("red"))
            screen.blit(rt, (screenwidth//2 - rt.get_width()//2, screenheight//2 - 50))
            st = smallfont.render(f"FINAL: {pw}-{ow}", True, pygame.Color("white"))
            screen.blit(st, (screenwidth//2 - st.get_width()//2, screenheight//2 + 10))
            ct = tinyfont.render("PRESS ESC TO RETURN TO MENU", True, pygame.Color("gray70"))
            screen.blit(ct, (screenwidth//2 - ct.get_width()//2, screenheight//2 + 60))
        
        if paused:
            screen.blit(pasov, (0, 0))
            pt = bigfont.render("PAUSED", True, pygame.Color("white"))
            screen.blit(pt, (screenwidth//2 - pt.get_width()//2, screenheight//2))
        
        pygame.display.update()
        clock.tick(fps)

def optionsmenu():
    global musicvolume
    
    btn = pygame.transform.scale(pygame.image.load("assets/button.png"), (200, 80))
    hov = pygame.transform.scale(pygame.image.load("assets/buttonhover.png"), (200, 80))
    bg = pygame.transform.scale(pygame.image.load("assets/background.png"), (screenwidth, screenheight))
    bg.set_alpha(26)
    
    back = button(btn, hov, screenwidth//2, screenheight - 80, "BACK")
    
    sx = screenwidth//2 - 200
    sy = screenheight//2
    sw = 400
    sh = 6
    kx = sx + int(sw * musicvolume)
    ky = sy + sh//2
    kr = 10
    dragging = False
    
    knob = getcircle(kr * 2, pygame.Color("darkgreen"))
    
    while True:
        m = pygame.mouse.get_pos()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            if e.type == pygame.MOUSEBUTTONDOWN:
                if back.clicked(m):
                    return "menu"
                if abs(e.pos[0] - kx) < kr + 3:
                    dragging = True
            if e.type == pygame.MOUSEBUTTONUP:
                dragging = False
            if e.type == pygame.MOUSEMOTION:
                if dragging:
                    nx = e.pos[0]
                    if nx < sx:
                        nx = sx
                    if nx > sx + sw:
                        nx = sx + sw
                    kx = nx
                    musicvolume = (kx - sx) / sw
                    pygame.mixer.music.set_volume(musicvolume)
        
        screen.fill(pygame.Color("gray15"))
        screen.blit(bg, (0, 0))
        
        t = bigfont.render("OPTIONS", True, pygame.Color("white"))
        screen.blit(t, (screenwidth//2 - 70, 100))
        
        vt = bigfont.render(f"VOLUME: {int(musicvolume * 100)}%", True, pygame.Color("white"))
        screen.blit(vt, (screenwidth//2 - 120, screenheight//2 - 50))
        
        
        pygame.draw.rect(screen, pygame.Color("gray30"), (sx, sy, sw, sh))
        
        screen.blit(knob, (kx - kr, ky - kr))
        
        back.draw(m)
        
        pygame.display.update()
        clock.tick(fps)


def skillsmenu():
    global allskills, currentcharacter
    
    print(f"LOADING SKILLS FOR {currentcharacter}")
    
    btn = pygame.transform.scale(pygame.image.load("assets/button.png"), (200, 80))
    hov = pygame.transform.scale(pygame.image.load("assets/buttonhover.png"), (200, 80))
    bg = pygame.transform.scale(pygame.image.load("assets/background.png"), (screenwidth, screenheight))
    bg.set_alpha(26)
    
    back = button(btn, hov, 140, 70, "BACK")
    medicb = button(btn, hov, screenwidth - 630, 70, "MEDIC")
    gamblerb = button(btn, hov, screenwidth - 420, 70, "GAMBLER")
    markb = button(btn, hov, screenwidth - 210, 70, "MARKIPLIER")
    
    invy = toparea + 137
    invx = 550
    
    inventory = []
    
    if currentcharacter == "medic":
        data = [
            ("COMBAT TRIAGE", "GAIN 3K POINTS PER BATTLE BONUS", pygame.Color("lightsalmon"), "points", "tails"),
            ("FIELD SURGERY", "GAIN 2.5 MULT PER BATTLE BONUS", pygame.Color("lightblue"), "mult", "tails"),
            ("EMERGENCY PROTOCOL", "TRIGGER 2 ADJACENT, CHAIN TWICE", pygame.Color("plum"), "trigger", "tails"),
            ("PREVENTIVE MEDICINE", "GAIN 30K POINTS, TRIGGER 2 IF BB>4", pygame.Color("lightyellow"), "points", "heads"),
            ("STIMULANT OVERDOSE", "GAIN 12 MULT IF BB>5, ELSE 3", pygame.Color("lightcoral"), "mult", "heads"),
            ("MASS CASUALTY", "TRIGGER ALL MATCHING ADJACENT", pygame.Color("powderblue"), "trigger", "heads")
        ]
    elif currentcharacter == "gambler":
        data = [
            ("LUCKY STREAK", "GAIN 4K POINTS PER RISK LEVEL", pygame.Color("darkseagreen"), "points", "heads"),
            ("COMPOUNDING RETURNS", "GAIN 2 MULT PER RISK LEVEL", pygame.Color("lightgray"), "mult", "heads"),
            ("MOMENTUM PLAY", "TRIGGER X ADJACENT (X=RISK, MAX 5)", pygame.Color("lightgreen"), "trigger", "heads"),
            ("INSURANCE POLICY", "GAIN 100K POINTS (FIXED)", pygame.Color("palegreen"), "points", "tails"),
            ("CALCULATED LOSS", "GAIN 10 MULT (FIXED)", pygame.Color("gainsboro"), "mult", "tails"),
            ("HOUSE EDGE", "TRIGGER BEST CONNECTED TWICE", pygame.Color("darkgray"), "trigger", "tails")
        ]
    else:
        data = [
            ("BITE OF '82", "GAIN 5K POINTS + 2K PER WARFSTACHE", pygame.Color("lightcoral"), "points", "heads"),
            ("BITE OF '83", "GAIN 3 MULT + 1.5 PER WARFSTACHE", pygame.Color("tan"), "mult", "heads"),
            ("BITE OF '84", "TRIGGER 2 ADJACENT, 4 IF WARFSTACHE>3", pygame.Color("lightsalmon"), "trigger", "heads"),
            ("BITE OF '85", "GAIN 50K POINTS, RESET WARFSTACHE", pygame.Color("lightpink"), "points", "tails"),
            ("BITE OF '86", "GAIN 8 MULT IF WARFSTACHE=0, ELSE 2", pygame.Color("rosybrown"), "mult", "tails"),
            ("BITE OF '87", "TRIGGER ALL ADJACENT IF WARFSTACHE=0", pygame.Color("peachpuff"), "trigger", "tails")
        ]
    
    for i, (n, d, c, tg, tr) in enumerate(data):
        if i < 3:
            x = invx + i * 200
            y = invy
        else:
            x = invx + (i - 3) * 200
            y = invy + 100
        s = skill(n, d, c, (x, y), tg, tr)
        inventory.append(s)
    
    saved = savedpositions[currentcharacter]
    for s in inventory:
        if s.name in saved:
            savedx = saved[s.name][0][0]
            savedy = saved[s.name][0][1]
            savedcell = saved[s.name][1]
            s.x = savedx
            s.y = savedy
            s.cell = savedcell
            print(f"RESTORED {s.name} AT {savedcell}")
    
    allskills = inventory
    
    drags = None
    dox = 0
    doy = 0
    
    sx = 0
    sy = 0
    
    hovskill = None
    
    tilerad = 37
    tilesize = tilerad * 2
    tile = getcircle(tilesize, (100, 100, 100))
    tile.set_alpha(128)
    
    while True:
        m = pygame.mouse.get_pos()
        
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                return "quit"
            
            if e.type == pygame.MOUSEBUTTONDOWN:
                if back.clicked(m):
                    print("SAVING POSITIONS...")
                    savedpositions[currentcharacter] = {}
                    for s in inventory:
                        savedpositions[currentcharacter][s.name] = ((s.x, s.y), s.cell)
                    allskills = inventory
                    return "menu"
                
                if medicb.clicked(m) and currentcharacter != "medic":
                    savedpositions[currentcharacter] = {}
                    for s in inventory:
                        savedpositions[currentcharacter][s.name] = ((s.x, s.y), s.cell)
                    currentcharacter = "medic"
                    print("SWITCHED TO MEDIC")
                    return "skills"
                
                if gamblerb.clicked(m) and currentcharacter != "gambler":
                    savedpositions[currentcharacter] = {}
                    for s in inventory:
                        savedpositions[currentcharacter][s.name] = ((s.x, s.y), s.cell)
                    currentcharacter = "gambler"
                    print("SWITCHED TO GAMBLER")
                    return "skills"
                
                if markb.clicked(m) and currentcharacter != "markiplier":
                    savedpositions[currentcharacter] = {}
                    for s in inventory:
                        savedpositions[currentcharacter][s.name] = ((s.x, s.y), s.cell)
                    currentcharacter = "markiplier"
                    print("SWITCHED TO MARKIPLIER")
                    return "skills"
                
                for s in inventory:
                    if s.ishovered(m, sx, sy, 0):
                        if e.button == 3:
                            print(f"RESET {s.name}")
                            s.cell = None
                            s.x = s.homex
                            s.y = s.homey
                            break
                        if e.button == 1:
                            drags = s
                            print(f"STARTED DRAGGING {s.name}")
                            if s.cell is not None:
                                boardx = hexpositions[s.cell][0]
                                boardy = hexpositions[s.cell][1]
                                s.x = boardx + sx
                                s.y = boardy + sy
                            dox = s.x - m[0]
                            doy = s.y - m[1]
                            s.cell = None
                            break
            
            if e.type == pygame.MOUSEBUTTONUP:
                if drags is not None and e.button == 1:
                    besthex = None
                    bestdist = 999999
                    bestpix = None
                    mousex = m[0]
                    mousey = m[1]
                    
                    for cell in hexpositions:
                        hexx = hexpositions[cell][0]
                        hexy = hexpositions[cell][1]
                        tempx = hexx + sx
                        tempy = hexy + sy
                        distance = math.sqrt((mousex - tempx)**2 + (mousey - tempy)**2)
                        
                        if distance < bestdist:
                            bestdist = distance
                            besthex = cell
                            bestpix = (hexx, hexy)
                    
                    cell = None
                    pixel = None
                    if bestdist < hexpickdistance:
                        cell = besthex
                        pixel = bestpix
                    
                    if cell is not None:
                        celltaken = False
                        for s in inventory:
                            if s.cell == cell:
                                celltaken = True
                                break
                        
                        if not celltaken:
                            drags.cell = cell
                            drags.x = pixel[0]
                            drags.y = pixel[1]
                            clicksnd.play()
                            print(f"PLACED {drags.name} AT {cell}")
                        else:
                            drags.x = drags.homex
                            drags.y = drags.homey
                            drags.cell = None
                    else:
                        drags.x = drags.homex
                        drags.y = drags.homey
                        drags.cell = None
                    drags = None
            
            if e.type == pygame.MOUSEMOTION:
                if drags is not None:
                    drags.x = m[0] + dox
                    drags.y = m[1] + doy
            
            if e.type == pygame.MOUSEWHEEL:
                sy += e.y * 30
            
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_UP:
                    sy += 30
                if e.key == pygame.K_DOWN:
                    sy -= 30
                if e.key == pygame.K_LEFT:
                    sx += 30
                if e.key == pygame.K_RIGHT:
                    sx -= 30
        
        screen.fill(pygame.Color("gray25"))
        screen.blit(bg, (0, 0))
        
        for cell in hexpositions:
            hexx = hexpositions[cell][0]
            hexy = hexpositions[cell][1]
            screenx = hexx + sx
            screeny = hexy + sy
            
            screen.blit(tile, (int(screenx - tilerad), int(screeny - tilerad)))
            
            q = cell[0]
            r = cell[1]
            coordtext = f"{q},{r}"
            coords = smallfont.render(coordtext, True, pygame.Color("gray50"))
            coords.set_alpha(128)
            screen.blit(coords, (screenx - coords.get_width()//2, screeny - coords.get_height()//2))
        
        for s in inventory:
            if s.cell is not None and s != drags:
                s.draw(sx, sy, 0)
        
        invh = int((screenheight - (toparea + 100)) * 1.2)
        invrect = pygame.Rect(0, screenheight - invh, screenwidth, invh)
        pygame.draw.rect(screen, pygame.Color("gray10"), invrect)
        
        if currentcharacter == "medic":
            charimg = pygame.image.load("assets/character2.png")
            chardesc = [
                "MEDIC",
                "",
                "signature mechanic:",
                "GAINS +1 BATTLE BONUS",
                "WHEN COIN LANDS ON TAILS",
                "LOSES 2 BATTLE BONUS",
                "WHEN COIN LANDS ON HEADS"
            ]
        elif currentcharacter == "gambler":
            charimg = pygame.image.load("assets/character3.png")
            chardesc = [
                "GAMBLER",
                "",
                "signature mechanic:",
                "GAINS +2 RISK WHEN COIN",
                "LANDS ON HEADS.",
                "LOSES ALL RISK WHEN COIN",
                "LANDS ON TAILS."
            ]
        else:
            charimg = pygame.image.load("assets/character1.png")
            chardesc = [
                "MARKIPLIER",
                "",
                "signature mechanic:",
                "GAINS +1 WARFSTACHE WHEN",
                "COIN LANDS ON HEADS.",
                "LOSES 2 WARFSTACHE WHEN",
                "COIN LANDS ON TAILS."
            ]
        
        charimg = pygame.transform.scale(charimg, (180, 180))
        
        imgx = 30
        textx = imgx + 200
        
        imgy = toparea + 120
        
        screen.blit(charimg, (imgx, imgy))
        
        texty = imgy
        lineheight = tinyfont.get_height() + 2
        for i in range(len(chardesc)):
            line = chardesc[i]
            if i == 0:
                txt = smallfont.render(line, True, pygame.Color("white"))
            else:
                txt = tinyfont.render(line, True, pygame.Color("white"))
            screen.blit(txt, (textx, texty + i * lineheight))
        
        for s in inventory:
            if s.cell is None and s != drags:
                s.draw(sx, sy, 0)
        
        if drags is not None:
            drags.draw(0, 0, 0)
        
        medicb.draw(m)
        gamblerb.draw(m)
        markb.draw(m)
        
        if currentcharacter == "medic":
            screen.blit(hov, medicb.rect)
            trect = medicb.txtsurf.get_rect(center=medicb.rect.center)
            screen.blit(medicb.txtsurf, trect)
        if currentcharacter == "gambler":
            screen.blit(hov, gamblerb.rect)
            trect = gamblerb.txtsurf.get_rect(center=gamblerb.rect.center)
            screen.blit(gamblerb.txtsurf, trect)
        if currentcharacter == "markiplier":
            screen.blit(hov, markb.rect)
            trect = markb.txtsurf.get_rect(center=markb.rect.center)
            screen.blit(markb.txtsurf, trect)
        
        hovskill = None
        for s in inventory:
            if s.ishovered(m, sx, sy, 0):
                hovskill = s
                break
        
        if hovskill:
            if hovskill.cell != None:
                boardx = hexpositions[hovskill.cell][0]
                boardy = hexpositions[hovskill.cell][1]
                pixelx = boardx + sx
                pixely = boardy + sy
            else:
                pixelx = hovskill.x
                pixely = hovskill.y
            
            desctext = hovskill.desc
            textsurf = smallfont.render(desctext, True, pygame.Color("white"))
            textwidth = textsurf.get_width()
            textheight = textsurf.get_height()
            
            padding = 8
            boxwidth = textwidth + padding * 2
            boxheight = textheight + padding * 2
            
            tooltip_rect = pygame.Rect(pixelx - boxwidth//2, pixely - hovskill.rad - boxheight - 4, boxwidth, boxheight)
            tooltip_surf = pygame.Surface((boxwidth, boxheight))
            tooltip_surf.set_alpha(180)
            tooltip_surf.fill(pygame.Color("gray10"))
            screen.blit(tooltip_surf, tooltip_rect)
            pygame.draw.rect(screen, pygame.Color("gray40"), tooltip_rect, 1)
            screen.blit(textsurf, (pixelx - textwidth//2, pixely - hovskill.rad - boxheight - 4 + padding))
        
        back.draw(m)
        
        pygame.display.update()
        clock.tick(fps)

def rungame():
    currentscreen = "menu"
    while currentscreen != "quit":
        if currentscreen == "menu":
            currentscreen = mainmenu()
        elif currentscreen == "options":
            currentscreen = optionsmenu()
        elif currentscreen == "skills":
            currentscreen = skillsmenu()
        elif currentscreen == "play":
            currentscreen = playloop()
    pygame.quit()
    sys.exit()

rungame()
