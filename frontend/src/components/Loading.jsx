export default function Loading({ text = 'Loading...' }) {
  return (
    <div className="flex items-center gap-3 text-slate-400 py-12 justify-center">
      <div className="w-5 h-5 border-2 border-cyan-500 border-t-transparent rounded-full animate-spin" />
      <span className="text-sm">{text}</span>
    </div>
  )
}
