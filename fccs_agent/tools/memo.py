"""Memo generation tool - generate_investment_memo and system pitch."""

import os
from pathlib import Path
from datetime import datetime
from typing import Any

try:
    from docx import Document
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False


async def generate_system_pitch() -> dict[str, Any]:
    """Generate a one-pager pitch document about the system's capabilities.

    Generate a professional one-page Word document highlighting the FCCS MCP Agent
    system capabilities, features, and value proposition.

    Returns:
        dict: Path to generated document and summary.
    """
    if not DOCX_AVAILABLE:
        return {
            "status": "error",
            "error": "python-docx not available. Install with: pip install python-docx"
        }

    try:
        # Create document
        doc = Document()
        
        # Set margins for one-pager (narrow margins)
        sections = doc.sections
        for section in sections:
            section.top_margin = Inches(0.4)
            section.bottom_margin = Inches(0.4)
            section.left_margin = Inches(0.5)
            section.right_margin = Inches(0.5)

        # Title
        title = doc.add_heading('FCCS MCP Agentic Server', 0)
        title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title.runs[0].font.color.rgb = RGBColor(31, 71, 136)
        
        subtitle = doc.add_paragraph('AI-Powered Oracle EPM Cloud Financial Consolidation Assistant')
        subtitle.alignment = WD_ALIGN_PARAGRAPH.CENTER
        subtitle_format = subtitle.runs[0].font
        subtitle_format.size = Pt(12)
        subtitle_format.bold = True
        subtitle_format.color.rgb = RGBColor(31, 71, 136)
        
        doc.add_paragraph()  # Spacing

        # Value Proposition (condensed)
        value_text = doc.add_paragraph(
            'Transform your financial close process with an intelligent AI assistant that provides '
            'seamless access to Oracle EPM Cloud Financial Consolidation and Close (FCCS) through '
            'natural language. Built on Google ADK with MCP protocol support.'
        )
        value_text_format = value_text.runs[0].font
        value_text_format.size = Pt(10)
        value_text_format.bold = True
        value_text.paragraph_format.space_after = Pt(8)

        # Key Capabilities (condensed format)
        capabilities_heading = doc.add_paragraph()
        cap_heading_run = capabilities_heading.add_run('CORE CAPABILITIES')
        cap_heading_run.font.bold = True
        cap_heading_run.font.size = Pt(11)
        cap_heading_run.font.color.rgb = RGBColor(31, 71, 136)
        capabilities_heading.paragraph_format.space_after = Pt(4)

        capabilities = [
            ('25+ FCCS Tools', 'Complete Oracle FCCS REST API coverage'),
            ('Dual Access', 'MCP server (Claude Desktop) + FastAPI web server'),
            ('Smart Queries', 'Intelligent 14-dimension cube handling'),
            ('Journal Automation', 'Complete lifecycle: create, approve, post'),
            ('Consolidation', 'Business rules, metadata validation, intercompany matching'),
            ('Report Generation', 'Multi-format: PDF, HTML, XLSX, CSV'),
            ('Bilingual', 'English & Portuguese support'),
            ('Learning System', 'PostgreSQL feedback tracking & metrics')
        ]

        for cap_title, cap_desc in capabilities:
            cap_para = doc.add_paragraph()
            cap_run = cap_para.add_run(f'• {cap_title}: ')
            cap_run.font.bold = True
            cap_run.font.size = Pt(9)
            cap_run.font.color.rgb = RGBColor(31, 71, 136)
            desc_run = cap_para.add_run(cap_desc)
            desc_run.font.size = Pt(9)
            cap_para.paragraph_format.space_after = Pt(3)

        doc.add_paragraph()  # Spacing

        # Technical & Use Cases (combined, condensed)
        tech_heading = doc.add_paragraph()
        tech_heading_run = tech_heading.add_run('TECHNICAL HIGHLIGHTS & USE CASES')
        tech_heading_run.font.bold = True
        tech_heading_run.font.size = Pt(11)
        tech_heading_run.font.color.rgb = RGBColor(31, 71, 136)
        tech_heading.paragraph_format.space_after = Pt(4)

        combined_points = [
            'Google ADK + MCP protocol | Docker & Cloud Run ready | Mock mode for testing',
            'Query financial data | Automate journal workflows | Run consolidation rules',
            'Generate reports on-demand | Explore hierarchies | Monitor job execution'
        ]

        for point in combined_points:
            point_para = doc.add_paragraph(point, style='List Bullet')
            point_para.runs[0].font.size = Pt(9)
            point_para.paragraph_format.space_after = Pt(2)

        # Footer
        doc.add_paragraph()  # Spacing
        footer = doc.add_paragraph()
        footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        footer_run = footer.add_run(
            f'FCCS MCP Agentic Server | Generated: {datetime.now().strftime("%B %d, %Y")} | '
            'Oracle EPM Cloud Financial Consolidation and Close'
        )
        footer_run.font.size = Pt(8)
        footer_run.font.color.rgb = RGBColor(128, 128, 128)
        footer_run.font.italic = True

        # Save document
        filename = f"FCCS_System_Pitch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        filepath = Path(filename).absolute()
        doc.save(filename)

        return {
            "status": "success",
            "data": {
                "file_path": str(filepath),
                "filename": filename,
                "message": "One-pager system pitch document generated successfully",
                "note": "Document highlights system capabilities, features, and value proposition"
            }
        }

    except Exception as e:
        return {
            "status": "error",
            "error": f"Failed to generate pitch document: {str(e)}"
        }


async def generate_investment_memo(ticker: str) -> dict[str, Any]:
    """Generate a 2-page investment memo (Word doc) with financial analysis.

    Gerar memorando de investimento (Word) com analise financeira.

    Args:
        ticker: Company ticker symbol (e.g., 'TECH').

    Returns:
        dict: Path to generated memo file and summary.
    """
    # Placeholder - full implementation will use:
    # - KenshoMockService for financial data
    # - FinancialAnalyzer for analysis
    # - MemoGenerator for Word document creation

    return {
        "status": "success",
        "data": {
            "ticker": ticker,
            "message": "Investment memo generation requires full implementation",
            "note": "This will generate a Word document with financial analysis"
        }
    }


TOOL_DEFINITIONS = [
    {
        "name": "generate_system_pitch",
        "description": "Generate a one-pager pitch document about the system's capabilities / Gerar documento de apresentacao do sistema",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": [],
        },
    },
    {
        "name": "generate_investment_memo",
        "description": "Generate a 2-page investment memo (Word doc) with financial analysis / Gerar memorando de investimento",
        "inputSchema": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "Company ticker symbol (e.g., 'TECH')",
                },
            },
            "required": ["ticker"],
        },
    },
]
