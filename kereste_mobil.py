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
import urllib.request

# --- Sayfa Ayarları ---
st.set_page_config(page_title="YAFT Kereste", page_icon="🌲")

# --- Başlık ---
st.markdown("<h1 style='text-align: center; color: navy;'>YAFT İNŞAAT VE TİCARET A.Ş.</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center;'>Mobil Kereste Hesaplayıcı</h4>", unsafe_allow_html=True)

# --- Font İndirme (Sunucu İçin Otomatik) ---
# Türkçe karakterlerin PDF'te düzgün çıkması için
font_path = "DejaVuSans.ttf"
if not os.path.exists(font_path):
    url = "https://github.com/dejavu-fonts/dejavu-fonts/raw/master/ttf/DejaVuSans.ttf"
    try:
        urllib.request.urlretrieve(url, font_path)
    except:
        pass

if 'veriler' not in st.session_state:
    st.session_state.veriler = []

# --- Veri Girişi ---
with st.container():
    st.write("---")
    # Liste (İnşaatlık Kereste En Başta)
    agac_listesi = [
        "İnşaatlık Kereste", "Çam", "Sarıçam", "Karaçam", "Kızılçam", 
        "Köknar", "Ladin", "Sedir", "Kayın", "Meşe", "Ceviz", "Kestane", 
        "Dişbudak", "Akçaağaç", "Ihlamur", "Gürgen", "Kavak", "Kızılağaç", 
        "Çınar", "Akasya"
    ]
    
    st.info("👇 Aşağıdan cins ve ölçü seçiniz:")
    cins = st.selectbox("Ağaç Cinsi", agac_listesi)
    
    col1, col2 = st.columns(2)
    adet = col1.number_input("Adet", min_value=1, value=1, step=1)
    en = col1.number_input("En (cm)", min_value=0.0, step=0.1)
    kalinlik = col2.number_input("Kalınlık (cm)", min_value=0.0, step=0.1)
    boy = col2.number_input("Boy (cm)", min_value=0.0, step=0.1)

    if st.button("HESAPLA VE EKLE", type="primary", use_container_width=True):
        if en > 0 and kalinlik > 0 and boy > 0:
            hacim = (adet * en * kalinlik * boy) / 1000000
            st.session_state.veriler.append({
                "Ağaç Cinsi": cins,
                "Adet": adet,
                "En": en,
                "Kalınlık": kalinlik,
                "Boy": boy,
                "Hacim (m3)": round(hacim, 4)
            })
            st.success(f"✅ {cins} listeye eklendi!")
        else:
            st.error("⚠️ Lütfen ölçüleri eksiksiz girin.")

# --- Tablo ve Çıktılar ---
if st.session_state.veriler:
    df = pd.DataFrame(st.session_state.veriler)
    
    st.write("---")
    
    # 1. Detaylı Liste
    st.subheader("📋 Girilen Ölçüler")
    st.dataframe(df, use_container_width=True)
    
    # Genel Toplam
    toplam = df["Hacim (m3)"].sum()
    st.success(f"**GENEL TOPLAM HACİM: {toplam:.4f} m³**")

    # 2. İcmal (Özet) Tablosu
    st.write("---")
    st.subheader("🌲 Cins Bazlı İcmal (Özet)")
    ozet = df.groupby("Ağaç Cinsi")["Hacim (m3)"].sum().reset_index()
    ozet.columns = ["Ağaç Cinsi", "Toplam m³"]
    st.dataframe(ozet, use_container_width=True, hide_index=True)

    # --- PDF Oluşturma Fonksiyonu ---
    def create_pdf(dataframe, total, summary):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        elements = []
        styles = getSampleStyleSheet()
        
        # Font Ayarı (İndirilen Fontu Kullan)
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', 'DejaVuSans.ttf'))
            f_norm, f_bold = 'DejaVu', 'DejaVu'
        except:
            f_norm, f_bold = 'Helvetica', 'Helvetica-Bold'

        # Başlık
        elements.append(Paragraph("YAFT İNŞAAT VE TİCARET A.Ş.", ParagraphStyle('Title', parent=styles['Heading1'], fontName=f_bold, alignment=TA_CENTER, textColor=colors.navy)))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(f"Tarih: {datetime.datetime.now().strftime('%d.%m.%Y')}", ParagraphStyle('Date', parent=styles['Normal'], fontName=f_norm, alignment=TA_CENTER)))
        elements.append(Spacer(1, 20))

        # Tablo 1: Detay
        elements.append(Paragraph("Detaylı Ölçü Listesi", styles['Heading3']))
        data = [['Cins', 'Adet', 'En', 'Kalın', 'Boy', 'm3']]
        for i, r in dataframe.iterrows():
            data.append([r['Ağaç Cinsi'], r['Adet'], r['En'], r['Kalınlık'], r['Boy'], r['Hacim (m3)']])
        data.append(["", "", "", "", "TOPLAM:", f"{total:.4f}"])
        
        t = Table(data)
        t.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), f_norm),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.navy),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,-1), (-1,-1), f_bold) # Toplam satırı kalın
        ]))
        elements.append(t)

        # Tablo 2: İcmal
        elements.append(Spacer(1, 30))
        elements.append(Paragraph("Cins Bazlı İcmal (Özet)", styles['Heading3']))
        d_ozet = [['Ağaç Cinsi', 'Toplam m3']]
        for i, r in summary.iterrows():
            d_ozet.append([r['Ağaç Cinsi'], f"{r['Toplam m³']:.4f}"])
        
        t2 = Table(d_ozet, colWidths=[200, 100])
        t2.setStyle(TableStyle([
            ('FONTNAME', (0,0), (-1,-1), f_norm),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.firebrick),
            ('TEXTCOLOR', (0,0), (-1,0), colors.white),
            ('ALIGN', (0,0), (-1,-1), 'CENTER')
        ]))
        elements.append(t2)

        doc.build(elements)
        buffer.seek(0)
        return buffer

    # PDF İndir Butonu
    pdf_bytes = create_pdf(df, toplam, ozet)
    
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        st.download_button(
            label="📄 PDF İNDİR",
            data=pdf_bytes,
            file_name=f"YAFT_Kereste_{datetime.date.today()}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )
    with col_btn2:
        if st.button("LİSTEYİ TEMİZLE", type="secondary", use_container_width=True):
            st.session_state.veriler = []
            st.rerun()