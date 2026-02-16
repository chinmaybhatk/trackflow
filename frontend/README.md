# TrackFlow Frontend Override

This directory contains Vue.js components that override Frappe CRM's frontend to add TrackFlow navigation.

## How It Works

1. **Component Override**: The `Sidebar.vue` file overrides CRM's default sidebar to include TrackFlow navigation
2. **Build Process**: Vite builds these components and outputs them to `trackflow/public/dist/`
3. **Frappe Integration**: The `app_override_files` hook in `hooks.py` tells Frappe to use TrackFlow's components instead of CRM's

## Setup

### Prerequisites
- Node.js 16+ and Yarn installed
- Frappe CRM installed in the same bench

### Installation

```bash
cd ~/frappe-bench/apps/trackflow/frontend
yarn install
```

### Development

```bash
# Watch mode - auto-rebuild on changes
yarn dev

# Or build once
yarn build
```

### Production Build

```bash
yarn build
cd ~/frappe-bench
bench build --app trackflow
bench restart
```

## File Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── Layouts/
│   │       └── Sidebar.vue          # Overrides CRM sidebar
│   ├── views/
│   │   └── TrackFlow/
│   │       └── Dashboard.vue        # TrackFlow dashboard view
│   └── router/
│       └── index.js                 # TrackFlow routes (if needed)
├── package.json                      # Dependencies
├── vite.config.js                    # Build configuration
└── README.md                         # This file
```

## How Override Works

### In hooks.py:

```python
app_override_files = {
    "crm": {
        "frontend/src/components/Layouts/Sidebar.vue": "frontend/src/components/Layouts/Sidebar.vue"
    }
}
```

This tells Frappe: "When CRM tries to load `Sidebar.vue`, use TrackFlow's version instead"

### Build Output

The built files go to `trackflow/public/dist/` and are served by Frappe.

## Frappe Cloud Deployment

For Frappe Cloud, you need a build script:

Create `.frappe_cloud/build.sh`:

```bash
#!/bin/bash
cd apps/trackflow/frontend
yarn install
yarn build
```

Then in Frappe Cloud settings:
1. Enable "Rebuild Assets"
2. Deploy

## Troubleshooting

### Components not loading

1. Check if files are built:
   ```bash
   ls ~/frappe-bench/apps/trackflow/trackflow/public/dist/
   ```

2. Rebuild:
   ```bash
   cd ~/frappe-bench/apps/trackflow/frontend
   yarn build
   cd ~/frappe-bench
   bench clear-cache
   bench restart
   ```

### Sidebar not showing TrackFlow

1. Check browser console for errors
2. Verify CRM is installed: `bench --site your-site list-apps | grep crm`
3. Check if override is registered: Look for TrackFlow in CRM sidebar
4. Verify bootinfo includes TrackFlow: Check browser devtools → Application → Local Storage

### Build errors

1. Ensure Node.js version: `node --version` (should be 16+)
2. Clear node_modules: `rm -rf node_modules && yarn install`
3. Check vite.config.js paths are correct

## Alternative: JavaScript Injection

If the override approach doesn't work, the JavaScript injection method (`crm_navigation_hook.js`) is still active as a fallback, though it's less reliable.

## Notes

- The override approach is **the proper way** to extend CRM
- JavaScript injection is a **workaround** with limitations
- For production, always use component override
- Keep this frontend in sync with CRM version updates

## References

- [Frappe App Override Docs](https://frappeframework.com/docs)
- [Vue 3 Documentation](https://vuejs.org/)
- [Vite Documentation](https://vitejs.dev/)
