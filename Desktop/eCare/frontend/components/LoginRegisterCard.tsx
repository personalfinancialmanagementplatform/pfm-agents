
interface LoginRegisterCardProps {
    title: string
    subtitle?: string
    children: React.ReactNode
    footer?: React.ReactNode
    className?: string
  }
  
  const LoginRegisterCard = ({
    title,
    subtitle,
    children,
    footer,
    className = "",
  }: LoginRegisterCardProps) => {
    return (
      <div className={`bg-white p-8 rounded-xl shadow-md w-full max-w-md ${className}`}>
        <h2 className="text-2xl font-bold mb-2 text-center text-blue-700">{title}</h2>
        {subtitle && <p className="text-sm text-gray-500 mb-6 text-center">{subtitle}</p>}
        <div>{children}</div>
        {footer && <div className="mt-6 text-sm text-center text-gray-600">{footer}</div>}
      </div>
    )
  }
  
  export default LoginRegisterCard
  