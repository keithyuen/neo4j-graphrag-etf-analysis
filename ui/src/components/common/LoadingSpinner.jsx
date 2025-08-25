import clsx from 'clsx'

function LoadingSpinner({ 
  size = 'md', 
  color = 'primary', 
  className = '', 
  label = 'Loading...' 
}) {
  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-6 h-6',
    lg: 'w-8 h-8',
    xl: 'w-12 h-12'
  }
  
  const colorClasses = {
    primary: 'text-primary-600',
    white: 'text-white',
    gray: 'text-gray-600',
    green: 'text-green-600',
    red: 'text-red-600'
  }
  
  return (
    <div className={clsx('flex items-center justify-center', className)}>
      <div
        className={clsx(
          'loading-spinner',
          sizeClasses[size],
          colorClasses[color]
        )}
        role="status"
        aria-label={label}
      />
      {label && (
        <span className="ml-2 text-sm text-gray-600">
          {label}
        </span>
      )}
    </div>
  )
}

export default LoadingSpinner