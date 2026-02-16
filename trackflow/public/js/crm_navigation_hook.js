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
      console.log('CRM Sidebar not found, retrying...')
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

    console.log('TrackFlow navigation added successfully!')
  }

  function createNavItem() {
    const item = document.createElement('a')
    item.href = '/app/trackflow-dashboard'
    item.className = 'sidebar-item flex items-center gap-3 rounded px-3 py-2 text-sm font-medium transition-colors'
    item.setAttribute('data-trackflow-nav', 'true')

    item.innerHTML = `
      <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"
           class="lucide lucide-trending-up">
        <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"></polyline>
        <polyline points="17 6 23 6 23 12"></polyline>
      </svg>
      <span>TrackFlow</span>
    `

    // Add styles inline
    item.style.cssText = `
      color: #4b5563;
      text-decoration: none;
      transition: all 0.2s;
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
