# JARVIS --- Claude Code Project Context

## Mission

JARVIS is evolving from the existing Python desktop assistant into a
**personal AI control plane**: one simple interface through which a
normal user can ask for goals and JARVIS coordinates AI helpers,
computers, phone, Google Workspace, files, and the web behind the
scenes.

Core promise:

> The user thinks in goals. JARVIS handles agents, devices, tools,
> permissions, services, azznd execution.

JARVIS is not merely a chatbot, voice assistant, coding agent, or
OpenClaw frontend. OpenClaw is an optional integration/worker. JARVIS
must remain useful without OpenClaw.

------------------------------------------------------------------------

## 1. Current Repository --- Inspect Before Changing

Repository: `https://github.com/sohail-bhai/jarvis`

The current main branch was inspected on 2026-09-04. It is a small
Python desktop project currently described as **JARVIS Desktop
Assistant - Version 1.2**. The GitHub tree currently includes:

``` text
assistant/
data/
gui/
tests/
AGENTS.md
README.md
config.json
context.md
jarvis_gui.py
main.py
plan.md
requirements.txt
test_scaffold.py
```

The existing README says the current GUI is a CustomTkinter dashboard.
Existing user-facing functionality includes voice input/output, opening
apps and websites, Google/YouTube search, time/date/battery,
screenshots, Windows volume control, notes, shutdown/restart
confirmation, and config-driven personalization.

The existing `AGENTS.md`, `context.md`, and `plan.md` describe
additional work already present in the repository, including Ollama
local LLM integration, tool calling, short-term conversation memory,
OCR/screen awareness, PyAutoGUI actions, a multi-step agent loop,
persistent memory, event bus/audit/guard/confirmation/overwatch
infrastructure, dynamic configuration, and phone/remote-execution
roadmap work.

**Do not assume the README is the whole implementation. Inspect the
actual source.**

Important existing modules include:

``` text
main.py
jarvis_gui.py
assistant/controller.py
assistant/state.py
assistant/events.py
assistant/text_utils.py
assistant/commands.py
assistant/speech.py
assistant/system_tasks.py
assistant/config.py
assistant/notes.py
assistant/ai_brain.py
assistant/smoke_test.py
assistant/memory.py
assistant/audit.py
assistant/guard.py
assistant/confirm.py
assistant/overwatch.py
assistant/logging_setup.py
assistant/vision.py
gui/app.py
gui/theme.py
gui/widgets/*
```

The current runtime roughly follows:

``` text
main.py
  -> AssistantController
  -> listen/text input
  -> normalize command
  -> command router / AI brain
  -> tools/system actions
  -> result + speech + events
  -> GUI
```

The GUI/event architecture must remain thread-safe. CustomTkinter
updates belong on the main thread; worker threads should communicate
through the existing event mechanism.

------------------------------------------------------------------------

## 2. Existing Project Direction

The old project vision was a local, self-learning, screen-aware
assistant. The current repository has already progressed beyond the
original rigid `if/else` command-router design.

Existing work described in the repository includes:

### Local AI

-   Ollama/local LLM
-   unrecognized commands falling back to AI
-   tool calling
-   short-term conversational context

### Computer control

-   screenshots
-   OCR/text detection
-   PyAutoGUI interaction
-   typing/keyboard actions
-   screen-aware interaction
-   multi-step tool loop

### Memory

-   persistent local memory
-   remembered facts
-   memory injection into AI context
-   roadmap toward scalable/RAG memory

### Voice

-   speech recognition
-   TTS
-   online TTS + local fallback work
-   wake-word roadmap

### Safety/observability

-   confirmation
-   audit
-   guard
-   overwatch
-   event bus

Preserve these capabilities. Extend them instead of rebuilding duplicate
versions.

------------------------------------------------------------------------

# 3. Target Product

JARVIS should become a **framework-agnostic personal AI control plane**.

Conceptually:

``` text
                         USER
                           |
                 Desktop / Phone / CLI
                           |
                           v
                    +-------------+
                    |   JARVIS    |
                    | Control Core |
                    +------+------+
                           |
        +------------------+------------------+
        |                  |                  |
        v                  v                  v
     AI HELPERS         DEVICES           SERVICES
        |                  |                  |
   Native helper       Desktop             Google
   OpenClaw            Laptop              Gmail
   LangGraph           Phone               Drive
   CrewAI              Server              Calendar
   MCP                 NAS                 Docs
   Custom              Cloud               Sheets
                                             Slides
                                              Web
```

The fundamental workflow is:

``` text
User goal
  -> JARVIS understands intent
  -> determine required capabilities
  -> choose/coordinate helper(s) and device(s)
  -> obtain required access
  -> execute
  -> show understandable progress
  -> request approval for high-impact actions
  -> complete
  -> explain what happened
```

------------------------------------------------------------------------

# 4. Complete Feature Set

## A. AI Helper Management

### 4.1 Helper Registry

JARVIS maintains a registry of connected AI helpers with: - name -
implementation/framework - device - status - capabilities - current
task - permissions - last activity

User-facing language should say **AI helper**, not runtime/RPC/etc.

### 4.2 Capability Discovery

Helpers advertise what they can do, e.g.:

``` text
Coding helper: files, Git, terminal, tests
Research helper: web research, document reading, summarization
ML helper: Python, GPU, model training
```

A user says "train this model" rather than selecting a server/agent.
JARVIS finds the appropriate capability.

### 4.3 Framework-Agnostic Network

Support a common JARVIS abstraction over: - native JARVIS helpers -
OpenClaw - LangGraph - CrewAI - MCP-based tools/agents - custom Python
agents - custom TypeScript agents

OpenClaw is an adapter, not the core.

### 4.4 Multi-Helper Orchestration

Accept high-level goals and break them into dependent steps.

Example:

``` text
Prepare my project
  -> research
  -> code analysis
  -> model work
  -> presentation
```

### 4.5 Helper Handoff

A helper can request another capability through JARVIS.

``` text
Coding helper
  -> needs GPU
  -> JARVIS finds ML helper
  -> ML helper works
  -> result returns
  -> coding helper continues
```

### 4.6 Task Checkpoints and Recovery

Persist task state/checkpoints so work can continue after interruption
or helper/device failure when possible.

------------------------------------------------------------------------

## B. Devices

### 4.7 Cross-Device Execution

Connect: - desktop - laptop - phone - server - NAS - cloud machines

The user should say "run this on my GPU server" and JARVIS resolves the
actual machine/worker.

### 4.8 Cross-Device Files

Search/access files across connected devices. The user thinks in terms
of "my presentation", not filesystem paths.

Example:

``` text
Find my Hackwave presentation
  -> JARVIS searches computer/phone/server/connected storage
  -> returns likely result
  -> user can open/send/share/use with JARVIS
```

SSH may be an implementation mechanism, but SSH is not the product
abstraction.

------------------------------------------------------------------------

## C. Security and Control

### 4.9 Temporary Task-Scoped Access

Access should be scoped by: - resource - action - task - device -
expiration

Example:

``` text
Hackwave project
Read + write
Expires in 30 minutes
```

### 4.10 Human Approval

Require explicit approval for high-impact actions such as: - merge
code - deploy - send email - submit a web form - delete important data -
share sensitive information - other consequential external actions

Approval UI must explain what will happen, why, and what changes.

### 4.11 Unified Activity Timeline

Record important observable actions: - task created - helper selected -
file accessed - Google service used - permission granted/revoked -
approval requested/granted/denied - web action performed - task
completed/failed

### 4.12 Security Center

Central view for: - security status - temporary access - pending
approvals - connected devices - blocked actions

### 4.13 Emergency Stop

One clear action that attempts to: - stop active work safely - cancel
tasks - revoke temporary permissions - invalidate temporary grants -
block new remote actions

Do not delete user data.

### 4.14 Quarantine

Isolate a problematic helper while keeping diagnostics/status visible.

------------------------------------------------------------------------

## D. Google Workspace Environment

Google is a first-class environment, not just a single integration.

Target services: - Google Drive - Gmail - Google Calendar - Google
Docs - Google Sheets - Google Slides

Use OAuth 2.0 and request the narrowest practical scopes. Respect the
user's actual permissions.

### 4.15 Google Connection

Provide a clear connect/disconnect flow and explain requested access in
plain language.

### 4.16 Google Drive

Support where practical: - search files/folders - metadata -
open/download - upload/create/update - summarize - pass relevant files
to helpers - My Drive - Shared Drives

Use actual Drive permission/capability information when deciding which
actions are available.

### 4.17 Gmail

Support where practical: - search - read - summarize - identify
important/unanswered mail - draft replies - send only with appropriate
confirmation/approval

### 4.18 Calendar

Support: - upcoming events - search - availability/free-busy -
create/update events - scheduling assistance

Do not create an event when key details are ambiguous.

### 4.19 Docs/Sheets/Slides

Support creation/manipulation workflows through JARVIS. Do not recreate
Google editors.

Examples:

``` text
Put these results into a spreadsheet.
Turn this research into a presentation.
Create a document summarizing this project.
```

### 4.20 Workspace as an Agent Environment

Allow workflows such as:

``` text
Research helper
 -> read Drive documents
 -> synthesize
 -> create Google Doc
 -> create Slides
```

JARVIS remains the coordinator and access-control layer.

------------------------------------------------------------------------

## E. Internet and Web

### 4.21 Internet Access

Provide a web layer for: - search - page reading - research -
comparison - documentation lookup - public file retrieval where
appropriate - source gathering - summarization

### 4.22 Browser Task Automation

Support multi-step browser workflows where technically and legally
appropriate:

``` text
Open site
 -> navigate
 -> read information
 -> fill fields
 -> upload file
 -> review
 -> ask approval if needed
 -> submit
```

Sensitive final actions must not silently execute.

------------------------------------------------------------------------

## F. Intelligence

### 4.23 Shared JARVIS Memory

Shared memory can contain: - projects - preferences - decisions -
workflows - recent tasks - approved facts - relevant context

Only relevant context should be passed to a helper.

### 4.24 Semantic Cross-Environment Search

Eventually search across: - local devices - Google Drive - Gmail -
Docs/Sheets - other connected sources - web

The user's query should be semantic, e.g. "find everything related to my
blockchain project".

### 4.25 Context/Privacy Firewall

Before data reaches a helper, minimize it to what is actually needed.

``` text
User data
 -> JARVIS
 -> relevant subset
 -> helper
```

### 4.26 Secret Broker

Do not expose raw credentials unnecessarily. Prefer operation-level
access through JARVIS/secret storage.

------------------------------------------------------------------------

## G. Automation

### 4.27 Event-Driven Automation

React to events such as: - CI failure - important email - device
becoming available - task completion - external service event

Example:

``` text
CI fails
 -> JARVIS
 -> coding helper investigates
```

### 4.28 Failure Recovery

If a helper becomes unavailable:

``` text
helper unavailable
 -> restore checkpoint
 -> find capable helper
 -> continue
```

Never claim recovery succeeded if it did not.

------------------------------------------------------------------------

# 5. Desktop UI Product Requirements

The desktop UI is for normal users, not infrastructure engineers.

Primary sidebar:

``` text
JARVIS

Home
My Devices
My Files
Google
Web
Activity
Settings

----------------
● JARVIS Online
```

Do not expose these as primary navigation: - agent registry -
capabilities - orchestrator - protocols - runtime - MCP -
permissions/token internals - Gmail as a separate primary page - Drive
as a separate primary page

Those concepts should be contextual or hidden under advanced settings.

------------------------------------------------------------------------

## 5.1 Home

Primary command box:

``` text
How can I help you today?
Tell me what you want to do...
```

Suggested actions: - Find my files - Continue my project - Research
something - Check my emails - Open Google Drive

Environment cards:

``` text
My Computer — Online
My Phone — Connected
Google — Connected
Internet — Ready
```

Current task:

``` text
Preparing your project
✓ Finding relevant files
● Researching on the web
○ Preparing the document
○ Finishing
```

Quick access cards: - My Files - Google - Web

Include a subtle explanation that users can simply ask JARVIS in normal
language.

------------------------------------------------------------------------

## 5.2 System Log --- Signature Component

Show a live right-side panel called **System Log**.

It must explain observable background activity in simple English.

Good:

``` text
3:24 PM
Looking through your files for "Hackwave presentation"

3:24 PM
Found 3 matching documents

3:25 PM
Checking your Google Drive too

3:26 PM
Researching the latest information online

3:28 PM
Preparing your presentation
```

Never expose: - chain-of-thought - hidden reasoning - API keys - access
tokens - passwords - raw authorization headers - low-level RPC/MCP noise

The System Log is an action/status log, not a model-reasoning window.

------------------------------------------------------------------------

## 5.3 My Devices

Show simple cards for connected machines. Technical metrics may exist
under an expandable Details section, but should not dominate the UI.

Device drawer should show: - online state - what JARVIS can do on the
device - connected helpers - recent activity - disconnect action

------------------------------------------------------------------------

## 5.4 My Files

Universal search across local devices and connected Google storage.

Result example:

``` text
Hackwave_Final.pptx
Computer / Projects / Hackwave
Modified yesterday

[Open] [Send to Phone]
```

File drawer can show source, path, date, size, and simple actions.

------------------------------------------------------------------------

## 5.5 Google

One primary Google page with tabs:

``` text
Overview | Drive | Gmail | Calendar | Docs
```

Keep each view lightweight; do not rebuild Google's products.

------------------------------------------------------------------------

## 5.6 Web

Simple input:

``` text
What should I find or do online?
```

Show recent web tasks and readable progress.

Browser progress example:

``` text
✓ Opened website
✓ Found the relevant page
● Comparing information
○ Preparing answer
```

If a form is ready to submit:

``` text
✓ Filled the form
⚠ Ready to submit

[Review]
```

------------------------------------------------------------------------

## 5.7 Activity

Readable timeline:

``` text
12:42
Finished checking your project

12:39
Opened your Hackwave presentation

12:35
You approved an action

12:31
Started researching your topic
```

Filters: - All - Files - Google - Web - Tasks

Clicking an item opens a detail drawer.

------------------------------------------------------------------------

## 5.8 Tasks

Use the simple label **Tasks**.

Show: - current tasks - progress - completed tasks - waiting/approval
state

Task detail should describe the work in human language rather than
showing raw orchestration.

------------------------------------------------------------------------

## 5.9 Approvals

Approval cards should answer: - What is JARVIS about to do? - Why? -
What changes? - What happens if I approve?

Example:

``` text
JARVIS needs your approval

I'm ready to merge your project changes.
14 files were changed.
All tests passed.

[Not now] [Approve]
```

------------------------------------------------------------------------

## 5.10 Security

Use simple language:

``` text
Your Security

● You're protected

Connected devices  4
Actions waiting    1
Temporary access   3
```

Include permission management, approvals, and emergency stop.

------------------------------------------------------------------------

## 5.11 Memory

Keep lightweight. Prefer an optional Settings/advanced area or a simple
"What JARVIS remembers" view.

------------------------------------------------------------------------

## 5.12 Integrations

Put under Settings.

Show:

``` text
Google        Connected
GitHub        Connected
OpenClaw      Connected
Other AI      Connected
```

------------------------------------------------------------------------

## 5.13 Settings

Keep simple: - General - Notifications - Appearance - Connected
Services - Privacy - Security - Advanced / Developer options

------------------------------------------------------------------------

# 6. Global UX Components

Build reusable components for:

``` text
Sidebar
TopBar
CommandPalette
DetailDrawer
NotificationCenter
StatusIndicator
Card
Modal
Toast
ConfirmationDialog
EmptyState
LoadingState
ProgressIndicator
ActivityTimeline
```

The **DetailDrawer** should be reused for devices, files, tasks,
approvals, activities, Google items, web tasks, and helper details.

The global command palette should support Ctrl+K and natural-language
input.

------------------------------------------------------------------------

# 7. Human-Language Rules

Prefer:

``` text
AI helper
What it can do
Temporary access
Working
JARVIS is handling this
JARVIS asked another AI to help
Couldn't finish this step
```

Avoid in the normal UI:

``` text
Agent runtime
Capability ID
Permission token
Task orchestration
RPC
MCP
Execution context
```

Advanced users may see technical details in a developer/advanced view.

------------------------------------------------------------------------

# 8. Visual Design

The UI must be: - minimal - calm - premium - aesthetic - easy for
non-technical users - light and clean

Use: - neutral background - white/near-white surfaces - charcoal text -
muted gray secondary text - restrained blue/indigo accent - muted green
for success - muted amber for attention - muted red only for destructive
actions - subtle borders - soft shadows - 10--16px radius - modern
sans-serif font - simple icons

Avoid: - neon - cyberpunk - excessive gradients - excessive
glassmorphism - glowing HUDs - giant statistics - dense tables - complex
analytics - sci-fi dashboard aesthetics

The product should feel like a premium productivity application, not a
developer console.

------------------------------------------------------------------------

# 9. Technical Direction

A practical future boundary is:

``` text
Existing Python JARVIS Core
        |
        v
JARVIS service/API boundary
        |
        v
Modern desktop frontend
```

Possible stack:

``` text
Frontend: React + TypeScript + Next.js or Vite + Tailwind + Lucide
Backend: Python + FastAPI + WebSockets
Hackathon storage: SQLite
Production storage: PostgreSQL
Realtime: WebSockets initially
AI: existing Ollama/local AI + optional model adapters
Execution: existing Python tools; sandbox later
```

Do not introduce Kubernetes, Kafka, Redis, or microservices merely for
architectural appearance.

For an 8-hour hackathon, one backend/service and SQLite are preferable.

------------------------------------------------------------------------

# 10. Internal Data Model Direction

The system can evolve around:

``` text
User
Device
Agent/Helper
Capability
Task
TaskStep
Permission
Approval
ActivityEvent
File
GoogleConnection
WebTask
Memory
Integration
```

Example conceptual models:

``` text
Agent:
  id
  name
  framework
  device_id
  status
  capabilities[]
```

``` text
Task:
  id
  user_goal
  status
  current_step
  assigned_agent
  progress
  checkpoint
  created_at
  updated_at
```

``` text
Permission:
  id
  task_id
  resource
  actions[]
  device_id
  expires_at
  status
```

``` text
ActivityEvent:
  id
  task_id
  type
  message
  timestamp
  actor
  device
  metadata
```

Keep these conceptual boundaries clean even if the hackathon
implementation uses simple storage.

------------------------------------------------------------------------

# 11. Agent Protocol Direction

Long-term protocol concepts:

``` text
REGISTER
HEARTBEAT
CAPABILITIES
EXECUTE
STATUS
CANCEL
PAUSE
RESUME
SHUTDOWN
```

REST/WebSockets are sufficient for the prototype. gRPC/protobuf can be
considered later.

JARVIS owns task state and coordination; external frameworks do not own
the whole system.

------------------------------------------------------------------------

# 12. OpenClaw Position

OpenClaw is an optional worker/integration.

Current OpenClaw itself already supports gateway/node concepts and
file-transfer functionality. Therefore do not position simple SSH/file
transfer as the unique innovation.

The JARVIS differentiator is the higher-level control plane:

``` text
User goal
 -> JARVIS
 -> choose worker/device
 -> control access
 -> coordinate work
 -> observe
 -> recover
 -> explain
```

The system must still work if OpenClaw is not installed.

------------------------------------------------------------------------

# 13. Google API Principles

Use current official Google Workspace APIs and OAuth 2.0.

Request the narrowest practical scopes. Clearly communicate requested
access. Respect actual user permissions and service capabilities.

Drive should account for My Drive and Shared Drives where practical. Use
Drive capability/permission information before exposing destructive or
modifying actions.

Do not put Google access tokens/secrets into model prompts or normal
activity logs.

For a hackathon, prioritize:

``` text
Google OAuth
Drive search
Gmail search/read
Calendar read
One useful write action with approval
```

Then expand.

------------------------------------------------------------------------

# 14. Security Rules

Never provide every worker unrestricted host access.

Use the principles:

``` text
Least privilege
Task-scoped access
Time-limited access
Human approval
Auditability
Revocation
Isolation
```

Never log credentials or tokens.

Never display private credentials in the UI.

------------------------------------------------------------------------

# 15. System Log Rules

The System Log is for **observable progress**, not chain-of-thought.

Good:

``` text
Searching your Google Drive
Found 4 matching files
Waiting for your approval
```

Bad:

``` text
I am internally considering whether...
Bearer eyJ...
API_KEY=...
```

------------------------------------------------------------------------

# 16. Failure and Demo Mode

Never fake successful external actions.

If an integration is unavailable, explicitly label demo/mock data:

``` text
Demo mode
Google isn't connected yet.
Showing an example result.
```

Do not display "Successfully searched Google Drive" unless the call
actually happened.

------------------------------------------------------------------------

# 17. 8-Hour Hackathon Scope

The full vision is intentionally larger than the hackathon
implementation.

Prioritize this vertical slice:

1.  Modern/simple desktop UI
2.  Natural-language command box
3.  Helper/device registry abstraction
4.  Task creation and progress
5.  System Log/activity timeline
6.  Permission + approval flow
7.  Google connection + one useful operation
8.  Web search/task abstraction
9.  Cross-device file/task demonstration

Do not spend the 8 hours building: - Kubernetes - Kafka - complex
distributed infrastructure - many microservices - a full Google
replacement - a custom browser - dozens of helpers - elaborate 3D HUDs -
cost tracking - trust scoring - unnecessary abstractions

Mock UI states are acceptable where a real integration cannot be
finished, but mock states must be clearly distinguishable in
development/demo mode.

------------------------------------------------------------------------

# 18. Ideal Demo

The UI should make this understandable in under three minutes.

User enters:

``` text
Continue my Hackwave project.
```

JARVIS shows:

``` text
I'm working on it.

✓ Found your project
✓ Found the latest files
● Checking related information online
○ Preparing changes
```

System Log:

``` text
Found your project on your computer
Found related files
Checked Google Drive
Researching online
Preparing the next step
```

Then:

``` text
JARVIS needs your approval

I'm ready to make the final changes.

[Not now] [Approve]
```

After approval:

``` text
✓ Done
Your project has been updated.
```

Activity shows the full sequence.

The demo should communicate:

``` text
Natural language
  -> JARVIS
  -> multiple environments
  -> coordination
  -> security
  -> transparency
  -> result
```

------------------------------------------------------------------------

# 19. Claude Code Operating Instructions

## Investigate first

Before changing code, inspect the relevant repository files. Do not
speculate about code that has not been opened.

At the beginning of a major task, read:

``` text
AGENTS.md
README.md
context.md
plan.md
```

Then inspect the actual source files relevant to the task.

## Preserve working functionality

Do not remove or replace existing voice, local AI, tool calling, memory,
screen awareness, system commands, safety infrastructure, or tests
unless explicitly required.

## Avoid overengineering

The user has an extremely short hackathon deadline. Prefer the smallest
working implementation.

Do not add: - unnecessary abstractions - speculative infrastructure -
large refactors unrelated to the current task - microservices for
appearance - complex dependency chains

## Keep the app runnable

Make incremental changes. Prefer changes that can be verified
independently.

## Verification

Safe verification commands include:

``` bash
python -m compileall -q main.py assistant gui jarvis_gui.py
python main.py --smoke-test
```

Run targeted tests as appropriate.

Do not automatically run:

``` bash
python main.py
```

because normal mode starts continuous microphone listening.

## No fake success

If a service is not connected, surface that state rather than pretending
it succeeded.

## No chain-of-thought exposure

Never implement UI that displays hidden model reasoning. Use concise
action/status updates instead.

------------------------------------------------------------------------

# 20. Source-of-Truth Order

When information conflicts, use:

1.  Actual source code
2.  `AGENTS.md`
3.  Tests
4.  `README.md`
5.  `context.md`
6.  `plan.md`
7.  This document's target architecture

This document describes the desired product direction. It does not
override existing working code without an explicit implementation
decision.

------------------------------------------------------------------------

# 21. Current Product Definition

The simplest accurate explanation is:

> **JARVIS is a personal AI control plane that connects your AI helpers,
> computers, phone, Google Workspace, files, and the internet. You give
> it goals in plain English; JARVIS coordinates the work behind the
> scenes and keeps you in control of important actions.**

The technical complexity belongs behind the interface.

The user should experience:

``` text
What do you want?
        ↓
JARVIS is working.
        ↓
Here's what I'm doing.
        ↓
I need your approval.
        ↓
Done.
```
