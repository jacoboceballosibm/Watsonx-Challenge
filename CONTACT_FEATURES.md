# Contact Features - Seat Detail Page

## Overview

I've added comprehensive contact functionality to the seat detail page, including hover cards, contact buttons, and integration with the outreach email feature.

---

## ✨ Features

### 1. **Hover Cards** (Like ProM)

**How it works:**
- Hover over any contact's avatar to see their details
- Shows: Name, Title, Division, Location, Email
- Smooth fade-in animation
- Auto-dismisses when mouse leaves

**Implementation:**
```javascript
// Automatically attached to all contact avatars
.contact-hover-trigger
```

---

### 2. **Contact Buttons**

**Three types of contacts, each with tailored functionality:**

#### **A. Owner & Delegate (Generic Contact)**
- Button: "Contact"
- **On click:** Opens modal with 2 options:
  1. **📧 Send Email via Outlook** - Opens native Outlook with pre-filled subject/body
  2. **💬 Send Slack Message** - Opens Slack conversation (ready for Slack API integration)

#### **B. Project Contact (AI-Powered)**
- Button: "Contact" (Primary blue button)
- **On click:** Automatically drafts personalized email using AI
- **Integration:** Uses `/api/agents/outreach-draft` endpoint
- **Features:**
  - Fetches candidate profile
  - Generates personalized subject and body
  - Shows editable draft modal
  - User can modify before sending
  - Sends via `/api/agents/outreach-send`

---

## 🔄 User Flows

### Flow 1: Contact Owner/Delegate

```
User clicks "Contact" on Owner
    ↓
Modal opens with 2 options
    ↓
User chooses "Send Email via Outlook"
    ↓
Native Outlook opens with pre-filled:
    - To: owner.name@ibm.com
    - Subject: "Regarding Position on IBM ProM"
    - Body: Brief introduction template
```

**Alternative:**
```
User chooses "Send Slack Message"
    ↓
Slack conversation opens (native integration)
```

---

### Flow 2: Contact Project Contact (AI-Powered)

```
User clicks "Contact" on Project Contact
    ↓
Button shows "Drafting..." spinner
    ↓
API call to /api/agents/outreach-draft
    ↓
AI generates personalized email:
    - Subject: "Interest in [Position] – [Client]"
    - Body: Customized based on candidate's skills
    ↓
Draft modal opens with editable fields:
    - To: (pre-filled)
    - Subject: (pre-filled, editable)
    - Message: (pre-filled, editable)
    ↓
User reviews and optionally edits
    ↓
User clicks "Send Email"
    ↓
API call to /api/agents/outreach-send
    ↓
Success toast: "Email sent successfully! (Dry run mode)"
```

---

## 🎨 UI Components

### Hover Card
```
┌─────────────────────────────┐
│ Victoria Ghine              │
│ Managing Consultant         │
│ Consulting                  │
│                             │
│ Bethesda, MD               │
│ Victoria.Ghine@ibm.com     │
└─────────────────────────────┘
```

### Contact Options Modal (Owner/Delegate)
```
┌──────────────────────────────────┐
│ Contact Jordan Martinez      ✕   │
├──────────────────────────────────┤
│                                  │
│ ┌──────────────────────────────┐│
│ │ 📧 Send Email via Outlook    ││
│ └──────────────────────────────┘│
│                                  │
│ ┌──────────────────────────────┐│
│ │ 💬 Send Slack Message        ││
│ └──────────────────────────────┘│
│                                  │
└──────────────────────────────────┘
```

### Email Draft Modal (Project Contact)
```
┌────────────────────────────────────────────┐
│ Send Email to Alex Thompson            ✕   │
├────────────────────────────────────────────┤
│ To:                                        │
│ ┌────────────────────────────────────────┐│
│ │ alex.thompson@ibm.com                  ││
│ └────────────────────────────────────────┘│
│                                            │
│ Subject:                                   │
│ ┌────────────────────────────────────────┐│
│ │ Interest in Senior Cloud Architect... ││
│ └────────────────────────────────────────┘│
│                                            │
│ Message:                                   │
│ ┌────────────────────────────────────────┐│
│ │ Dear Hiring Manager,                   ││
│ │                                        ││
│ │ I am reaching out regarding...        ││
│ │                                        ││
│ │ My name is John Smith and I bring...  ││
│ │                                        ││
│ │ [Editable AI-generated content]       ││
│ └────────────────────────────────────────┘│
│                                            │
│              [Cancel]  [Send Email]        │
└────────────────────────────────────────────┘
```

---

## 🔌 API Integration

### Outreach Draft Endpoint
```javascript
POST /api/agents/outreach-draft

Request:
{
  "seat_id": "SEAT-12345",
  "candidate_professional_id": "PROF-001"
}

Response:
{
  "seat_id": "SEAT-12345",
  "candidate_professional_id": "PROF-001",
  "to_email": null,
  "to_display_name": "Project Contact Name",
  "subject": "Interest in Senior Cloud Architect – Global Finance Corp",
  "body": "Dear Hiring Manager,\n\nI am reaching out regarding..."
}
```

### Outreach Send Endpoint
```javascript
POST /api/agents/outreach-send

Request:
{
  "seat_id": "SEAT-12345",
  "candidate_professional_id": "PROF-001",
  "to_email": "contact@ibm.com",
  "subject": "Interest in Position",
  "body": "Email body content..."
}

Response:
{
  "status": "drafted",  // or "sent"
  "provider": "outlook",
  "message_id": "dry-run-abc123",
  "detail": "Dry run only. No email was sent."
}
```

---

## 🎯 Contact Button Behavior Summary

| Contact Type | Button Style | Click Action | Integration |
|-------------|-------------|--------------|-------------|
| **Owner Name** | Secondary (gray) | Opens modal → Outlook/Slack choice | Native mailto: / Slack URL |
| **Delegate Name** | Secondary (gray) | Opens modal → Outlook/Slack choice | Native mailto: / Slack URL |
| **Project Contact** | Primary (blue) | Drafts AI email → Shows editable modal | `/outreach-draft` + `/outreach-send` |
| **Opportunity Owner** | Secondary (gray) | Single button in sidebar | Native mailto: |

---

## 🛠️ Technical Implementation

### Contact Data Structure
```javascript
{
  ownerName: "Jordan Martinez",
  ownerEmail: "jordan.martinez@ibm.com",
  ownerDepartment: "Innovation Lab/IBM",
  
  delegateOwnerName: "Alex Thompson",
  delegateOwnerEmail: "alex.thompson@ibm.com",
  delegateOwnerDepartment: "Cloud Center/IBM",
  
  projectContactName: "Sam Rivera",
  projectContactEmail: "sam.rivera@ibm.com",
  projectContactDepartment: "Platform Team/IBM",
  
  opportunityOwnerName: "Taylor Chen",
  opportunityOwnerEmail: "taylor.chen@ibm.com"
}
```

### JavaScript Functions

**Hover Cards:**
```javascript
setupContactHoverCards()  // Auto-attaches to .contact-hover-trigger elements
```

**Contact Modals:**
```javascript
showContactOptions(name, email, role)  // Generic contact (Owner/Delegate)
draftProjectContactEmail(name, email, title, seatId)  // AI-powered (Project Contact)
```

**Email Handling:**
```javascript
openOutlookDraft(name, email)  // Native Outlook integration
openSlackMessage(name)  // Native Slack integration (ready for API)
showEmailDraftModal(...)  // Editable draft modal
sendDraftEmail(seatId, professionalId)  // Send via API
```

---

## 🎨 CSS Classes

```css
.contact-hover-card         // Hover tooltip styling
.contact-modal              // Modal container
.contact-modal-overlay      // Backdrop blur
.contact-modal-content      // Modal content box
.contact-hover-trigger      // Trigger element for hover
```

**Animations:**
- `fadeIn` - Hover card appearance
- `slideUp` - Modal entrance

---

## 🔄 Current Status

**✅ Implemented:**
- Hover cards on all contacts
- Contact buttons for all 4 contacts
- Owner/Delegate: Modal with Outlook/Slack options
- Project Contact: AI-powered email drafting
- Native Outlook integration (mailto:)
- Editable draft modal
- API integration with outreach endpoints
- Dry-run email sending

**🚧 Ready for Production Integration:**
- Slack API integration (placeholder ready)
- Real Outlook API (currently using mailto:)
- Email sending (currently dry-run mode)

---

## 🧪 Testing

**Test Hover Cards:**
1. Navigate to seat detail page
2. Hover over any contact avatar
3. See info card appear
4. Move mouse away - card disappears

**Test Owner Contact:**
1. Click "Contact" on Owner Name
2. Modal opens with 2 options
3. Click "Send Email via Outlook"
4. Outlook opens with pre-filled email

**Test Project Contact (AI Email):**
1. Click "Contact" on Project Contact
2. Button shows "Drafting..."
3. Draft modal opens with AI-generated content
4. Edit subject/body if desired
5. Click "Send Email"
6. Success toast appears
7. Check console for API response

---

## 📝 Environment Variables

```bash
# Backend: .env or environment
OUTLOOK_SEND_MODE=dry_run  # or "production" for real sending
```

---

## 🚀 Future Enhancements

1. **Slack Deep Links**
   - Integrate Slack API for direct DMs
   - Pre-fill message content

2. **Outlook Calendar Integration**
   - Schedule interview/meeting directly

3. **Message Templates**
   - Save frequently used messages
   - Template library

4. **Contact History**
   - Track when you last contacted someone
   - See previous message threads

5. **Rich Text Editor**
   - Format emails with bold/italic
   - Add attachments (CV, portfolio)

---

## Summary

The contact feature provides a ProM-like experience with modern enhancements:
- **Hover to preview** contact details
- **One-click contact** with smart routing
- **AI-powered drafting** for project contacts
- **Native integrations** for Outlook and Slack
- **Editable drafts** for personalization

All contacts are now easily reachable with contextual, intelligent communication options! 🎉
