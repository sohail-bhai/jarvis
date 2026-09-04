# Doing work on the internet

JARVIS drives a real browser, calls any service that has an API, and remembers
what it learned about a site for next time. GitLab has a module of its own
because a code fix deserves exact operations, but nothing else does - and
nothing else needs one.

JARVIS drives a real browser and talks to GitLab's API. This is what makes
"go and look at the issues on that repo" or "ask ChatGPT where to eat" real
work rather than a canned answer.

## Three ways to work, in order of preference

| The service has… | Use | Why |
| --- | --- | --- |
| A REST API | `web_api_get` / `web_api_call` | Exact, and it either worked or it did not |
| Only a website | `browse` and the browser tools | The same thing a person would do |
| A code fix to land | the GitLab tools | A real commit on a real branch |

A new service usually needs **no new code**. Store a credential, and the API
tools reach it:

```bash
curl -X PUT localhost:8765/api/secrets/github_token \
     -H 'Content-Type: application/json' -d '{"value": "ghp_..."}'
```

```python
web_api_get("https://api.github.com/repos/you/app/issues",
            params={"state": "open"}, auth_secret="github_token")

web_api_call("POST", "https://api.github.com/repos/you/app/issues/12/comments",
             body={"body": "Looking at this now."}, auth_secret="github_token")
```

The model names the credential; it never sees the value. `auth_style` covers
how each service expects it: `bearer` (GitHub, most), `private-token`
(GitLab), `token`, `x-api-key`, `basic`. Reading is medium risk and runs;
changing something is high risk and asks you first.

That one pair of tools covers Jira, Linear, Notion, Slack, Home Assistant, a
home server, your own backend - anything with HTTP and a token.

## The browser

One Chromium window, kept between tasks, with a persistent profile in
`data/browser_profile/`. A site you log into once stays logged in, so JARVIS
never handles your password for GitLab, ChatGPT or anything else.

```python
from assistant import browser

browser.browse("https://gitlab.com/group/repo/-/issues")
browser.browser_click("Login button does nothing")
browser.browser_type(3, "looks like a Safari-only bug", submit=True)
```

### How the model uses it

Every action answers with the page as it now is, plus a numbered list of what
can be clicked or typed into:

```
Page: Issues · group/repo (https://gitlab.com/group/repo/-/issues)
Open  Closed  All  ...

Things you can click or type into:
[1] link: New issue
[2] textbox: Search or filter results
[3] link: Login button does nothing
```

So the model clicks `3`, or clicks `"Login button does nothing"` - never a CSS
selector it guessed. When a click misses, the failure hands the list back:

```
Nothing on this page looks like 'Sign in'.

Things you can click or type into:
[1] link: New issue
...
```

That is the whole loop: look, act, look at what actually changed, decide again.

### Asking a site a question

`browser_ask_site` does the round trip in one call - open, find the box a
person would type into, send, wait for the answer to finish arriving, and
bring back what appeared:

```python
browser.browser_ask_site("https://chatgpt.com", "best places for food nearby?")
```

It waits for the page to have real content and then to hold still, because a
chat writes its answer a word at a time and a search engine fills results in
after the page itself has loaded.

| Tool | What it does |
| --- | --- |
| `browse(url)` | Open a page and read it |
| `browser_read(full)` | Read the current page again |
| `browser_elements()` | Numbered list of what can be clicked or typed into |
| `browser_click(target)` | Click by number or by visible text |
| `browser_type(target, text, submit)` | Type, optionally pressing Enter |
| `browser_press(key)` | One key |
| `browser_wait_for(text, seconds)` | Wait for text to appear |
| `browser_screenshot()` | Save a picture when text is not enough |
| `browser_ask_site(url, prompt)` | Ask a question on a site and return the answer |
| `browser_fill_form(fields)` | Fill several boxes at once |
| `browser_tabs()` / `browser_new_tab(url)` / `browser_switch_tab(n)` | Work in more than one place |
| `browser_wait_for_login(seconds)` | Hand the window over so the user signs in |
| `remember_about_site(url, note)` | Write down what you worked out |

### Signing in

JARVIS never types a password and never reads one. When a page asks for a
sign-in, `browse` says so and the model calls `browser_wait_for_login`, which
waits for the page to stop asking - which is what a person signing in
themselves looks like from here. The profile remembers it afterwards, so it
happens once per site.

### Learning a site

Whatever the model works out - where a page lives, which element is the search
box, that a site is slow - it can write down with `remember_about_site`. Those
notes are keyed by domain in `data/site_notes.json` and handed back
automatically the next time that domain is opened:

```
What you learned about news.ycombinator.com before:
- front page stories are the numbered links; comments are 'N comments'

Page: New Links | Hacker News (https://news.ycombinator.com/newest)
...
```

Eight notes per site, trimmed to keep them promptable. No model and no network
needed to read or write them.

### Headless or watched

`browser_headless` in `config.json` defaults to `false`, so you see the window
and can take over. Headless is faster, but some sites - DuckDuckGo among them -
serve an empty page to a headless browser. If results come back suspiciously
bare, that is why.

## GitLab

The browser is how JARVIS reads a page. GitLab has a real API, so a fix lands
as a real commit on a real branch rather than as clicks that might have gone
wrong.

```bash
# Store the token once. It is encrypted, and the model never sees it.
curl -X PUT localhost:8765/api/secrets/gitlab_token \
     -H 'Content-Type: application/json' \
     -d '{"value": "glpat-...", "description": "GitLab API token"}'
```

Self-hosted GitLab: set `gitlab_url` in `config.json`.

### The order that works

```
gitlab_list_issues("group/repo")          → #7 Login button does nothing
gitlab_read_issue("group/repo", 7)        → the description and the comments
gitlab_find_file("group/repo", "login")   → app/login.py
gitlab_read_file("group/repo", "app/login.py")
gitlab_propose_fix("group/repo", 7, "app/login.py", <whole new file>, summary)
                                          → merge request !12, not merged
gitlab_merge("group/repo", 12)            → only when you ask
```

`gitlab_propose_fix` takes the **complete new contents** of the file, not a
patch - small models produce unusable diffs, and a whole file either applies or
obviously does not. It creates `jarvis/issue-<n>`, commits, and opens a merge
request that says `Closes #7`. It never merges.

### Why proposing and merging are separate

| Tool | Capability | Risk | What happens |
| --- | --- | --- | --- |
| `gitlab_read_issue` | `gitlab.read` | medium | runs |
| `gitlab_propose_fix` | `gitlab.write` | high | asks you first |
| `gitlab_merge` | `gitlab.merge` | critical | asks you first |

Merging changes a real repository other people depend on, so it is a critical
capability: the task stops, your phone asks, and approving is what grants the
access. Reading a page is low risk and just runs; clicking and typing as you
(`browser.interact`) is high, because on the web those are the same thing.

## How many steps a task gets

A web flow is many small tool calls - open, look, click, look again - so a
control plane step runs the loop up to `agent_max_steps` times (15 by default,
set it in `config.json`). Repeated identical calls break out early, and the
cancel token is checked before every one, so a long flow can still be stopped
mid-way.

## What this does not do yet

- **No local checkout.** Fixes are written against the file as read from
  GitLab. Nothing is cloned, so tests are not run against the change before
  the merge request is opened.
- **One file per fix.** `gitlab_propose_fix` commits a single file. A change
  spanning several files needs several calls, or a task per file.
- **GitHub has no dedicated module,** but `web_api_get` and `web_api_call`
  reach its API today, which covers issues, comments, pull requests and
  reviews. Only GitLab has purpose-built tools, for the propose-a-fix flow.
- **Login is manual, on purpose.** The first time a site needs a password, log
  in yourself in the window JARVIS opened. The profile remembers it after that.
- **Site notes are written by the model,** so they are as good as the model
  that wrote them. They are plain text in `data/site_notes.json`, and easy to
  correct or delete by hand.
- **No captcha handling.** A site that challenges automation needs you to take
  over in the window.
- **A small model will struggle with real code.** `qwen2.5:3b` reads issues and
  navigates well; for an actual code fix, switch to a larger local model first.
