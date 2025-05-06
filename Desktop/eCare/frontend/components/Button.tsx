interface ButtonProps {
    label: string
    onClick: () => void
    variant?: 'solid' | 'outline'
    className?: string
  }
  
  const Button = ({
    label,
    onClick,
    variant = 'solid',
    className = '',
  }: ButtonProps) => {
    return (
      <button
        onClick={onClick}
        className={`px-6 py-2 rounded font-bold transition-colors duration-200 outline-none ${
          variant === 'solid'
            ? 'bg-[#1E40AF] text-white border-2 border-transparent hover:bg-white hover:text-[#1E40AF] hover:border-[#1E40AF]'
            : 'border-2 border-[#1E40AF] text-[#1E40AF] hover:bg-[#1E40AF] hover:text-white'
        } ${className}`}
      >
        {label}
      </button>
    )
  }
  
  export default Button
  