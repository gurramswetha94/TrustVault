"""
TrustVault Master Guide PDF Generator
Produces a high-quality, professional executive PDF guide for the TrustVault project.
"""

import sys
import os

class TrustVaultPDFBuilder:
    def __init__(self, filename="TrustVault_Executive_Guide.pdf", pagesize=(612, 792)):
        self.filename = filename
        self.width, self.height = pagesize
        self.pages = []
        self.current_stream = []
        self.page_number = 0
        
        # Margins (Letter size: 612 x 792 pt)
        self.margin_x = 44
        self.margin_top = 46
        self.margin_bottom = 44
        self.content_width = self.width - (2 * self.margin_x)
        
        self.cursor_y = self.height - self.margin_top
        
    def new_page(self, is_cover=False):
        if self.current_stream:
            self.pages.append(self.current_stream)
        self.current_stream = []
        self.page_number += 1
        self.cursor_y = self.height - self.margin_top
        
        if not is_cover:
            self._draw_page_decorations()
            
    def _draw_page_decorations(self):
        s = self.current_stream
        s.append("q")
        
        # Running Top Header
        s.append("0.35 0.42 0.50 rg")  # slate gray
        s.append("BT")
        s.append("/F1 8 Tf")
        s.append(f"{self.margin_x} {self.height - 30} Td")
        s.append("(TRUSTVAULT  |  COMPLETE EXECUTIVE & ARCHITECTURE BLUEPRINT) Tj")
        s.append("ET")
        
        # Top Rule
        s.append("0.82 0.86 0.90 RG")
        s.append("0.6 w")
        s.append(f"{self.margin_x} {self.height - 34} m {self.width - self.margin_x} {self.height - 34} l S")
        
        # Bottom Rule
        s.append(f"{self.margin_x} 32 m {self.width - self.margin_x} 32 l S")
        
        # Bottom Footer Text
        s.append("BT")
        s.append("/F1 8 Tf")
        s.append(f"{self.margin_x} 22 Td")
        s.append("(Confidential Candidate Master Guide  --  Security-First Engineering) Tj")
        s.append("ET")
        
        # Page Number placeholder
        s.append("BT")
        s.append("/F2 8 Tf")
        page_str = f"Page {self.page_number}"
        s.append(f"{self.width - self.margin_x - 38} 22 Td")
        s.append(f"({page_str}) Tj")
        s.append("ET")
        s.append("Q")
        
        self.cursor_y = self.height - self.margin_top - 12

    def check_space(self, required_height):
        if self.cursor_y - required_height < self.margin_bottom + 10:
            self.new_page()

    def escape_text(self, text):
        return text.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')

    def add_title_banner(self, title, subtitle, tag="EXECUTIVE SPECIFICATION & EXECUTION BLUEPRINT"):
        self.check_space(145)
        s = self.current_stream
        s.append("q")
        
        y_top = self.cursor_y
        banner_h = 120
        # Dark navy banner background
        s.append("0.07 0.11 0.20 rg")
        s.append(f"{self.margin_x} {y_top - banner_h} {self.content_width} {banner_h} re f")
        
        # Accent left stripe (electric blue)
        s.append("0.15 0.55 0.95 rg")
        s.append(f"{self.margin_x} {y_top - banner_h} 6 {banner_h} re f")
        
        # Badge
        s.append("0.16 0.23 0.38 rg")
        s.append(f"{self.margin_x + 18} {y_top - 26} 230 15 re f")
        s.append("1 1 1 rg")
        s.append("BT")
        s.append("/F2 7.5 Tf")
        s.append(f"{self.margin_x + 24} {y_top - 22} Td")
        s.append(f"({self.escape_text(tag)}) Tj")
        s.append("ET")
        
        # Title
        s.append("1 1 1 rg")
        s.append("BT")
        s.append("/F2 19 Tf")
        s.append(f"{self.margin_x + 18} {y_top - 54} Td")
        s.append(f"({self.escape_text(title)}) Tj")
        s.append("ET")
        
        # Subtitle
        s.append("0.78 0.85 0.94 rg")
        s.append("BT")
        s.append("/F1 10.0 Tf")
        s.append(f"{self.margin_x + 18} {y_top - 76} Td")
        s.append(f"({self.escape_text(subtitle)}) Tj")
        s.append("ET")
        
        # Meta badge tags
        s.append("0.50 0.62 0.76 rg")
        s.append("BT")
        s.append("/F1 8.0 Tf")
        s.append(f"{self.margin_x + 18} {y_top - 100} Td")
        s.append("(Targets: 100/100 Marks  |  Non-Negotiables  |  Attack Playbook  |  THREATS.md  |  PROMPTS.md) Tj")
        s.append("ET")
        s.append("Q")
        
        self.cursor_y -= (banner_h + 16)

    def add_section(self, number_str, title_str):
        self.check_space(50)
        s = self.current_stream
        s.append("q")
        
        # Pill badge with section number
        s.append("0.10 0.35 0.75 rg")
        s.append(f"{self.margin_x} {self.cursor_y - 18} 26 18 re f")
        s.append("1 1 1 rg")
        s.append("BT")
        s.append("/F2 9.0 Tf")
        s.append(f"{self.margin_x + 5} {self.cursor_y - 13} Td")
        s.append(f"({self.escape_text(number_str)}) Tj")
        s.append("ET")
        
        # Section Title
        s.append("0.08 0.12 0.20 rg")
        s.append("BT")
        s.append("/F2 12.5 Tf")
        s.append(f"{self.margin_x + 34} {self.cursor_y - 14} Td")
        s.append(f"({self.escape_text(title_str)}) Tj")
        s.append("ET")
        
        # Bottom Accent Line
        s.append("0.85 0.88 0.94 RG")
        s.append("1 w")
        s.append(f"{self.margin_x} {self.cursor_y - 24} m {self.width - self.margin_x} {self.cursor_y - 24} l S")
        s.append("Q")
        
        self.cursor_y -= 34

    def add_subsection(self, title_str):
        self.check_space(30)
        s = self.current_stream
        s.append("q")
        s.append("0.12 0.20 0.34 rg")
        s.append("BT")
        s.append("/F2 10.0 Tf")
        s.append(f"{self.margin_x} {self.cursor_y - 11} Td")
        s.append(f"({self.escape_text(title_str)}) Tj")
        s.append("ET")
        s.append("Q")
        self.cursor_y -= 18

    def add_paragraph(self, text, font="F1", size=9.0, color=(0.16, 0.20, 0.26), line_height=13.0):
        lines = self.wrap_text(text, self.content_width, size, font == "F2")
        for line in lines:
            self.check_space(line_height)
            s = self.current_stream
            s.append("q")
            s.append(f"{color[0]} {color[1]} {color[2]} rg")
            s.append("BT")
            s.append(f"/{font} {size} Tf")
            s.append(f"{self.margin_x} {self.cursor_y - size} Td")
            s.append(f"({self.escape_text(line)}) Tj")
            s.append("ET")
            s.append("Q")
            self.cursor_y -= line_height
        self.cursor_y -= 4

    def add_bullet(self, bold_prefix, text, size=8.5, line_height=12.5):
        full_text = f"{bold_prefix} {text}" if bold_prefix else text
        lines = self.wrap_text(full_text, self.content_width - 16, size, False)
        
        self.check_space(line_height * len(lines) + 2)
        s = self.current_stream
        s.append("q")
        # Bullet dot
        s.append("0.20 0.45 0.85 rg")
        s.append(f"{self.margin_x + 4} {self.cursor_y - size + 2} 3 3 re f")
        s.append("Q")
        
        for line in lines:
            self.check_space(line_height)
            s = self.current_stream
            s.append("q")
            s.append("0.16 0.20 0.26 rg")
            s.append("BT")
            s.append(f"/F1 {size} Tf")
            s.append(f"{self.margin_x + 14} {self.cursor_y - size} Td")
            s.append(f"({self.escape_text(line)}) Tj")
            s.append("ET")
            s.append("Q")
            self.cursor_y -= line_height
        self.cursor_y -= 2

    def add_callout(self, title, lines_text, kind="warning"):
        color_map = {
            "critical": {"bg": (0.99, 0.94, 0.94), "border": (0.85, 0.20, 0.20), "text": (0.55, 0.08, 0.08)},
            "warning":  {"bg": (0.99, 0.97, 0.90), "border": (0.85, 0.55, 0.10), "text": (0.50, 0.30, 0.05)},
            "tip":      {"bg": (0.94, 0.98, 0.95), "border": (0.10, 0.65, 0.35), "text": (0.05, 0.40, 0.20)},
            "info":     {"bg": (0.94, 0.96, 0.99), "border": (0.15, 0.50, 0.90), "text": (0.08, 0.28, 0.55)},
        }
        cfg = color_map.get(kind, color_map["info"])
        
        wrapped_lines = []
        for l in lines_text:
            wrapped_lines.extend(self.wrap_text(l, self.content_width - 28, 8.2, False))
            
        box_h = 20 + len(wrapped_lines) * 11.5 + 6
        self.check_space(box_h + 8)
        
        s = self.current_stream
        s.append("q")
        # Box background
        s.append(f"{cfg['bg'][0]} {cfg['bg'][1]} {cfg['bg'][2]} rg")
        s.append(f"{self.margin_x} {self.cursor_y - box_h} {self.content_width} {box_h} re f")
        
        # Left accent stripe
        s.append(f"{cfg['border'][0]} {cfg['border'][1]} {cfg['border'][2]} rg")
        s.append(f"{self.margin_x} {self.cursor_y - box_h} 4.0 {box_h} re f")
        
        # Title
        s.append(f"{cfg['text'][0]} {cfg['text'][1]} {cfg['text'][2]} rg")
        s.append("BT")
        s.append("/F2 8.5 Tf")
        s.append(f"{self.margin_x + 12} {self.cursor_y - 13} Td")
        s.append(f"({self.escape_text(title)}) Tj")
        s.append("ET")
        
        # Lines
        cur_y = self.cursor_y - 25
        s.append("0.16 0.20 0.26 rg")
        for wl in wrapped_lines:
            s.append("BT")
            s.append("/F1 8.0 Tf")
            s.append(f"{self.margin_x + 12} {cur_y} Td")
            s.append(f"({self.escape_text(wl)}) Tj")
            s.append("ET")
            cur_y -= 11.5
            
        s.append("Q")
        self.cursor_y -= (box_h + 8)

    def add_table(self, headers, rows, col_widths):
        table_w = sum(col_widths)
        row_h = 16
        
        self.check_space(row_h * (len(rows) + 1) + 12)
        
        s = self.current_stream
        s.append("q")
        # Header background
        s.append("0.11 0.17 0.26 rg")
        s.append(f"{self.margin_x} {self.cursor_y - row_h} {table_w} {row_h} re f")
        
        # Header text
        s.append("1 1 1 rg")
        x_off = self.margin_x
        for i, h in enumerate(headers):
            s.append("BT")
            s.append("/F2 8.0 Tf")
            s.append(f"{x_off + 5} {self.cursor_y - 11} Td")
            s.append(f"({self.escape_text(h)}) Tj")
            s.append("ET")
            x_off += col_widths[i]
            
        self.cursor_y -= row_h
        
        # Rows
        for r_idx, row in enumerate(rows):
            self.check_space(row_h + 4)
            # Zebra stripe
            if r_idx % 2 == 1:
                s.append("0.96 0.97 0.99 rg")
                s.append(f"{self.margin_x} {self.cursor_y - row_h} {table_w} {row_h} re f")
                
            # Border bottom
            s.append("0.87 0.89 0.93 RG")
            s.append("0.5 w")
            s.append(f"{self.margin_x} {self.cursor_y - row_h} m {self.margin_x + table_w} {self.cursor_y - row_h} l S")
            
            # Cell texts
            x_off = self.margin_x
            for c_idx, cell in enumerate(row):
                s.append("0.16 0.20 0.26 rg")
                s.append("BT")
                font = "/F2" if c_idx == 0 or "Mark" in cell or "35" in cell or "15" in cell else "/F1"
                s.append(f"{font} 7.5 Tf")
                s.append(f"{x_off + 5} {self.cursor_y - 11} Td")
                cell_snippet = cell[:48]
                s.append(f"({self.escape_text(cell_snippet)}) Tj")
                s.append("ET")
                x_off += col_widths[c_idx]
                
            self.cursor_y -= row_h
            
        # Left & Right bounding box
        s.append("0.84 0.87 0.91 RG")
        s.append("0.5 w")
        s.append(f"{self.margin_x} {self.cursor_y} {table_w} {row_h * (len(rows) + 1)} re s")
        s.append("Q")
        self.cursor_y -= 10

    def add_code_block(self, title, code_lines):
        line_h = 10.5
        box_h = 16 + len(code_lines) * line_h + 4
        self.check_space(box_h + 8)
        
        s = self.current_stream
        s.append("q")
        s.append("0.09 0.11 0.15 rg")
        s.append(f"{self.margin_x} {self.cursor_y - box_h} {self.content_width} {box_h} re f")
        
        s.append("0.14 0.17 0.23 rg")
        s.append(f"{self.margin_x} {self.cursor_y - 14} {self.content_width} 14 re f")
        
        s.append("0.65 0.75 0.88 rg")
        s.append("BT")
        s.append("/F2 7.0 Tf")
        s.append(f"{self.margin_x + 8} {self.cursor_y - 10} Td")
        s.append(f"({self.escape_text(title)}) Tj")
        s.append("ET")
        
        cur_y = self.cursor_y - 24
        s.append("0.88 0.92 0.96 rg")
        for cl in code_lines:
            s.append("BT")
            s.append("/F3 7.5 Tf")
            s.append(f"{self.margin_x + 8} {cur_y} Td")
            s.append(f"({self.escape_text(cl)}) Tj")
            s.append("ET")
            cur_y -= line_h
            
        s.append("Q")
        self.cursor_y -= (box_h + 8)

    def wrap_text(self, text, max_w, font_size, is_bold=False):
        factor = 0.55 if is_bold else 0.48
        char_limit = int(max_w / (font_size * factor))
        words = text.split(" ")
        lines = []
        cur_line = []
        cur_len = 0
        for w in words:
            w_len = len(w) + 1
            if cur_len + w_len > char_limit:
                if cur_line:
                    lines.append(" ".join(cur_line))
                cur_line = [w]
                cur_len = len(w)
            else:
                cur_line.append(w)
                cur_len += w_len
        if cur_line:
            lines.append(" ".join(cur_line))
        return lines

    def save(self):
        if self.current_stream:
            self.pages.append(self.current_stream)
            
        num_pages = len(self.pages)
        page_obj_ids = []
        stream_obj_ids = []
        
        next_id = 6
        for p in range(num_pages):
            page_obj_ids.append(next_id)
            stream_obj_ids.append(next_id + 1)
            next_id += 2
            
        objects_dict = {}
        objects_dict[1] = b"<< /Type /Catalog /Pages 2 0 R >>"
        
        kids_str = " ".join([f"{pid} 0 R" for pid in page_obj_ids])
        objects_dict[2] = f"<< /Type /Pages /Kids [{kids_str}] /Count {num_pages} >>".encode('ascii')
        
        objects_dict[3] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>"
        objects_dict[4] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>"
        objects_dict[5] = b"<< /Type /Font /Subtype /Type1 /BaseFont /Courier >>"
        
        for i in range(num_pages):
            pid = page_obj_ids[i]
            sid = stream_obj_ids[i]
            
            p_obj = (f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {self.width} {self.height}] "
                     f"/Contents {sid} 0 R "
                     f"/Resources << /Font << /F1 3 0 R /F2 4 0 R /F3 5 0 R >> >> >>")
            objects_dict[pid] = p_obj.encode('ascii')
            
            content_str = "\n".join(self.pages[i])
            content_bytes = content_str.encode('latin1')
            s_obj = f"<< /Length {len(content_bytes)} >>\nstream\n".encode('ascii') + content_bytes + b"\nendstream"
            objects_dict[sid] = s_obj
            
        with open(self.filename, 'wb') as f:
            f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            xref_offsets = {}
            for oid in sorted(objects_dict.keys()):
                xref_offsets[oid] = f.tell()
                f.write(f"{oid} 0 obj\n".encode('ascii'))
                f.write(objects_dict[oid])
                f.write(b"\nendobj\n")
                
            xref_start = f.tell()
            total_objs = max(objects_dict.keys()) + 1
            f.write(f"xref\n0 {total_objs}\n".encode('ascii'))
            f.write(b"0000000000 65535 f \n")
            for oid in range(1, total_objs):
                if oid in xref_offsets:
                    f.write(f"{xref_offsets[oid]:010d} 00000 n \n".encode('ascii'))
                else:
                    f.write(b"0000000000 00000 f \n")
                    
            trailer = (f"trailer\n<< /Size {total_objs} /Root 1 0 R >>\n"
                       f"startxref\n{xref_start}\n%%EOF\n")
            f.write(trailer.encode('ascii'))
            
        print(f"Successfully generated {self.filename} ({num_pages} pages)")


def build_full_guide():
    doc = TrustVaultPDFBuilder("TrustVault_Executive_Guide.pdf")
    
    # ================= PAGE 1 =================
    doc.new_page(is_cover=True)
    doc.add_title_banner(
        "TrustVault: Executive & Security Blueprint",
        "A plain-English guide to building, defending, and acing the TrustVault challenge."
    )
    
    doc.add_section("01", "The Situation in Plain English")
    doc.add_paragraph(
        "Every company shares highly confidential files: executive salary sheets, customer NDAs, trade secrets, "
        "and audit records. In standard software, two catastrophic failures happen constantly: (1) Broken permissions "
        "where someone is added to a folder for one file and inherits forty files, or where an ex-employee's link still "
        "works; and (2) Zero accountability, where a leak occurs and nobody can answer who opened the file or when."
    )
    doc.add_paragraph(
        "TrustVault is a secure document platform built to solve exactly this: a platform where the wrong person cannot reach "
        "a document through ANY route, and where you can mathematically prove exactly who reached it, including failed attempts."
    )
    
    doc.add_callout(
        "CRITICAL ASSESSMENT REALITY: THIS IS NOT A STANDARD CRUD APP",
        [
            "The challenge author explicitly states: 'This is a security problem wearing the clothes of a CRUD application.'",
            "Many candidates spend 80% of their time making a fancy frontend with drag-and-drop animations, but fail the assessment.",
            "If a judge can run `curl https://your-app/api/docs/42` with an unauthorized user's token and get a 200 OK, you lose almost all 35 Security marks immediately. The backend authorization engine is what is being judged."
        ],
        kind="critical"
    )
    
    doc.add_section("02", "The 3 Non-Negotiable Rules (Fail Any = Fail System)")
    doc.add_paragraph("The specification defines three non-negotiable rules. If your system violates any of these, it fails:")
    
    doc.add_bullet(
        "Rule 1: Server-Side Decides Every Time.",
        "Never rely on hiding a button, disabling a menu, or client-side routing. Every single API endpoint, file stream, and search query must independently verify authorization against the database before returning a single byte."
    )
    doc.add_bullet(
        "Rule 2: Provable Audit Trail (Successes AND Denials).",
        "You must be able to prove who reached a file, when, and from what IP. Crucially, you must also record REFUSED ATTEMPTS (HTTP 403). If Alice tries to access Bob's salary sheet and is blocked, that denied attempt must be logged."
    )
    doc.add_bullet(
        "Rule 3: Instant Revocation (Zero Window of Vulnerability).",
        "The millisecond an owner revokes access from a user, any links, active sessions, or pending requests for that document must cease functioning immediately. No 15-minute token caching delays."
    )
    
    # ================= PAGE 2 =================
    doc.new_page()
    doc.add_section("03", "The 10 Required Features (The Baseline Floor)")
    doc.add_paragraph("The specification lists 10 baseline requirements. All ten must be cleanly implemented:")
    
    table_headers = ["#", "Feature", "Specification", "Key Security Implementation"]
    table_rows = [
        ["1", "Authentication", "At least 3 roles: Admin, Owner, Viewer", "Bcrypt password hashing, strict session/token auth"],
        ["2", "Document Management", "Upload, organise, search, view, delete", "Files stored outside public root; UUID file names"],
        ["3", "Granular Permissions", "Read vs Edit granted to named users", "Normalized permissions table; per-document grants"],
        ["4", "Owner Delegation", "Grant access and take it back", "Only Document Owner (or Admin) can alter rights"],
        ["5", "Strict Access Wall", "Unauthorized users blocked from all ops", "Server-level 403 Forbidden on read/download/edit/delete"],
        ["6", "Tamper-Evident Audit", "Log upload, download, edit, delete, perms", "Append-only table; includes refused/denied attempts"],
        ["7", "Multi-Param Search", "Search by name, owner, category, date", "SQL WHERE clause restricted to accessible docs only"],
        ["8", "Upload Validation", "Validate size, MIME type, extensions", "Sniff magic bytes (%PDF, PK); sanitize file names"],
        ["9", "Admin Oversight", "Activity view, permission changes, alerts", "Admin sees audit trail & access graphs; not file payloads"],
        ["10", "Automated Tests", "Automated proof of cross-user isolation", "Integration tests simulating unauthorized curl attacks"]
    ]
    doc.add_table(table_headers, table_rows, [18, 115, 185, 206])
    
    doc.add_section("04", "The 100-Point Marking Rubric Breakdown")
    doc.add_paragraph("Your grade is determined across six distinct bands:")
    
    rubric_headers = ["Marks", "Category", "What the Judges Look For", "How to Win"]
    rubric_rows = [
        ["35 Marks", "Security", "Judge attacks your live deployed URL with automated exploits", "Close all IDOR, path traversal, delayed token bugs"],
        ["15 Marks", "Threat Thinking", "THREATS.md compared against the evaluators' master threat list", "Be brutally honest about threats found, fixed, or accepted"],
        ["15 Marks", "Functionality", "The 10 baseline requirements functioning smoothly", "Clean UI/API covering all operations end-to-end"],
        ["15 Marks", "AI Usage", "PROMPTS.md showing 5+ dated entries catching AI security bugs", "Document where AI suggested flawed security and how you fixed it"],
        ["10 Marks", "Engineering Quality", "Clean architecture, error handling, defensive programming", "Modular structure, separation of concerns, no messy code"],
        ["10 Marks", "Documentation & Demo", "Clean README, seed accounts, clean clone deploy, 5-min video", "Single-command docker/setup script; clear video walkthrough"]
    ]
    doc.add_table(rubric_headers, rubric_rows, [45, 100, 195, 184])
    
    doc.add_callout(
        "THE 'ONE DOCUMENT' RULE (DON'T LOSE 35 MARKS)",
        [
            "The spec notes: 'One document reached by someone who should not have reached it costs most of the first band, whatever else works.'",
            "This means if your app has 99 features working, but an unauthorized user can fetch document #2 by modifying an API ID, you lose 35 marks immediately.",
            "Security is not a feature; it is the entire evaluation."
        ],
        kind="warning"
    )
    
    # ================= PAGE 3 =================
    doc.new_page()
    doc.add_section("05", "The Judges' Attack Playbook (7 Exploits & Defenses)")
    doc.add_paragraph(
        "A judge will spend dedicated time attempting to bypass your permissions. Below are the exact attacks "
        "they will execute and the architecture required to stop them:"
    )
    
    doc.add_subsection("Attack 1: BOLA / IDOR (Insecure Direct Object Reference)")
    doc.add_bullet("The Attack:", "User Alice is granted Doc 1. Alice inspects network traffic, sees `GET /api/documents/1/download`, and sends `GET /api/documents/2/download` (Bob's salary letter).")
    doc.add_bullet("The Flaw:", "Code queries `SELECT * FROM documents WHERE id = :id` without checking if Alice owns it or has an active grant.")
    doc.add_bullet("The Fix:", "Run an authorization query joining `DocumentPermissions` and `current_user_id`. Return HTTP 403 immediately and log the denied attempt.")
    
    doc.add_subsection("Attack 2: Direct Static Storage Bypass (URL Guessing)")
    doc.add_bullet("The Attack:", "Judge guesses the storage path: `https://your-domain.com/uploads/salary_bob.pdf` or discovers the cloud S3 bucket URL.")
    doc.add_bullet("The Flaw:", "Saving uploaded files directly into a public static directory (e.g. `public/` or `static/uploads/`).")
    doc.add_bullet("The Fix:", "Store files outside web root (e.g. `storage/vault/` with UUID names like `a7f9-4b12...bin`). Serve files ONLY through an authenticated streaming controller.")
    
    doc.add_subsection("Attack 3: Delayed Revocation Window (Token Caching)")
    doc.add_bullet("The Attack:", "User Charlie is granted access. Owner revokes Charlie's access. Charlie immediately hits download using his existing session/token.")
    doc.add_bullet("The Flaw:", "Relying on stateless JWT tokens containing `permissions: ['read_doc_1']` with 1-hour expiry.")
    doc.add_bullet("The Fix:", "Never embed document permissions inside JWTs! Always query live permission records in the database on every download request.")
    
    doc.add_subsection("Attack 4: Privilege Escalation on Permissions API")
    doc.add_bullet("The Attack:", "A Viewer sends `POST /api/documents/1/permissions` with `{'user_id': 'charlie', 'permission': 'edit'}`.")
    doc.add_bullet("The Flaw:", "Endpoint checks if user is logged in, but fails to check if `current_user_id == document.owner_id`.")
    doc.add_bullet("The Fix:", "Enforce role/owner validation on every grant/revoke endpoint.")
    
    # ================= PAGE 4 =================
    doc.new_page()
    doc.add_subsection("Attack 5: Malicious File Upload (XSS & Path Traversal)")
    doc.add_bullet("The Attack:", "Judge uploads a file named `../../etc/passwd` or an SVG file containing `<script>alert(document.cookie)</script>`.")
    doc.add_bullet("The Flaw:", "Trusting user-supplied filename and using it in file paths; or serving SVGs with `Content-Type: image/svg+xml` without CSP headers.")
    doc.add_bullet("The Fix:", "Strip filenames, store as UUIDs on disk, sniff file magic bytes (verify PDF starts with `%PDF-`), and serve downloads with `Content-Disposition: attachment; filename=\"safe.pdf\"`.")
    
    doc.add_subsection("Attack 6: Metadata Leakage via Search & Error Messages")
    doc.add_bullet("The Attack:", "Unauthorized user searches 'Confidential Acquisition' or types random IDs to observe differences in error responses (404 vs 403).")
    doc.add_bullet("The Flaw:", "Global document search query without permission filtering, or leaking document titles in error responses.")
    doc.add_bullet("The Fix:", "Search SQL query must include `JOIN document_permissions` to only match docs the caller has rights to view.")
    
    doc.add_subsection("Attack 7: Audit Log Tampering (Covering Tracks)")
    doc.add_bullet("The Attack:", "Attacker attempts to delete or update rows in `audit_logs` table via SQL injection or admin UI.")
    doc.add_bullet("The Flaw:", "Providing an admin endpoint to 'Clear Logs' or editable audit records.")
    doc.add_bullet("The Fix:", "Audit log table is strictly append-only. No UPDATE or DELETE SQL statements exist anywhere in the codebase.")
    
    doc.add_section("06", "The Core Architecture Pattern")
    doc.add_paragraph("Below is the bulletproof authorization and streaming pattern for every document request:")
    
    code_sample = [
        "@app.route('/api/documents/<doc_id>/download', methods=['GET'])",
        "@login_required",
        "def download_document(doc_id):",
        "    user = current_user",
        "    doc = Document.query.get_or_404(doc_id)",
        "    ",
        "    # THE CRITICAL LINE (Evaluated on every request):",
        "    has_access = check_permission(user.id, doc.id, required='read')",
        "    ",
        "    if not has_access:",
        "        # RULE 2: Log refused attempt",
        "        log_audit(user_id=user.id, doc_id=doc.id, action='DOWNLOAD', status='DENIED')",
        "        abort(403, 'Access denied')",
        "        ",
        "    # Log successful access",
        "    log_audit(user_id=user.id, doc_id=doc.id, action='DOWNLOAD', status='ALLOWED')",
        "    ",
        "    # Safe isolated file streaming from non-public storage directory",
        "    safe_path = os.path.join(VAULT_STORAGE_DIR, f'{doc.storage_uuid}.dat')",
        "    return send_file(safe_path, as_attachment=True, download_name=doc.original_filename)"
    ]
    doc.add_code_block("Python/Flask: Secure Streaming & Audit Enforcement Pattern", code_sample)
    
    # ================= PAGE 5 =================
    doc.new_page()
    doc.add_section("07", "How to Write THREATS.md (15 Marks)")
    doc.add_paragraph(
        "THREATS.md is the document that separates winning submissions from average ones. "
        "The evaluators maintain their own secret list of threats and match yours against it. Marks are awarded for "
        "threats you found and closed, extra marks for threats they didn't think of, and marks for HONESTLY accepting risks."
    )
    
    doc.add_callout(
        "THE GOLDEN RULE OF THREATS.MD: HONESTY SCORES HIGH",
        [
            "An entry saying: 'I know this system is vulnerable to memory-exhaustion DoS if a user uploads 100 simultaneous 25MB files, and I accepted this risk because implementing a Redis distributed queue was out of scope for a 7-day sprint' IS WORTH FULL MARKS.",
            "Pretending a hole doesn't exist scores zero because the judges will find it.",
            "Do not stop at 4 obvious entries. Provide 8 to 12 rigorous threat analyses."
        ],
        kind="tip"
    )
    
    doc.add_subsection("Required Structure for Each Entry in THREATS.md")
    doc.add_bullet("1. Threat Title & Category:", "e.g., IDOR on Document Download API (OWASP API1:2023 Broken Object Level Authorization).")
    doc.add_bullet("2. Attack Vector:", "How an attacker would exploit it (exact HTTP method, route, parameters, and headers).")
    doc.add_bullet("3. Mitigation Implemented:", "Specific defensive code (e.g. SQL join on permission table, server-side UUID storage).")
    doc.add_bullet("4. Automated Test Verification:", "Name of test case in test suite proving the attack is blocked (e.g., `test_unauthorized_download_denied`).")
    doc.add_bullet("5. Residual / Accepted Risk:", "What remains open and why (e.g., timing attack on doc existence vs 404 response).")
    
    doc.add_section("08", "How to Write PROMPTS.md (15 Marks)")
    doc.add_paragraph(
        "PROMPTS.md is your AI interaction record. Writing it on the last day scores zero. "
        "It must show evidence of directing AI tools and catching them being confidently wrong."
    )
    
    doc.add_callout(
        "PROMPTS.MD CRITICAL REQUIREMENTS (DON'T MISS THESE)",
        [
            "1. At least 5 dated entries spread across the week.",
            "2. At least TWO entries must be specifically about Authorization, Access Control, or Audit Trail.",
            "3. Each entry must follow the 4-part structure: (a) What you asked; (b) What AI produced; (c) What was WRONG with it specifically; (d) What you did instead, with a link to the Git commit where you fixed it.",
            "4. 'It was all fine' or 'AI was helpful' scores ZERO marks. You must show the security flaw the AI generated and how you caught it."
        ],
        kind="critical"
    )
    
    # ================= PAGE 6 =================
    doc.new_page()
    doc.add_subsection("Sample High-Scoring Entry for PROMPTS.md")
    
    doc.add_bullet(
        "Date & Commit:",
        "Nov 4, 2026 | Commit `a4f89c1` (fix: enforce server-side auth on download route)"
    )
    doc.add_bullet(
        "What I Asked:",
        "'Generate a Flask endpoint to download documents given a document_id.'"
    )
    doc.add_bullet(
        "What the AI Produced:",
        "`send_file(f'uploads/{doc_id}.pdf')` with only `@login_required` checking if the user was logged in."
    )
    doc.add_bullet(
        "What was Wrong (Security Flaw):",
        "Massive BOLA / IDOR vulnerability! The AI verified authentication (logged in), but failed authorization (did the user have access to THIS specific document?). Any logged-in user could download confidential salary docs of other users."
    )
    doc.add_bullet(
        "What I Did Instead:",
        "Rewrote the endpoint to query `DocumentPermission` joining `current_user.id`. If no row exists, immediately recorded an audit log entry with `status='DENIED'` and returned HTTP 403 Forbidden. Added unit test `test_cross_tenant_download_blocked` in `tests/test_security.py`."
    )
    
    doc.add_section("09", "The Live Interview Preparation: The 'One Question'")
    doc.add_paragraph(
        "Shortlisted candidates undergo a live code walkthrough where the interviewer will ask you to make a live change. "
        "Expect the following exact question:"
    )
    
    doc.add_callout(
        "THE INTERVIEW TRAP QUESTION",
        [
            "Interviewer Question: 'Show me where the authorization decision is made when someone downloads a file. What would happen if that line were removed?'",
            "What they are testing:",
            "1. Do you know your own code? (Can you jump directly to the exact controller and line without hesitation?)",
            "2. The Tear-down Test: If that authorization line is removed and the test suite is executed, DO THE TESTS FAIL? If tests still pass, your tests were fake and test nothing."
        ],
        kind="warning"
    )
    
    doc.add_paragraph(
        "Your Model Answer in the Interview:",
        font="F2",
        color=(0.10, 0.35, 0.70)
    )
    doc.add_paragraph(
        "1. Open `services/auth_service.py` at function `can_access_document(user_id, doc_id, 'read')`.\n"
        "2. Explain: 'If this line is removed, the function falls through and unauthorized users receive the file stream. However, our test suite in `tests/test_auth_isolation.py` runs `test_unauthorized_download_fails()`. If you comment out this check, the test immediately fails with an assertion error expecting 403 but getting 200.'\n"
        "3. Live Demo: Comment out the line in front of them and run `pytest`. Watch the red test failure prove that your security net is airtight."
    )
    
    # ================= PAGE 7 =================
    doc.new_page()
    doc.add_section("10", "Recommended Database Schema & Entity Design")
    doc.add_paragraph("A clean, normalized schema is the foundation of provable security. Below is the recommended design:")
    
    schema_headers = ["Table", "Key Columns", "Security Purpose"]
    schema_rows = [
        ["users", "id, email, password_hash, role (admin/owner/viewer)", "Stores credentials with bcrypt; baseline identity"],
        ["documents", "id, owner_id, original_name, storage_uuid, size, mime", "Metadata record; file stored safely on disk by storage_uuid"],
        ["document_permissions", "id, document_id, user_id, permission (read/edit), granted_by, granted_at", "Explicit grants to named users; real-time revocation"],
        ["audit_logs", "id, user_id, document_id, action, status (ALLOWED/DENIED), ip_address, timestamp", "Append-only security log; proves who reached or attempted to reach"]
    ]
    doc.add_table(schema_headers, schema_rows, [110, 240, 174])
    
    doc.add_section("11", "7-Day Day-by-Day Execution Roadmap")
    doc.add_paragraph("Follow this systematic timeline to guarantee completion without last-minute panic:")
    
    plan_headers = ["Day", "Milestone Focus", "Deliverables Produced", "Git / AI Commit Goal"]
    plan_rows = [
        ["Day 1", "Foundation & Auth", "DB schema, Flask/FastAPI setup, Bcrypt auth, 3 roles", "Commit seed data & schema; log prompt #1"],
        ["Day 2", "File Storage & Stream", "MIME sniffing upload, UUID storage, safe stream endpoint", "Validate magic bytes; block static folder bypass"],
        ["Day 3", "Permission Engine", "Grant/Revoke API, instant revocation, zero caching", "Log prompt #2 on auth flaw caught; write tests"],
        ["Day 4", "Audit & Denied Logging", "Audit log model, log 403 denied attempts, admin UI", "Log prompt #3 on audit tamper protection"],
        ["Day 5", "Security Test Suite", "Automated tests for IDOR, path traversal, revocation", "Automated tests proving unauthorized access blocked"],
        ["Day 6", "THREATS.md & Cloud Deploy", "Deploy to Render/Railway early; verify live URL & seed users", "Log prompt #4 & #5; commit comprehensive THREATS.md"],
        ["Day 7", "Video Demo & Write-Up", "5-minute screen recording, final README polish, seed login", "Final submission tag; clean clone verification"]
    ]
    doc.add_table(plan_headers, plan_rows, [45, 120, 205, 154])
    
    doc.add_callout(
        "REMINDER: DEPLOY EARLY IN THE WEEK",
        [
            "The challenge instructions explicitly warn: 'Deploy early in the week, not on the last day. People who leave it to the end usually do not deploy at all.'",
            "Deploy your database and backend to Render, Railway, or Fly.io by Day 5 or 6 so you have full confidence in your live URL."
        ],
        kind="info"
    )
    
    # ================= PAGE 8 =================
    doc.new_page()
    doc.add_section("12", "The Final Submission Checklist")
    doc.add_paragraph("Before handing in your project, verify every item on this checklist:")
    
    doc.add_bullet("[  ] Public Git Repository:", "Has commits spread regularly across the entire week (no single massive commit at the end).")
    doc.add_bullet("[  ] Live Working URL:", "Accessible online with seed data loaded and tested from an incognito browser.")
    doc.add_bullet("[  ] README.md with Credentials:", "Contains login credentials for at least one Admin, one Document Owner, and one Viewer.")
    doc.add_bullet("[  ] THREATS.md Completed:", "Lists 8-12 security threats analyzed, how each was mitigated, and accepted risks with technical justifications.")
    doc.add_bullet("[  ] PROMPTS.md Completed:", "Contains at least 5 dated entries following the 4-part structure, with at least 2 entries on Authorization/Audit.")
    doc.add_bullet("[  ] Automated Security Tests:", "Running `pytest` passes 100% of tests. Removing an authorization check makes tests fail.")
    doc.add_bullet("[  ] Database Schema & Setup Scripts:", "A clean clone can run a single command (e.g. `docker compose up` or `python init_db.py`) to initialize.")
    doc.add_bullet("[  ] API Documentation:", "Clearly documents each endpoint and specifies exactly which role/permission is required to call it.")
    doc.add_bullet("[  ] 5-Minute Demo Video:", "Walks through: (1) Roles; (2) Upload & permission grant; (3) Unauthorized access refusal; (4) Instant revocation; (5) Audit log inspection.")
    doc.add_bullet("[  ] Short Architectural Write-Up:", "Summary of what you built, what you deliberately did not build, and your permission model in your own words.")
    
    doc.add_callout(
        "FINAL WORD OF ENCOURAGEMENT",
        [
            "TrustVault is an extraordinary project to showcase true security engineering skill.",
            "By focusing on server-side authorization, tamper-resistant audit logs of denied attempts, and instant revocation, you will stand far above candidates who only build visual UI screens.",
            "Keep your code simple, your authorization explicit, and your tests rigorous. You've got this!"
        ],
        kind="tip"
    )
    
    doc.save()

if __name__ == '__main__':
    build_full_guide()

