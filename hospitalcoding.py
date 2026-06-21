import streamlit as st
import re
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

st.set_page_config(page_title="CPT Text to PDF", layout="centered")

st.title("CPT Text → Downloadable PDF Table")

patient_name = st.text_input("Patient Name", placeholder="LastName, FirstName")

st.write("Paste raw billing text below:")

raw_text = st.text_area("Input Text", height=300)

def parse_text(text):
    lines = text.splitlines()
    rows = []
    current_row_index = None

    for line in lines:
        line = line.strip()
        if not line:
            continue

        cpt_match = re.search(r"\b\d{5}\b", line)
        date_match = re.search(r"\b\d{1,2}/\d{1,2}/\d{4}\b", line)

        if cpt_match and date_match:
            cpt = cpt_match.group()
            date = date_match.group()

            modifier_match = re.search(r"\b([A-Z]{2}|\d{2})\b", line.split(date)[-1])
            modifier = modifier_match.group() if modifier_match else ""

            rows.append({
                "Date": date,
                "CPT Code": cpt,
                "Modifiers": modifier,
                "ICD10 Code": ""
            })

            current_row_index = len(rows) - 1
            continue

        if "Associated Dx" in line and current_row_index is not None:
            codes = re.findall(r"\[([A-Z0-9\.]+)\]", line)
            if codes:
                rows[current_row_index]["ICD10 Code"] = ", ".join(codes)

    return pd.DataFrame(rows)

if st.button("Generate Table"):
    if patient_name.strip() == "":
        st.warning("Please enter patient name.")
    elif raw_text.strip() == "":
        st.warning("Please paste text first.")
    else:
        df = parse_text(raw_text)

        if df.empty:
            st.error("No valid CPT/date rows detected.")
        else:
            pdf_title = f"{patient_name.strip()} Billing Sheet"

            st.success("Table generated successfully.")
            st.subheader(pdf_title)
            st.dataframe(df)

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)

            styles = getSampleStyleSheet()
            title = Paragraph(pdf_title, styles["Title"])

            data = [df.columns.tolist()] + df.values.tolist()

            table = Table(data, repeatRows=1)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))

            elements = [
                title,
                Spacer(1, 12),
                table
            ]

            doc.build(elements)

            buffer.seek(0)

            # safe_file_name = re.sub(r"[^A-Za-z0-9_-]+", "_", pdf_title)

            st.download_button(
                label="Download PDF",
                data=buffer,
                file_name=f"{pdf_title}.pdf",
                mime="application/pdf"
            )
