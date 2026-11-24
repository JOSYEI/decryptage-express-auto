import os, math
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import sys
HERE=os.path.dirname(os.path.abspath(__file__))
FONTS=["/usr/share/fonts/truetype/roboto/unhinted/RobotoCondensed-Black.ttf","/usr/share/fonts/truetype/roboto/unhinted/Roboto-Black.ttf",
       "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"]
def font(s,w=900):
    for p in FONTS:
        try: return ImageFont.truetype(p,s)
        except Exception: pass
    return ImageFont.load_default()
FPS=30
def ease_out_back(t,c=1.7):
    t=min(max(t,0),1); return 1+(c+1)*(t-1)**3+c*(t-1)**2
def ease(t): t=min(max(t,0),1); return 1-(1-t)**3
LOGO=Image.open(os.path.join(HERE,'logo.jpg')).convert('RGB')
def logo_card(sz):
    l=LOGO.resize((sz,sz)); m=Image.new('L',(sz,sz),0); ImageDraw.Draw(m).rounded_rectangle((0,0,sz-1,sz-1),sz//7,fill=255)
    c=Image.new('RGBA',(sz,sz),(0,0,0,0)); c.paste(l,(0,0),m)
    ImageDraw.Draw(c).rounded_rectangle((2,2,sz-3,sz-3),sz//7,outline=(255,214,0,255),width=max(4,sz//60))
    return c
def logo_anim(out,canvas,card,n_in,n_hold,n_out,text=None,ring_at=None):
    os.makedirs(out,exist_ok=True)
    base=logo_card(card); N=n_in+n_hold+n_out
    for i in range(N):
        im=Image.new('RGBA',(canvas,canvas),(0,0,0,0)); d=ImageDraw.Draw(im)
        if i<n_in: sc=0.35+0.65*ease_out_back(i/n_in); a=min(1,i/(n_in*0.5))
        elif i<n_in+n_hold: sc=1+0.012*math.sin((i-n_in)/6); a=1
        else: sc=1+0.06*((i-n_in-n_hold)/n_out); a=1-(i-n_in-n_hold)/n_out
        # ring burst when card lands
        rb=ring_at if ring_at is not None else n_in
        if rb<=i<rb+14:
            k=(i-rb)/14; r=int(card*(0.52+0.22*k)); al=int(220*(1-k))
            d.ellipse((canvas//2-r,canvas//2-r,canvas//2+r,canvas//2+r),outline=(255,214,0,al),width=8)
        s=int(card*sc); c=base.resize((s,s),Image.LANCZOS)
        if a<1:
            al=c.getchannel('A').point(lambda v:int(v*a)); c.putalpha(al)
        im.alpha_composite(c,(canvas//2-s//2,canvas//2-s//2-(40 if text else 0)))
        if text:
            f=font(int(card*0.11)); b=d.textbbox((0,0),text,font=f,stroke_width=5)
            tw=b[2]-b[0]; col=(255,214,0,int(255*a)); 
            d.text((canvas//2-tw//2-b[0],canvas//2+card//2-40+int(card*0.07)),text,font=f,fill=col,stroke_width=5,stroke_fill=(0,0,0,int(255*a)))
        im.save(f"{out}/{i:03d}.png")
def hand(d,x,y,s,press=0):
    # pointing hand: x,y = fingertip
    W=(255,255,255,255);K=(20,20,20,255)
    yy=y+int(press*6*s)
    def rr(b,r): d.rounded_rectangle(b,r,fill=W,outline=K,width=max(2,int(3*s)))
    rr((x-int(9*s),yy,x+int(9*s),yy+int(46*s)),int(9*s))            # index finger
    rr((x-int(27*s),yy+int(34*s),x+int(40*s),yy+int(92*s)),int(14*s)) # palm
    for k in range(3):
        bx=x+int((-8+k*14)*s)
    rr((x-int(27*s),yy+int(40*s),x-int(9*s),yy+int(70*s)),int(9*s))  # thumb side
def cta(out,w,h,scale=1.0):
    os.makedirs(out,exist_ok=True); N=int(3.6*FPS)
    for i in range(N):
        t=i/FPS
        im=Image.new('RGBA',(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
        pop=ease_out_back(t/0.35); fade=1 if t<3.2 else max(0,1-(t-3.2)/0.4)
        clicked=t>=1.55
        bw,bh=int(330*scale),int(88*scale)
        cx,cy=int(w*0.38),int(h*0.40)
        press=0.0
        if 1.40<=t<1.62: press=1-abs((t-1.51)/0.11) if abs(t-1.51)<0.11 else 0
        sc=max(0.01,pop)*(1-0.07*press)
        bw2,bh2=int(bw*sc),int(bh*sc)
        col=(255,40,40,255) if not clicked else (70,70,70,255)
        txt="S'ABONNER" if not clicked else "ABONNÉ ✓"
        if clicked: txt="ABONNÉ"
        d.rounded_rectangle((cx-bw2//2,cy-bh2//2,cx+bw2//2,cy+bh2//2),int(18*scale*sc),fill=col,outline=(255,255,255,255),width=max(2,int(4*scale)))
        f=font(max(10,int(40*scale*sc)));b=d.textbbox((0,0),txt,font=f);d.text((cx-(b[2]-b[0])//2-b[0],cy-(b[3]-b[1])//2-b[1]),txt,font=f,fill=(255,255,255,255))
        # bell
        bx,by=cx+bw2//2+int(46*scale),cy
        sw=int(8*math.sin((t-1.6)*30)*max(0,1-(t-1.6)/0.8)) if clicked and t<2.5 else 0
        if pop>0.3:
            r=int(26*scale)
            d.pieslice((bx-r+sw,by-r,bx+r+sw,by+r),180,360,fill=(255,214,0,255))
            d.rectangle((bx-r+sw,by,bx+r+sw,by+int(r*0.6)),fill=(255,214,0,255))
            d.ellipse((bx-int(6*scale)+sw,by+int(r*0.6),bx+int(6*scale)+sw,by+int(r*0.6)+int(12*scale)),fill=(255,214,0,255))
        # hand movement
        if t>=0.5:
            k=ease((t-0.5)/0.9) if t<1.4 else 1
            sx,sy=w+int(40*scale),h+int(20*scale); ex,ey=cx+int(20*scale),cy+int(30*scale)
            hx=int(sx+(ex-sx)*k); hy=int(sy+(ey-sy)*k)
            hand(d,hx,hy,scale*1.0,press)
        # ripple on click
        if 1.5<=t<2.1:
            k=(t-1.5)/0.6; r=int((20+90*k)*scale); d.ellipse((cx+int(20*scale)-r,cy+int(30*scale)-r,cx+int(20*scale)+r,cy+int(30*scale)+r),outline=(255,255,255,int(200*(1-k))),width=4)
        if fade<1: im.putalpha(im.getchannel('A').point(lambda v:int(v*fade)))
        im.save(f"{out}/{i:03d}.png")
def build(out, short):
    os.makedirs(out, exist_ok=True)
    logo_anim(os.path.join(out,"logo_in"),800,520,52,12,18,None,ring_at=52)
    if short: cta(os.path.join(out,"cta"),820,380,1.3)
    else: cta(os.path.join(out,"cta"),620,300,1.0)
if __name__=="__main__": build(sys.argv[1], sys.argv[2]=="short")
