# JabCross — Idea

## Prompt (see PROMPT.md)

Accessibility tools for navigating the medical care system for disabled users.
Judged on: practicality/relevance, creativity/innovation, significance, technical complexity.

Format: 5-hour hackathon, 3 team members. Submission is a **video** + the codebase + a few written
questions. Judging is done through the video. The codebase only needs to be generally acceptable;
it will not be scrutinized line by line.

## Concept

A single at-home hub for disabled users. Each team member takes one specific disability (chosen
because it causes demonstrable harm when navigating care) and engineers a focused solution for it.
The three solutions plus one general-purpose feature are packaged together into one app with a
shared account system.

Four features:

1. **General: care requests (adapted from BetterBell).** The user taps what they need instead of
   pressing a binary call bell, and their caregiver is notified with the specific request.
2. **Disability-specific feature A.** Owner: TBD. Example: depth/obstacle detection for blind users.
3. **Disability-specific feature B.** Owner: TBD.
4. **Disability-specific feature C.** Owner: TBD.

## Reuse of BetterBell

BetterBell (betterbell.care) is an existing project by a team member: a patient request platform
that replaces the physical hospital call bell with a mobile app. Hackathon organizers confirmed that
reusing concepts is allowed as long as the project meaningfully deviates from BetterBell and is
themed toward this prompt.

What we take from BetterBell:
- Account system (email login, user profile)
- Patient <-> caregiver linking (BetterBell `CareLink`)
- Request types + requests, generalized beyond hospital use
- Push notifications to the caregiver

What we leave behind (this is a proof of concept; security is out of scope):
- Audit logging, Postgres RLS, audit triggers
- Argon2 hashing config, hashed session tokens, throttling
- Setup/reset email links, soft delete, HIPAA/compliance infrastructure
- Hospital facility/bed/QR code paths

BetterBell stack for reference: Django + Django REST Framework + PostgreSQL backend,
React Native (Expo, expo-router, TypeScript) mobile client.

## Open decisions

- Which three disabilities, and who owns each
- Stack for JabCross (keep Django + Expo from BetterBell, or something lighter)
- How the features connect so it reads as one product in the video, not four separate demos
