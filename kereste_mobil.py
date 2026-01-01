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

# --- GARANTİLİ FONT AYARLAMA ---
def get_turkish_font():
    # Font dosyasının kodun yanında olduğunu varsayıyoruz (GitHub'a yükledik)
    font_name = "DejaVuSans"
    font_file = "DejaVuSans.ttf" 
    
    try:
        # Yanındaki dosyayı tanıtmaya çalış
        pdfmetrics.registerFont(TTFont(font_name, font_file))
        return font_name # Başarılı olursa bu fontu kullan
    except:
        # Dosya yoksa veya hata olursa standarda dön (Ama dosya varsa bu çalışır)
        return "Helvetica"

# --- Hafıza ---
if 'veriler' not in st.session_state:
    st.session_state.veriler = []

# --- GİRİŞ ALANI ---
with st.container():
    st.write("---")
    
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
    st.dataframe(df, use_container_width=True)
    
    toplam_m3 = df["Hacim (m3)"].sum()
    st.info(f"**TOPLAM HACİM:** {toplam_m3:.4f} m³")

    # PDF Fonksiyonu
    def create_pdf(dataframe, total_m3):
        buffer = io.BytesIO()
        # Yüklediğimiz fontu al
        tr_font = get_turkish_font()

        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()

        baslik_stili = ParagraphStyle('Baslik', parent=styles['Heading1'], fontName=tr_font, fontSize=18, textColor=colors.darkblue, alignment=TA_CENTER, spaceAfter=12)
        elements.append(Paragraph("YAFT İNŞAAT VE TİCARET A.Ş.", baslik_stili))
        elements.append(Spacer(1, 10))
        
        alt_baslik_stili = ParagraphStyle('AltBaslik', parent=styles['Normal'], fontName=tr_font, alignment=TA_CENTER)
        elements.append(Paragraph(f"Kereste Hesap Dökümü - {datetime.datetime.now().strftime('%d.%m.%Y')}", alt_baslik_stili))
        elements.append(Spacer(1, 20))

        data = [['Ağaç Cinsi', 'Adet', 'En', 'Kalınlık', 'Boy', 'Hacim (m3)']]
        for index, row in dataframe.iterrows():
            data.append([row['Ağaç Cinsi'], row['Adet'], row['En'], row['Kalınlık'], row['Boy'], row['Hacim (m3)']])
        
        data.append(["", "", "", "", "TOPLAM:", f"{total_m3:.4f}"])

        t = Table(data)
        style = TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), tr_font), # BÜTÜN TABLOYA FONTU UYGULA
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.aliceblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BACKGROUND', (0, -1), (-1, -1), colors.lightgrey),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
        ])
        t.setStyle(style)
        elements.append(t)
        doc.build(elements)
        buffer.seek(0)
        return buffer

    pdf_bytes = create_pdf(df, toplam_m3)
    st.download_button(label="📄 PDF İNDİR", data=pdf_bytes, file_name=f"YAFT_Kereste_{datetime.datetime.now().strftime('%Y-%m-%d')}.pdf", mime="application/pdf", type="secondary", use_container_width=True)
    
    if st.button("LİSTEYİ TEMİZLE", type="secondary", use_container_width=True):
        st.session_state.veriler = []
        st.rerun()
