from pathlib import Path
import os, io
import numpy as np
import cv2
from PIL import Image, ImageOps
import streamlit as st
from rembg import remove, new_session

st.set_page_config(page_title="Portrait Studio Offline", layout="wide")
st.title("Portrait Studio | استودیوی پرتره")
st.caption("پردازش کاملاً محلی؛ هیچ عکسی به سرور ارسال نمی‌شود.")

@st.cache_resource
def get_session():
    home = Path(__file__).resolve().parent / "models"
    model = home / "birefnet-portrait.onnx"
    if not model.is_file():
        raise FileNotFoundError(f"Model missing: {model}")
    os.environ["U2NET_HOME"] = str(home)
    try:
        session = new_session("birefnet-portrait")
        st.session_state["active_model"] = "BiRefNet-Portrait"
        return session
    except Exception as exc:
        st.warning("مدل پرتره بارگذاری نشد؛ مدل پشتیبان U2NetP استفاده می‌شود. جزئیات: " + str(exc)[:250])
        fallback = home / "u2netp.onnx"
        if not fallback.is_file():
            raise RuntimeError("Fallback model is missing: " + str(fallback)) from exc
        session = new_session("u2netp")
        st.session_state["active_model"] = "U2NetP (Fallback)"
        return session

def studio_background(w, h, center, edge):
    y, x = np.mgrid[:h, :w].astype("float32")
    distance = np.sqrt(((x-w/2)/max(w*.73,1))**2 + ((y-h*.39)/max(h*.8,1))**2)
    f = np.clip(distance,0,1)
    gray = np.clip(center*(1-f)+edge*f,0,255).astype("uint8")
    return np.stack([gray]*3,axis=-1)

def detect_face(rgb):
    classifier = cv2.CascadeClassifier(cv2.data.haarcascades+"haarcascade_frontalface_default.xml")
    faces = classifier.detectMultiScale(cv2.cvtColor(rgb,cv2.COLOR_RGB2GRAY),1.1,5,minSize=(45,45))
    return max(faces,key=lambda b:b[2]*b[3]) if len(faces) else None

def process(img, model, bgimg, center, edge, lighting, face_override):
    src=np.asarray(ImageOps.exif_transpose(img).convert("RGB"))
    h,w=src.shape[:2]
    bg=np.asarray(ImageOps.fit(bgimg.convert("RGB"),(w,h))) if bgimg is not None else studio_background(w,h,center,edge)
    alpha=np.asarray(remove(Image.fromarray(src).convert("RGBA"),session=model).getchannel("A"),dtype="float32")/255
    if alpha.max()<.2:raise ValueError("سوژه پیدا نشد")
    face=face_override if face_override is not None else detect_face(src)
    lock=np.zeros((h,w),dtype="uint8")
    if face is not None:
        x,y,fw,fh=map(int,face)
        cv2.ellipse(lock,(x+fw//2,y+fh//2),(max(1,int(.40*fw)),max(1,int(.49*fh))),0,0,360,255,-1)
    fixed=(lock==255)&(alpha>.25)
    alpha[fixed]=1.
    fg=src.astype("float32")
    if lighting>0:
        allowed=(alpha>.9)&(lock==0)
        if allowed.any():
            factor=np.clip(float(np.median(bg))/max(float(np.median(src[allowed])),1),.85,1.15)
            fg[allowed]=fg[allowed]*(1-lighting)+np.clip(fg[allowed]*factor,0,255)*lighting
    out=np.clip(np.round(fg*alpha[:,:,None]+bg*(1-alpha[:,:,None])),0,255).astype("uint8")
    out[fixed]=src[fixed]
    assert np.array_equal(out[fixed],src[fixed])
    return Image.fromarray(out),Image.fromarray((alpha*255).astype("uint8")),Image.fromarray(lock),face is not None

with st.sidebar:
    st.header("تنظیمات")
    mode=st.radio("ورودی",["یک عکس","پوشه"])
    background=st.radio("بک‌گراند",["خاکستری استودیویی","تصویر دلخواه"])
    background_file=st.file_uploader("تصویر بک‌گراند",type=["jpg","jpeg","png","webp"]) if background=="تصویر دلخواه" else None
    center=st.slider("روشنایی مرکز",90,245,206)
    edge=st.slider("روشنایی لبه",40,220,115)
    light=st.slider("تطبیق نور خارج از چهره",0.,1.,0.,.05)
    debug=st.checkbox("ذخیره ماسک‌ها")
    manual=st.checkbox("مختصات دستی چهره")
    face=None
    if manual:
        face=tuple(st.number_input(k,0,10000,v) for k,v in [("X",0),("Y",0),("W",200),("H",250)])
bgim=Image.open(background_file).copy() if background_file else None
disabled=background=="تصویر دلخواه" and bgim is None

if mode=="یک عکس":
    uploaded=st.file_uploader("عکس پرتره",type=["jpg","jpeg","png","webp","bmp","tif","tiff"])
    if uploaded and st.button("پردازش عکس",disabled=disabled):
        try:
            with st.spinner("در حال پردازش"):
                out,mask,locked,found=process(Image.open(uploaded),get_session(),bgim,center,edge,light,face)
            a,b=st.columns(2)
            a.image(uploaded,caption="اصل تصویر",use_container_width=True)
            b.image(out,caption="نتیجه",use_container_width=True)
            data=io.BytesIO();out.save(data,"PNG")
            st.download_button("دانلود PNG",data.getvalue(),file_name=Path(uploaded.name).stem+"_studio.png",mime="image/png")
            if not found:st.warning("چهره تشخیص داده نشد؛ از مختصات دستی استفاده کن")
            if debug:st.image(mask,caption="ماسک");st.image(locked,caption="قفل چهره")
        except Exception as e:st.error(str(e))
else:
    srcdir=st.text_input("پوشه عکس‌ها",r"C:\Portraits\Input")
    dstdir=st.text_input("پوشه خروجی",r"C:\Portraits\Output")
    recursive=st.checkbox("شامل زیرپوشه‌ها")
    if st.button("پردازش کل پوشه",disabled=disabled):
        try:
            src=Path(srcdir).resolve();dst=Path(dstdir).resolve()
            if not src.is_dir():raise ValueError("پوشه ورودی وجود ندارد")
            if dst==src or src in dst.parents:raise ValueError("خروجی باید خارج از ورودی باشد")
            files=[p for p in (src.rglob("*") if recursive else src.iterdir()) if p.is_file() and p.suffix.lower() in {".jpg",".jpeg",".png",".bmp",".tif",".tiff",".webp"}]
            if not files:raise ValueError("عکسی یافت نشد")
            dst.mkdir(parents=True,exist_ok=True)
            bar=st.progress(0);ok=0
            sess=get_session()
            for i,p in enumerate(files,1):
                try:
                    out,mask,locked,found=process(Image.open(p),sess,bgim,center,edge,light,face)
                    rel=p.relative_to(src);target=(dst/rel).with_name(p.stem+"_studio.png")
                    target.parent.mkdir(parents=True,exist_ok=True);out.save(target)
                    if debug:
                        mask.save(target.with_name(p.stem+"_alpha.png"))
                        locked.save(target.with_name(p.stem+"_face_lock.png"))
                    ok+=1
                except Exception as e:st.error(f"{p.name}: {e}")
                bar.progress(i/len(files))
            st.success(f"انجام شد: {ok}/{len(files)}")
        except Exception as e:st.error(str(e))
