import * as React from "react"

const DropdownMenu = ({ children }: { children: React.ReactNode }) => {
  const [isOpen, setIsOpen] = React.useState(false)
  
  return (
    <div className="relative inline-block text-left">
      {React.Children.map(children, child => {
        if (React.isValidElement(child)) {
          if (child.type === DropdownMenuTrigger) {
            const originalOnClick = child.props.onClick
            return React.cloneElement(child, { 
              onClick: (e: React.MouseEvent) => {
                // Call the original onClick first (for stopPropagation, etc.)
                if (originalOnClick) {
                  originalOnClick(e)
                }
                // Then toggle the dropdown
                setIsOpen(!isOpen)
              }
            })
          }
          if (child.type === DropdownMenuContent) {
            return isOpen ? React.cloneElement(child, { onClose: () => setIsOpen(false) }) : null
          }
        }
        return child
      })}
    </div>
  )
}

const DropdownMenuTrigger = ({ children, onClick, ...props }: any) => (
  <button onClick={onClick} {...props}>
    {children}
  </button>
)

const DropdownMenuContent = ({ children, onClose }: any) => {
  React.useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as HTMLElement
      if (!target.closest('.dropdown-content')) {
        onClose()
      }
    }
    
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [onClose])

  return (
    <div className="dropdown-content absolute right-0 z-10 mt-2 w-48 origin-top-right rounded-md bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none">
      <div className="py-1" role="menu">
        {children}
      </div>
    </div>
  )
}

const DropdownMenuItem = ({ children, onClick, className = "", ...props }: any) => (
  <button
    className={`flex items-center w-full px-4 py-2 text-left text-sm text-gray-700 hover:bg-gray-100 hover:text-gray-900 ${className}`}
    role="menuitem"
    onClick={onClick}
    {...props}
  >
    {children}
  </button>
)

export { DropdownMenu, DropdownMenuTrigger, DropdownMenuContent, DropdownMenuItem }