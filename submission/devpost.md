# JabCross Devpost submission

Each section below matches one field on the form, in order. Copy only the text inside
each fenced block. Do not copy the notes around it.

## General info

### Project name (60 characters max)

```text
JabCross: Google Maps for Hospitals
```

### Elevator pitch (200 characters max)

```text
Google Maps for hospitals, built first for blind patients. Say where you need to go, and a chest-worn phone guides you there with spoken directions and obstacle warnings.
```

### Thumbnail

`submission/thumbnail.png` (the team photo) is under the 5 MB limit, but it is wider than
3:2, so the sides may get cropped. A photo of the walker wearing the phone would explain
the project better at thumbnail size.

## Project Story

### About the project

Select everything in the box, including the template headings, and replace it with this.

```markdown
## Inspiration

Google Maps gets you to the front door of a hospital, then it stops. Inside, there is no GPS, the corridors look alike, and the directions are printed on signs. For a blind patient, that usually means depending on whoever happens to be nearby.

The CDC estimates that over 7 million Americans live with vision loss or blindness, about 1 million of them blind ([CDC](https://www.cdc.gov/vision-health-data/prevalence-estimates/vision-loss-prevalence.html)). Researchers at Michigan Medicine note that blind and low-vision patients face disability-related barriers in health care settings, and their response was to train staff as human guides ([JMIR, 2025](https://rehab.jmir.org/2025/1/e64666)). We wanted to know if a phone could give a patient that kind of guidance on their own.

## What it does

JabCross is indoor navigation for blind and low-vision patients. The patient wears a phone on their chest with the camera facing forward, taps once to start, taps the mic, and says something like "take me to radiology."

From there the app talks them through the route:

- **Directions:** "Turn right about 90 degrees," then "Walk forward about 7 steps."
- **Safety:** if something is less than about 1 meter ahead, it plays a tone, says stop, and says which side has more space.
- **Bad camera view:** if the lens is covered, it tells the patient to fix the phone.
- **Location:** printed markers on the walls tell the app exactly where the patient is.
- **Arrival:** it announces each destination out loud.

Patients can also ask "where am I," "repeat," "stop," or "cancel." Destinations understand everyday words, so "radiology," "imaging," and "x-ray" all lead to the same place.

## How we built it

**Phone.** A plain HTML and JavaScript page sends a camera frame and compass heading to a laptop about every 300 ms, and speaks the replies. It uses the browser's speech recognition and speech synthesis, Web Audio for alert tones, and a wake lock so the screen stays on. A Cloudflare tunnel provides the HTTPS connection that phone cameras require.

**Perception.** A FastAPI server runs the Ultralytics YOLO26 depth model on each frame. It finds the nearest distance in meters in the left, center, and right thirds of the view, ignoring the bottom quarter so the floor does not count as an obstacle. OpenCV detects ArUco markers, which are printed black and white squares, and solvePnP turns each one into a distance and a bearing.

**Navigation.** Our navigator holds a graph of the building, finds the shortest route, and decides what to say. Safety always comes first: blocked camera, then obstacle, then turn correction, then the next marker, then walking. A marker sighting overrides the app's estimate of position. It also corrects the compass. If marker \\(M\\) is seen at bearing \\(b\\), the patient's heading on the map is:

$$\theta_{\text{map}} = \text{facing}_M - b$$

We store the difference between that heading and the phone's compass, so turns stay accurate between markers. The heading of a hallway from point \\(a\\) to point \\(b\\), with the map's y axis pointing down, is:

$$\theta = \operatorname{atan2}(b_x - a_x,\; -(b_y - a_y))$$

**Map and viewer.** We started from the real Grady Memorial Hospital ground floor plans, then built a staged four-stop route for filming: Entrance, Lobby, Pharmacy, X-ray. The same map file drives the navigator and a Three.js viewer. The hospital walkthrough in our video is a scripted simulation shown beside the real phone footage. It does not track the phone live.

## Challenges we ran into

- **Knowing where you are without GPS.** Depth tells you what is in front of you, not where you are. That is why we added printed markers, which give an exact position at each stop.
- **Depth was fooled in two ways.** Stretching each frame into a square made indoor scenes read about 24% too far away on the NYU Depth V2 dataset, so we kept each frame's real shape. The model also reports a smooth wall about 1 meter away when the lens is covered, so we check image contrast separately.
- **Too much talking.** Our first version repeated instructions every 3 seconds, which is exhausting when speech is your only interface. We rebuilt it to speak only when something changes. A patient must drift more than 30 degrees to get a correction, then return within 15 degrees to clear it. An obstacle must show up in two frames in a row to trigger a stop, and the path must open past 1.3 meters to end it.
- **Close markers can mislead.** Standing slightly off to one side of a nearby marker skews its bearing, so we only correct the compass from markers more than 2 meters away.
- **iPhone permissions.** Camera, motion, and audio all need a real tap, so one start button has to unlock all of them at once. We planned always-on listening, then settled on tap to talk, which also stops the app from transcribing its own voice.

## Accomplishments that we're proud of

We built the full loop in one hackathon: phone camera to depth and marker perception to routing and back to spoken guidance. The navigator has 50 automated tests that replay simulated camera readings, including obstacles, missed markers, and arrivals, so we could develop it before the perception code existed. We are also proud of how quiet it is. Saying less took more engineering than saying more.

## What we learned

For someone who cannot see the screen, the interface is timing. A correct instruction at the wrong moment is still a bad instruction. We also learned to pair two imperfect signals: a printed marker is exact but occasional, a compass is constant but drifts, and each one covers for the other.

## What's next for JabCross

- Test with blind and low-vision users, and with orientation and mobility specialists.
- Calibrate step counts and depth distances in real hallways.
- Run a pilot in one real hospital corridor. Our Grady geometry is illustrative and has not been validated for real navigation.
- Replace printed markers with camera-based recognition of the location, so hospitals need no new signage.
- Add routes for other disabilities, such as step-free routes for wheelchair users.
```

## Built with

Type each one and press Enter or comma. Pick the suggested tag when one appears.

```text
python, javascript, html5, fastapi, uvicorn, pytorch, ultralytics, yolo26, opencv, aruco, three.js, web-speech-api, web-audio-api, cloudflare-tunnel, claude-code
```

## "Try it out" links

First link:

```text
https://github.com/jasperwchen/JABCross
```

Click ADD ANOTHER LINK for the second one:

```text
https://jabcross-gsmst-cafeteria.purplegull36.chatgpt.site
```

The second link works, but it still shows the older viewer without the first-person
hospital walkthrough. Add it anyway only if that is acceptable. The update needs Sites
editor access.

## Project Media

### Image gallery

JPG, PNG, or GIF, up to 5 MB each, 3:2 ratio. Upload these in this order:

1. The blindfolded walker wearing the phone, with the spotter nearby.
2. The phone screen during navigation, showing the camera and depth views.
3. A printed marker taped up at the venue next to its department sign.
4. The first-person hospital view from `/map/`.
5. The overhead route view from `/map/`.

### Video demo link

Paste the YouTube or Vimeo URL. Open it in a private window first to confirm that it
plays without signing in. Unlisted is fine on YouTube. Private is not.

## Additional info

Leave the file upload empty. The GitHub link already covers the code.
