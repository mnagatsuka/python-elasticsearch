# Interface Navigation

**Master the modern Kibana 9.0 user interface and navigation patterns**

*Estimated reading time: 20 minutes*

## Overview

Kibana 9.0 features a redesigned interface optimized for productivity and ease of use. This guide will help you navigate efficiently between applications, understand the layout structure, and master the key interface elements that make data exploration and visualization seamless.

## 🎯 Interface Architecture

### Main Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│ Global Header (Navigation + Search + User Menu)            │
├─────────────────────────────────────────────────────────────┤
│ │                                                         │ │
│ │                                                         │ │
│ │              Main Content Area                          │ │
│ │                                                         │ │
│ │                                                         │ │
│S│                                                         │P│
│i│                                                         │a│
│d│                                                         │n│
│e│                                                         │e│
│b│                                                         │l│
│a│                                                         │ │
│r│                                                         │A│
│ │                                                         │r│
│ │                                                         │e│
│ │                                                         │a│
├─────────────────────────────────────────────────────────────┤
│ Status Bar (Space, Time Range, Global Filters)             │
└─────────────────────────────────────────────────────────────┘
```

## 🧭 Global Header Navigation

### Application Launcher

**Main Navigation Menu (Top Left)**
- Click the hamburger menu (☰) to access all applications
- Applications are grouped by category for easy discovery
- Search functionality to quickly find specific apps

**Application Categories:**
```
Analytics
├── Discover (Data exploration)
├── Lens (Drag-and-drop visualizations)
├── Dashboard (Combined views)
├── Canvas (Custom presentations)
└── Maps (Geospatial analysis)

Observability
├── APM (Application Performance)
├── Logs (Log analysis)
├── Metrics (Infrastructure monitoring)
└── Uptime (Service availability)

Security
├── SIEM (Security information)
├── Cases (Incident management)
└── Timeline (Security events)

Management
├── Stack Management (System configuration)
├── Dev Tools (API console)
└── Monitoring (Cluster health)
```

### Global Search

**Unified Search Bar (Top Center)**
- Search across all Kibana content (dashboards, visualizations, maps)
- Recently viewed items appear in dropdown
- Quick access to create new content

**Search Scope:**
```
Global Search includes:
├── Dashboards and visualizations
├── Saved searches and queries
├── Maps and canvas workpads
├── Machine learning jobs
└── Index patterns and data views
```

**Search Examples:**
```
sales dashboard          # Find dashboards with "sales"
lens:revenue            # Find Lens visualizations about revenue
map:store locations     # Find maps showing store locations
```

### User Menu (Top Right)

**Profile and Settings Access:**
- User profile and preferences
- Theme selection (Light/Dark mode)
- Language preferences
- Keyboard shortcuts reference
- Sign out option

## 📱 Sidebar Navigation

### Collapsible Sidebar

**Default State:** Expanded with labels
**Collapsed State:** Icons only for more screen space
**Toggle:** Click the collapse button (‹) to minimize

**Sidebar Sections:**
```
Recently Viewed
├── Last 5 accessed items
├── Quick access to favorites
└── Resume previous work

Current Space Items
├── Dashboards in current space
├── Saved searches
├── Visualizations and maps
└── Canvas workpads

Pinned Items
├── Frequently used dashboards
├── Important visualizations
└── Custom shortcuts
```

### Space Switcher

**Current Space Indicator**
- Displayed at top of sidebar
- Click to switch between spaces
- Visual indicator of active space

**Space Navigation:**
```
Default Space (Usually "Default")
├── Shared content accessible to all users
├── Public dashboards and visualizations
└── Common data views

Team Spaces
├── Marketing (marketing-specific content)
├── Sales (sales dashboards and reports)
├── Engineering (technical monitoring)
└── Custom spaces per department
```

## 🎨 Theme and Appearance

### Dark Mode vs Light Mode

**Toggle Dark Mode:**
1. Click user menu (top right)
2. Select "Appearance"
3. Choose "Dark theme" or "Light theme"

**Dark Mode Benefits:**
- Reduced eye strain during long sessions
- Better contrast for charts and visualizations
- Modern professional appearance
- Energy savings on OLED displays

**Light Mode Benefits:**
- Better for presentations and printing
- Familiar interface for new users
- High contrast for detailed data review
- Better visibility in bright environments

### Responsive Design

**Desktop View (> 1200px)**
- Full sidebar with labels
- Multiple panel layout
- Complete navigation visible

**Tablet View (768px - 1200px)**
- Collapsible sidebar
- Stacked panel layout
- Touch-optimized controls

**Mobile View (< 768px)**
- Hidden sidebar (hamburger menu access)
- Single column layout
- Swipe gestures for navigation

## 🔍 Application-Specific Navigation

### Discover App Navigation

**Main Areas:**
```
Discover Interface
├── Query Bar (KQL search)
├── Field List (left sidebar)
├── Document Table (main area)
├── Time Filter (top right)
└── Save/Share Controls (top)
```

**Navigation Patterns:**
- Click field names to add filters
- Click document rows to view details
- Use time picker for date range selection
- Save searches for later use

### Dashboard Navigation

**Dashboard Controls:**
```
Dashboard Header
├── Edit/View mode toggle
├── Time range picker
├── Global filters
├── Save/Share options
└── Settings menu

Panel Controls (when editing)
├── Add visualization panel
├── Resize and move panels
├── Panel options menu
└── Clone/delete panels
```

**Interaction Patterns:**
- Click visualizations to drill down
- Use filters to refine data
- Hover for tooltips and details
- Double-click to enter edit mode

### Lens Visualization Builder

**Lens Interface Areas:**
```
Lens Builder
├── Data Panel (left - fields and filters)
├── Configuration Panel (right - chart settings)
├── Preview Area (center - live chart)
├── Suggestions Panel (top - smart recommendations)
└── Save Controls (top right)
```

**Drag-and-Drop Workflow:**
1. Drag fields from data panel to configuration areas
2. Drop fields on appropriate zones (X-axis, Y-axis, Color)
3. Adjust chart type and settings
4. Preview updates in real-time

## ⚡ Keyboard Shortcuts

### Global Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl/Cmd + /` | Open global search |
| `Ctrl/Cmd + Shift + O` | Open application launcher |
| `g + d` | Go to Discover |
| `g + v` | Go to Visualize |
| `g + a` | Go to Dashboard |
| `g + m` | Go to Maps |

### Application-Specific Shortcuts

**Discover:**
| Shortcut | Action |
|----------|--------|
| `r` | Refresh data |
| `f` | Focus on search bar |
| `t` | Toggle time filter |

**Dashboard:**
| Shortcut | Action |
|----------|--------|
| `e` | Enter edit mode |
| `s` | Save dashboard |
| `f` | Enter fullscreen |
| `Esc` | Exit fullscreen |

**Lens:**
| Shortcut | Action |
|----------|--------|
| `s` | Save visualization |
| `r` | Reset to defaults |
| `p` | Toggle preview |

## 🎛️ Control Panels and Filters

### Time Range Picker

**Quick Time Ranges:**
```
Common Ranges
├── Last 15 minutes
├── Last hour
├── Last 24 hours
├── Last 7 days
├── Last 30 days
└── Custom range picker
```

**Auto-Refresh Options:**
- 10 seconds, 30 seconds, 1 minute, 5 minutes, 15 minutes, 30 minutes
- Pause auto-refresh when focusing on specific data
- Resume auto-refresh automatically

### Global Filters

**Filter Types:**
```
Filter Bar Components
├── Field filters (category: electronics)
├── Query filters (KQL expressions)
├── Time range filter (automatic)
├── Geo filters (location-based)
└── Negation filters (exclude results)
```

**Filter Interactions:**
- **Pin filters** to persist across navigation
- **Disable filters** temporarily without deleting
- **Edit filters** to modify conditions
- **Copy filters** between dashboards

### Panel Area (Right Side)

**Contextual Information:**
- Field statistics and distributions
- Filter suggestions based on current data
- Recently used filters and queries
- Data view information and field mapping

## 🔧 Customization Options

### Personal Preferences

**Access via User Menu → Preferences:**

```yaml
Interface Preferences:
  theme: "dark" | "light"
  language: "en" | "es" | "fr" | "de" | ...
  timezone: "browser" | "UTC" | custom
  date_format: "browser" | "MMM D, YYYY" | custom
  
Navigation Preferences:
  default_route: "/app/home" | "/app/discover" | custom
  sidebar_collapsed: true | false
  recent_items_count: 5 | 10 | 15
```

### Space Customization

**Space Settings (Admin only):**
- Custom space name and description
- Space avatar/icon
- Feature toggles (hide unused applications)
- Default time range for the space

## 🚨 Common Navigation Patterns

### Efficient Workflow Patterns

**Data Exploration Workflow:**
1. Start in **Discover** to understand data structure
2. Create filters and saved searches
3. Build visualizations in **Lens**
4. Combine into **Dashboard**
5. Share and collaborate

**Monitoring Workflow:**
1. Set up **Dashboard** with key metrics
2. Configure **Alerts** for anomalies
3. Use **APM** for application deep-dive
4. Create **Canvas** reports for executives
5. Schedule automated **Reports**

**Investigation Workflow:**
1. Receive alert or notice issue
2. Jump to relevant **Dashboard**
3. Apply time filters to incident period
4. Drill down with **Discover**
5. Create **Case** for tracking (if security-related)

### Quick Navigation Tips

**Speed Navigation:**
- Use browser bookmarks for frequently accessed dashboards
- Pin important filters to persist across sessions
- Leverage "Recently Viewed" in sidebar
- Use global search instead of clicking through menus

**Context Preservation:**
- Filters and time ranges persist when switching between related apps
- Use "Open in new tab" for comparison workflows
- Browser back/forward buttons work intuitively
- Bookmark specific filtered views

## 🔗 Next Steps

Now that you understand the interface:

1. **Connect to Data** → [Data Views & Index Patterns](../02-data-views-discovery/data-views-index-patterns.md)
2. **Explore Data** → [Discover Application](../02-data-views-discovery/discover-application.md)
3. **Create Visualizations** → [Kibana Lens Basics](../03-visualization-fundamentals/kibana-lens-basics.md)

## 📚 Quick Reference Card

### Essential Interface Elements

```
Navigation Hierarchy:
Global Header > Application > Space > Content

Key Areas:
├── Application Launcher (☰ top left)
├── Global Search (🔍 top center)  
├── User Menu (👤 top right)
├── Sidebar (collapsible left)
├── Time Picker (⏰ top right)
├── Filter Bar (below header)
└── Main Content (center)

Common Actions:
├── Click to select/open
├── Drag to move/configure
├── Right-click for context menus
├── Double-click to edit
└── Hover for tooltips
```

Mastering Kibana's interface will significantly speed up your data analysis workflows. The modern design prioritizes efficiency while maintaining powerful functionality at your fingertips!