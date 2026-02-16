# Setup TrackFlow Navigation in Frappe CRM

## You're Right - TrackFlow CAN Override CRM! 🎉

Since TrackFlow is already a custom Frappe app, it can override CRM's frontend components. Here's how:

## Quick Setup (Local Development)

```bash
# 1. Navigate to TrackFlow frontend
cd ~/frappe-bench/apps/trackflow/frontend

# 2. Install dependencies
yarn install

# 3. Build the frontend
yarn build

# 4. Restart Frappe
cd ~/frappe-bench
bench restart

# 5. Clear browser cache and refresh CRM
```

## How It Works

### The Magic: `app_override_files` Hook

In `trackflow/hooks.py`:

```python
app_override_files = {
    "crm": {
        "frontend/src/components/Layouts/Sidebar.vue": "frontend/src/components/Layouts/Sidebar.vue"
    }
}
```

This tells Frappe: **"When CRM needs Sidebar.vue, use TrackFlow's version instead!"**

### What Gets Overridden

- **CRM's Sidebar.vue** → **TrackFlow's Sidebar.vue** (with TrackFlow navigation added)

### The Build Process

1. **Vue Components** (`frontend/src/`) → Built by Vite
2. **Output** → `trackflow/public/dist/`
3. **Frappe** → Serves TrackFlow's built files
4. **CRM** → Uses TrackFlow's Sidebar instead of its own

## Frappe Cloud Deployment

### Automatic Build

The `.frappe_cloud/build.sh` script will:
1. Install Node dependencies
2. Build Vue components
3. Output to public/dist/

### Enable in Frappe Cloud

1. Go to your site settings
2. Enable **"Rebuild Assets"**
3. Deploy
4. The build script runs automatically

## File Structure

```
trackflow/
├── frontend/                         # NEW: Frontend override
│   ├── src/
│   │   ├── components/
│   │   │   └── Layouts/
│   │   │       └── Sidebar.vue      # Overrides CRM sidebar
│   │   └── views/
│   │       └── TrackFlow/
│   │           └── Dashboard.vue     # TrackFlow views
│   ├── package.json                  # Vue dependencies
│   ├── vite.config.js                # Build config
│   └── README.md
├── trackflow/
│   ├── hooks.py                      # UPDATED: Override config
│   ├── boot.py                       # UPDATED: Bootinfo injection
│   └── public/
│       ├── js/
│       │   └── crm_navigation_hook.js # Fallback (if override fails)
│       └── dist/                      # Build output (auto-generated)
└── .frappe_cloud/
    └── build.sh                       # Cloud build script
```

## Verification

### 1. Check Build Output

```bash
ls -la ~/frappe-bench/apps/trackflow/trackflow/public/dist/
```

You should see built JavaScript files.

### 2. Check Browser Console

Open CRM → DevTools → Console

Look for:
- No Vue errors
- TrackFlow component loaded
- Navigation rendered

### 3. Check Bootinfo

DevTools → Console:
```javascript
console.log(frappe.boot.crm_navigation_items)
```

Should show TrackFlow navigation item.

## Troubleshooting

### "TrackFlow still not showing in CRM"

**Option 1: Rebuild Everything**
```bash
cd ~/frappe-bench/apps/trackflow/frontend
rm -rf node_modules dist
yarn install
yarn build
cd ~/frappe-bench
bench build --app trackflow
bench clear-cache
bench restart
```

**Option 2: Check CRM is installed**
```bash
bench --site your-site list-apps | grep -E "(crm|trackflow)"
```

Both should be listed.

**Option 3: Verify Override Hook**

Check `trackflow/hooks.py` has:
- `app_override_files` defined
- `extend_bootinfo` enabled
- `build_apps = ["trackflow"]`

### "Build failing"

**Check Node version:**
```bash
node --version  # Should be 16+
```

**Check dependencies:**
```bash
cd frontend
yarn install --check-files
```

**Check paths in vite.config.js:**
- Verify CRM path points to correct location
- Adjust if your bench structure is different

### "Components not updating"

After making changes to Vue files:
```bash
cd frontend
yarn build
cd ../..
bench restart
```

Hard refresh browser (Ctrl+Shift+R)

## Development Workflow

### Watch Mode (Auto-rebuild)

```bash
cd ~/frappe-bench/apps/trackflow/frontend
yarn dev
```

This watches for changes and rebuilds automatically.

### Testing Changes

1. Edit `frontend/src/components/Layouts/Sidebar.vue`
2. Save (auto-rebuilds if in watch mode)
3. Refresh browser
4. Check changes

## Why This is Better Than JavaScript Injection

| Aspect | JavaScript Injection | Component Override |
|--------|---------------------|-------------------|
| **Reliability** | ❌ Unreliable (Vue can remove) | ✅ Proper Vue integration |
| **Performance** | ⚠️ Timing issues | ✅ Native rendering |
| **Maintenance** | ❌ Fragile | ✅ Stable |
| **Router Integration** | ❌ No | ✅ Yes |
| **Hot Module Reload** | ❌ No | ✅ Yes (in dev) |
| **Type Safety** | ❌ No | ✅ Vue TypeScript support |

## Next Steps

After setup, you can:

1. **Add more routes** in `Sidebar.vue`
2. **Create sub-menus** for TrackFlow sections
3. **Add badges** (e.g., "5 new clicks")
4. **Customize styling** to match your brand
5. **Add permissions** to control visibility

## Support

If you encounter issues:

1. Check `frontend/README.md` for detailed troubleshooting
2. Review browser console for errors
3. Check Frappe logs: `bench logs`
4. Verify build output exists

## Summary

✅ TrackFlow **CAN** override CRM components (it's a custom app!)
✅ Proper Vue component override is now implemented
✅ JavaScript injection is kept as fallback
✅ Frappe Cloud build script is ready
✅ Development workflow is set up

**Just run `cd frontend && yarn install && yarn build` and you're done!** 🚀
