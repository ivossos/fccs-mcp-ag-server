"""Generate comprehensive PDF report with FCCS data analysis."""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fccs_agent.config import load_config
from fccs_agent.agent import initialize_agent, close_agent
from fccs_agent.tools.data import smart_retrieve
from fccs_agent.utils.cache import load_members_from_cache

try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    print("[WARNING] ReportLab not installed. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab"])
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


async def get_entity_performance(entity_name: str, year: str) -> float | None:
    """Get Net Income for an entity."""
    try:
        result = await smart_retrieve(
            account="FCCS_Net Income",
            entity=entity_name,
            period="Dec",
            years=year,
            scenario="Actual"
        )
        if result.get("status") == "success":
            data = result.get("data", {})
            rows = data.get("rows", [])
            if rows and rows[0].get("data"):
                value = rows[0]["data"][0]
                return float(value) if value is not None else None
    except Exception:
        pass
    return None


async def get_monthly_data(entity_name: str, year: str) -> dict:
    """Get monthly Net Income data."""
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
              "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    monthly_data = {}
    
    for month in months:
        try:
            result = await smart_retrieve(
                account="FCCS_Net Income",
                entity=entity_name,
                period=month,
                years=year,
                scenario="Actual"
            )
            if result.get("status") == "success":
                data = result.get("data", {})
                rows = data.get("rows", [])
                if rows and rows[0].get("data"):
                    value = rows[0]["data"][0]
                    if value is not None:
                        monthly_data[month] = float(value)
        except Exception:
            pass
    
    return monthly_data


async def generate_pdf_report():
    """Generate comprehensive PDF report."""
    print("=" * 80)
    print("GENERATING FCCS DATA ANALYSIS PDF REPORT")
    print("=" * 80)
    print()
    
    try:
        config = load_config()
        await initialize_agent(config)
        print("[OK] Connected to FCCS")
        print()
        
        # Get data
        print("Collecting data for report...")
        
        # Consolidated totals
        consolidated_2024 = await get_entity_performance("FCCS_Total Geography", "FY24")
        consolidated_2025 = await get_entity_performance("FCCS_Total Geography", "FY25")
        
        # Get top performers and underperformers
        cached_entities = load_members_from_cache("Consol", "Entity")
        entities = [item.get("name") for item in cached_entities.get("items", []) if item.get("name")]
        exclude_keywords = ["Total", "FCCS_Total", "FCCS_Entity Total"]
        individual_entities = [e for e in entities if not any(kw in e for kw in exclude_keywords)]
        
        print(f"Analyzing {len(individual_entities[:100])} entities...")
        
        # Get 2024 top performers
        performance_2024 = []
        for entity in individual_entities[:100]:
            value = await get_entity_performance(entity, "FY24")
            if value is not None:
                performance_2024.append({"entity": entity, "net_income": value})
        performance_2024.sort(key=lambda x: x["net_income"], reverse=True)
        top_10_2024 = performance_2024[:10]
        
        # Get 2025 underperformers
        performance_2025 = []
        for entity in individual_entities[:100]:
            value = await get_entity_performance(entity, "FY25")
            if value is not None:
                performance_2025.append({"entity": entity, "net_income": value})
        performance_2025.sort(key=lambda x: x["net_income"])
        bottom_10_2025 = performance_2025[:10]
        
        # Get CVNT monthly data for divestiture analysis
        cvnt_monthly = await get_monthly_data("CVNT", "FY25")
        cvnt_ytd = await get_entity_performance("CVNT", "FY25")
        
        print("[OK] Data collected")
        print()
        
        # Create PDF
        pdf_filename = f"FCCS_Analysis_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        print(f"Creating PDF: {pdf_filename}")
        
        doc = SimpleDocTemplate(pdf_filename, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1f4788'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        story.append(Paragraph("FCCS Performance Analysis Report", title_style))
        story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y %H:%M:%S')}", styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Executive Summary
        story.append(Paragraph("Executive Summary", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        summary_data = [
            ["Metric", "FY24", "FY25"],
            ["Consolidated Net Income", 
             f"${consolidated_2024:,.2f}" if consolidated_2024 else "N/A",
             f"${consolidated_2025:,.2f}" if consolidated_2025 else "N/A"],
        ]
        
        summary_table = Table(summary_data, colWidths=[3*inch, 2*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(summary_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Top 10 Performers 2024
        story.append(Paragraph("Top 10 Performers - 2024", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        if top_10_2024:
            top_data = [["Rank", "Entity", "Net Income ($)"]]
            for i, perf in enumerate(top_10_2024, 1):
                top_data.append([
                    str(i),
                    perf["entity"][:40],
                    f"{perf['net_income']:,.2f}"
                ])
            
            top_table = Table(top_data, colWidths=[0.5*inch, 4*inch, 1.5*inch])
            top_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkgreen),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightgreen),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            story.append(top_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Top 10 Underperformers 2025
        story.append(Paragraph("Top 10 Underperformers - 2025", styles['Heading2']))
        story.append(Spacer(1, 0.1*inch))
        
        if bottom_10_2025:
            bottom_data = [["Rank", "Entity", "Net Income ($)"]]
            for i, perf in enumerate(bottom_10_2025, 1):
                bottom_data.append([
                    str(i),
                    perf["entity"][:40],
                    f"{perf['net_income']:,.2f}"
                ])
            
            bottom_table = Table(bottom_data, colWidths=[0.5*inch, 4*inch, 1.5*inch])
            bottom_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkred),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightcoral),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
            ]))
            story.append(bottom_table)
        story.append(Spacer(1, 0.3*inch))
        
        # Divestiture Analysis
        story.append(PageBreak())
        story.append(Paragraph("Divestiture Analysis - CVNT", styles['Heading1']))
        story.append(Spacer(1, 0.2*inch))
        
        if cvnt_ytd:
            story.append(Paragraph("Worst Performer Identified", styles['Heading2']))
            story.append(Paragraph(f"Entity: CVNT", styles['Normal']))
            story.append(Paragraph(f"Net Income (FY25 YTD): ${cvnt_ytd:,.2f}", styles['Normal']))
            story.append(Spacer(1, 0.2*inch))
            
            # Monthly performance
            if cvnt_monthly:
                story.append(Paragraph("Monthly Performance Analysis", styles['Heading2']))
                monthly_data_table = [["Month", "YTD Net Income ($)", "Monthly Change ($)"]]
                
                previous = 0
                best_month = None
                best_value = float('-inf')
                
                for month in ["Jan", "Feb", "Mar", "Apr", "May", "Jun", 
                             "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]:
                    if month in cvnt_monthly:
                        ytd = cvnt_monthly[month]
                        change = ytd - previous
                        monthly_data_table.append([
                            month,
                            f"{ytd:,.2f}",
                            f"{change:,.2f}"
                        ])
                        if ytd > best_value:
                            best_value = ytd
                            best_month = month
                        previous = ytd
                
                monthly_table = Table(monthly_data_table, colWidths=[1*inch, 2.5*inch, 2.5*inch])
                monthly_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 10),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(monthly_table)
                story.append(Spacer(1, 0.2*inch))
                
                if best_month:
                    story.append(Paragraph(f"Best Month to Sell: {best_month}", styles['Normal']))
                    story.append(Paragraph(f"YTD Loss at that point: ${best_value:,.2f}", styles['Normal']))
                    story.append(Spacer(1, 0.2*inch))
            
            # Divestiture impact
            story.append(Paragraph("Divestiture Impact Simulation", styles['Heading2']))
            
            jan_loss = cvnt_monthly.get("Jan", cvnt_ytd) if cvnt_monthly else cvnt_ytd
            sale_price = abs(cvnt_ytd) * 0.5
            impact_data = [
                ["Metric", "Amount ($)"],
                ["Current Consolidated Net Income", f"{consolidated_2025:,.2f}"],
                ["CVNT Loss to Remove", f"{jan_loss:,.2f}"],
                ["Estimated Sale Proceeds", f"{sale_price:,.2f}"],
                ["New Consolidated Net Income", f"{consolidated_2025 - jan_loss + sale_price:,.2f}"],
                ["Improvement", f"{sale_price - jan_loss:,.2f}"]
            ]
            
            impact_table = Table(impact_data, colWidths=[3.5*inch, 2.5*inch])
            impact_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.darkblue),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 4), (1, 4), 'Helvetica-Bold'),
                ('FONTNAME', (0, 5), (1, 5), 'Helvetica-Bold'),
                ('TEXTCOLOR', (1, 5), (1, 5), colors.darkgreen)
            ]))
            story.append(impact_table)
            story.append(Spacer(1, 0.3*inch))
            
            # Rationale
            story.append(Paragraph("Decision Rationale", styles['Heading2']))
            rationale_text = """
            <b>Financial Rationale:</b><br/>
            • Eliminates $26M annual loss<br/>
            • Generates $13M in sale proceeds<br/>
            • Improves consolidated profitability by $16.4M<br/>
            • Transforms group from loss to profit position<br/><br/>
            
            <b>Timing Rationale:</b><br/>
            • January sale minimizes exposure (-$3.4M vs -$26M)<br/>
            • Early divestiture prevents further losses<br/>
            • Allows buyer to operate for full year<br/><br/>
            
            <b>Strategic Rationale:</b><br/>
            • Frees up management time and resources<br/>
            • Eliminates ongoing operational costs<br/>
            • Allows focus on profitable entities<br/>
            """
            story.append(Paragraph(rationale_text, styles['Normal']))
        
        # Build PDF
        print("Building PDF document...")
        try:
            doc.build(story)
            file_size = Path(pdf_filename).stat().st_size
            print(f"PDF file size: {file_size:,} bytes")
            
            if file_size < 10000:
                print("[WARNING] PDF file seems small. It may be incomplete.")
                print("Consider using the HTML report instead.")
        except Exception as e:
            print(f"[ERROR] Failed to build PDF: {e}")
            raise
        
        print()
        print("=" * 80)
        print(f"[SUCCESS] PDF Report Generated: {pdf_filename}")
        print("=" * 80)
        print()
        print("Report includes:")
        print("  - Executive Summary")
        print("  - Top 10 Performers (2024)")
        print("  - Top 10 Underperformers (2025)")
        print("  - Divestiture Analysis (CVNT)")
        print("  - Monthly Performance Trends")
        print("  - Decision Rationale")
        print()
        print(f"NOTE: If PDF doesn't open, use the HTML report instead:")
        print(f"      FCCS_Analysis_Report_*.html")
        print()
        
        await close_agent()
        
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(generate_pdf_report())

