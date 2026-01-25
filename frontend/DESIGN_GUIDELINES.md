# Moreach.ai Design Guidelines

## Overview

Moreach.ai is an AI-powered influencer discovery and lead generation platform with a modern, minimal, and professional design aesthetic. This guide outlines the design principles, components, and patterns used across the application.

---

## Design Philosophy

### Core Principles

1. **Minimal & Clean** - Prioritize clarity and simplicity over decoration
2. **Professional** - Maintain a business-focused, trustworthy appearance
3. **Card-Based Layout** - Use cards to organize and separate content sections
4. **Icon-Driven** - Leverage icons to enhance visual communication and usability
5. **Responsive First** - Design for mobile, scale up to desktop
6. **AI-Focused** - Highlight AI capabilities and automation features

---

## Visual Identity

### Color Palette

#### Primary Colors
```css
Gray 900 (Primary Dark):    #111827  /* Main text, dark buttons */
Gray 50 (Light Background): #f9fafb  /* Page backgrounds */
White:                      #ffffff  /* Cards, content areas */
```

#### Accent Colors
```css
Blue 600:  #2563eb  /* Primary actions, links */
Purple 600: #9333ea /* Secondary gradients */
Green 500: #10b981  /* Success states, active badges */
Red 500:   #ef4444  /* Errors, warnings */
```

#### Semantic Colors
```css
Success:  bg-green-100 text-green-700
Warning:  bg-yellow-100 text-yellow-700
Info:     bg-blue-100 text-blue-700
Error:    bg-red-50 text-red-700
Neutral:  bg-gray-100 text-gray-700
```

### Typography

#### Font Families
- **Primary Font**: Space Grotesk (sans-serif) - For body text, UI elements
- **Display Font**: Fraunces (serif) - For headings and brand elements

#### Font Sizes
```css
Hero Title:    text-5xl md:text-6xl lg:text-7xl (48-72px)
Page Title:    text-3xl md:text-4xl (30-36px)
Section Title: text-2xl (24px)
Card Title:    text-xl (20px)
Body:          text-base (16px)
Small:         text-sm (14px)
Tiny:          text-xs (12px)
```

#### Font Weights
```css
Regular:   font-normal (400)
Medium:    font-medium (500)
Semibold:  font-semibold (600)
Bold:      font-bold (700)
```

---

## Layout System

### Page Structure

Every page should follow this hierarchy:

```
<Navigation /> (fixed top bar)
  ↓
<Main Content Area> (with pt-24 for nav spacing)
  ↓
  <Container> (max-w-7xl mx-auto)
    ↓
    <Page Header>
      - Title
      - Description/Subtitle
      - Action Buttons
    </Page Header>
    ↓
    <Content Sections>
      - Cards
      - Lists
      - Forms
    </Content Sections>
```

### Spacing Scale

Use Tailwind's spacing scale consistently:

```css
Tiny:    p-2, gap-2   (8px)
Small:   p-3, gap-3   (12px)
Medium:  p-4, gap-4   (16px)
Large:   p-6, gap-6   (24px)
XLarge:  p-8, gap-8   (32px)
Section: py-20, px-6  (80px vertical, 24px horizontal)
```

### Grid System

```css
/* Standard content width */
max-w-7xl mx-auto

/* Narrow content (forms) */
max-w-3xl mx-auto

/* Full width with padding */
px-6 md:px-8 lg:px-12
```

---

## Component Patterns

### Navigation Bar

**Design Specs:**
- Fixed position: `fixed top-0 left-0 right-0 z-50`
- Background: `bg-white/90 backdrop-blur-md`
- Border: `border-b border-gray-200`
- Height: Approximately 72px (py-4)
- Elements: Logo, Platform Links, CTA Buttons

**Implementation:**
```tsx
<nav className="fixed top-0 left-0 right-0 z-50 bg-white/90 backdrop-blur-md border-b border-gray-200">
  <div className="max-w-7xl mx-auto px-6 py-4">
    <div className="flex items-center justify-between">
      <Logo />
      <Menu />
      <CTAs />
    </div>
  </div>
</nav>
```

**Page Spacing:** Add `pt-24` to main content to account for fixed nav

---

### Cards

Cards are the primary content container pattern.

#### Standard Card
```tsx
<div className="bg-white p-6 rounded-lg border border-gray-200 hover:shadow-md transition">
  <CardHeader />
  <CardContent />
  <CardFooter />
</div>
```

#### Hover States
- Add `hover:shadow-md transition` for interactive cards
- Use `hover:bg-gray-50` for clickable card backgrounds

#### Card Variants

**Info Card:**
```tsx
className="bg-white p-6 rounded-lg border"
```

**Interactive Card:**
```tsx
className="bg-white p-6 rounded-lg border hover:shadow-md transition cursor-pointer"
```

**Selected Card:**
```tsx
className="bg-blue-50 border-blue-500 p-6 rounded-lg"
```

---

### Buttons

#### Primary Button
```tsx
className="px-6 py-3 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition font-medium"
```

#### Secondary Button
```tsx
className="px-6 py-3 border border-gray-300 rounded-lg hover:bg-gray-50 transition font-medium"
```

#### Accent Button (Blue)
```tsx
className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition font-medium"
```

#### Disabled State
```tsx
className="... disabled:opacity-50 disabled:cursor-not-allowed"
```

#### Size Variants
- **Small**: `px-4 py-2 text-sm`
- **Medium** (default): `px-6 py-3 text-base`
- **Large**: `px-8 py-4 text-lg`

---

### Forms

#### Input Fields
```tsx
<input
  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
/>
```

#### Textarea
```tsx
<textarea
  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
  rows={4}
/>
```

#### Select Dropdown
```tsx
<select
  className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
>
  <option>Option</option>
</select>
```

#### Checkbox (Custom)
```tsx
<label className="flex items-start p-4 border rounded-lg cursor-pointer transition hover:bg-gray-50">
  <input type="checkbox" className="mt-1 mr-3" />
  <div>Label content</div>
</label>
```

---

### Badges & Status Indicators

#### Status Badge Pattern
```tsx
<span className={`px-3 py-1 rounded-full text-sm font-medium ${statusColor}`}>
  {status}
</span>
```

#### Status Colors
```css
Active:     bg-green-100 text-green-700
Processing: bg-blue-100 text-blue-700
Paused:     bg-gray-100 text-gray-700
Error:      bg-red-100 text-red-700
Warning:    bg-yellow-100 text-yellow-700
```

---

### Icons

Use Heroicons (inline SVG) for consistent iconography.

#### Icon Sizes
- Small: `w-4 h-4` (16px)
- Medium: `w-5 h-5` (20px)
- Large: `w-6 h-6` (24px)

#### Example Usage
```tsx
<svg className="w-5 h-5 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="..." />
</svg>
```

#### Common Icon Positions
- **Leading Icon**: Left side of text with `mr-2` or `mr-3`
- **Trailing Icon**: Right side of text with `ml-2` or `ml-3`
- **Button Icon**: Use `flex items-center gap-2` for icon + text

---

## Page-Specific Patterns

### Instagram Discovery Page (`/try`)

**Key Features:**
- Hero section with form
- Real-time status indicator
- Grid of influencer cards
- Profile images with follower counts
- Action buttons per card

**Card Layout:**
```tsx
<div className="bg-white rounded-lg border p-6">
  <ProfileImage />
  <Stats />
  <Bio />
  <ActionButtons />
</div>
```

---

### Reddit Lead Generation (`/reddit`)

**Key Features:**
- Campaign management dashboard
- Step-by-step workflow (Create → Discover → Select → Leads)
- Subreddit selection with checkboxes
- Lead cards with scoring and suggestions
- Status filtering tabs

**Campaign Card:**
```tsx
<div className="bg-white p-6 rounded-lg border hover:shadow-md transition">
  <StatusBadge />
  <Description />
  <Metrics />
  <ActionButtons />
</div>
```

**Lead Card:**
```tsx
<div className="bg-white p-6 rounded-lg border">
  <PostHeader />
  <PostContent />
  <AIInsights />
  <ActionButtons />
</div>
```

---

## Interaction Patterns

### Hover States

- **Cards**: `hover:shadow-md`
- **Buttons**: `hover:bg-{color}-{darker}`
- **Links**: `hover:text-{color}-900`
- **Selectable Items**: `hover:bg-gray-50`

### Active States

- **Selected Items**: `border-blue-500 bg-blue-50`
- **Active Tab**: `bg-blue-600 text-white`
- **Focused Input**: `ring-2 ring-blue-500`

### Loading States

```tsx
<div className="text-center py-12">
  <div className="animate-spin">⏳</div>
  <p className="mt-4 text-gray-600">Loading...</p>
</div>
```

### Empty States

```tsx
<div className="text-center py-12 bg-white rounded-lg border">
  <p className="text-gray-500 mb-4">No items found</p>
  <button>Create First Item</button>
</div>
```

### Error States

```tsx
<div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
  {errorMessage}
</div>
```

---

## Animations & Transitions

### Standard Transitions
```css
transition /* Default (150ms) */
transition-all duration-300
```

### Fade In Animation
```css
@keyframes fadeIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
```

### Hover Transforms
```css
hover:-translate-y-0.5  /* Subtle lift */
hover:scale-105         /* Slight grow */
```

---

## Responsive Design

### Breakpoints (Tailwind)
```css
sm:  640px
md:  768px
lg:  1024px
xl:  1280px
2xl: 1536px
```

### Mobile-First Approach

Always start with mobile layout, then add responsive classes:

```tsx
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {/* Cards */}
</div>
```

### Common Responsive Patterns

**Typography:**
```tsx
className="text-3xl md:text-4xl lg:text-5xl"
```

**Spacing:**
```tsx
className="p-4 md:p-6 lg:p-8"
```

**Layout:**
```tsx
className="flex flex-col md:flex-row gap-4"
```

**Visibility:**
```tsx
className="hidden md:block"  /* Hide on mobile */
className="md:hidden"         /* Hide on desktop */
```

---

## Accessibility

### Focus States
All interactive elements must have visible focus states:
```css
focus:ring-2 focus:ring-blue-500 focus:outline-none
```

### Color Contrast
- Ensure text meets WCAG AA standards (4.5:1 minimum)
- Primary text: Gray 900 on White (19:1 ✓)
- Secondary text: Gray 600 on White (7:1 ✓)

### Semantic HTML
- Use proper heading hierarchy (h1 → h2 → h3)
- Use `<nav>`, `<main>`, `<section>`, `<article>` tags
- Add `aria-label` to icon-only buttons

### Keyboard Navigation
- All interactive elements accessible via Tab
- Logical tab order maintained
- Enter/Space activates buttons and links

---

## Best Practices

### Do's ✅

- Use card-based layouts for organizing content
- Maintain consistent spacing throughout
- Use icons to enhance communication
- Keep forms simple and focused
- Provide clear feedback for user actions
- Use loading states for async operations
- Show empty states when no data exists
- Group related actions together
- Use semantic status colors consistently

### Don'ts ❌

- Don't mix rounded corner styles (stick to `rounded-lg`)
- Don't use more than 3 levels of shadow
- Don't overcomplicate color schemes
- Don't ignore mobile breakpoints
- Don't forget hover/focus states
- Don't hide errors without explanation
- Don't use low-contrast text
- Don't create buttons smaller than 44x44px (mobile)

---

## Design Tokens Reference

### Border Radius
```css
rounded-lg:   8px  (Standard for cards, buttons)
rounded-xl:   12px (Large cards, modals)
rounded-full: 9999px (Pills, badges, avatars)
```

### Shadows
```css
shadow-sm:  0 1px 2px rgba(0,0,0,0.05)
shadow-md:  0 4px 6px rgba(0,0,0,0.1)
shadow-lg:  0 10px 15px rgba(0,0,0,0.1)
shadow-xl:  0 20px 25px rgba(0,0,0,0.1)
```

### Z-Index Layers
```css
z-0:   Base content
z-10:  Dropdowns, tooltips
z-20:  Sticky elements
z-30:  Modals
z-40:  Notifications
z-50:  Navigation bar
```

---

## Component Library

### Reusable Components

Create these as shared components when building new features:

1. **Navigation** - Already exists (`/components/Navigation.tsx`)
2. **Card** - Standard card wrapper
3. **Button** - All button variants
4. **Badge** - Status indicators
5. **Input** - Form input with label
6. **Modal** - Overlay dialogs
7. **Toast** - Notification system
8. **Loader** - Loading spinner/skeleton
9. **EmptyState** - No data placeholder
10. **ErrorBoundary** - Error handling UI

---

## Platform-Specific Guidelines

### Instagram Feature
- Focus on visual-first design (profile images prominent)
- Show follower counts and engagement metrics
- Use grid layouts for profiles
- Include action buttons (DM, View Profile)

### Reddit Feature
- Emphasize text content over visuals
- Show subreddit context (r/subredditname)
- Display upvotes and comment counts
- Include AI-generated suggestions clearly labeled
- Use campaign-based organization

### Future Platforms (Twitter, TikTok)
- Maintain same card-based structure
- Adapt metrics to platform (retweets, views, etc.)
- Keep consistent status badges and actions
- Follow established color and spacing patterns

---

## File Structure

```
frontend/
├── app/
│   ├── globals.css          # Global styles
│   ├── layout.tsx           # Root layout with fonts
│   ├── page.tsx             # Homepage
│   ├── try/page.tsx         # Instagram discovery
│   └── reddit/page.tsx      # Reddit leads
├── components/
│   └── Navigation.tsx       # Shared nav component
└── lib/
    ├── api.ts               # API client
    └── types.ts             # TypeScript types
```

---

## Getting Started

When building a new page or feature:

1. Import `Navigation` component
2. Add `pt-24` to main container for nav spacing
3. Use `max-w-7xl mx-auto` for content width
4. Structure content with cards (`bg-white rounded-lg border`)
5. Follow spacing scale (p-4, p-6, p-8, gap-4, etc.)
6. Add hover states to interactive elements
7. Include loading and empty states
8. Test on mobile, tablet, and desktop breakpoints

---

## Resources

- **Tailwind CSS Docs**: https://tailwindcss.com/docs
- **Heroicons**: https://heroicons.com
- **Color Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Space Grotesk Font**: https://fonts.google.com/specimen/Space+Grotesk
- **Fraunces Font**: https://fonts.google.com/specimen/Fraunces

---

## Version History

- **v1.0** (2026-01-13) - Initial design guidelines established
  - Card-based minimal design
  - Icon-driven interface
  - Responsive patterns
  - Instagram & Reddit features

---

## Questions or Suggestions?

This is a living document. As new patterns emerge or the design evolves, update this guide to maintain consistency across the platform.

**Last Updated:** January 13, 2026

