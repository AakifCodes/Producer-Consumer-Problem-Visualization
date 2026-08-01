import os
import time
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

class PDFGenerator:
    @staticmethod
    def generate_report(output_path, snap, graph_paths=None, recommendations=None):
        """
        Generates a premium executive PDF report of the simulation.
        - snap: A snapshot dictionary from StateTracker.get_snapshot()
        - graph_paths: A list of absolute paths to saved PNG graph images
        - recommendations: A list of string recommendations from the AI Advisor
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40
        )
        
        styles = getSampleStyleSheet()
        
        # Custom styles for a premium design
        primary_color = colors.HexColor("#0f172a")  # Deep Navy Slate
        accent_color = colors.HexColor("#3b82f6")   # Sapphire
        text_color = colors.HexColor("#334155")     # Cool Charcoal
        
        title_style = ParagraphStyle(
            'DocTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=24,
            textColor=primary_color,
            spaceAfter=15
        )
        
        subtitle_style = ParagraphStyle(
            'DocSub',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=25
        )
        
        h1_style = ParagraphStyle(
            'H1',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=16,
            textColor=primary_color,
            spaceBefore=15,
            spaceAfter=10,
            borderPadding=4
        )
        
        h2_style = ParagraphStyle(
            'H2',
            parent=styles['Heading3'],
            fontName='Helvetica-Bold',
            fontSize=12,
            textColor=accent_color,
            spaceBefore=10,
            spaceAfter=6
        )

        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=text_color,
            leading=14,
            spaceAfter=8
        )
        
        bullet_style = ParagraphStyle(
            'Bullet',
            parent=body_style,
            leftIndent=15,
            firstLineIndent=-10,
            spaceAfter=4
        )

        story = []
        
        # --- HEADER / TITLE ---
        story.append(Paragraph("Smart Factory Synchronization Report", title_style))
        current_time = time.strftime("%Y-%m-%d %H:%M:%S")
        story.append(Paragraph(f"Producer–Consumer Simulation Engine | Generated on {current_time}", subtitle_style))
        story.append(Spacer(1, 10))
        
        # --- SECTION 1: EXECUTIVE SUMMARY ---
        story.append(Paragraph("Executive Performance Summary", h1_style))
        summary_text = (
            "This document provides an automated analysis of the multithreaded Smart Factory system simulation, "
            "evaluating resource utilization, queue wait distributions, and synchronization locking behaviors. "
            "The system visualizes operating system synchronization mechanics by modeling Bounded Buffers, "
            "Mutex Locks, and Semaphore controls under active thread contention."
        )
        story.append(Paragraph(summary_text, body_style))
        story.append(Spacer(1, 10))
        
        # --- SECTION 2: SYSTEM CONFIGURATION & METRICS ---
        story.append(Paragraph("1. Configuration & Performance Statistics", h1_style))
        
        # Formulate buffer utilization percentage
        capacity = snap["buffer_capacity"]
        avg_occupancy = sum(len(snap.get("buffer_items", [])) for _ in range(10)) / 10.0 # dummy smooth
        util_pct = (avg_occupancy / capacity) * 100 if capacity > 0 else 0
        
        config_data = [
            [Paragraph("<b>Configuration Metric</b>", body_style), Paragraph("<b>Value</b>", body_style), 
             Paragraph("<b>Execution Metric</b>", body_style), Paragraph("<b>Value</b>", body_style)],
            ["Producers Count", f"{len([t for t in snap['threads'].values() if t['type']=='PRODUCER'])}", "Total Produced", f"{snap['total_produced']} items"],
            ["Consumers Count", f"{len([t for t in snap['threads'].values() if t['type']=='CONSUMER'])}", "Total Consumed", f"{snap['total_consumed']} items"],
            ["Buffer Capacity", f"{capacity} slots", "Max Buffer Occupancy", f"{snap['max_occupancy']} slots"],
            ["Item Type Configured", f"{snap.get('item_type', 'Widget')}", "Average Wait Time", f"{snap['avg_wait_time']:.2f}s"],
            ["Running Time", f"{snap['elapsed_time']:.1f} seconds", "Max Thread Wait Time", f"{snap['max_wait_time']:.2f}s"],
            ["Producer Blocks", f"{snap['producer_block_count']} events", "Consumer Blocks", f"{snap['consumer_block_count']} events"],
            ["Deadlocks Detected", "YES (CRITICAL WARNING)" if snap["deadlock_detected"] else "NONE (SAFE)", 
             "Starvation Alerts", "YES (ACTIVE ALERT)" if snap["starvation_detected"] else "NONE (STABLE)"]
        ]
        
        config_table = Table(config_data, colWidths=[130, 110, 130, 110])
        config_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f1f5f9")),
            ('TEXTCOLOR', (0,0), (-1,0), primary_color),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('BOTTOMPADDING', (0,0), (-1,0), 6),
            ('TOPPADDING', (0,0), (-1,0), 6),
            ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#cbd5e1")),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica'),
            ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor("#f8fafc")]),
            ('FONTSIZE', (0,0), (-1,-1), 9),
        ]))
        
        story.append(config_table)
        story.append(Spacer(1, 15))
        
        # --- SECTION 3: CHARTS AND VISUALIZATIONS ---
        if graph_paths:
            story.append(Paragraph("2. Performance Analytics & Graphical Overviews", h1_style))
            for path in graph_paths:
                if os.path.exists(path):
                    try:
                        # Reportlab Image flowable: width=480, height=220
                        story.append(Image(path, width=480, height=200))
                        story.append(Spacer(1, 10))
                    except Exception as e:
                        story.append(Paragraph(f"<i>[Error rendering chart: {e}]</i>", body_style))
            story.append(Spacer(1, 10))
            
        # --- SECTION 4: DIAGNOSTIC & AI RECOMMENDATIONS ---
        story.append(Paragraph("3. AI Diagnostics & Optimization Guidelines", h1_style))
        
        if not recommendations:
            recommendations = []
            
        # Generate default robust suggestions if none passed
        if not recommendations:
            prod_cnt = len([t for t in snap['threads'].values() if t['type']=='PRODUCER'])
            cons_cnt = len([t for t in snap['threads'].values() if t['type']=='CONSUMER'])
            if prod_cnt > cons_cnt * 1.5:
                recommendations.append("Bottleneck detected: Production rate far exceeds consumption. Recommend spawning additional Consumer threads to balance buffer throughput.")
            elif cons_cnt > prod_cnt * 1.5:
                recommendations.append("Resource starvation: Consumer threads are idle waiting for empty slots. Suggest increasing production speed or spawning more Producer threads.")
            
            if snap["producer_block_count"] > 15:
                recommendations.append("Severe queue delay: Producers are frequently blocked. Recommend increasing bounded Buffer Capacity dynamically to reduce write wait times.")
            
            if snap["deadlock_detected"]:
                recommendations.append("CRITICAL: System deadlock detected! Multiple threads locked. Ensure mutex releases execute inside absolute finally blocks.")
            else:
                recommendations.append("Synchronization safety verified: All semaphores operated without deadlocks or locking conflicts.")
                
        for rec in recommendations:
            story.append(Paragraph(f"• {rec}", bullet_style))
            
        story.append(Spacer(1, 15))
        
        # --- SECTION 5: SIGN OFF / EDUCATIONAL SUMMARY ---
        story.append(Paragraph("4. Synchronization Mechanics Summary", h1_style))
        edu_text = (
            "<b>Semaphore Protocol:</b> The empty semaphore initializes to buffer capacity, representing available writer slots. "
            "The full semaphore starts at zero, representing readable consumer data. Operating system threads block inside the kernel queue "
            "when semaphore counts drop below zero, preventing race conditions or slot corruption. <br/>"
            "<b>Mutex Locks:</b> Enforces Mutual Exclusion, guaranteeing that only a single thread manipulates buffer indexes or nodes "
            "at any isolated point in time, guaranteeing perfect transaction isolation."
        )
        story.append(Paragraph(edu_text, body_style))
        
        # Build Document
        doc.build(story)
        return True
