# Page Design Workflow

Before implementing or modifying any page, follow this process.

## Step 1 — Understand the page

Identify:

1. Page goal.
2. Main user type.
3. User knowledge level.
4. Primary action.
5. Secondary actions.
6. Information required from the user.
7. User fears or doubts.
8. Success condition.

Do not write code before this analysis.

## Step 2 — Define UX structure

Define:

1. Page sections.
2. Content hierarchy.
3. Main visual focus.
4. Primary CTA location.
5. Secondary CTA location.
6. Empty/loading/error states.
7. Desktop layout.
8. Mobile layout.

## Step 3 — Choose layout

For desktop-first pages, prefer:

- Two-column layout when there is a visual or video module.
- Centered max-width container.
- Strong hero card.
- Clear CTA area.

For wizard steps, prefer:

- One focused task.
- Main card centered.
- Clear progress indicator.
- Primary CTA always visible.

## Step 4 — Write copy

Before coding, define final copy:

- Title.
- Subtitle.
- Helper text.
- Button labels.
- Error messages.
- Empty state messages.
- Loading messages.

Copy must be simple, human, and non-technical.

## Step 5 — Design component structure

Define the component tree.

Example:

IntroScreen
  IntroHeroCard
  IntroVideoCard
  WizardIntroActions

Do not create unnecessary components.

## Step 6 — Implement UI

Only after steps 1–5 are defined, implement the page.

Implementation must:

- Use existing components when possible.
- Respect visual style guide.
- Respect responsive behavior.
- Include accessible labels.
- Include hover/focus states.
- Avoid hardcoded layout hacks.

## Step 7 — Self-review

After implementation, review the screen using the UX Review Checklist.

If any item fails, fix it before finishing.