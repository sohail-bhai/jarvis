# JARVIS on your phone

The phone is not a second JARVIS. It is a way into the one running on your
computer: you ask for something on the phone, the work happens on the
computer, and the phone shows what actually happened and asks you to approve
anything consequential.

```
     Your computer (Fedora)              Your teammate's laptop (Windows)
     control plane + AI brain                    desktop app
     python -m assistant.api                          |
             ^        ^                               |
             |        |  paired device token          |
             |        +-------------------------------+
             |
             |  paired device token
        Your phone (Expo app)
```

One computer holds the tasks, the timeline, the approvals and the files.
Every other device is a client holding its own token, and any one of those
tokens can be revoked without disturbing the others.

## Start the computer side

On the machine that should do the work:

```bash
python -m assistant.api --host 0.0.0.0
```

It prints the address to type on the phone:

```
  JARVIS is listening.

  Enter on your phone:     192.168.1.20:8765
  To connect a phone:      python -m assistant.api --pair --port 8765
```

> `--host 0.0.0.0` means anything on the network can reach the port. That is
> why reaching it is not the same as being allowed to use it: a client still
> has to pair. Use it on a network you trust.

## Connect the phone

```bash
cd mobile
npm install
npx expo start          # then open it with Expo Go, or run a dev build
```

The app opens on **Connect to your computer**, and asks for two things in the
order you can actually supply them:

1. **The address.** `192.168.1.20:8765`, or a Tailscale name. It is checked
   before anything else, so a typo is reported as a wrong address rather than
   as a wrong code. The scheme and port are filled in when you leave them out.
2. **The code.** Run this on the computer:

   ```bash
   python -m assistant.api --pair
   ```

   It prints a six-digit code that lasts ten minutes. Type it on the phone.

The phone stores its token in the platform keystore, and the address beside
it. It stays paired until you disconnect it from **You → Disconnect this
phone**, or revoke it on the computer:

```bash
curl -X DELETE localhost:8765/api/devices/<id>/token
```

To point a build at a computer by default, set `EXPO_PUBLIC_JARVIS_URL`.
Anything typed on the phone wins over it.

## Reaching the computer from anywhere

The address is all that changes between these:

| Where you are | What to enter |
| --- | --- |
| Same Wi-Fi | The LAN address JARVIS printed, e.g. `192.168.1.20:8765` |
| Anywhere, over Tailscale | The Tailscale name or address of the computer |
| Same machine, web preview | `127.0.0.1:8765` |

Tailscale is worth setting up before a demo: a venue's Wi-Fi often blocks
devices from seeing each other, and a private network is unaffected by that.

## What the phone does with the real API

| Screen | Where its content comes from |
| --- | --- |
| Home, command box | `POST /api/tasks` with `autoplan` and `run` - the computer plans the steps and works them |
| Home, current task | `GET /api/tasks`, then `GET /api/tasks/{id}` for the steps |
| Tasks | `GET /api/tasks`, `POST /api/tasks/{id}/cancel` |
| Task detail | `GET /api/tasks/{id}`, following `/ws/events?task_id=` |
| Activity | `GET /api/activity`, then every event live over `/ws/events` |
| Approvals | `GET /api/approvals`, `POST /api/approvals/{id}` |
| Files | `GET /api/files`, `GET /api/files/search` over the shared folders |
| Devices | `GET /api/devices` |
| Security | `GET /api/permissions`, `GET /api/status`, `POST /api/emergency-stop` |
| Google | Nothing. It is marked **Demo mode** on the screen itself. |

### Live rather than polled

The screens used to ask the computer for everything twice a second. Over a
real network that is both slow and enough to trip the API's own rate limit, so
the phone now listens on `/ws/events` and reloads when something actually
changed, with a slow reload behind it for whatever arrived while the phone was
asleep. The socket carries the same token as the REST calls, drops constantly
on a phone, and reconnects on its own with a backoff.

## The parts of the app

| File | Responsibility |
| --- | --- |
| `src/api/client.ts` | The address, the token, one request shape, one error shape |
| `src/api/storage.ts` | The keystore on a device, `localStorage` in a browser |
| `src/api/session.ts` | Pairing, disconnecting, and whether the computer is answering |
| `src/api/mappers.ts` | Control-plane JSON to the types the screens render |
| `src/api/live.ts` | The `/ws/events` stream, and reconnecting to it |
| `src/services/*.ts` | One module per part of the product, all going through the client |

`src/api/mappers.ts` is the only place that knows both vocabularies. The
server talks about goals, steps, helpers and events; the components were
written against their own types. Translating in one place means a renamed
server field breaks in one file rather than in nine screens.

## What is not connected yet

Said plainly, because a screen that pretends is worse than a screen that
admits:

- **Google** is example data, labelled Demo mode on the page.
- **What JARVIS remembers** is example data.
- **Files** are read-only from the phone. Upload, move and delete exist on the
  API but have no screen yet.
- **Notifications** need the app open. There is no push service, so a phone in
  a pocket sees an approval when it next asks.
- **The desktop app still talks to its own control plane in-process**, so a
  desktop on another machine does not yet see these tasks. That is the next
  piece of work.
