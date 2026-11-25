import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime

# Import PDF layout libraries
from reportlab.lib.pagesizes import A4, letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import mm

# --- 1. TARIFF CONFIGURATION ---
TARIFF_CONFIG_R = {
    "tiers": [
        {"max_limit": 30, "rate": 0.9443},         # Tier 1: 0 to 30 kWh
        {"max_limit": 300, "rate": 2.1394},        # Tier 2: >30 to 300 kWh
        {"max_limit": float('inf'), "rate": 2.8268} # Tier 3: 300+ kWh
    ],
    "surcharge_threshold": 30,
    "surcharge_amount": 44.4540,
    "low_user_service_fee": 2.1333
}
TARIFF_CONFIG_NR = { 
    "tiers": [
        {"max_limit": 300, "rate": 2.2219},        # Tier 1: 0 to 300 kWh
        {"max_limit": float('inf'), "rate": 2.7061} # Tier 2: 300+ kWh
    ],
    "service_fee": 14.9138
}
TARIFF_CONFIG_LV={
    "tiers": [
        {"max_limit": 300, "rate": 3.0026},        #
    ],
    "service_fee": 600.00
}
TARIFF_CONFIG_MV={
    "tiers": [
        {"max_limit": 0, "rate": 2.6079},        #
    ],
    "service_fee": 600.00
}
TARIFF_CONFIG_HV={
    "tiers": [
        {"max_limit": 0, "rate": 2.3560},        #
    ],
    "service_fee": 600.00
}
def _calculate_daily_charge_residential(row): 
    daily_kwh = float(row['kWh Consumed (Daily)'])
    cum_kwh_end = float(row['kWh Consumed (Cumulative Current Month)'])
    cum_kwh_start = cum_kwh_end - daily_kwh

    energy_charge = 0.0
    thresh = TARIFF_CONFIG_R["surcharge_threshold"]
    
    # Safe date execution handling regardless of incoming series type string/timestamp
    timestamp = pd.to_datetime(row['Data Time'])

    # 1. Apply service fee on Day 1 based on entry status to avoid cross-over edge losses
    if timestamp.day == 1 and cum_kwh_start <= thresh:
        energy_charge += TARIFF_CONFIG_R["low_user_service_fee"]

    # 2. Early escape guard for zero/negative consumption entries
    if daily_kwh <= 0:
        return round(energy_charge, 4)
        
    # 3. Progressive Interval Split Loop
    previous_limit = 0.0
    for tier in TARIFF_CONFIG_R["tiers"]:
        limit = tier["max_limit"]
        rate = tier["rate"]
        
        tier_start = max(previous_limit, cum_kwh_start)
        tier_end = min(limit, cum_kwh_end)
        
        if tier_end > tier_start:
            energy_charge += (tier_end - tier_start) * rate
            
        previous_limit = limit

    # 4. Threshold Surcharge Trigger
    if cum_kwh_start <= thresh and cum_kwh_end > thresh:
        energy_charge += TARIFF_CONFIG_R["surcharge_amount"]
       
    return round(energy_charge, 4)

def _calculate_daily_charge_non_residential(row:dict[str,float]):
    daily_kwh:float = row['kWh Consumed (Daily)']
    cum_kwh_end:float = row['kWh Consumed (Cumulative Current Month)']
    cum_kwh_start:float = cum_kwh_end - daily_kwh
   

    energy_charge = 0.0000
    previous_limit = 0.0000
    timestamp=pd.to_datetime(row['Data Time'])

    if timestamp.day==1:
        energy_charge+=TARIFF_CONFIG_NR["service_fee"]

    if daily_kwh<=0:
        return round(energy_charge,4)

    for tier in TARIFF_CONFIG_NR["tiers"]:
        limit:float = tier["max_limit"]
        rate:float = tier["rate"]
        
        tier_start:float = max(previous_limit, cum_kwh_start)
        tier_end:float = min(limit, cum_kwh_end)

        if tier_end > tier_start:
            energy_charge+=(tier_end-tier_start)*rate

        previous_limit=limit

    return round(energy_charge, 4)

def _calculate_daily_charge_LV(row:dict[str,float]):
    daily_kwh:float = row['kWh Consumed (Daily)']
    cum_kwh_end:float = row['kWh Consumed (Cumulative Current Month)']
    cum_kwh_start:float = cum_kwh_end - daily_kwh
   

    energy_charge = 0.0000
   
    timestamp=pd.to_datetime(row['Data Time'])

    if timestamp.day==1:
        energy_charge+=TARIFF_CONFIG_LV["service_fee"]

    if daily_kwh<=0:
        return round(energy_charge, 4)
    
    tier= TARIFF_CONFIG_LV["tiers"][0]

    energy_charge+= (daily_kwh* tier['rate'])
    return round(energy_charge, 4)

def _calculate_daily_charge_MV(row:dict[str,float]):
    daily_kwh:float = row['kWh Consumed (Daily)']
    cum_kwh_end:float = row['kWh Consumed (Cumulative Current Month)']
    cum_kwh_start:float = cum_kwh_end - daily_kwh
    

    energy_charge = 0.0000
    
    timestamp=pd.to_datetime(row['Data Time'])

    if timestamp.day==1:
        energy_charge+=TARIFF_CONFIG_MV["service_fee"]

    if daily_kwh<=0:
        return round(energy_charge, 4)
    
    tier= TARIFF_CONFIG_MV["tiers"][0]

    energy_charge+= (daily_kwh* tier['rate'])

    return round(energy_charge, 4)
def _calculate_daily_charge_HV(row:dict[str,float]):
    daily_kwh:float = row['kWh Consumed (Daily)']
    cum_kwh_end:float = row['kWh Consumed (Cumulative Current Month)']
    cum_kwh_start:float = cum_kwh_end - daily_kwh
    

    energy_charge = 0.0000
    
    timestamp=pd.to_datetime(row['Data Time'])

    if timestamp.day==1:
        energy_charge+=TARIFF_CONFIG_HV["service_fee"]

    if daily_kwh<=0:
        return round(energy_charge, 4)
    
    tier= TARIFF_CONFIG_HV["tiers"][0]

    energy_charge+= (daily_kwh* tier['rate'])

    return round(energy_charge, 4)


# --- 3. PDF GENERATION ENGINE ---
def _generate_pdf(dataframe:pd.DataFrame,ct_r:str,pt_r:str):
    buffer = BytesIO()
    # Margins setup
    margin_y=12*mm
    margin_x=10*mm
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=margin_x, leftMargin=margin_x, topMargin=margin_y, bottomMargin=margin_y)
    story = []
    ctr= ct_r.replace('_',"/") if ct_r!="_" else "5/5"
    ptr=pt_r.replace("_","/") if pt_r!="_" else "1/1"
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=20, spaceAfter=15, textColor=colors.HexColor("#1A365D"))
    meta_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=10, textColor=colors.HexColor("#4A5568"))
    tr_style = ParagraphStyle('MetaStyle', parent=styles['Normal'], fontSize=12, textColor=colors.HexColor("#10274F"))
        
    # Document Header
    story.append(Paragraph("⚡ Smart-Meter Billing & Tariff Report", title_style))
    story.append(Paragraph(f"Generated Rows: {len(dataframe)} rows processed.", meta_style))
    story.append(Paragraph(f"CT Ratio: {ctr} --|||-- PT Ratio: {ptr}",tr_style))
    story.append(Spacer(1, 15))
    header_style=styles["Normal"].clone("TableHeader")
    header_style.fontName="Helvetica-Bold"
    header_style.fontSize=8.5
    header_style.leading=10
    header_style.aligment=1
    header_style.textColor=colors.white
    body_style=styles["Normal"].clone("TableBody")
    body_style.fontName="Helvetica-Bold"
    body_style.fontSize=8
    body_style.leading=10
    body_style.aligment=1
    body_style.textColor=colors.black
        
   
    
    # Setup Table Data & Headers
    table_data = [[Paragraph("Row Index",header_style),Paragraph("Meter Asset No.",header_style)
                   , Paragraph("Data Time",header_style), Paragraph('kWh Consumed (Cumulative Current Month)',header_style),
                     Paragraph("Daily Consumption (kWh)",header_style),
                       Paragraph("Daily Charge (GHS)",header_style)]]
    
    # Loop over dataframe to populate layout rows
    for _, row in dataframe.iterrows():
        table_data.append([
            Paragraph(str(row.name),body_style),
           Paragraph( str(row["Meter Asset No."]),body_style),
            Paragraph(row["Data Time"].strftime('%Y-%m-%d'),body_style),
            Paragraph(f"{row['kWh Consumed (Cumulative Current Month)']:.4f}",body_style),
          Paragraph ( f"{row['kWh Consumed (Daily)']:.4f}",body_style),
           Paragraph (f"{row['kWh Charge (GHS)']:.4f}",body_style)
        ])
        
    # Set clear explicit widths for standard 8.5" x 11" letter size page
    letter_width=[130, 110, 150, 120]
    # Set clear explicit widths for standard 8.27" x 11.89" A4 size page
    A4_width=[36,86,82,152,86,94]
    tariff_table = Table(table_data, colWidths=A4_width,repeatRows=1)
    
    # Apply clean corporate styling properties
    tariff_table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1A365D")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('ALIGN', (0,0), (-1,-1), 'CENTER'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,0), 8),
        ('TOPPADDING', (0,0), (-1,0), 8),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#F7FAFC")]),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#E2E8F0")),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('FONTSIZE', (0,0), (-1,-1), 9),
    ]))
    
    story.append(tariff_table)
    doc.build(story)
    buffer.seek(0)
    return buffer




CT_RATIO=["_","100_5","200_5","300_5","400_5","500_5","800_5","1200_5","2000_5"]
CT_RATIO_DIC={"_":1,"100_5":20,"200_5":50,"300_5":60,"400_5":80,"500_5":100,"800_5":160,"1200_5":240,"2000_5":400}
PT_RATIO=["_","11.5kV_110V","34.5kV_110V"]
PT_RATIO_DIC={"_":1,"11.5kV_110V":104.55,"34.5kV_110V":313.64}
TARIFF_TYPE=["_","Residential", "Non-Residential","SLT-LV","SLT-MV","SLT-HV"]

with st.container(horizontal=False,key="ct_page",width="stretch"):
    st.set_page_config(page_title="CT Computation", page_icon="⚡", layout="wide")


    st.title("CT | CTPT Page")
  
    uploaded_file = st.file_uploader("Import Meter Excel Spreadsheet (.xlsx)", type=["xlsx","xls"],width='stretch', help="Upload the raw meter data export",key="upload_ct")
    tariff_type = st.selectbox("Select Tariff Type",TARIFF_TYPE , index=0, help="Select the tariff type for calculations")
     
    col1,col2 = st.columns([1,1])
    ct_r = col1.selectbox("Select CT ratio", CT_RATIO, index=0, help="Select the CT Ratio for calculations")
    pt_r = col2.selectbox("Select PT ratio", PT_RATIO, index=0, help="Select the PT Ratio for calculations")
    total_multiplier:float =float(CT_RATIO_DIC[ct_r] * PT_RATIO_DIC[pt_r])
    col2.text(f"Total multiplier:{round(total_multiplier,4)}",text_alignment="right")
if uploaded_file is not None:
    try:
        # Load raw file data layer
        df_raw = pd.read_excel(uploaded_file,engine='calamine',sheet_name=0)
        required_cols = ["Child Data Item", "Data Time", "Meter Asset No.", "Reading Result(secondary side)"]
        if not all(col in df_raw.columns for col in required_cols):
            st.error(f"Error: Spreadsheet format incorrect. Missing columns. File must contain exact headers: {required_cols}")
        else:
             # Filter targeted data rows
            mask = df_raw["Child Data Item"] == "Active Energy (+) Total [Daily]"
            df_filtered = df_raw[mask].copy()
            row_count=df_raw[mask].shape[0]
           
            if row_count >0:

                if st.button("Run Consumption Computation", type="primary"):
                    with st.spinner("Processing tiers..."):
                        # Core Processing Pipeline
                        df_filtered['Data Time'] = pd.to_datetime(df_filtered['Data Time'])
                        df_filtered = df_filtered.sort_values(by=['Meter Asset No.', 'Data Time']).reset_index(drop=True)
                        df_filtered['Primary Reading'] = (
                                                    df_filtered.apply(lambda x: (x['Reading Result(secondary side)']*total_multiplier),axis=1)
                                                )
                        df_filtered['kWh Consumed (Daily)'] = (
                                                df_filtered.groupby('Meter Asset No.')['Primary Reading'].diff().fillna(0.0)
                                            )
                                            
                        df_filtered['Month'] = df_filtered['Data Time'].dt.to_period('M')
                        df_filtered['kWh Consumed (Cumulative Current Month)'] = (
                            df_filtered.groupby(['Meter Asset No.', 'Month'])['kWh Consumed (Daily)'].cumsum()
                        )

                        
                        if tariff_type == "Residential":
                            df_filtered['kWh Charge (GHS)'] = df_filtered.apply(_calculate_daily_charge_residential, axis=1)
                        elif tariff_type== "Non-Residential":
                            df_filtered['kWh Charge (GHS)'] = df_filtered.apply(_calculate_daily_charge_non_residential, axis=1)
                        elif tariff_type=="SLT-LV":
                            df_filtered['kWh Charge (GHS)'] = df_filtered.apply(_calculate_daily_charge_LV, axis=1)
                        elif tariff_type=="SLT-MV":
                            df_filtered['kWh Charge (GHS)'] = df_filtered.apply(_calculate_daily_charge_MV, axis=1)
                        elif tariff_type=="SLT-HV":
                            df_filtered['kWh Charge (GHS)'] = df_filtered.apply(_calculate_daily_charge_HV, axis=1)
                        else:
                            st.warning("Tariff type not selected!😒")         

                        if tariff_type!="_":
                            df_filtered = df_filtered.drop(columns=['Month'])
                                                
                            # Display success message and visual summary table inside screen views
                            st.success("Calculations complete!")
                        
                            display_cols = ['Meter Asset No.', 'Data Time','kWh Consumed (Cumulative Current Month)', 'kWh Consumed (Daily)', 'kWh Charge (GHS)']
                            st.dataframe(df_filtered[display_cols], use_container_width=True)

                        
                            # Pass calculations context directly into binary PDF compilation engine
                            pdf_data_stream = _generate_pdf(dataframe= df_filtered[display_cols],ct_r=ct_r,pt_r=pt_r)
                        
                            # Create Native Download Link inside view state windows
                            now = datetime.now()
                            string_date = now.strftime("%Y%m%d%H%M%S")
                            st.download_button(
                            label="📥 Download Generated PDF Report",
                            data=pdf_data_stream,
                            file_name=f"Tariff_Computation_Report_{string_date}.pdf",
                            mime="application/pdf",
                            type="primary"
                            )
            else:
                st.warning('Your data does not contain "Active Energy (+) Total [Daily]" readings 🙈')


    except Exception as error_msg:
            st.error(f"Processing structural anomaly detected: {error_msg}")
            print(error_msg.with_traceback)



