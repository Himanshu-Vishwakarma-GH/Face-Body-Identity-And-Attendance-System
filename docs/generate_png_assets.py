import os
from PIL import Image, ImageDraw, ImageFont

def get_fonts():
    bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 36)
    title_bold = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 40)
    h2 = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 20)
    h3 = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 15)
    body = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 14)
    mono_bold = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 12)
    mono_sm = ImageFont.truetype("C:/Windows/Fonts/consola.ttf", 11)
    mono_badge = ImageFont.truetype("C:/Windows/Fonts/consolab.ttf", 10)
    return {
        "title": title_bold,
        "h2": h2,
        "h3": h3,
        "body": body,
        "mono_b": mono_bold,
        "mono_sm": mono_sm,
        "mono_badge": mono_badge
    }

def create_hero_banner(path):
    W, H = 1200, 420
    img = Image.new("RGB", (W, H), color=(9, 13, 22))
    draw = ImageDraw.Draw(img)
    f = get_fonts()

    # Outer border
    draw.rounded_rectangle([15, 15, W - 15, H - 15], radius=16, outline=(30, 41, 59), width=1)
    
    # Corner brackets (Cyber Cyan)
    c_color = (6, 182, 212)
    # TL
    draw.line([(15, 55), (15, 15), (55, 15)], fill=c_color, width=3)
    # TR
    draw.line([(W - 55, 15), (W - 15, 15), (W - 15, 55)], fill=c_color, width=3)
    # BL
    draw.line([(15, H - 55), (15, H - 15), (55, H - 15)], fill=c_color, width=3)
    # BR
    draw.line([(W - 55, H - 15), (W - 15, H - 15), (W - 15, H - 55)], fill=c_color, width=3)

    # Status Pill
    draw.rounded_rectangle([45, 35, 305, 63], radius=14, fill=(16, 185, 129, 35), outline=(16, 185, 129), width=1)
    draw.ellipse([58, 45, 66, 53], fill=(16, 185, 129))
    draw.text((75, 41), "SYSTEM ARMED & OPERATIONAL", fill=(16, 185, 129), font=f["mono_badge"])

    # IBM Hackathon Pill
    draw.rounded_rectangle([W - 245, 35, W - 45, 63], radius=14, fill=(59, 130, 246, 35), outline=(59, 130, 246), width=1)
    draw.text((W - 225, 41), "IBM HACKATHON 2026", fill=(96, 165, 250), font=f["mono_badge"])

    # Title & Subtitle
    draw.text((45, 95), "AI Face & Body Identity Matrix", fill=(255, 255, 255), font=f["title"])
    draw.text((45, 150), "Autonomous Enterprise Access Control • Biometric Anti-Tailgating • Multi-Zone Surveillance", fill=(6, 182, 212), font=f["h2"])
    draw.text((45, 185), "Continuous 1:1 Cosine Similarity Verification • Anthropometric Body Ratios • Zero-Technical Hardware Pairing", fill=(148, 163, 184), font=f["body"])

    # 4 Feature Badges
    cards = [
        ("512-DIM INSIGHTFACE", "ArcFace Cosine Matching", ">92% Verified Confidence", (6, 182, 212)),
        ("YOLOV8 POSE ESTIMATION", "Body Anthropometrics", "Shoulder-to-Hip Skeletal Ratios", (16, 185, 129)),
        ("TAILGATING RADAR", "Person-Swipe Correlation", "5-Second Corridor Detection", (244, 63, 94)),
        ("REDIS VECTOR VAULT", "AES-256-GCM Encrypted", "Sub-15ms In-Memory TTL Cache", (168, 85, 247))
    ]

    card_w = 260
    card_gap = 20
    start_x = 45
    card_y = 235

    for i, (tag, heading, desc, col) in enumerate(cards):
        x = start_x + i * (card_w + card_gap)
        draw.rounded_rectangle([x, card_y, x + card_w, card_y + 130], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
        draw.text((x + 18, card_y + 18), tag, fill=col, font=f["mono_b"])
        draw.text((x + 18, card_y + 45), heading, fill=(255, 255, 255), font=f["h3"])
        draw.text((x + 18, card_y + 85), desc, fill=(100, 116, 139), font=f["mono_sm"])

    img.save(path, "PNG")
    print(f"Created {path}")

def create_kiosk_preview(path):
    W, H = 1000, 620
    img = Image.new("RGB", (W, H), color=(7, 10, 18))
    draw = ImageDraw.Draw(img)
    f = get_fonts()

    # Outer Monitor Frame
    draw.rounded_rectangle([8, 8, W - 8, H - 8], radius=16, outline=(51, 65, 85), width=2)
    # Header bar
    draw.rounded_rectangle([10, 10, W - 10, 52], radius=12, fill=(15, 23, 42))
    draw.ellipse([26, 26, 36, 36], fill=(239, 68, 68))
    draw.ellipse([44, 26, 54, 36], fill=(234, 179, 8))
    draw.ellipse([62, 26, 72, 36], fill=(34, 197, 94))
    draw.text((320, 24), "DOOR ENTRY KIOSK • LIVE RETICLE STATION (PORT 8000/camera)", fill=(148, 163, 184), font=f["mono_b"])

    # Left Viewport (Camera Box)
    cam_x, cam_y, cam_w, cam_h = 25, 70, 640, 525
    draw.rounded_rectangle([cam_x, cam_y, cam_x + cam_w, cam_y + cam_h], radius=14, fill=(5, 8, 15), outline=(6, 182, 212), width=1)

    # Reticle brackets
    rk = 35
    draw.line([(cam_x + 25, cam_y + 25 + rk), (cam_x + 25, cam_y + 25), (cam_x + 25 + rk, cam_y + 25)], fill=(6, 182, 212), width=3)
    draw.line([(cam_x + cam_w - 25 - rk, cam_y + 25), (cam_x + cam_w - 25, cam_y + 25), (cam_x + cam_w - 25, cam_y + 25 + rk)], fill=(6, 182, 212), width=3)
    draw.line([(cam_x + 25, cam_y + cam_h - 25 - rk), (cam_x + 25, cam_y + cam_h - 25), (cam_x + 25 + rk, cam_y + cam_h - 25)], fill=(6, 182, 212), width=3)
    draw.line([(cam_x + cam_w - 25 - rk, cam_y + cam_h - 25), (cam_x + cam_w - 25, cam_y + cam_h - 25), (cam_x + cam_w - 25, cam_y + cam_h - 25 - rk)], fill=(6, 182, 212), width=3)

    # Center Face Detection Box
    fx, fy, fw, fh = cam_x + 220, cam_y + 110, 200, 230
    draw.rounded_rectangle([fx, fy, fx + fw, fy + fh], radius=8, outline=(16, 185, 129), width=2)
    # Pose lines
    draw.ellipse([fx + 95, fy + 60, fx + 105, fy + 70], fill=(56, 189, 248))
    draw.ellipse([fx + 55, fy + 140, fx + 65, fy + 150], fill=(56, 189, 248))
    draw.ellipse([fx + 135, fy + 140, fx + 145, fy + 150], fill=(56, 189, 248))
    draw.line([(fx + 60, fy + 145), (fx + 140, fy + 145)], fill=(56, 189, 248), width=2)

    # Reticle active badge
    draw.rounded_rectangle([cam_x + 20, cam_y + 20, cam_x + 190, cam_y + 50], radius=8, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
    draw.ellipse([cam_x + 30, cam_y + 31, cam_x + 38, cam_y + 39], fill=(16, 185, 129))
    draw.text((cam_x + 46, cam_y + 27), "RETICLE ACTIVE", fill=(255, 255, 255), font=f["mono_badge"])
    draw.text((cam_x + 145, cam_y + 27), "29 FPS", fill=(56, 189, 248), font=f["mono_badge"])

    # Bottom Access Granted Banner
    ban_x, ban_y, ban_w, ban_h = cam_x + 30, cam_y + cam_h - 75, cam_w - 60, 52
    draw.rounded_rectangle([ban_x, ban_y, ban_x + ban_w, ban_y + ban_h], radius=10, fill=(16, 185, 129, 45), outline=(16, 185, 129), width=2)
    draw.text((ban_x + 20, ban_y + 15), "ACCESS GRANTED • VERIFIED", fill=(16, 185, 129), font=f["h3"])
    draw.text((ban_x + ban_w - 180, ban_y + 16), "Himanshu V. (EMP-104)", fill=(255, 255, 255), font=f["mono_sm"])

    # Right Telemetry Sidebar
    side_x, side_y, side_w, side_h = cam_x + cam_w + 20, 70, 290, 525
    draw.rounded_rectangle([side_x, side_y, side_x + side_w, side_y + side_h], radius=14, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
    draw.text((side_x + 20, side_y + 22), "Biometric Telemetry", fill=(255, 255, 255), font=f["h2"])
    draw.text((side_x + 20, side_y + 48), "REAL-TIME INFERENCE STREAM", fill=(100, 116, 139), font=f["mono_badge"])

    # Metric 1: Face
    draw.text((side_x + 20, side_y + 85), "FACE COSINE SIMILARITY", fill=(148, 163, 184), font=f["mono_badge"])
    draw.text((side_x + side_w - 55, side_y + 85), "94.8%", fill=(16, 185, 129), font=f["mono_b"])
    draw.rounded_rectangle([side_x + 20, side_y + 105, side_x + side_w - 20, side_y + 115], radius=5, fill=(30, 41, 59))
    draw.rounded_rectangle([side_x + 20, side_y + 105, side_x + 235, side_y + 115], radius=5, fill=(16, 185, 129))

    # Metric 2: Body
    draw.text((side_x + 20, side_y + 140), "BODY SKELETON RATIO", fill=(148, 163, 184), font=f["mono_badge"])
    draw.text((side_x + side_w - 55, side_y + 140), "91.2%", fill=(56, 189, 248), font=f["mono_b"])
    draw.rounded_rectangle([side_x + 20, side_y + 160, side_x + side_w - 20, side_y + 170], radius=5, fill=(30, 41, 59))
    draw.rounded_rectangle([side_x + 20, side_y + 160, side_x + 225, side_y + 170], radius=5, fill=(56, 189, 248))

    # Metric 3: Tailgating Radar
    draw.text((side_x + 20, side_y + 195), "DETECTED PERSON COUNT", fill=(148, 163, 184), font=f["mono_badge"])
    draw.text((side_x + side_w - 75, side_y + 195), "1 PERSON", fill=(168, 85, 247), font=f["mono_b"])
    draw.rounded_rectangle([side_x + 20, side_y + 215, side_x + side_w - 20, side_y + 225], radius=5, fill=(30, 41, 59))
    draw.rounded_rectangle([side_x + 20, side_y + 215, side_x + 140, side_y + 225], radius=5, fill=(168, 85, 247))

    # Radar status card
    draw.rounded_rectangle([side_x + 20, side_y + 250, side_x + side_w - 20, side_y + 325], radius=10, fill=(16, 185, 129, 20), outline=(16, 185, 129), width=1)
    draw.text((side_x + 35, side_y + 265), "TAILGATING RADAR", fill=(16, 185, 129), font=f["mono_b"])
    draw.text((side_x + 35, side_y + 285), "Perimeter Clear", fill=(255, 255, 255), font=f["h3"])
    draw.text((side_x + 35, side_y + 305), "Swipe-Person correlation: 1:1", fill=(100, 116, 139), font=f["mono_badge"])

    # Badge reader card
    draw.rounded_rectangle([side_x + 20, side_y + 345, side_x + side_w - 20, side_y + 500], radius=10, fill=(2, 6, 23), outline=(51, 65, 85), width=1)
    draw.text((side_x + 35, side_y + 365), "BADGE SIMULATOR", fill=(148, 163, 184), font=f["mono_badge"])
    draw.rounded_rectangle([side_x + 35, side_y + 385, side_x + side_w - 35, side_y + 425], radius=8, fill=(30, 41, 59))
    draw.text((side_x + 50, side_y + 397), "EMP-104", fill=(255, 255, 255), font=f["mono_b"])
    draw.rounded_rectangle([side_x + 35, side_y + 440, side_x + side_w - 35, side_y + 485], radius=8, fill=(37, 99, 235))
    draw.text((side_x + 85, side_y + 455), "Swipe & Verify", fill=(255, 255, 255), font=f["h3"])

    img.save(path, "PNG")
    print(f"Created {path}")

def create_admin_preview(path):
    W, H = 1000, 620
    img = Image.new("RGB", (W, H), color=(7, 10, 18))
    draw = ImageDraw.Draw(img)
    f = get_fonts()

    # Frame & header
    draw.rounded_rectangle([8, 8, W - 8, H - 8], radius=16, outline=(51, 65, 85), width=2)
    draw.rounded_rectangle([10, 10, W - 10, 52], radius=12, fill=(15, 23, 42))
    draw.ellipse([26, 26, 36, 36], fill=(239, 68, 68))
    draw.ellipse([44, 26, 54, 36], fill=(234, 179, 8))
    draw.ellipse([62, 26, 72, 36], fill=(34, 197, 94))
    draw.text((360, 24), "ENTERPRISE ADMIN PORTAL (PORT 8000/admin)", fill=(148, 163, 184), font=f["mono_b"])

    # Left Sidebar
    sb_w = 200
    draw.rounded_rectangle([20, 68, 20 + sb_w, H - 20], radius=12, fill=(11, 17, 32), outline=(30, 41, 59), width=1)
    draw.text((35, 88), "AI ACCESS GUARD", fill=(255, 255, 255), font=f["h3"])
    draw.text((35, 106), "SECURITY CONTROL", fill=(100, 116, 139), font=f["mono_badge"])

    nav = [
        ("Live Camera Wall", True),
        ("Dashboard", False),
        ("Employee Directory", False),
        ("Enroll New Member", False),
        ("Cameras & Zones", False),
        ("Camera Health", False),
        ("Cross-Cam Journey", False),
        ("Access Audit Logs", False)
    ]

    for idx, (label, is_active) in enumerate(nav):
        ny = 135 + idx * 45
        if is_active:
            draw.rounded_rectangle([30, ny - 6, 20 + sb_w - 10, ny + 30], radius=8, fill=(30, 41, 59))
            draw.text((45, ny), label, fill=(56, 189, 248), font=f["body"])
        else:
            draw.text((45, ny), label, fill=(148, 163, 184), font=f["body"])

    # Main Area: 4-Camera Grid
    grid_x = 240
    draw.text((grid_x, 80), "Surveillance Matrix", fill=(255, 255, 255), font=f["h2"])
    draw.text((grid_x, 108), "ACTIVE CHECKPOINT VIDEO WALL • 4 CAMERAS CONNECTED", fill=(100, 116, 139), font=f["mono_badge"])

    # Connect button
    draw.rounded_rectangle([W - 170, 78, W - 25, 114], radius=8, fill=(37, 99, 235))
    draw.text((W - 155, 88), "+ Connect Camera", fill=(255, 255, 255), font=f["mono_sm"])

    cams = [
        ("CAM-01", "Main Entrance Kiosk", "Entry Zone A", "LIVE", (239, 68, 68)),
        ("CAM-02", "Rear Security Gate", "Entry Zone B", "LIVE", (239, 68, 68)),
        ("CAM-04", "High-Security Server Room", "Restricted S", "LIVE", (239, 68, 68)),
        ("CAM-PHONE", "Mobile Security Patrol", "Transit Zone C", "PHONE WI-FI", (16, 185, 129))
    ]

    cw, ch = 350, 215
    for idx, (cid, cname, czone, cstat, ccol) in enumerate(cams):
        col = idx % 2
        row = idx // 2
        cx = grid_x + col * (cw + 25)
        cy = 135 + row * (ch + 20)

        draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=12, fill=(15, 23, 42), outline=(51, 65, 85), width=1)
        # Inner feed
        draw.rounded_rectangle([cx + 10, cy + 10, cx + cw - 10, cy + ch - 65], radius=8, fill=(5, 8, 15), outline=(6, 182, 212), width=1)
        
        # Pill
        draw.rounded_rectangle([cx + 20, cy + 20, cx + 100, cy + 42], radius=11, fill=(ccol[0], ccol[1], ccol[2], 40), outline=ccol, width=1)
        draw.ellipse([cx + 28, cy + 28, cx + 34, cy + 34], fill=ccol)
        draw.text((cx + 38, cy + 25), cstat, fill=ccol, font=f["mono_badge"])

        draw.text((cx + 15, cy + ch - 50), cname, fill=(255, 255, 255), font=f["h3"])
        draw.text((cx + 15, cy + ch - 28), f"{cid} • {czone}", fill=(100, 116, 139), font=f["mono_sm"])

        draw.rounded_rectangle([cx + cw - 80, cy + ch - 48, cx + cw - 15, cy + ch - 22], radius=6, fill=(30, 41, 59))
        draw.text((cx + cw - 65, cy + ch - 42), "Identify", fill=(56, 189, 248), font=f["mono_badge"])

    img.save(path, "PNG")
    print(f"Created {path}")

def create_pipeline_architecture(path):
    W, H = 1100, 480
    img = Image.new("RGB", (W, H), color=(7, 10, 18))
    draw = ImageDraw.Draw(img)
    f = get_fonts()

    draw.rounded_rectangle([8, 8, W - 8, H - 8], radius=16, outline=(51, 65, 85), width=2)
    draw.text((360, 25), "Full-Stack Biometric Inference & Decision Pipeline", fill=(255, 255, 255), font=f["h2"])
    draw.text((345, 55), "SUB-500MS VERIFICATION LATENCY • DUAL-VECTOR ENCRYPTION AT REST", fill=(100, 116, 139), font=f["mono_b"])

    stages = [
        ("1. SENSOR INGESTION", (6, 182, 212), [
            "Multi-Modal Streams:",
            "• RFID Badge Scan (ID)",
            "• DirectShow USB Webcam",
            "• Wi-Fi Phone Camera",
            "• ONVIF / RTSP Network",
            "",
            "FAST BUFFER PIPELINE",
            "Non-blocking acquisition",
            "~25 FPS multipart MJPEG"
        ]),
        ("2. AI FEATURE EXTRACTION", (16, 185, 129), [
            "InsightFace ArcFace:",
            "• Buffalo_s ONNX Runtime",
            "• 512-dim Normalized Vector",
            "",
            "YOLOv8 Pose Keypoints:",
            "• 17 Skeletal Landmarks",
            "• Scale-Invariant Ratios",
            "",
            "YOLOv8 Person Radar:",
            "• Corridor Person Counting"
        ]),
        ("3. REDIS VECTOR VAULT", (168, 85, 247), [
            "Zero-Knowledge Cipher:",
            "• AES-256-GCM at rest",
            "• Single MGET Batching",
            "• In-Memory TTL Cache",
            "",
            "1:1 MATCH ENGINE:",
            "Cosine >= 0.50 Threshold",
            "Body Ratio >= 0.65 Tol",
            "1:N Biometric Search"
        ]),
        ("4. ENFORCEMENT & AUDIT", (244, 63, 94), [
            "Access Decisions:",
            "[ GRANTED ] Biometric Match",
            "[ DENIED ] Mismatch Alert",
            "[ TAILGATE ] Person Mismatch",
            "",
            "Audit & Operations:",
            "• Real-time Attendance",
            "• Cross-Cam Journey Log",
            "• Auto Hardware Tickets"
        ])
    ]

    box_w = 230
    box_h = 360
    start_x = 35
    box_y = 85
    gap = 40

    for i, (stitle, scol, lines) in enumerate(stages):
        bx = start_x + i * (box_w + gap)
        draw.rounded_rectangle([bx, box_y, bx + box_w, box_y + box_h], radius=12, fill=(15, 23, 42), outline=scol, width=2)
        draw.rounded_rectangle([bx + 10, box_y + 10, bx + box_w - 10, box_y + 38], radius=6, fill=(scol[0], scol[1], scol[2], 30))
        draw.text((bx + 20, box_y + 16), stitle, fill=scol, font=f["mono_b"])

        curr_y = box_y + 55
        for line in lines:
            if line.startswith("[ GRANTED ]"):
                draw.text((bx + 18, curr_y), line, fill=(16, 185, 129), font=f["mono_b"])
            elif line.startswith("[ DENIED ]") or line.startswith("[ TAILGATE ]"):
                draw.text((bx + 18, curr_y), line, fill=(244, 63, 94), font=f["mono_b"])
            elif line.endswith(":"):
                draw.text((bx + 18, curr_y), line, fill=(255, 255, 255), font=f["h3"])
            elif line == "":
                curr_y += 5
            else:
                draw.text((bx + 18, curr_y), line, fill=(148, 163, 184), font=f["mono_sm"])
            curr_y += 24

        # Arrow to next stage
        if i < 3:
            ax = bx + box_w + 10
            ay = box_y + box_h // 2
            draw.line([(ax, ay), (ax + 20, ay)], fill=(100, 116, 139), width=3)

    img.save(path, "PNG")
    print(f"Created {path}")

if __name__ == "__main__":
    os.makedirs("docs/assets", exist_ok=True)
    create_hero_banner("docs/assets/hero_banner.png")
    create_kiosk_preview("docs/assets/kiosk_preview.png")
    create_admin_preview("docs/assets/admin_preview.png")
    create_pipeline_architecture("docs/assets/pipeline_architecture.png")
    print("All PNG assets generated successfully!")
