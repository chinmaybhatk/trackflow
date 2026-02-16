# Step-by-Step Implementation Guide

This guide provides the exact steps to add TrackFlow to Frappe CRM's left navigation bar.

## Prerequisites

- Frappe CRM installed and working
- TrackFlow app installed
- Node.js and Yarn installed
- Access to the bench directory

## Method 1: Full Vue.js Integration (Recommended)

### Step 1: Access Frappe CRM Frontend

```bash
cd ~/frappe-bench/apps/crm
ls frontend/
```

If the frontend directory doesn't exist, you may need to clone the CRM repository or update it.

### Step 2: Install Frontend Dependencies

```bash
cd frontend
yarn install
```

### Step 3: Modify the Sidebar Component

**Location:** `frontend/src/components/Layouts/Sidebar.vue`

Find the navigation items section and add TrackFlow:

```vue
<!-- Before (example) -->
<SidebarItem to="/deals" icon="DollarSign" label="Deals" />
<SidebarItem to="/organizations" icon="Building2" label="Organizations" />

<!-- After - Add TrackFlow -->
<SidebarItem to="/deals" icon="DollarSign" label="Deals" />
<SidebarItem to="/organizations" icon="Building2" label="Organizations" />

<!-- TrackFlow Section -->
<div class="mt-4 pt-4 border-t border-gray-200">
  <div class="px-3 mb-2">
    <span class="text-xs font-semibold text-gray-500 uppercase">Marketing</span>
  </div>
  <SidebarItem to="/trackflow" icon="TrendingUp" label="TrackFlow" />
</div>
```

**Alternative:** Use the provided `Sidebar.vue` file from the implementation folder.

```bash
# Backup original
cp frontend/src/components/Layouts/Sidebar.vue frontend/src/components/Layouts/Sidebar.vue.backup

# Copy new version
cp /path/to/implementation/Sidebar.vue frontend/src/components/Layouts/Sidebar.vue
```

### Step 4: Add Routes

**Location:** `frontend/src/router/index.js`

Add the TrackFlow routes:

```javascript
// Import at the top
import TrackFlowDashboard from '@/views/TrackFlow/Dashboard.vue'

// Add to routes array
const routes = [
  // ... existing routes
  {
    path: '/trackflow',
    name: 'TrackFlow',
    component: TrackFlowDashboard,
    meta: {
      requiresAuth: true,
      title: 'TrackFlow'
    }
  }
]
```

### Step 5: Create Vue Components

Create the directory structure:

```bash
cd frontend/src/views
mkdir -p TrackFlow/components
```

Copy the dashboard component:

```bash
cp /path/to/implementation/TrackFlowDashboard.vue frontend/src/views/TrackFlow/Dashboard.vue
```

### Step 6: Build the Frontend

```bash
cd ~/frappe-bench/apps/crm/frontend
yarn build

# Watch for development
yarn dev
```

### Step 7: Restart Bench

```bash
cd ~/frappe-bench
bench restart
```

### Step 8: Test

1. Open your CRM in browser
2. Clear browser cache (Ctrl+Shift+R)
3. Check left sidebar for "TrackFlow" item
4. Click on it to navigate

## Method 2: JavaScript Hook (Quick & Dirty)

This method injects the navigation item using JavaScript without modifying CRM frontend.

### Step 1: Create Navigation Script

In your TrackFlow app, create:

`trackflow/public/js/crm_navigation_hook.js`

```javascript
(() => {
  'use strict'

  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTrackFlow)
  } else {
    initTrackFlow()
  }

  function initTrackFlow() {
    // Wait for Vue app to mount
    setTimeout(addTrackFlowNav, 2000)
  }

  function addTrackFlowNav() {
    // Try to find the sidebar
    const sidebar = document.querySelector('[role="navigation"]') ||
                    document.querySelector('.sidebar') ||
                    document.querySelector('aside')

    if (!sidebar) {
      console.log('Sidebar not found, retrying...')
      setTimeout(addTrackFlowNav, 1000)
      return
    }

    // Check if already added
    if (document.querySelector('[data-trackflow-nav]')) {
      return
    }

    console.log('Adding TrackFlow navigation...')

    // Create the navigation item
    const navItem = createNavItem()

    // Find where to insert (after "Deals" or at end)
    const dealsLink = Array.from(sidebar.querySelectorAll('a'))
      .find(a => a.textContent.includes('Deals'))

    if (dealsLink && dealsLink.parentElement) {
      dealsLink.parentElement.insertAdjacentElement('afterend', navItem)
    } else {
      const navList = sidebar.querySelector('nav, ul')
      if (navList) {
        navList.appendChild(navItem)
      }
    }

    console.log('TrackFlow navigation added!')
  }

  function createNavItem() {
    const item = document.createElement('a')
    item.href = '/app/trackflow-dashboard'
    item.className = 'sidebar-item'
    item.setAttribute('data-trackflow-nav', 'true')

    item.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
        <polyline points="17 6 23 6 23 12"></polyline>
      </svg>
      <span>TrackFlow</span>
    `

    // Add styles inline
    item.style.cssText = `
      display: flex;
      align-items: center;
      gap: 0.75rem;
      padding: 0.75rem 1rem;
      color: #4b5563;
      text-decoration: none;
      border-radius: 0.375rem;
      transition: all 0.2s;
    `

    item.addEventListener('mouseenter', function() {
      this.style.backgroundColor = '#f3f4f6'
      this.style.color = '#1f2937'
    })

    item.addEventListener('mouseleave', function() {
      this.style.backgroundColor = 'transparent'
      this.style.color = '#4b5563'
    })

    return item
  }

  // Watch for route changes (for SPAs)
  const observer = new MutationObserver((mutations) => {
    const hasTrackFlowNav = document.querySelector('[data-trackflow-nav]')
    if (!hasTrackFlowNav) {
      addTrackFlowNav()
    }
  })

  observer.observe(document.body, {
    childList: true,
    subtree: true
  })
})()
```

### Step 2: Include in Hooks

Edit `trackflow/hooks.py`:

```python
app_include_js = [
    "/assets/trackflow/js/crm_navigation_hook.js"
]
```

### Step 3: Build and Deploy

```bash
cd ~/frappe-bench

# Build the app
bench build --app trackflow

# Clear cache
bench clear-cache
bench clear-website-cache

# Restart
bench restart
```

### Step 4: Test

1. Open CRM in browser
2. Hard refresh (Ctrl+Shift+R)
3. Wait 2-3 seconds for script to load
4. Check sidebar for TrackFlow item

## Method 3: Frappe Workspace (Fallback)

If the above methods don't work, use Frappe's native workspace feature.

### Step 1: Create Workspace JSON

Create file: `trackflow/trackflow/workspace/trackflow/trackflow.json`

```json
{
  "name": "TrackFlow",
  "title": "TrackFlow",
  "icon": "trending-up",
  "module": "TrackFlow",
  "app": "trackflow",
  "category": "Modules",
  "extends_another_page": 0,
  "public": 1,
  "shortcuts": [
    {
      "type": "Page",
      "label": "Dashboard",
      "link_to": "trackflow-dashboard",
      "color": "blue"
    },
    {
      "type": "DocType",
      "label": "Campaigns",
      "link_to": "Link Campaign",
      "color": "green"
    }
  ]
}
```

### Step 2: Migrate

```bash
bench --site your-site migrate
bench restart
```

### Step 3: Access

The workspace will appear in Frappe Desk (not CRM's custom UI).

## Troubleshooting

### Navigation Not Appearing

**Issue:** TrackFlow item not showing in sidebar

**Solutions:**
1. Clear browser cache completely
2. Check browser console for JavaScript errors
3. Verify CRM frontend was rebuilt
4. Check that TrackFlow app is installed: `bench --site your-site list-apps`

### Clicking Does Nothing

**Issue:** Navigation item appears but doesn't work

**Solutions:**
1. Verify the route exists in router config
2. Check that the TrackFlow page exists: Navigate directly to `/app/trackflow-dashboard`
3. Look for 404 errors in browser console

### Styling Issues

**Issue:** Navigation item looks wrong

**Solutions:**
1. Inspect the element to see applied styles
2. Match the class names with existing sidebar items
3. Use browser DevTools to adjust styles
4. Add custom CSS in `trackflow/public/css/trackflow.css`

### Icons Not Showing

**Issue:** Icon missing or showing as box

**Solutions:**
1. Use Lucide icon names (CRM uses Lucide)
2. Check icon name is correct: `TrendingUp` not `trending-up`
3. Fallback to SVG if icon library unavailable

### Method 2 Script Not Running

**Issue:** JavaScript hook not executing

**Solutions:**
1. Check script is included: View page source, search for `crm_navigation_hook.js`
2. Check console for errors
3. Increase setTimeout delays if CRM loads slowly
4. Verify `app_include_js` in hooks.py is correct

## Verification Checklist

- [ ] Frappe CRM is installed and running
- [ ] TrackFlow app is installed
- [ ] Frontend dependencies installed (`yarn install`)
- [ ] Sidebar.vue modified or script added
- [ ] Routes added to router config
- [ ] Frontend built (`yarn build`)
- [ ] Bench restarted
- [ ] Browser cache cleared
- [ ] Navigation item visible in sidebar
- [ ] Navigation item is clickable
- [ ] TrackFlow page loads correctly

## Next Steps

After successfully adding navigation:

1. **Create Additional Views**: Add Campaigns, Links, Analytics views
2. **Add Submenus**: Implement collapsible submenu for TrackFlow
3. **Add Badges**: Show notification counts (e.g., "5 new clicks")
4. **Customize Icons**: Use custom SVG icons
5. **Add Permissions**: Control who can see TrackFlow nav

## Resources

- [Frappe CRM GitHub](https://github.com/frappe/crm)
- [Vue Router Docs](https://router.vuejs.org/)
- [Lucide Icons](https://lucide.dev/icons/)
- [Frappe Forum](https://discuss.frappe.io/)

## Need Help?

If you're still stuck:

1. **Check Reddit Thread**: Look for the specific Reddit post you mentioned
2. **Post on Forum**: [discuss.frappe.io](https://discuss.frappe.io)
3. **GitHub Issues**: Check CRM repo issues for similar problems
4. **Contact Me**: chinmaybhatk@gmail.com

---

**Pro Tip:** For development, use `yarn dev` in the CRM frontend directory to see changes instantly without rebuilding.
