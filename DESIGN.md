# Design Guidelines

> **Instructions**: Customize this template for your product's design system. This helps Claude Code generate consistent, well-designed UIs and follow your design principles. Delete this block when done.

## Design Philosophy

**Core Principle**: [e.g., "Simplicity and clarity over complexity. Every element should have a purpose."]

**Design Framework**: We follow **Jakob Nielsen's 10 Usability Heuristics**

### Jakob's 10 Usability Heuristics

1. **Visibility of system status**: Keep users informed about what's happening
2. **Match between system and real world**: Use familiar language and concepts
3. **User control and freedom**: Provide undo/redo, easy exits
4. **Consistency and standards**: Follow platform conventions
5. **Error prevention**: Design to prevent problems before they occur
6. **Recognition rather than recall**: Make options visible, reduce memory load
7. **Flexibility and efficiency**: Allow shortcuts for power users
8. **Aesthetic and minimalist design**: Remove unnecessary elements
9. **Help users recognize and recover from errors**: Clear error messages with solutions
10. **Help and documentation**: Provide contextual help when needed

---

## Target Users

### Primary Persona: [Persona Name]

**Demographics**:
- Age: [Age range]
- Role: [Job title/role]
- Tech Savviness: [Low / Medium / High]

**Context**:
- **Problem**: [What problem do they face?]
- **Goal**: [What are they trying to achieve?]
- **Environment**: [Where/when do they use this? Desktop? Mobile? In a hurry?]

**Pain Points**:
1. [Pain point 1]
2. [Pain point 2]
3. [Pain point 3]

**Design Implications**:
- [How this affects design decisions]
- [What they need to succeed]

### Secondary Persona: [Persona Name]

[Repeat structure above]

---

## Typography

### Font Stack

**Primary Font**: [Font family]
```css
font-family: [Font name], -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
```

**Monospace Font** (code, data):
```css
font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;
```

### Type Scale

**Headings**:
```css
h1: 32px / 2rem      (Page titles)
h2: 24px / 1.5rem    (Section headers)
h3: 20px / 1.25rem   (Subsection headers)
h4: 18px / 1.125rem  (Component headers)
```

**Body Text**:
```css
body: 16px / 1rem        (Normal text)
small: 14px / 0.875rem   (Secondary text)
tiny: 12px / 0.75rem     (Captions, labels)
```

**Font Weights**:
- **Regular**: 400 (body text)
- **Medium**: 500 (emphasis)
- **Semibold**: 600 (headings)
- **Bold**: 700 (strong emphasis)

### Line Height

```css
tight: 1.25    (Headings)
normal: 1.5    (Body text)
relaxed: 1.75  (Long-form content)
```

### Usage Guidelines

**DO**:
- Use h1 for page titles only (one per page)
- Use 16px minimum for body text
- Use consistent line heights
- Use system fonts for performance

**DON'T**:
- Mix too many font weights (max 3)
- Use fonts smaller than 12px
- Use line heights < 1.2 for readability

---

## Color Palette

### Brand Colors

**Primary** (Main brand color):
```
Primary-50:  [Lightest]  #[hex]
Primary-100: ...         #[hex]
Primary-500: [Base]      #[hex]
Primary-900: [Darkest]   #[hex]
```

**Secondary** (Accent color):
```
Secondary-500: [Base]    #[hex]
```

### Semantic Colors

**Success** (Positive actions, confirmations):
```
Success-50:  #[hex]  (Background)
Success-500: #[hex]  (Text/icons)
Success-900: #[hex]  (Dark text)
```

**Warning** (Caution, non-critical alerts):
```
Warning-50:  #[hex]
Warning-500: #[hex]
Warning-900: #[hex]
```

**Error** (Errors, destructive actions):
```
Error-50:  #[hex]
Error-500: #[hex]
Error-900: #[hex]
```

**Info** (Informational messages):
```
Info-50:  #[hex]
Info-500: #[hex]
Info-900: #[hex]
```

### Neutral Colors

**Grays** (Text, borders, backgrounds):
```
Gray-50:  #[hex]  (Backgrounds)
Gray-100: #[hex]  (Subtle backgrounds)
Gray-200: #[hex]  (Borders)
Gray-300: #[hex]  (Borders hover)
Gray-500: #[hex]  (Secondary text)
Gray-700: #[hex]  (Primary text)
Gray-900: #[hex]  (Headings)
```

### Color Usage

**Text**:
- Primary text: Gray-900
- Secondary text: Gray-500
- Disabled text: Gray-300
- Link text: Primary-500
- Link hover: Primary-700

**Backgrounds**:
- Page background: White or Gray-50
- Card background: White
- Input background: White
- Hover background: Gray-100
- Active background: Primary-50

**Borders**:
- Default border: Gray-200
- Hover border: Gray-300
- Focus border: Primary-500
- Error border: Error-500

---

## Spacing System

**Base Unit**: 4px (0.25rem)

**Scale**:
```
xs:  4px   (0.25rem)
sm:  8px   (0.5rem)
md:  16px  (1rem)
lg:  24px  (1.5rem)
xl:  32px  (2rem)
2xl: 48px  (3rem)
3xl: 64px  (4rem)
```

**Usage**:
- Use multiples of 4px for all spacing
- Component padding: 16px (md) or 24px (lg)
- Section spacing: 48px (2xl) or 64px (3xl)
- Element margins: 8px (sm) or 16px (md)

---

## Visual Hierarchy

### Principles

1. **Size**: Larger elements draw more attention
2. **Color**: High contrast elements stand out
3. **Weight**: Bolder text is more prominent
4. **Position**: Top-left gets noticed first (in LTR languages)
5. **Whitespace**: More space = more importance

### Hierarchy Pattern

```
┌─────────────────────────────────────────┐
│  [Large, bold heading]                  │  ← Primary focus
│                                         │
│  [Medium, gray text description]        │  ← Secondary
│                                         │
│  ┌──────────────────┐  ┌─────────────┐ │
│  │  [Primary CTA]   │  │ [Secondary] │ │  ← Actions
│  └──────────────────┘  └─────────────┘ │
│                                         │
│  [Small, light text for metadata]       │  ← Tertiary
└─────────────────────────────────────────┘
```

### Visual Weight

**Primary Actions**:
- Large size (40-48px height)
- High contrast color (Primary-500)
- Bold text (600 weight)
- Prominent position (top or bottom-right)

**Secondary Actions**:
- Medium size (36-40px height)
- Lower contrast (Gray-500 or outline)
- Normal text (500 weight)
- Adjacent to primary action

**Tertiary Actions**:
- Small size (32px height)
- Minimal styling (text-only or subtle)
- Regular text (400 weight)
- Less prominent position

---

## Components

### Buttons

**Primary Button**:
```css
background: Primary-500
color: White
padding: 12px 24px
border-radius: 8px
font-weight: 600

hover: Primary-600
active: Primary-700
disabled: Gray-300
```

**Secondary Button**:
```css
background: Transparent
color: Primary-500
border: 2px solid Primary-500
padding: 12px 24px
border-radius: 8px

hover: Primary-50 background
disabled: Gray-300 color and border
```

**Destructive Button** (delete, remove):
```css
background: Error-500
color: White
padding: 12px 24px
border-radius: 8px

hover: Error-600
```

**Usage**:
- Use **one** primary button per section
- Use secondary for alternative actions
- Use destructive for irreversible actions
- Minimum touch target: 44x44px (mobile)

### Form Inputs

**Text Input**:
```css
border: 1px solid Gray-200
border-radius: 6px
padding: 10px 12px
font-size: 16px

focus: Primary-500 border, blue focus ring
error: Error-500 border
disabled: Gray-100 background
```

**Label**:
```css
font-size: 14px
font-weight: 500
color: Gray-700
margin-bottom: 6px
```

**Help Text**:
```css
font-size: 14px
color: Gray-500
margin-top: 4px
```

**Error Message**:
```css
font-size: 14px
color: Error-500
margin-top: 4px
```

### Cards

**Standard Card**:
```css
background: White
border: 1px solid Gray-200
border-radius: 12px
padding: 24px
box-shadow: 0 1px 3px rgba(0,0,0,0.1)

hover: box-shadow: 0 4px 6px rgba(0,0,0,0.1)
```

**Usage**:
- Use for grouping related content
- Consistent padding (24px)
- Clear visual separation from page background

### Modals/Dialogs

**Structure**:
```
┌─────────────────────────────────┐
│  [X] Close                      │
│                                 │
│  [Modal Title]                  │
│                                 │
│  [Content goes here...]         │
│                                 │
│                                 │
│  [Cancel]     [Primary Action]  │
└─────────────────────────────────┘
```

**Styling**:
- Max width: 500px
- Overlay: rgba(0,0,0,0.5)
- Centered on screen
- Close button top-right
- Actions bottom-right

---

## Layout Patterns

### Grid System

**Breakpoints**:
```
mobile:  < 640px
tablet:  640px - 1024px
desktop: > 1024px
```

**Container**:
```css
max-width: 1200px
margin: 0 auto
padding: 0 24px
```

**Grid**:
```css
display: grid
gap: 24px

mobile:  1 column
tablet:  2 columns
desktop: 3-4 columns
```

### Common Layouts

**Dashboard Layout**:
```
┌──────────────────────────────────────┐
│  Header / Navigation                 │
├────────┬─────────────────────────────┤
│ Side   │  Main Content               │
│ bar    │                             │
│        │                             │
│        │                             │
└────────┴─────────────────────────────┘
```

**Form Layout**:
```
┌──────────────────────────────────────┐
│  [Form Title]                        │
│                                      │
│  [Label]                             │
│  [Input field────────────────────]   │
│  [Help text]                         │
│                                      │
│  [Label]                             │
│  [Input field────────────────────]   │
│                                      │
│         [Cancel]    [Submit Button]  │
└──────────────────────────────────────┘
```

**List/Detail Layout**:
```
┌──────────┬───────────────────────────┐
│ Item 1   │  [Detail View]            │
│ Item 2   │                           │
│ Item 3 ← │  Content for Item 3       │
│ Item 4   │                           │
│ Item 5   │                           │
└──────────┴───────────────────────────┘
```

---

## Interaction Patterns

### States

**Default**:
```
Normal state, ready for interaction
```

**Hover**:
```
Subtle color change, shows interactivity
cursor: pointer
```

**Active/Pressed**:
```
Darker color, shows depression
```

**Focus**:
```
Visible outline (accessibility)
outline: 2px solid Primary-500
outline-offset: 2px
```

**Disabled**:
```
Reduced opacity or gray color
cursor: not-allowed
no interaction
```

**Loading**:
```
Spinner or skeleton
Disabled interaction
Clear loading indicator
```

### Feedback

**Success**:
- Toast notification (green)
- Checkmark icon
- Success message
- Auto-dismiss after 3-5 seconds

**Error**:
- Toast notification (red)
- Error icon
- Clear error message
- Actionable solution
- Stays until user dismisses

**Loading**:
- Skeleton screens for content
- Spinners for actions
- Progress bars for long operations
- Clear "processing" state

---

## Motion and Animation

### Principles

1. **Purposeful**: Animations should guide attention
2. **Quick**: Keep under 300ms
3. **Natural**: Use easing for realism
4. **Consistent**: Same animations for same actions

### Timing

```
Fast:    150ms  (button hover, small changes)
Normal:  250ms  (transitions, fades)
Slow:    400ms  (large movements, page transitions)
```

### Easing

```css
ease-out: cubic-bezier(0, 0, 0.2, 1)     /* Elements entering */
ease-in:  cubic-bezier(0.4, 0, 1, 1)     /* Elements exiting */
ease-in-out: cubic-bezier(0.4, 0, 0.2, 1) /* Elements moving */
```

### Common Animations

**Fade In**:
```css
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

animation: fadeIn 250ms ease-out;
```

**Slide In**:
```css
@keyframes slideIn {
  from { transform: translateY(20px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

animation: slideIn 300ms ease-out;
```

**Hover Scale**:
```css
transition: transform 150ms ease-out;

hover: transform: scale(1.05);
```

### When to Animate

**DO animate**:
- Button interactions (hover, press)
- Modal enter/exit
- Dropdown open/close
- Page transitions
- Loading states

**DON'T animate**:
- Text content (hard to read)
- Critical actions (too slow)
- Continuously (distracting)
- Without purpose

---

## Accessibility

### WCAG 2.1 AA Compliance

**Color Contrast**:
- Normal text: 4.5:1 minimum
- Large text (18px+): 3:1 minimum
- UI components: 3:1 minimum

**Keyboard Navigation**:
- All interactive elements focusable
- Visible focus indicators
- Logical tab order
- Skip navigation links

**Screen Readers**:
- Semantic HTML (nav, main, button, etc.)
- Alt text for images
- ARIA labels for custom components
- Meaningful link text

**Forms**:
- Labels associated with inputs
- Error messages linked to fields
- Clear validation messages
- Required field indicators

### Accessibility Checklist

- [ ] All images have alt text
- [ ] Color is not the only indicator
- [ ] All interactive elements keyboard accessible
- [ ] Focus visible on all elements
- [ ] Forms have proper labels and error messages
- [ ] Headings follow hierarchical order (h1, h2, h3)
- [ ] Links have descriptive text (not "click here")
- [ ] ARIA attributes used correctly

---

## ASCII Wireframe Examples

### Login Screen

```
┌─────────────────────────────────────────┐
│                                         │
│           [LOGO]                        │
│                                         │
│         Welcome Back                    │
│         Sign in to your account         │
│                                         │
│  Email                                  │
│  ┌───────────────────────────────────┐  │
│  │ you@example.com                   │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Password                               │
│  ┌───────────────────────────────────┐  │
│  │ ••••••••••                        │  │
│  └───────────────────────────────────┘  │
│                                         │
│  [ ] Remember me      Forgot password?  │
│                                         │
│  ┌───────────────────────────────────┐  │
│  │        Sign In                    │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Don't have an account? Sign up         │
│                                         │
└─────────────────────────────────────────┘
```

### Dashboard

```
┌──────────────────────────────────────────────────────┐
│  [LOGO]    Dashboard    Profile    Settings  [Logout]│
├──────────────────────────────────────────────────────┤
│                                                      │
│  Welcome back, Jurgen!                              │
│                                                      │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │
│  │    Total     │  │    Active    │  │  Pending   │ │
│  │    Users     │  │   Projects   │  │   Tasks    │ │
│  │              │  │              │  │            │ │
│  │    1,234     │  │      23      │  │     45     │ │
│  └──────────────┘  └──────────────┘  └────────────┘ │
│                                                      │
│  Recent Activity                       [View All →] │
│  ┌────────────────────────────────────────────────┐ │
│  │  ● User John joined Project Alpha   2min ago  │ │
│  │  ● Task "Design review" completed   1hr ago   │ │
│  │  ● New comment on Issue #234        3hr ago   │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
└──────────────────────────────────────────────────────┘
```

### Form with Validation

```
┌─────────────────────────────────────────┐
│  Create New Project                     │
│                                         │
│  Project Name *                         │
│  ┌───────────────────────────────────┐  │
│  │ My Awesome Project                │  │
│  └───────────────────────────────────┘  │
│                                         │
│  Description                            │
│  ┌───────────────────────────────────┐  │
│  │ Enter description here...         │  │
│  │                                   │  │
│  │                                   │  │
│  └───────────────────────────────────┘  │
│  500 characters remaining               │
│                                         │
│  Team Members *                         │
│  ┌───────────────────────────────────┐  │
│  │ [Select members...]            ▼ │  │
│  └───────────────────────────────────┘  │
│  ⚠️ Please select at least one member   │
│                                         │
│  Start Date *                           │
│  ┌──────────────┐                       │
│  │ 2026-01-20  │📅│                     │
│  └──────────────┘                       │
│                                         │
│            [Cancel]    [Create Project] │
│                                         │
└─────────────────────────────────────────┘
```

---

## Responsive Design

### Mobile-First Approach

**Design for mobile first**, then enhance for larger screens

### Breakpoint Guidelines

**Mobile (< 640px)**:
- Single column layout
- Larger touch targets (44px minimum)
- Simplified navigation (hamburger menu)
- Reduced content density
- Bottom navigation for key actions

**Tablet (640px - 1024px)**:
- Two-column layouts
- More content density
- Side navigation possible
- Larger images/media

**Desktop (> 1024px)**:
- Multi-column layouts
- Side navigation
- Hover interactions
- Keyboard shortcuts
- More information density

---

## Design Checklist

Before implementing a new screen/feature:

### Planning
- [ ] User story defined (who, what, why)
- [ ] Success metrics identified
- [ ] Edge cases considered
- [ ] Mobile and desktop layouts planned

### Design
- [ ] Follows typography scale
- [ ] Uses colors from palette
- [ ] Spacing uses 4px grid
- [ ] Visual hierarchy is clear
- [ ] Accessibility considered

### Implementation
- [ ] Matches design mockup
- [ ] Responsive on all breakpoints
- [ ] Keyboard accessible
- [ ] Screen reader tested
- [ ] Performance optimized

---

## Resources

### Internal
- Design System: [Link to Figma/Storybook]
- Brand Guidelines: [Link]
- Component Library: [Link]

### External
- [Jakob Nielsen's 10 Usability Heuristics](https://www.nngroup.com/articles/ten-usability-heuristics/)
- [Material Design Guidelines](https://material.io/design)
- [Human Interface Guidelines (Apple)](https://developer.apple.com/design/human-interface-guidelines/)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

---

**Last Updated**: [Date]
**Maintained By**: [Design team/Your name]
