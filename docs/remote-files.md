# Your files, from anywhere

The phone is not just a remote control for VAVE. It is also a way into the
files on the computer: browse them, pull one down, push one up, from a train
or another country.

## What is reachable

Nothing, until you say so. `file_shares` in `config.json` is the whole of the
answer:

```json
"file_shares": ["~/Documents", "~/Pictures", "/mnt/projects"],
"files_allow_write": true,
"files_allow_delete": false
```

Every path that arrives from outside is **resolved first and checked second**,
so a request for `../../.ssh`, an absolute `/etc/passwd`, or a symlink inside a
share pointing at your home directory all fail the same way: outside the
folders you shared. Dot-files are not listed, and a short list of names -
`.ssh`, `.aws`, `.env`, `secret.key`, `control.db` - is never served whatever
it is called from.

Deleting is off by default. Writing is on, and every upload and download is
written to the timeline with the device that asked:

```
Received phone_photo.txt from Rav phone.
Sent q3.txt to Rav phone.
```

## The endpoints

| Method | Path | Does |
| --- | --- | --- |
| `GET` | `/api/files/shares` | The folders that are reachable at all |
| `GET` | `/api/files?path=` | List a folder, folders first |
| `GET` | `/api/files/search?query=` | Find a file by name, anywhere in the shares |
| `GET` | `/api/files/download?path=` | Stream a file to the phone |
| `POST` | `/api/files/upload` | Multipart: `file`, `folder`, `overwrite` |
| `POST` | `/api/files/folder` | Make a folder |
| `POST` | `/api/files/move` | Rename or move, both ends inside the shares |
| `DELETE` | `/api/files?path=` | Delete a file or an empty folder |

Every one needs the paired device token, exactly like the rest of the API.
Downloads are streamed and support range requests, so a large file resumes
rather than starting again.

```bash
TOKEN=...   # from pairing

curl -H "Authorization: Bearer $TOKEN" localhost:8765/api/files
curl -H "Authorization: Bearer $TOKEN" \
     "localhost:8765/api/files/download?path=reports/q3.txt" -o q3.txt
curl -H "Authorization: Bearer $TOKEN" \
     -F "file=@photo.jpg" -F "folder=Pictures" localhost:8765/api/files/upload
```

An upload never silently replaces something: a name that already exists gets a
timestamp added, unless `overwrite=true` says otherwise.

## VAVE can reach them too

The same access is a set of tools, so the assistant can answer "where did I put
the Q3 report?" without you opening anything:

| Tool | Capability |
| --- | --- |
| `shared_folders()` | `filesystem.read` |
| `list_shared_files(path)` | `filesystem.read` |
| `find_shared_file(query)` | `filesystem.read` |

## Reaching the computer from a train

The API binds to `127.0.0.1` by default, which no phone on mobile data can
reach. Three ways out, in the order they are worth trying:

**A private network (recommended).** Tailscale or WireGuard puts the phone and
the computer on the same private network wherever they are. Run
`python -m assistant.api --host 0.0.0.0` and use the machine's address on that
network. Nothing is exposed to the public internet, and the device token still
applies.

**A tunnel.** `cloudflared tunnel --url http://localhost:8765` gives a public
HTTPS address without touching your router. Convenient, and worth remembering
that the tunnel provider sees the traffic.

**Port forwarding.** Works, and is the one to avoid: it puts the API on the
public internet with no TLS. If you do it anyway, use a private network for the
token exchange first and treat the port as hostile.

> Binding to `0.0.0.0` means anything that can route to the machine can try.
> A token is still required, and localhost trust covers only the machine
> itself - but there is no TLS yet, so on an untrusted network the token
> crosses in the clear. Use a private network or a tunnel.

## Browsing from the top

`GET /api/files` with no path lists the **shares themselves**, and every entry
names its share first - `Pictures/holiday/beach.jpg`. That is what makes a
second and third shared folder reachable at all: a client that knows nothing
starts at the top, walks down, and hands back the name it was given. Each
listing also carries the `parent` to walk back out, so no client has to trim a
path itself and risk stepping outside a share.

## From the phone

The Files tab does the round trip. **Send** picks a file on the phone and puts
it in the folder you are looking at; a file's sheet offers **Open on this
phone** and **Save a copy here**, and Delete when the computer allows it. Every
transfer is written to the timeline with the device that asked.

## What this does not do yet

- **No TLS of its own.** Put a private network or a tunnel in front of it.
- **No folder downloads.** One file at a time; nothing is zipped up for you.
- **No thumbnails or previews.** A phone client gets names, sizes and types,
  and has to render what it downloads.
- **No per-device scoping.** Every paired device sees the same shares. There is
  no "this phone may read but not write" yet, beyond the global switches.
- **Deleting is a global switch, not an approval.** Turning
  `files_allow_delete` on means any paired device can delete inside a share.
