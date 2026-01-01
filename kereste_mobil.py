import streamlit as st
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import io
import datetime
import os

# --- Sayfa Ayarları ---
st.set_page_config(page_title="YAFT Kereste", page_icon="🌲")

# --- BAŞLIK ---
st.markdown("<h1 style='text-align: center; color: darkblue;'>YAFT İNŞAAT VE TİCARET A.Ş.</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Mobil Kereste Hesaplayıcı</h4>", unsafe_allow_html=True)

# --- FONT AYARLAMA (Garantili Yöntem) ---
def get_turkish_font():
    # GitHub'a yüklediğin dosyanın adı tam olarak böyle olmalı
    font_name = "DejaVuSans"
    font_file = "DejaVuSans.ttf" 
    
    try:
        # Fontu sisteme tanıtıyoruz
        pdfmetrics.registerFont(TTFont(font_name, font_file))
        return font_name 
    except:
        # Dosya bulunamazsa standart fonta dön (ama yüklediysen bu çalışır)
        return "Helvetica"

# --- Hafıza ---
if 'veriler' not in st.session_state:
    st.session_state.veriler = []

# --- GİRİŞ ALANI ---
with st.container():
    st.write("---")
    
    # Ağaç Listesi
    agac_listesi = ["İnşaatlık", "Çam", "Meşe", "Kayın", "Gürgen", "Ladin", "Kavak", "Diğer"]
    secilen = st.selectbox("Cins Seç:", agac_listesi)
    
    if secilen == "Diğer":
        cins = st.text_input("Diğer Cinsi Yazın:", value="")
    else:
        cins = secilen

    col1, col2 = st.columns(2)
    with col1:
        adet = st.number_input("Adet", min_value=1, value=1, step=1)
        en = st.number_input("En (cm)", min_value=0.0, step=0.1)
    with col2:
        kalinlik = st.number_input("Kalınlık (cm)", min_value=0.0, step=0.1)
        boy = st.number_input("Boy (cm)", min_value=0.0, step=0.1)

    if st.button("HESAPLA VE LİSTEYE EKLE", type="primary", use_container_width=True):
        if en > 0 and kalinlik > 0 and boy > 0:
            hacim_m3 = (adet * en * kalinlik * boy) / 1000000
            if not cins: cins = "-"
            
            yeni_veri = {
                "Ağaç Cinsi": cins,
                "Adet": adet,
                "En": en,
                "Kalınlık": kalinlik,
                "Boy": boy,
                "Hacim (m3)": round(hacim_m3, 4)
            }
            st.session_state.veriler.append(yeni_veri)
            st.success(f"{cins} Eklendi!")
        else:
            st.error("Lütfen ölçüleri eksiksiz girin.")

# --- LİSTE VE PDF ---
if len(st.session_state.veriler) > 0:
    st.divider()
    df = pd.DataFrame(st.session_state.veriler)
    
    # 1. EKRANDA GÖSTERİM (Detaylı)
    st.subheader("📋 Detaylı Liste")
    st.dataframe(df, use_container_width=True)
    
    # 2. EKRANDA GÖSTERİM (Özet)
    st.divider()
    st.subheader("📊 Özet Rapor")
    
    # Gruplama İşlemi
    ozet_df = df.groupby("Ağaç Cinsi")["Hacim (m3)"].sum().reset_index()
    ozet_df.columns = ["Ağaç Cinsi", "Toplam Hacim (m3)"]
    st.dataframe(ozet_df, use_container_width=True)

    # Genel Toplam
    genel_toplam = df["Hacim (m3)"].sum()
    st.info(f"**GENEL
