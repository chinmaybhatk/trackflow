(() => {
  'use strict'

  console.log('TrackFlow CRM Navigation Hook: Initializing...')

  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTrackFlow)
  } else {
    initTrackFlow()
  }

  function initTrackFlow() {
    // Detect if we're in CRM or standard Frappe
    const isCRM = window.location.pathname.startsWith('/crm') ||
                  window.location.hostname.includes('crm') ||
                  document.querySelector('[data-v-app]') // Vue app indicator

    console.log('TrackFlow: Environment detected -', isCRM ? 'CRM Vue Frontend' : 'Standard Frappe Desk')

    if (isCRM) {
      // For CRM, wait longer for Vue to mount and use multiple retry strategies
      let attempts = 0
      const maxAttempts = 20

      const tryAddNav = () => {
        attempts++
        console.log(`TrackFlow: Attempt ${attempts}/${maxAttempts} to add CRM navigation...`)

        if (addTrackFlowNavToCRM()) {
          console.log('TrackFlow: Successfully added to CRM navigation!')
        } else if (attempts < maxAttempts) {
          setTimeout(tryAddNav, 500)
        } else {
          console.warn('TrackFlow: Failed to add CRM navigation after', maxAttempts, 'attempts')
          console.log('TrackFlow: Available sidebar elements:', {
            navigation: document.querySelector('[role="navigation"]'),
            sidebar: document.querySelector('.sidebar'),
            aside: document.querySelector('aside'),
            allNavs: document.querySelectorAll('nav').length,
            allAsides: document.querySelectorAll('aside').length
          })
        }
      }

      tryAddNav()
    } else {
      // For standard Frappe, use original timing
      setTimeout(addTrackFlowNav, 2000)
    }
  }

  function addTrackFlowNavToCRM() {
    // Check if already added
    if (document.querySelector('[data-trackflow-nav]')) {
      return true
    }

    // Multiple strategies to find CRM sidebar
    const strategies = [
      // Strategy 1: Look for CRM-specific sidebar container
      () => document.querySelector('aside.flex.flex-col'),
      // Strategy 2: Look for navigation role
      () => document.querySelector('[role="navigation"]'),
      // Strategy 3: Look for sidebar class
      () => document.querySelector('.sidebar'),
      // Strategy 4: Look for aside element
      () => document.querySelector('aside'),
      // Strategy 5: Look for nav inside Vue app
      () => {
        const vueApp = document.querySelector('[data-v-app]') || document.querySelector('#app')
        return vueApp ? vueApp.querySelector('nav, aside') : null
      }
    ]

    let sidebar = null
    for (const strategy of strategies) {
      sidebar = strategy()
      if (sidebar) {
        console.log('TrackFlow: Found sidebar using strategy', strategies.indexOf(strategy) + 1)
        break
      }
    }

    if (!sidebar) {
      return false
    }

    // Create the navigation item
    const navItem = createNavItem()

    // Find where to insert - try multiple patterns
    const insertionPatterns = [
      // Pattern 1: After "Deals" link
      () => {
        const dealsLink = Array.from(sidebar.querySelectorAll('a'))
          .find(a => a.textContent.trim() === 'Deals')
        return dealsLink
      },
      // Pattern 2: After "Call Logs" link (shown in screenshot)
      () => {
        const callLogsLink = Array.from(sidebar.querySelectorAll('a'))
          .find(a => a.textContent.includes('Call Logs'))
        return callLogsLink
      },
      // Pattern 3: Find last navigation item
      () => {
        const allLinks = sidebar.querySelectorAll('a')
        return allLinks[allLinks.length - 1]
      }
    ]

    let insertAfter = null
    for (const pattern of insertionPatterns) {
      insertAfter = pattern()
      if (insertAfter) {
        console.log('TrackFlow: Found insertion point using pattern', insertionPatterns.indexOf(pattern) + 1)
        break
      }
    }

    if (insertAfter) {
      insertAfter.parentElement.insertAdjacentElement('afterend', navItem)
      return true
    }

    // Fallback: append to the nav container
    const navContainer = sidebar.querySelector('nav') || sidebar
    if (navContainer) {
      navContainer.appendChild(navItem)
      console.log('TrackFlow: Added using fallback append method')
      return true
    }

    return false
  }

  function addTrackFlowNav() {
    // Original method for standard Frappe Desk
    const sidebar = document.querySelector('[role="navigation"]') ||
                    document.querySelector('.sidebar') ||
                    document.querySelector('aside')

    if (!sidebar) {
      console.log('TrackFlow: Standard Frappe sidebar not found, retrying...')
      setTimeout(addTrackFlowNav, 1000)
      return
    }

    // Check if already added
    if (document.querySelector('[data-trackflow-nav]')) {
      return
    }

    console.log('TrackFlow: Adding to standard Frappe navigation...')

    const navItem = createNavItem()

    // Find where to insert
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

    console.log('TrackFlow: Added to standard Frappe navigation successfully!')
  }

  function createNavItem() {
    // Try to match existing navigation item styling
    const existingNavItem = document.querySelector('aside a[href], nav a[href]')
    let baseClasses = 'flex items-center gap-2 rounded px-3 py-2 text-sm transition-colors'

    if (existingNavItem) {
      // Copy classes from existing nav items
      const classes = existingNavItem.className
      if (classes) {
        baseClasses = classes
        console.log('TrackFlow: Copied classes from existing nav item:', classes)
      }
    }

    const item = document.createElement('a')
    item.href = '/app/trackflow-dashboard'
    item.className = baseClasses
    item.setAttribute('data-trackflow-nav', 'true')

    // Create icon (matching Lucide icon style in CRM)
    const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg')
    icon.setAttribute('width', '20')
    icon.setAttribute('height', '20')
    icon.setAttribute('viewBox', '0 0 24 24')
    icon.setAttribute('fill', 'none')
    icon.setAttribute('stroke', 'currentColor')
    icon.setAttribute('stroke-width', '2')
    icon.setAttribute('stroke-linecap', 'round')
    icon.setAttribute('stroke-linejoin', 'round')
    icon.classList.add('lucide', 'lucide-trending-up')

    const polyline1 = document.createElementNS('http://www.w3.org/2000/svg', 'polyline')
    polyline1.setAttribute('points', '23 6 13.5 15.5 8.5 10.5 1 18')
    const polyline2 = document.createElementNS('http://www.w3.org/2000/svg', 'polyline')
    polyline2.setAttribute('points', '17 6 23 6 23 12')

    icon.appendChild(polyline1)
    icon.appendChild(polyline2)

    const span = document.createElement('span')
    span.textContent = 'TrackFlow'

    item.appendChild(icon)
    item.appendChild(span)

    // Add inline styles as fallback
    item.style.cssText = `
      color: #4b5563;
      text-decoration: none;
      transition: all 0.2s;
      cursor: pointer;
    `

    // Add hover effects
    item.addEventListener('mouseenter', function() {
      this.style.backgroundColor = '#f3f4f6'
      this.style.color = '#1f2937'
    })

    item.addEventListener('mouseleave', function() {
      this.style.backgroundColor = 'transparent'
      this.style.color = '#4b5563'
    })

    // Highlight when active
    if (window.location.pathname.includes('/trackflow')) {
      item.style.backgroundColor = '#eff6ff'
      item.style.color = '#2563eb'
      item.setAttribute('aria-current', 'page')
    }

    return item
  }

  // Watch for route changes (for SPAs)
  const observer = new MutationObserver(() => {
    const hasTrackFlowNav = document.querySelector('[data-trackflow-nav]')
    if (!hasTrackFlowNav) {
      addTrackFlowNav()
    } else {
      // Update active state on route change
      const navItem = document.querySelector('[data-trackflow-nav]')
      if (navItem) {
        if (window.location.pathname.includes('/trackflow')) {
          navItem.style.backgroundColor = '#eff6ff'
          navItem.style.color = '#2563eb'
        } else {
          navItem.style.backgroundColor = 'transparent'
          navItem.style.color = '#4b5563'
        }
      }
    }
  })

  observer.observe(document.body, {
    childList: true,
    subtree: true
  })
})()
