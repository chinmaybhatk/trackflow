# Adding TrackFlow Tab to Frappe CRM Navigation

## Overview
This guide demonstrates how to add a "TrackFlow" tab to the left navigation bar in Frappe CRM. The challenge with Frappe CRM's Vue.js frontend is that it requires custom modifications to the CRM's frontend code.

## Understanding the Architecture

Frappe CRM uses a Vue.js frontend (separate from the Frappe Framework backend). The navigation is defined in the CRM's frontend codebase, not in the backend app.

**Key Points:**
- Frappe CRM frontend: Vue 3 + Vite
- Navigation is rendered from Vue components
- Custom apps like TrackFlow need frontend modifications to add navigation items

## Solution Approach

There are **two main approaches** to add TrackFlow to the CRM navigation:

### Approach 1: Frappe CRM Frontend Modification (Recommended)

This involves modifying the Frappe CRM frontend repository.

#### Step 1: Clone Frappe CRM Frontend

```bash
cd ~/frappe-bench/apps
git clone https://github.com/frappe/crm.git
cd crm/frontend
```

#### Step 2: Locate Navigation Configuration

The navigation is typically defined in:
```
frontend/src/components/Layout/Sidebar.vue
# OR
frontend/src/router/index.js
# OR
frontend/src/App.vue
```

#### Step 3: Add TrackFlow Navigation Item

Find the navigation items array and add TrackFlow:

```javascript
// In Sidebar.vue or similar component
const navigationItems = [
  {
    label: 'Leads',
    icon: 'Users',
    route: '/leads'
  },
  {
    label: 'Deals',
    icon: 'DollarSign',
    route: '/deals'
  },
  {
    label: 'TrackFlow',
    icon: 'TrendingUp',
    route: '/trackflow'
  },
  // ... other items
]
```

#### Step 4: Create TrackFlow Route

Add the route in `frontend/src/router/index.js`:

```javascript
{
  path: '/trackflow',
  name: 'TrackFlow',
  component: () => import('../views/TrackFlow/Dashboard.vue'),
  meta: {
    requiresAuth: true
  }
}
```

#### Step 5: Create TrackFlow Vue Component

Create `frontend/src/views/TrackFlow/Dashboard.vue`:

```vue
<template>
  <div class="trackflow-dashboard">
    <h1>TrackFlow Analytics</h1>
    <!-- Embed your Frappe page or create custom Vue components -->
    <iframe
      :src="`${frappe.base_url}/app/trackflow-dashboard`"
      style="width: 100%; height: calc(100vh - 120px); border: none;"
    />
  </div>
</template>

<script setup>
import { inject } from 'vue'

const frappe = inject('$frappe')
</script>

<style scoped>
.trackflow-dashboard {
  padding: 20px;
}
</style>
```

#### Step 6: Build Frontend

```bash
cd ~/frappe-bench/apps/crm/frontend
yarn install
yarn build

# Restart bench
cd ~/frappe-bench
bench restart
```

### Approach 2: Using Frappe Page with Custom Hook (Simpler)

If you want to avoid modifying CRM frontend, you can use a custom hook to inject navigation via JavaScript.

#### Step 1: Create Custom JS File

In your TrackFlow app, create:
`trackflow/public/js/trackflow_navigation.js`

```javascript
frappe.ready(function() {
  // Wait for CRM sidebar to load
  setTimeout(function() {
    addTrackFlowToNav();
  }, 1000);
});

function addTrackFlowToNav() {
  // Find the sidebar navigation
  const sidebar = document.querySelector('.sidebar-nav') ||
                  document.querySelector('[role="navigation"]');

  if (!sidebar) {
    console.warn('Sidebar not found, retrying...');
    setTimeout(addTrackFlowToNav, 1000);
    return;
  }

  // Check if TrackFlow item already exists
  if (document.querySelector('[data-nav-item="trackflow"]')) {
    return;
  }

  // Create TrackFlow navigation item
  const trackflowItem = document.createElement('a');
  trackflowItem.href = '/app/trackflow-dashboard';
  trackflowItem.className = 'nav-link sidebar-nav-item';
  trackflowItem.setAttribute('data-nav-item', 'trackflow');
  trackflowItem.innerHTML = `
    <svg class="icon icon-sm">
      <use href="#icon-trending-up"></use>
    </svg>
    <span>TrackFlow</span>
  `;

  // Insert after "Deals" or at the end
  const dealsItem = sidebar.querySelector('[data-nav-item="deals"]');
  if (dealsItem && dealsItem.parentElement) {
    dealsItem.parentElement.insertAdjacentElement('afterend', trackflowItem);
  } else {
    sidebar.appendChild(trackflowItem);
  }
}
```

#### Step 2: Include JS in hooks.py

Edit `trackflow/hooks.py`:

```python
app_include_js = [
    "/assets/trackflow/js/trackflow_navigation.js"
]

# OR for specific doctypes
doctype_js = {
    "CRM Lead": "public/js/trackflow_navigation.js"
}
```

#### Step 3: Build and Deploy

```bash
cd ~/frappe-bench
bench build --app trackflow
bench restart
```

### Approach 3: Workspace Sidebar (Native Frappe)

Use Frappe's native Workspace feature to add TrackFlow to the sidebar.

#### Step 1: Create Workspace DocType

Create `trackflow/trackflow/workspace/trackflow/trackflow.json`:

```json
{
  "name": "TrackFlow",
  "title": "TrackFlow",
  "icon": "trending-up",
  "parent_page": "",
  "public": 1,
  "is_hidden": 0,
  "extends": "CRM",
  "extends_another_page": 1,
  "charts": [],
  "shortcuts": [
    {
      "label": "TrackFlow Dashboard",
      "type": "Page",
      "link_to": "trackflow-dashboard",
      "doc_view": "",
      "color": "#4C51BF"
    },
    {
      "label": "Campaigns",
      "type": "DocType",
      "link_to": "Link Campaign",
      "doc_view": "List",
      "color": "#10B981"
    },
    {
      "label": "Tracked Links",
      "type": "DocType",
      "link_to": "Tracked Link",
      "doc_view": "List",
      "color": "#F59E0B"
    }
  ],
  "cards": [
    {
      "label": "Analytics",
      "items": [
        {
          "label": "Click Events",
          "type": "DocType",
          "link_to": "Click Event"
        },
        {
          "label": "Visitors",
          "type": "DocType",
          "link_to": "Visitor"
        },
        {
          "label": "Attribution Models",
          "type": "DocType",
          "link_to": "Attribution Model"
        }
      ]
    }
  ]
}
```

#### Step 2: Add to Frappe Desk

The workspace will automatically appear in Frappe's sidebar, but to integrate with CRM's Vue navigation, you still need Approach 1 or 2.

## Recommended Solution

**For Production:** Use **Approach 1** - Modify the CRM frontend properly. This is the cleanest and most maintainable solution.

**For Quick Testing:** Use **Approach 2** - JavaScript injection hook. This is faster but less elegant.

**For Frappe Standard:** Use **Approach 3** - Workspace, which works in standard Frappe Desk but not in CRM's custom Vue frontend.

## Testing

1. Clear cache:
   ```bash
   bench clear-cache
   bench clear-website-cache
   ```

2. Rebuild:
   ```bash
   bench build --app trackflow
   ```

3. Restart:
   ```bash
   bench restart
   ```

4. Navigate to your CRM and check the sidebar

## Troubleshooting

### Navigation Item Not Appearing

1. **Check if CRM frontend is built:**
   ```bash
   cd ~/frappe-bench/apps/crm/frontend
   ls -la dist/
   ```

2. **Check browser console for errors:**
   Open DevTools → Console tab

3. **Verify TrackFlow is installed:**
   ```bash
   bench --site your-site list-apps
   ```

### Icons Not Showing

Frappe CRM uses specific icon libraries. Check:
- Lucide icons (most common in CRM)
- Feather icons
- Custom SVG icons

Update the icon name accordingly:
```javascript
icon: 'TrendingUp'  // Lucide
icon: 'trending-up'  // Feather
```

### Route Not Working

Ensure you've created the corresponding view component or Frappe Page that matches the route.

## Additional Resources

- [Frappe CRM GitHub](https://github.com/frappe/crm)
- [Frappe Framework Docs](https://frappeframework.com/docs)
- [Vue Router Documentation](https://router.vuejs.org/)

## Need Help?

If you encounter issues:
1. Check Frappe CRM's frontend source code for navigation structure
2. Post on Frappe Forum: https://discuss.frappe.io
3. Create an issue on the TrackFlow GitHub repo

---

**Note:** The exact file paths and component names may vary depending on your Frappe CRM version. Always check the latest CRM frontend structure before making modifications.
